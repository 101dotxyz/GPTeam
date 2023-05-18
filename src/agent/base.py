import asyncio
import json
import os
import random
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

from src.utils.database.base import Tables
from src.utils.database.client import get_database
from src.utils.discord import announce_bot_move
from src.utils.logging import agent_logger

from ..event.base import Event, EventsManager, EventType, MessageEventSubtype
from ..location.base import Location
from ..memory.base import MemoryType, RelatedMemory, SingleMemory, get_relevant_memories
from ..tools.base import CustomTool, get_tools
from ..tools.context import ToolContext
from ..tools.name import ToolName
from ..utils.colors import LogColor
from ..utils.embeddings import get_embedding
from ..utils.formatting import print_to_console
from ..utils.model_name import ChatModelName
from ..utils.models import ChatModel
from ..utils.parameters import (
    DEFAULT_SMART_MODEL,
    DEFAULT_WORLD_ID,
    DISCORD_ENABLED,
    PLAN_LENGTH,
    REFLECTION_MEMORY_COUNT,
)
from ..utils.prompt import Prompter, PromptString
from ..world.context import WorldContext
from .executor import PlanExecutor, PlanExecutorResponse
from .importance import ImportanceRatingResponse
from .message import (
    AgentMessage,
    LLMMessageResponse,
    get_conversation_history,
    get_latest_messages,
)
from .plans import LLMPlanResponse, LLMSinglePlan, PlanStatus, SinglePlan
from .react import LLMReactionResponse, Reaction
from .reflection import ReflectionQuestions, ReflectionResponse

SUMMARIZE_ACTIVITY_INTERVAL = 20  # seconds


