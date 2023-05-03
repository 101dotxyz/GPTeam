import json
import os
from ctypes import Union
from datetime import datetime, timedelta
from typing import Literal, Optional, Type, cast
from uu import Error
from uuid import UUID, uuid4

import pytz
from colorama import Fore
from langchain.output_parsers import OutputFixingParser, PydanticOutputParser
from langchain.schema import AIMessage, HumanMessage
from pydantic import BaseModel

from ..event.base import Event, EventsManager, EventType
from ..location.base import Location
from ..memory.base import MemoryType, SingleMemory
from ..tools.base import CustomTool, get_tools
from ..tools.context import ToolContext
from ..tools.name import ToolName
from ..tools.send_message import send_message
from ..utils.colors import LogColor
from ..utils.database.database import supabase
from ..utils.embeddings import get_embedding
from ..utils.formatting import print_to_console
from ..utils.model_name import ChatModelName
from ..utils.models import ChatModel
from ..utils.parameters import (
    DEFAULT_FAST_MODEL,
    DEFAULT_LOCATION_ID,
    DEFAULT_SMART_MODEL,
    DEFAULT_WORLD_ID,
    PLAN_LENGTH,
    REFLECTION_MEMORY_COUNT,
)
from ..utils.prompt import Prompter, PromptString
from ..world.context import WorldContext
from .executor import PlanExecutor, PlanExecutorResponse
from .importance import ImportanceRatingResponse
from .message import AgentMessage, LLMMessageResponse, get_latest_messages
from .plans import LLMPlanResponse, LLMSinglePlan, PlanStatus, SinglePlan
from .react import LLMReactionResponse, Reaction
from .reflection import ReflectionQuestions, ReflectionResponse


class RelatedMemory(BaseModel):
    memory: SingleMemory
    relevance: float

    def __str__(self) -> str:
        return f"SingleMemory: {self.memory.description}, Relevance: {self.relevance}"