class Agent(BaseModel):
    id: UUID
    full_name: str
    private_bio: str
    public_bio: str
    directives: Optional[list[str]]
    last_checked_events: datetime
    last_summarized_activity: datetime
    memories: list[SingleMemory]
    plans: list[SinglePlan]
    authorized_tools: list[ToolName]
    world_id: UUID
    notes: list[str] = []
    plan_executor: PlanExecutor = None
    context: WorldContext
    location: Location
    discord_bot_token: str = None
    react_response: LLMReactionResponse = None
    recent_activity: str = ""

    class Config:
        allow_underscore_names = True

    def __init__(
        self,
        full_name: str,
        private_bio: str,
        public_bio: str,
        context: WorldContext,
        location: Location,
        directives: list[str] = None,
        last_checked_events: datetime = None,
        last_summarized_activity: datetime = None,
        memories: list[SingleMemory] = [],
        plans: list[SinglePlan] = [],
        authorized_tools: list[ToolName] = [],
        id: Optional[str | UUID] = None,
        world_id: Optional[UUID] = DEFAULT_WORLD_ID,
        discord_bot_token: str = None,
        recent_activity: str = "",
    ):
        if id is None:
            id = uuid4()
        elif isinstance(id, str):
            id = UUID(id)
        if last_checked_events is None:
            last_checked_events = datetime.fromtimestamp(0, tz=pytz.utc)
        if last_summarized_activity is None:
            last_summarized_activity = datetime.fromtimestamp(0, tz=pytz.utc)

        # initialize the base model
        super().__init__(
            id=id,
            full_name=full_name,
            private_bio=private_bio,
            public_bio=public_bio,
            directives=directives,
            last_checked_events=last_checked_events,
            last_summarized_activity=last_summarized_activity,
            authorized_tools=authorized_tools,
            memories=memories,
            plans=plans,
            world_id=world_id,
            location=location,
            context=context,
            discord_bot_token=discord_bot_token,
            recent_activity=recent_activity,
        )

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
                for memory in self.memories[-5:]
            ]
        )
        plans = " " + "\n ".join([str(plan) for plan in self.plans])

        return f"{self.full_name} - {self.location.name}\nprivate_bio: {private_bio}\nDirectives: {self.directives}\n\nRecent Memories: \n{memories}\n\nPlans: \n{plans}\n"

    @property
    async def allowed_locations(self) -> list[Location]:
        """Get locations that this agent is allowed to be in."""
        database = await get_database()
        data = await database.get_by_field_contains(
            Tables.Locations, "allowed_agent_ids", str(self.id)
        )

        # For testing purposes include locations with 0 allowed agents as well
        other_data = await database.get_by_field(
            Tables.Locations, "allowed_agent_ids", "{}"
        )

        return [Location(**location) for location in data + other_data]

    @classmethod
    async def from_db_dict(
        cls, agent_dict: dict, locations: list[Location], context: WorldContext
    ):
        """Create an agent from a dictionary retrieved from the database."""
        database = await get_database()
        plans = await database.get_by_ids(Tables.Plans, agent_dict["ordered_plan_ids"])

        ordered_plans: list[dict] = sorted(
            plans, key=lambda plan: agent_dict["ordered_plan_ids"].index(plan["id"])
        )

        memories_data = await database.get_by_field(
            Tables.Memories, "agent_id", str(agent_dict["id"])
        )

        plans = []
        for plan in ordered_plans:
            location = [
                location
                for location in locations
                if str(location.id) == plan["location_id"]
            ][0]

            related_event = (
                await Event.from_id(plan["related_event_id"])
                if plan["related_event_id"] is not None
                else None
            )
            related_message = (
                AgentMessage.from_event(related_event, context)
                if related_event
                else None
            )
            plans.append(
                SinglePlan(
                    **{
                        key: value
                        for key, value in plan.items()
                        if (key != "location_id" and key != "related_event_id")
                    },
                    location=location,
                    related_message=related_message,
                )
            )

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
            memories=[SingleMemory(**memory) for memory in memories_data],
            plans=plans,
            discord_bot_token=agent_dict["discord_bot_token"],
        )

    @classmethod
    async def from_id(cls, id: UUID, context: WorldContext):
        database = await get_database()
        agents_data = await database.get_by_id(Tables.Agents, str(id))
        if len(agents_data) == 0:
            raise ValueError("No agent with that id")
        agent = agents_data[1][0]
        # get all the plans in db that are in the agent's plan list
        plans_data = await database.get_by_ids(Tables.Plans, agent["ordered_plan_ids"])
        ordered_plans_data = sorted(
            plans_data, key=lambda plan: agent["ordered_plan_ids"].index(plan["id"])
        )

        locations_data = await database.get_by_field(
            Tables.Locations, "world_id", agent["world_id"]
        )

        location = [
            location
            for location in locations_data
            if str(location["id"]) == agent["location_id"]
        ][0]

        available_tools = list(
            map(lambda name: ToolName(name), location.get("available_tools"))
        )

        print("available tools", available_tools)

        locations = {
            str(location["id"]): Location(
                id=location["id"],
                name=location["name"],
                description=location["description"],
                channel_id=location["channel_id"],
                available_tools=available_tools,
                world_id=location["world_id"],
                allowed_agent_ids=list(
                    map(lambda id: UUID(id), location.get("allowed_agent_ids"))
                ),
            )
            for location in locations_data
        }

        memories_data = await database.get_by_field(Tables.Memory, "agent_id", str(id))

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
            discord_bot_token=agent.get("discord_bot_token"),
        )

    @property
    def color(self) -> LogColor:
        return self.context.get_agent_color(self.id)

    async def _add_memory(
        self,
        description: str,
        created_at: datetime = datetime.now(),
        type: MemoryType = MemoryType.OBSERVATION,
        related_memory_ids: list[UUID] = [],
        log: bool = True,
    ) -> SingleMemory:
        memory = SingleMemory(
            agent_id=self.id,
            type=type,
            description=description,
            importance=await self._calculate_importance(description),
            embedding=await get_embedding(description),
            related_memory_ids=related_memory_ids,
            created_at=created_at,
        )

        self.memories.append(memory)

        # add to database
        await (await get_database()).insert(Tables.Memories, memory.db_dict())

        if log:
            self._log("New Memory", f"{memory}")

        return memory

    async def _update_agent_row(self):
        row = {
            "full_name": self.full_name,
            "private_bio": self.private_bio,
            "directives": self.directives,
            "location_id": str(self.location.id),
            "last_checked_events": self.last_checked_events.isoformat(),
            "ordered_plan_ids": [str(plan.id) for plan in self.plans],
        }

        return await (await get_database()).update(Tables.Agents, str(self.id), row)

    async def _upsert_plan_rows(self, plans: list[SinglePlan]):
        database = await get_database()
        for plan in plans:
            await database.insert(Tables.Plans, plan._db_dict(), upsert=True)

    def update_plan(self, new_plan: SinglePlan):
        old_plan = [
            p
            for p in self.plans
            if (p.id == new_plan.id or p.description == new_plan.description)
        ][0]
        self.plans = [
            plan if plan.id is not old_plan.id else new_plan for plan in self.plans
        ]

    async def _get_memories_since(self, date: datetime):
        data = await (await get_database()).get_memories_since(date, str(self.id))
        memories = [SingleMemory(**memory) for memory in data]
        return memories

    async def _should_reflect(self) -> bool:
        """Check if the agent should reflect on their memories.
        Returns True if the cumulative importance score of memories
        since the last reflection is over 100
        """
        data = await (await get_database()).get_should_reflect(str(self.id))

        last_reflection_time = (
            data[0]["created_at"] if len(data) > 0 else datetime(1970, 1, 1)
        )

        memories_since_last_reflection = await self._get_memories_since(
            last_reflection_time
        )

        cumulative_importance = sum(
            [memory.importance for memory in memories_since_last_reflection]
        )

        return cumulative_importance > 500

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
            "discord_bot_token": self.discord_bot_token,
        }

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
                    [memory.verbose_description for memory in recent_memories]
                ),
            },
        )

        low_temp_llm = ChatModel(DEFAULT_SMART_MODEL, temperature=0)

        response = await low_temp_llm.get_chat_completion(
            summary_prompter.prompt,
            loading_text="🤔 Summarizing recent activity...",
        )

        self.recent_activity = response

        return response

    def _log(self, title: str, description: str = ""):
        agent_logger.info(f"[{self.full_name}] [{self.color}] [{title}] {description}")
        print_to_console(f"[{self.full_name}] {title}", self.color, description)

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

    async def _move_to_location(
        self,
        location: Location,
    ) -> None:
        """Move the agents, send event to Events table"""
        old_location = self.location

        self._log(
            "Moved Location",
            f"{self.location.name} -> {location.name} @ {datetime.now(pytz.utc).strftime('%H:%M:%S')}",
        )

        departure_event = Event(
            type=EventType.NON_MESSAGE,
            description=f"{self.full_name} left the {old_location.name}",
            location_id=old_location.id,
            agent_id=self.id,
            timestamp=datetime.now(pytz.utc),
        )

        arrival_event = Event(
            type=EventType.NON_MESSAGE,
            description=f"{self.full_name} arrived at the {location.name}",
            location_id=location.id,
            agent_id=self.id,
            timestamp=datetime.now(pytz.utc),
        )

        # Update the local agent, do we need both of these lines?
        self.location = location
        self.context.update_agent(self._db_dict())

        # update agent in db
        await self._update_agent_row(),

        if DISCORD_ENABLED:
            await announce_bot_move(
                self.full_name, old_location.channel_id, location.channel_id
            )

        # Add events to the events manager, which handles the DB updates
        await self.context.add_event(departure_event)
        await self.context.add_event(arrival_event)

    async def _reflect(self):
        recent_memories = sorted(
            self.memories,
            key=lambda memory: memory.last_accessed or memory.created_at,
            reverse=True,
        )[:REFLECTION_MEMORY_COUNT]

        self._log("Reflection", "Beginning reflection... 🤔")

        # Set up a complex chat model
        chat_llm = ChatModel(DEFAULT_SMART_MODEL, temperature=0)

        # Set up the parser
        question_parser = OutputFixingParser.from_llm(
            parser=PydanticOutputParser(pydantic_object=ReflectionQuestions),
            llm=chat_llm.defaultModel,
        )

        # Create questions Prompter
        questions_prompter = Prompter(
            PromptString.REFLECTION_QUESTIONS,
            {
                "memory_descriptions": str(
                    [memory.verbose_description for memory in recent_memories]
                ),
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
            related_memories = await get_relevant_memories(question, self.memories, 20)

            # Format them into a string
            memory_strings = [
                f"{index}. {related_memory.description}"
                for index, related_memory in enumerate(related_memories, start=1)
            ]

            # Make the reflection parser
            reflection_parser = OutputFixingParser.from_llm(
                parser=PydanticOutputParser(pydantic_object=ReflectionResponse),
                llm=chat_llm.defaultModel,
            )

            self._log("Reflecting on Question", f"{question}")

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
                    related_memories[index - 1].id
                    for index in reflection_insight.related_statements
                ]

                # Add a new memory
                await self._add_memory(
                    description=reflection_insight.insight,
                    type=MemoryType.REFLECTION,
                    related_memory_ids=related_memory_ids,
                )

        # Gossip to other agents

        # Get other agents at the location
        agents_at_location = self.context.get_agents_at_location(
            location_id=self.location.id
        )

        other_agents = [a for a in agents_at_location if str(a["id"]) != str(self.id)]

        # names of other agents at location
        other_agent_names = ", ".join([a["full_name"] for a in other_agents])

        # Make the reaction prompter
        gossip_prompter = Prompter(
            PromptString.GOSSIP,
            {
                "full_name": self.full_name,
                "memory_descriptions": str(
                    [memory.description for memory in recent_memories]
                ),
                "other_agent_names": other_agent_names,
            },
        )

        response = await chat_llm.get_chat_completion(
            gossip_prompter.prompt,
            loading_text="🤔 Creating gossip...",
        )

        self._log(
            "Gossip",
            f"{response}",
        )

        event = Event(
            agent_id=self.id,
            type=EventType.MESSAGE,
            subtype=MessageEventSubtype.AGENT_TO_AGENT,
            description=f"{self.full_name} said to everyone in the {self.location.name}: '{response}'",
            location_id=self.location.id,
        )

        await self.context.add_event(event)

    async def _plan(self, thought_process: str = "") -> list[SinglePlan]:
        """Trigger the agent's planning process

        Args:
            location_context (str): A description of the current location and list of the other agents in this location
        """

        self._log("Starting to Plan", "📝")

        low_temp_llm = ChatModel(DEFAULT_SMART_MODEL, temperature=0, streaming=True)

        # Make the plan parser
        plan_parser = OutputFixingParser.from_llm(
            parser=PydanticOutputParser(
                pydantic_object=LLMPlanResponse,
            ),
            llm=low_temp_llm.defaultModel,
        )

        # Get a summary of the recent activity
        if (
            datetime.now(pytz.utc) - self.last_summarized_activity
        ).total_seconds() > SUMMARIZE_ACTIVITY_INTERVAL:
            recent_activity = await self._summarize_activity()
        else:
            recent_activity = self.recent_activity

        self._log("Recent Activity Summary", recent_activity)

        # Make the Plan prompter
        plan_prompter = Prompter(
            PromptString.MAKE_PLANS,
            {
                "time_window": PLAN_LENGTH,
                "allowed_location_descriptions": [
                    f"'uuid: {location.id}, name: {location.name}, description: {location.description}\n"
                    for location in await self.allowed_locations
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

        chat_llm = ChatModel(temperature=0, streaming=True, request_timeout=600)

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
            not in [location.id for location in await self.allowed_locations]
        ]

        if invalid_locations:
            self._log(
                "Invalid Locations in Plan",
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
                        for location in await self.allowed_locations
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
        await self._update_agent_row()

        # add the plans to the plan table
        await self._upsert_plan_rows(new_plans)

        # Loop through each plan and print it to the console
        for index, plan in enumerate(new_plans):
            self._log(
                "New Plan",
                f"#{index}: {plan.description} @ {plan.location.name} (<{plan.max_duration_hrs} hrs) [Stop Condition: {plan.stop_condition}]",
            )

        return new_plans

    async def _react(self, events: list[Event]) -> LLMReactionResponse:
        """Get the recent activity and decide whether to replan to carry on"""

        self._log("React", "Deciding how to react to recent events...")

        # LLM call to decide how to react to new events
        # Make the reaction parser
        reaction_parser = OutputFixingParser.from_llm(
            parser=PydanticOutputParser(pydantic_object=LLMReactionResponse),
            llm=ChatModel(temperature=0).defaultModel,
        )

        # Get a summary of the recent activity
        if (
            datetime.now(pytz.utc) - self.last_summarized_activity
        ).total_seconds() > SUMMARIZE_ACTIVITY_INTERVAL:
            recent_activity = await self._summarize_activity()
        else:
            recent_activity = self.recent_activity

        # Make the reaction prompter
        reaction_prompter = Prompter(
            PromptString.REACT,
            {
                "format_instructions": reaction_parser.get_format_instructions(),
                "full_name": self.full_name,
                "private_bio": self.private_bio,
                "directives": str(self.directives),
                "recent_activity": recent_activity,
                "current_plan": self.plans[0].description,
                "location_context": self.context.location_context_string(self.id),
                "event_descriptions": [
                    f"{index}. {event.description}"
                    for index, event in enumerate(events)
                ],
                "conversation_history": await get_conversation_history(
                    self.id, self.context
                ),
            },
        )

        # Get the reaction
        llm = ChatModel(DEFAULT_SMART_MODEL, temperature=0)
        response = await llm.get_chat_completion(
            reaction_prompter.prompt,
            loading_text="🤔 Deciding how to react...",
        )

        # parse the reaction response
        parsed_reaction_response: LLMReactionResponse = reaction_parser.parse(response)

        self._log(
            "Reaction",
            f"Decided to {parsed_reaction_response.reaction.value} the current plan: {parsed_reaction_response.thought_process}",
        )

        self.context.update_agent(self._db_dict())
        await self._update_agent_row()

        return parsed_reaction_response

    async def _act(
        self,
        plan: SinglePlan,
    ) -> PlanStatus:
        """Act on a plan"""

        self._log("Act", "Starting to act on plan.")

        # If we are not in the right location, move to the new location
        if (hasattr(plan, 'location') and plan.location and self.location.id != plan.location.id):
            await self._move_to_location(plan.location)

        # Observe and react to new events
        await self.observe()

        # Gather relevant memories
        relevant_memories = await get_relevant_memories(
            plan.related_message.get_event_message()
            if plan.related_message
            else plan.description,
            memories=self.memories,
            k=20,
        )

        self.plan_executor = PlanExecutor(
            self.id,
            world_context=self.context,
            message_to_respond_to=plan.related_message,
            relevant_memories=relevant_memories,
        )

        resp: PlanExecutorResponse = await self.plan_executor.start_or_continue_plan(
            plan, tools=self._get_current_tools()
        )

        # IF the plan failed
        if resp.status == PlanStatus.FAILED:
            self._log(
                "Action Failed",
                f"{plan.description} Error: {resp.output}",
            )

            # update the plan in the local agent object
            plan.scratchpad = resp.scratchpad
            plan.status = resp.status
            self.update_plan(plan)

            # update the plan in the db
            await self._upsert_plan_rows([plan])

            # remove all plans with the same description
            self.plans = [p for p in self.plans if p.description != plan.description]

            event = Event(
                agent_id=self.id,
                timestamp=datetime.now(pytz.utc),
                type=EventType.NON_MESSAGE,
                description=f"{self.full_name} has failed to complete the following: {plan.description} at the location: {plan.location.name}. {self.full_name} had the following problem: {resp.output}.",
                location_id=self.location.id,
            )

            event = await self.context.add_event(event)

        # If the plan is in progress
        elif resp.status == PlanStatus.IN_PROGRESS:
            self._log("Action In Progress", f"{plan.description}")

            # update the plan in the local agent object
            plan.scratchpad = resp.scratchpad
            plan.status = resp.status
            self.update_plan(plan)

            # update the plan in the db
            await self._upsert_plan_rows([plan])

            # IF the tool use failed, there will be no tool object
            if resp.tool:
                tool_usage_summary = await resp.tool.summarize_usage(
                    plan_description=plan.description,
                    tool_input=resp.tool_input,
                    tool_result=resp.output,
                    agent_full_name=self.full_name,
                )

        # If the plan is done, remove it from the list of plans
        elif resp.status == PlanStatus.DONE:
            self._log("Action Completed", f"{plan.description}")

            # update the plan in the local agent object
            plan.completed_at = datetime.now(pytz.utc)
            plan.scratchpad = resp.scratchpad
            plan.status = resp.status
            self.update_plan(plan)

            # update the plan in the db
            await self._upsert_plan_rows([plan])

            # remove all plans with the same description
            self.plans = [p for p in self.plans if p.description != plan.description]

        return resp.status

    async def _do_first_plan(self) -> None:
        """Do the first plan in the list"""

        current_plan = None

        # If we do not have a plan state, consult the plans or plan something new
        # If we have no plans, make some
        if len(self.plans) == 0:
            print(f"{self.full_name} has no plans, making some...")
            await self._plan()

        current_plan = self.plans[0]

        await self._act(current_plan)

    async def observe(self) -> list[Event]:
        # Take in new events and add them to memory. Return the events

        # Get new events witnessed by this agent
        last_checked_events = self.last_checked_events

        self.last_checked_events = datetime.now(pytz.utc)

        (events, _) = await self.context.events_manager.get_events(
            after=last_checked_events, witness_ids=[self.id], force_refresh=True
        )

        self._log(
            "Observe",
            f"Observed {len(events)} new events since {last_checked_events.strftime('%H:%M:%S')}",
        )

        if len(events) > 0:
            # Make new memories based on the events
            new_memories = [
                await self._add_memory(
                    event.description,
                    created_at=event.timestamp,
                    type=MemoryType.OBSERVATION,
                    log=False,
                )
                for event in events
            ]

        return events

    async def write_progress_to_file(self):
        agents_folder = os.path.join(os.getcwd(), "agents")
        if not os.path.exists(agents_folder):
            os.makedirs(agents_folder)

        file_path = os.path.join(agents_folder, f"{self.full_name}.txt")

        plans_in_progress = [
            "🏃‍♂️ " + plan.description
            for plan in self.plans
            if plan.status == PlanStatus.IN_PROGRESS
        ]

        current_action = (
            "\n".join(plans_in_progress) if len(plans_in_progress) > 0 else "No actions"
        )

        conversation_history = await get_conversation_history(self.id, self.context)

        plans_to_do = [
            "📆 " + plan.description
            for plan in self.plans
            if plan.status == PlanStatus.TODO
        ]

        current_plans = "\n".join(plans_to_do) if len(plans_to_do) > 0 else "No plans"

        # Sort memories in reverse chronological order
        sorted_memories = sorted(
            self.memories, key=lambda m: m.created_at, reverse=True
        )

        memories = "\n".join(
            [
                f"{memory.created_at.replace(tzinfo=pytz.utc).strftime('%Y-%m-%d %H:%M:%S')}: {'👀' if memory.type == MemoryType.OBSERVATION else '💭'} {memory.description} (Importance: {memory.importance})"
                for memory in sorted_memories
            ]
        )

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(
                f"* {self.full_name}\n\nCurrent Action:\n{current_action}\n\nLocation: {self.location.name}\n\nCurrent Conversations:\n{conversation_history}\n\nCurrent Plans:\n{current_plans}\n\nMemories:\n{memories}\n"
            )

    async def run_for_one_step(self):
        await asyncio.sleep(random.random() * 3)

        events = await self.observe()

        # if there's no current plan, make some
        if len(self.plans) == 0:
            print(f"{self.full_name} has no plans, making some...")
            await self._plan()

        # Decide how to react to these events
        self.react_response = await self._react(events)

        # If the reaction calls to cancel the current plan, remove the first one
        if self.react_response.reaction == Reaction.CANCEL:
            self.plans = self.plans[1:]

        # If the reaction calls to postpone the current plan, insert the new plan at the top
        elif self.react_response.reaction == Reaction.POSTPONE:
            self.plans.insert(0, self.react_response.new_plan)

        # Work through the plans
        await self._do_first_plan()

        # Reflect, if we should
        if await self._should_reflect():
            await self._reflect()

        await self.write_progress_to_file()