class Agent(BaseModel):
    id: UUID
    full_name: str
    private_bio: str
    public_bio: str
    directives: Optional[list[str]]
    last_checked_events: datetime
    memories: list[SingleMemory]
    plans: list[SinglePlan]
    authorized_tools: list[ToolName]
    world_id: UUID
    notes: list[str] = []
    plan_executor: PlanExecutor = None
    context: WorldContext
    location: Location

    class Config:
        allow_underscore_names = True

    def __init__(
        self,
        full_name: str,
        private_bio: str,
        public_bio: str,
        last_checked_events: datetime,
        context: WorldContext,
        directives: list[str] = None,
        memories: list[SingleMemory] = [],
        plans: list[SinglePlan] = [],
        authorized_tools: list[ToolName] = [],
        id: Optional[str | UUID] = None,
        world_id: Optional[UUID] = DEFAULT_WORLD_ID,
        location: Location = Location.from_id(DEFAULT_LOCATION_ID),
    ):
        if id is None:
            id = uuid4()
        elif isinstance(id, str):
            id = UUID(id)

        # initialize the base model
        super().__init__(
            id=id,
            full_name=full_name,
            private_bio=private_bio,
            public_bio=public_bio,
            directives=directives,
            last_checked_events=last_checked_events,
            authorized_tools=authorized_tools,
            memories=memories,
            plans=plans,
            world_id=world_id,
            location=location,
            context=context,
        )

        # if the memories are None, retrieve them
        if memories is None or len(memories) == 0:
            self.memories = self._get_memories()

        print("\n\nAGENT INITIALIZED --------------------------\n")
        print(self)

    def __str__(self) -> str:
        private_bio = (
            self.private_bio[:100] + "..."
            if len(self.private_bio) > 100
            else self.private_bio
        )
        memories = " " + "\n ".join(
            [
                str(memory)[:100] + "..." if len(str(memory)) > 100 else str(memory)
                for memory in self.memories
            ]
        )
        plans = " " + "\n ".join([str(plan) for plan in self.plans])

        return f"{self.full_name} - {self.location.name}\nprivate_bio: {private_bio}\nDirectives: {self.directives}\n\nMemories: \n{memories}\n\nPlans: \n{plans}\n"

    @property
    def allowed_locations(self) -> list[Location]:
        """Get locations that this agent is allowed to be in."""
        data, count = (
            supabase.table("Locations")
            .select("*")
            .contains("allowed_agent_ids", [str(self.id)])
            .execute()
        )
        # For testing purposes include locations with 0 allowed agents as well
        other_data, count = (
            supabase.table("Locations")
            .select("*")
            .eq("allowed_agent_ids", "{}")
            .execute()
        )
        return [Location(**location) for location in data[1] + other_data[1]]

    @classmethod
    def from_db_dict(
        cls, agent_dict: dict, locations: list[Location], context: WorldContext
    ):
        """Create an agent from a dictionary retrieved from the database."""

        (_, plans), count = (
            supabase.table("Plans")
            .select("*")
            .in_("id", agent_dict["ordered_plan_ids"])
            .execute()
        )

        ordered_plans = sorted(
            plans, key=lambda plan: agent_dict["ordered_plan_ids"].index(plan["id"])
        )

        memories_data, memories_count = (
            supabase.table("Memories")
            .select("*")
            .eq("agent_id", str(agent_dict["id"]))
            .execute()
        )

        plans = [
            SinglePlan(
                **{key: value for key, value in plan.items() if key != "location_id"},
                location=[
                    location
                    for location in locations
                    if str(location.id) == plan["location_id"]
                ][0],
            )
            for plan in ordered_plans
        ]

        agent_location = [
            location
            for location in locations
            if str(location.id) == agent_dict["location_id"]
        ][0]

        return cls(
            id=agent_dict["id"],
            full_name=agent_dict["full_name"],
            private_bio=agent_dict["private_bio"],
            public_bio=agent_dict["public_bio"],
            directives=agent_dict["directives"],
            last_checked_events=agent_dict["last_checked_events"],
            world_id=agent_dict["world_id"],
            location=agent_location,
            context=context,
            memories=[SingleMemory(**memory) for memory in memories_data[1]],
            plans=plans,
        )

    @classmethod
    def from_id(cls, id: UUID, context: WorldContext):
        agents_data, agents_count = (
            supabase.table("Agents").select("*").eq("id", str(id)).execute()
        )
        if agents_count == 0:
            raise ValueError("No agent with that id")
        agent = agents_data[1][0]
        # get all the plans in db that are in the agent's plan list
        plans_data, plans_count = (
            supabase.table("Plans")
            .select("*")
            .in_("id", agent["ordered_plan_ids"])
            .execute()
        )
        ordered_plans_data = sorted(
            plans_data[1], key=lambda plan: agent["ordered_plan_ids"].index(plan["id"])
        )

        (_, locations_data), _ = (
            supabase.table("Locations")
            .select("*")
            .eq("world_id", agent["world_id"])
            .execute()
        )

        locations = {
            str(location["id"]): Location(
                id=location["id"],
                name=location["name"],
                description=location["description"],
                channel_id=location["channel_id"],
                available_tools=list(
                    map(lambda name: ToolName(name), location.get("available_tools"))
                ),
                world_id=location["world_id"],
                allowed_agent_ids=list(
                    map(lambda id: UUID(id), location.get("allowed_agent_ids"))
                ),
            )
            for location in locations_data
        }

        memories_data, memories_count = (
            supabase.table("Memories").select("*").eq("agent_id", str(id)).execute()
        )

        plans = [
            SinglePlan(
                **{key: value for key, value in plan.items() if key != "location_id"},
                location=locations[plan["location_id"]],
            )
            for plan in ordered_plans_data
        ]

        location = locations[agent["location_id"]]

        authorized_tools = list(
            map(lambda name: ToolName(name), agent.get("authorized_tools"))
        )

        return Agent(
            id=id,
            full_name=agent.get("full_name"),
            private_bio=agent.get("private_bio"),
            public_bio=agent.get("public_bio"),
            directives=agent.get("directives"),
            last_checked_events=agent.get("last_checked_events"),
            authorized_tools=authorized_tools,
            memories=[SingleMemory(**memory) for memory in memories_data[1]],
            plans=plans,
            world_id=agent.get("world_id"),
            location=location,
            context=context,
        )

    def _get_memories(self):
        (_, data), count = (
            supabase.table("Memories")
            .select("*")
            .eq("agent_id", str(self.id))
            .execute()
        )

        memories = [SingleMemory(**memory) for memory in data]
        return memories

    async def _add_memory(
        self,
        description: str,
        type: MemoryType = MemoryType.OBSERVATION,
        related_memory_ids: list[UUID] = [],
    ) -> SingleMemory:
        memory = SingleMemory(
            agent_id=self.id,
            type=type,
            description=description,
            importance=await self._calculate_importance(description),
            embedding=await get_embedding(description),
            related_memory_ids=related_memory_ids,
        )

        self.memories.append(memory)

        # add to database
        supabase.table("Memories").insert(memory.db_dict()).execute()

        self._log("New Memory", LogColor.MEMORY, f"{memory}")

        return memory

    def _update_agent_row(self):
        row = {
            "full_name": self.full_name,
            "private_bio": self.private_bio,
            "directives": self.directives,
            "last_checked_events": self.last_checked_events.isoformat(),
            "ordered_plan_ids": [str(plan.id) for plan in self.plans],
        }

        return supabase.table("Agents").update(row).eq("id", str(self.id)).execute()

    def _add_plan_rows(self, plans: list[SinglePlan]):
        for plan in plans:
            row = {
                "id": str(plan.id),
                "description": plan.description,
                "max_duration_hrs": plan.max_duration_hrs,
                "agent_id": str(self.id),
                "location_id": str(plan.location.id),
                "created_at": plan.created_at.isoformat(),
                "stop_condition": plan.stop_condition,
            }

            return supabase.table("Plans").upsert(row).execute()

    def _get_memories_since(self, date: datetime):
        data, count = (
            supabase.table("Memories")
            .select("*")
            .eq("agent_id", str(self.id))
            .gt("created_at", date)
            .order("created_at", desc=True)
            .execute()
        )
        memories = [SingleMemory(**memory) for memory in data[1]]
        return memories

    def _should_reflect(self) -> bool:
        """Check if the agent should reflect on their memories.
        Returns True if the cumulative importance score of memories
        since the last reflection is over 100
        """
        data, count = (
            supabase.table("Memories")
            .select("type", "created_at", "agent_id")
            .eq("agent_id", str(self.id))
            .eq("type", MemoryType.REFLECTION.value)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )

        last_reflection_time = (
            data[1][0]["created_at"] if len(data[1]) > 0 else datetime(1970, 1, 1)
        )

        memories_since_last_reflection = self._get_memories_since(last_reflection_time)

        cumulative_importance = sum(
            [memory.importance for memory in memories_since_last_reflection]
        )

        return cumulative_importance > 100

    def _db_dict(self):
        return {
            "id": str(self.id),
            "full_name": self.full_name,
            "private_bio": self.private_bio,
            "public_bio": self.public_bio,
            "directives": self.directives,
            "last_checked_events": self.last_checked_events.isoformat(),
            "ordered_plan_ids": [str(plan.id) for plan in self.plans],
            "world_id": self.world_id,
            "location_id": self.location.id,
        }

    async def _related_memories(self, query: str, k: int = 5) -> list[RelatedMemory]:
        # Calculate relevance for each memory and store it in a list of dictionaries
        memories_with_relevance = [
            RelatedMemory(memory=memory, relevance=await memory.relevance(query))
            for memory in self.memories
        ]

        # Sort the list of dictionaries based on the 'relevance' key in descending order
        sorted_memories = sorted(
            memories_with_relevance, key=lambda x: x.relevance, reverse=True
        )

        return sorted_memories[:k]

    async def _summarize_activity(self, k: int = 20) -> str:
        recent_memories = sorted(
            self.memories, key=lambda memory: memory.created_at, reverse=True
        )[:k]

        if len(recent_memories) == 0:
            return "I haven't done anything recently."

        summary_prompter = Prompter(
            PromptString.RECENT_ACTIIVITY,
            {
                "full_name": self.full_name,
                "memory_descriptions": str(
                    [memory.description for memory in recent_memories]
                ),
            },
        )

        low_temp_llm = ChatModel(DEFAULT_SMART_MODEL, temperature=0)

        response = await low_temp_llm.get_chat_completion(
            summary_prompter.prompt,
            loading_text="🤔 Summarizing recent activity...",
        )

        return response

    def _log(
        self, title: str, color: LogColor = LogColor.GENERAL, description: str = ""
    ):
        print_to_console(f"{self.full_name}: {title}", color, description)

    async def _calculate_importance(self, memory_description: str) -> int:
        # Set up a complex chat model
        complex_llm = ChatModel(DEFAULT_SMART_MODEL, temperature=0)

        importance_parser = OutputFixingParser.from_llm(
            parser=PydanticOutputParser(pydantic_object=ImportanceRatingResponse),
            llm=complex_llm.defaultModel,
        )

        # make importance prompter
        importance_prompter = Prompter(
            PromptString.IMPORTANCE,
            {
                "full_name": self.full_name,
                "private_bio": self.private_bio,
                "memory_description": memory_description,
                "format_instructions": importance_parser.get_format_instructions(),
            },
        )

        response = await complex_llm.get_chat_completion(
            importance_prompter.prompt,
            loading_text="🤔 Calculating memory importance...",
        )

        parsed_response: ImportanceRatingResponse = importance_parser.parse(response)

        rating = parsed_response.rating

        return rating

    def _get_current_tools(self) -> list[CustomTool]:
        location_tools = self.location.available_tools

        all_tools = get_tools(
            location_tools,
            context=self.context,
            agent_id=self.id,
            include_worldwide=True,
        )

        authorized_tools = [
            tool
            for tool in all_tools
            if (tool.name in self.authorized_tools or not tool.requires_authorization)
        ]

        return authorized_tools

    def _move_to_location(
        self,
        location: Location,
    ):
        """Move the agents, send event to Events table"""

        self._log(
            "Moved Location", LogColor.MOVE, f"{self.location.name} -> {location.name}"
        )

        # Update the agents to the new location
        self.location = location
        self.context.update_agent(self._db_dict())

        # update the agents row in the db
        self._update_agent_row()

    async def _reflect(self):
        recent_memories = sorted(
            self.memories,
            key=lambda memory: memory.last_accessed or memory.created_at,
            reverse=True,
        )[:REFLECTION_MEMORY_COUNT]

        self._log("Reflection", LogColor.REFLECT, "Beginning reflection... 🤔")

        # Set up a complex chat model
        chat_llm = ChatModel(DEFAULT_SMART_MODEL, temperature=0)

        # Set up the parser
        question_parser = OutputFixingParser.from_llm(
            parser=PydanticOutputParser(pydantic_object=ReflectionQuestions),
            llm=chat_llm.defaultModel,
        )

        # Get memory descriptions
        memory_descriptions = [memory.description for memory in recent_memories]

        # Create questions Prompter
        questions_prompter = Prompter(
            PromptString.REFLECTION_QUESTIONS,
            {
                "memory_descriptions": str(memory_descriptions),
                "format_instructions": question_parser.get_format_instructions(),
            },
        )

        # Get the reflection questions
        response = await chat_llm.get_chat_completion(
            questions_prompter.prompt,
            loading_text="🤔 Thinking about what to reflect on...",
        )

        # Parse the response into an object
        parsed_questions_response: ReflectionQuestions = question_parser.parse(response)

        # For each question in the parsed questions...
        for question in parsed_questions_response.questions:
            # Get the related memories
            related_memories = await self._related_memories(question, 20)

            # Format them into a string
            memory_strings = [
                f"{index}. {related_memory.memory.description}"
                for index, related_memory in enumerate(related_memories, start=1)
            ]

            # Make the reflection parser
            reflection_parser = OutputFixingParser.from_llm(
                parser=PydanticOutputParser(pydantic_object=ReflectionResponse),
                llm=chat_llm.defaultModel,
            )

            self._log("Reflecting on Question", LogColor.REFLECT, f"{question}")

            # Make the reflection prompter
            reflection_prompter = Prompter(
                PromptString.REFLECTION_INSIGHTS,
                {
                    "full_name": self.full_name,
                    "memory_strings": str(memory_strings),
                    "format_instructions": reflection_parser.get_format_instructions(),
                },
            )

            # Get the reflection insights
            response = await chat_llm.get_chat_completion(
                reflection_prompter.prompt,
                loading_text="🤔 Reflecting",
            )

            # Parse the response into an object
            parsed_insights_response: ReflectionResponse = reflection_parser.parse(
                response
            )

            # For each insight in the parsed insights...
            for reflection_insight in parsed_insights_response.insights:
                # Get the related memory ids
                related_memory_ids = [
                    related_memories[index - 1].memory.id
                    for index in reflection_insight.related_statements
                ]

                # Add a new memory
                await self._add_memory(
                    description=reflection_insight.insight,
                    type=MemoryType.REFLECTION,
                    related_memory_ids=related_memory_ids,
                )

    async def _plan(self, thought_process: str = "") -> list[SinglePlan]:
        """Trigger the agent's planning process

        Args:
            location_context (str): A description of the current location and list of the other agents in this location
        """

        self._log("Starting to Plan", LogColor.PLAN, "📝")

        low_temp_llm = ChatModel(DEFAULT_SMART_MODEL, temperature=0, streaming=True)

        # Make the plan parser
        plan_parser = OutputFixingParser.from_llm(
            parser=PydanticOutputParser(
                pydantic_object=LLMPlanResponse,
            ),
            llm=low_temp_llm.defaultModel,
        )

        # Get a summary of the recent activity
        recent_activity = await self._summarize_activity()

        self._log("Recent Activity Summary", LogColor.PLAN, recent_activity)

        # Make the Plan prompter
        plan_prompter = Prompter(
            PromptString.MAKE_PLANS,
            {
                "time_window": PLAN_LENGTH,
                "allowed_location_descriptions": [
                    f"'uuid: {location.id}, name: {location.name}, description: {location.description}\n"
                    for location in self.allowed_locations
                ],
                "full_name": self.full_name,
                "private_bio": self.private_bio,
                "directives": str(self.directives),
                "recent_activity": recent_activity,
                "current_plans": [
                    f"{index}. {plan.description}"
                    for index, plan in enumerate(self.plans)
                ],
                "format_instructions": plan_parser.get_format_instructions(),
                "location_context": self.context.location_context_string(self.id),
                "thought_process": thought_process,
            },
        )

        chat_llm = ChatModel(temperature=0.5, streaming=True, request_timeout=600)

        # Get the plans
        response = await chat_llm.get_chat_completion(
            plan_prompter.prompt,
            loading_text="🤔 Making plans...",
        )

        # Parse the response into an object
        parsed_plans_response: LLMPlanResponse = plan_parser.parse(response)

        invalid_locations = [
            plan.location_id
            for plan in parsed_plans_response.plans
            if plan.location_id
            not in [location.id for location in self.allowed_locations]
        ]

        if invalid_locations:
            self._log(
                "Invalid Locations in Plan",
                LogColor.PLAN,
                f"The following locations are invalid: {invalid_locations}",
            )

            # Get the plans
            response = await chat_llm.get_chat_completion(
                plan_prompter.prompt
                + [
                    AIMessage(content=response),
                    HumanMessage(
                        content=f"Your response included the following invalid location_ids: {invalid_locations}. Please try again."
                    ),
                ],
                loading_text="🤔 Correcting plans...",
            )

            # Parse the response into an object
            parsed_plans_response: LLMPlanResponse = plan_parser.parse(response)

        # Delete existing plans
        self.plans = []

        # Make a bunch of new plan objects, put em into a list
        new_plans: list[SinglePlan] = []

        for plan in parsed_plans_response.plans:
            new_plan = SinglePlan(
                description=plan.description,
                location=next(
                    (
                        location
                        for location in self.allowed_locations
                        if str(location.id) == str(plan.location_id)
                    ),
                    None,
                ),
                max_duration_hrs=plan.max_duration_hrs,
                agent_id=self.id,
                stop_condition=plan.stop_condition,
            )
            new_plans.append(new_plan)

        # update the local agent object
        self.plans = new_plans

        # update the db agent row
        data, count = self._update_agent_row()

        # add the plans to the plan table
        data, count = self._add_plan_rows(new_plans)

        # Loop through each plan and print it to the console
        for index, plan in enumerate(new_plans):
            self._log(
                "New Plan",
                LogColor.PLAN,
                f"#{index}: {plan.description} @ {plan.location.name} (<{plan.max_duration_hrs} hrs) [Stop Condition: {plan.stop_condition}]",
            )

        return new_plans

    async def _respond_to_messages(self, events: list[Event]) -> None:
        """Respond to new messages"""

        new_message_events: list[Event] = [
            event for event in events if event.type == EventType.MESSAGE
        ]

        new_messages_at_location = [
            AgentMessage.from_event(event=event, context=self.context)
            for event in new_message_events
        ]

        new_messages = get_latest_messages(
            [
                message
                for message in new_messages_at_location
                if (message.recipient_id == self.id or message.recipient_id is None)
                and message.sender_id != self.id
            ]
        )

        if not new_messages:
            self._log("Inbox Empty", LogColor.MESSAGE, "No new messages.")
            return

        self._log(
            "New Messages",
            LogColor.MESSAGE,
            f"{len(new_messages)} new messages in inbox.",
        )

        low_temp_llm = ChatModel(DEFAULT_SMART_MODEL, temperature=0, streaming=True)

        # Make the response parser
        response_parser = OutputFixingParser.from_llm(
            parser=PydanticOutputParser(
                pydantic_object=LLMMessageResponse,
            ),
            llm=low_temp_llm.defaultModel,
        )

        for message in new_messages:
            conversation_history = message.get_chat_history()

            # Make the reaction prompter
            reaction_prompter = Prompter(
                PromptString.RESPOND,
                {
                    "format_instructions": response_parser.get_format_instructions(),
                    "sender_name": message.sender_name,
                    "full_name": self.full_name,
                    "private_bio": self.private_bio,
                    "directives": str(self.directives),
                    "current_plans": [
                        f"{index}. {plan.description}"
                        for index, plan in enumerate(self.plans)
                    ],
                    "conversation_history": conversation_history,
                    "location_context": self.context.location_context_string(self.id),
                },
            )

            # Get the reaction
            llm = ChatModel(DEFAULT_SMART_MODEL, temperature=0.5)
            response = await llm.get_chat_completion(
                reaction_prompter.prompt,
                loading_text="🤔 Responding to message...",
            )

            # parse the LLM message response
            parsed_response: LLMMessageResponse = response_parser.parse(response)

            # Format the agent_input for the send_message function
            agent_input = f"{message.sender_name};{parsed_response.content}"

            send_message(
                agent_input, ToolContext(context=self.context, agent_id=self.id)
            )

    async def _react(self) -> LLMReactionResponse:
        """Get the recent activity and decide whether to replan to carry on"""

        # Get the recent events
        (events, _) = self.context.events_manager.get_events(
            location_id=self.location.id, after=self.last_checked_events
        )

        # Store them as observations for this agent
        for event in events:
            await self._add_memory(event.description, MemoryType.OBSERVATION)

        # LLM call to decide how to react to new events
        # Make the reaction parser
        reaction_parser = OutputFixingParser.from_llm(
            parser=PydanticOutputParser(pydantic_object=LLMReactionResponse),
            llm=ChatModel(temperature=0).defaultModel,
        )

        # Make the reaction prompter
        reaction_prompter = Prompter(
            PromptString.REACT,
            {
                "format_instructions": reaction_parser.get_format_instructions(),
                "full_name": self.full_name,
                "private_bio": self.private_bio,
                "directives": str(self.directives),
                "recent_activity": await self._summarize_activity(),
                "current_plans": [
                    f"{index}. {plan.description}"
                    for index, plan in enumerate(self.plans)
                ],
                "location_context": self.context.location_context_string(self.id),
                "event_descriptions": [
                    f"{index}. {event.description}"
                    for index, event in enumerate(events)
                ],
            },
        )

        # Get the reaction
        llm = ChatModel(DEFAULT_SMART_MODEL, temperature=0.5)
        response = await llm.get_chat_completion(
            reaction_prompter.prompt,
            loading_text="🤔 Deciding how to react...",
        )

        # parse the reaction response
        parsed_reaction_response: LLMReactionResponse = reaction_parser.parse(response)

        self._log(
            "Reaction",
            LogColor.REACT,
            f"Decided to {parsed_reaction_response.reaction.value}: {parsed_reaction_response.thought_process}",
        )

        self.context.update_agent(self._db_dict())
        self._update_agent_row()

        return parsed_reaction_response

    async def _gossip(
        self,
        plan: SinglePlan,
        result: PlanExecutorResponse,
    ) -> None:
        # Make the reaction prompter
        reaction_prompter = Prompter(
            PromptString.GOSSIP,
            {
                "full_name": self.full_name,
                "plan_description": plan.description,
                "tool_name": result.tool.name,
                "tool_input": result.tool_input,
                "tool_result": result.output,
            },
        )

        # Get the reaction
        llm = ChatModel(DEFAULT_SMART_MODEL, temperature=0.5)
        response = await llm.get_chat_completion(
            reaction_prompter.prompt,
            loading_text="🤔 Creating gossip...",
        )

        self._log(
            "Gossip",
            LogColor.ACT,
            f"{response}",
        )

        event = Event(
            agent_id=self.id,
            type=EventType.NON_MESSAGE,
            description=f"{self.full_name} said the following: {response}",
            location_id=self.location.id,
        )

        self.context.events_manager.add_event(event)

    async def _act(
        self,
        plan: SinglePlan,
    ) -> None:
        """Act on a plan"""

        # If we are not in the right location, move to the new location
        if self.location.id != plan.location.id:
            self._move_to_location(plan.location)

        # Execute the plan

        self._log("Acting on Plan", LogColor.ACT, f"{plan.description}")

        if self.plan_executor is None:
            self.plan_executor = PlanExecutor(self.id, context=self.context)

        resp: PlanExecutorResponse = self.plan_executor.start_or_continue_plan(
            plan, tools=self._get_current_tools()
        )

        if resp.status == PlanStatus.FAILED:
            event = Event(
                agent_id=self.id,
                timestamp=datetime.now(pytz.utc),
                type=EventType.NON_MESSAGE,
                description=f"{self.full_name} has failed to complete the following: {plan.description} at the location: {plan.location.name}. {self.full_name} had the following problem: {resp.output}.",
                location_id=self.location.id,
            )

            self.context.events_manager.add_event(event)

            self._log(
                "Action Failed: Need help",
                LogColor.ACT,
                f"{plan.description} Error: {resp.output}",
            )
            # TODO: handle plan failure with a human

        elif resp.status == PlanStatus.IN_PROGRESS:
            event = Event(
                agent_id=self.id,
                type=EventType.NON_MESSAGE,
                description=f"{self.full_name} is currently doing the following: {plan.description} at the location: {plan.location.name}.",
                location_id=self.location.id,
            )

            self.context.events_manager.add_event(event)

            self._log("Action In Progress", LogColor.ACT, f"{plan.description}")

            # await self._gossip(plan, resp)

        # If the plan is done, remove it from the list of plans
        elif resp.status == PlanStatus.DONE:
            # remove all plans with the same description
            self.plans = [p for p in self.plans if p.description != plan.description]

            event = Event(
                agent_id=self.id,
                type=EventType.NON_MESSAGE,
                description=f"{self.full_name} has just completed the following: {plan.description} at the location: {plan.location.name}. The result was: {resp.output}.",
                location_id=self.location.id,
            )

            self.context.events_manager.add_event(event)

            self._log("Action Completed", LogColor.ACT, f"{plan.description}")

    async def _do_first_plan(self) -> None:
        """Do the first plan in the list"""

        current_plan = None

        # If we do not have a plan state, consult the plans or plan something new
        # If we have no plans, make some
        if len(self.plans) == 0:
            print(f"{self.full_name} has no plans, making some...")
            plans = await self._plan()
        # Otherwise, just use the existing plans
        else:
            plans = self.plans

        current_plan = plans[0]

        await self._act(current_plan)

    async def run_for_one_step(self):
        print(f"{self.full_name}: run_for_one_step...")  # TIMC
        print(
            f"Getting events at {self.location.name}, after {self.last_checked_events}..."
        )  # TIMC

        (events, first_refresh_time) = self.context.events_manager.get_events(
            location_id=self.location.id,
            after=self.last_checked_events,
        )

        print(
            f"\nNEW EVENTS AT {self.location.name}:\n{[event.description for event in events]}"
        )  # TIMC

        # Respond to all messages
        await self._respond_to_messages(events)

        # First we decide if we need to reflect
        if self._should_reflect():
            await self._reflect()

        # Generate a reaction to the latest events
        react_response = await self._react()

        # If the reaction calls for a new plan, make one
        if react_response.reaction == Reaction.REPLAN:
            await self._plan(react_response.thought_process)

        self.last_checked_events = first_refresh_time

        # Work through the plans
        await self._do_first_plan()
