import json
import os
from ctypes import Union
from datetime import datetime
from typing import Literal, Optional, Type, cast
from uu import Error
from uuid import UUID, uuid4

import pytz
from colorama import Fore
from langchain.output_parsers import OutputFixingParser, PydanticOutputParser
from langchain.schema import AIMessage, HumanMessage
from pydantic import BaseModel

from ..event.base import Event, EventManager, EventType
from ..location.base import Location
from ..memory.base import MemoryType, SingleMemory
from ..utils.colors import LogColor
from ..utils.database import supabase
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
from .executor import ExecutorStatus, run_executor
from .importance import ImportanceRatingResponse
from .plans import LLMPlanResponse, LLMSinglePlan, SinglePlan
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
    bio: str
    directives: Optional[list[str]]
    memories: list[SingleMemory]
    plans: list[SinglePlan]
    world_id: UUID
    location: Optional[Location]

    def __init__(
        self,
        full_name: str,
        bio: str,
        directives: list[str] = None,
        memories: list[SingleMemory] = [],
        plans: list[SinglePlan] = [],
        id: Optional[str | UUID] = None,
        world_id: Optional[UUID] = DEFAULT_WORLD_ID,
        location: Optional[Location] = Location.from_id(DEFAULT_LOCATION_ID),
    ):
        if id is None:
            id = uuid4()
        elif isinstance(id, str):
            id = UUID(id)

        # initialize the base model
        super().__init__(
            id=id,
            full_name=full_name,
            bio=bio,
            directives=directives,
            memories=memories,
            plans=plans,
            world_id=world_id,
            location=location,
        )

        # if the memories are None, retrieve them
        if memories is None or len(memories) == 0:
            self.memories = self._get_memories()

        print_to_console("Initialized Agent", LogColor.GENERAL, self.full_name)

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
    def from_json_profile(cls, id: str):
        path = os.path.dirname(os.path.abspath(__file__)) + f"/profiles/{id}.json"
        f = open(path, "r")
        profile = json.load(f)
        f.close()

        return cls(**profile)

    @classmethod
    def from_id(cls, id: UUID):
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
                world_id=location["world_id"],
                allowed_agent_ids=location["allowed_agent_ids"],
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

        return Agent(
            id=id,
            full_name=agent.get("full_name"),
            bio=agent.get("bio"),
            directives=agent.get("directives"),
            memories=[SingleMemory(**memory) for memory in memories_data[1]],
            plans=plans,
            world_id=agent.get("world_id"),
            location=location,
        )

    def _get_memories(self):
        data, count = (
            supabase.table("Memories")
            .select("*")
            .eq("agent_id", str(self.id))
            .execute()
        )
        memories = [SingleMemory(**memory) for memory in data[1]]
        return memories

    def _add_memory(
        self,
        description: str,
        type: MemoryType = MemoryType.OBSERVATION,
        related_memory_ids: list[UUID] = [],
    ) -> SingleMemory:
        memory = SingleMemory(
            agent_id=self.id,
            type=type,
            description=description,
            importance=self._calculate_importance(description),
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
            "bio": self.bio,
            "directives": self.directives,
            "ordered_plan_ids": [str(plan.id) for plan in self.plans],
        }
        print("Updated ", self.full_name, " in db.")
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
            print("Added plan to db.")
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
            "bio": self.bio,
            "directives": self.directives,
            "ordered_plan_ids": [str(plan.id) for plan in self.plans],
            "world_id": self.world_id,
            "location": self.location.id,
        }

    def _related_memories(self, query: str, k: int = 5) -> list[RelatedMemory]:
        # Calculate relevance for each memory and store it in a list of dictionaries
        memories_with_relevance = [
            RelatedMemory(memory=memory, relevance=memory.relevance(query))
            for memory in self.memories
        ]

        # Sort the list of dictionaries based on the 'relevance' key in descending order
        sorted_memories = sorted(
            memories_with_relevance, key=lambda x: x.relevance, reverse=True
        )

        return sorted_memories[:k]

    def _summarize_activity(self, k: int = 20) -> str:
        recent_memories = sorted(
            self.memories, key=lambda memory: memory.created_at, reverse=True
        )[:k]

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

        response = low_temp_llm.get_chat_completion(
            summary_prompter.prompt,
            loading_text="🤔 Summarizing recent activity...",
        )

        return response

    def _log(
        self, title: str, color: LogColor = LogColor.GENERAL, description: str = ""
    ):
        print_to_console(f"{self.full_name}: {title}", color, description)

    def _calculate_importance(self, memory_description: str) -> int:
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
                "bio": self.bio,
                "memory_description": memory_description,
                "format_instructions": importance_parser.get_format_instructions(),
            },
        )

        response = complex_llm.get_chat_completion(
            importance_prompter.prompt,
            loading_text="🤔 Calculating memory importance...",
        )

        parsed_response: ImportanceRatingResponse = importance_parser.parse(response)

        rating = parsed_response.rating

        return rating

    def _move_to_location(self, location: Location, event_manager: EventManager):
        """Move the agents, send event to Events table"""

        self._log(
            "Moved Location", LogColor.MOVE, f"{self.location.name} -> {location.name}"
        )

        # first emit the depature event to the db
        event = Event(
            timestamp=datetime.now(pytz.utc),
            type=EventType.NON_MESSAGE,
            description=f"{self.full_name} left location: {self.location.name}",
            location_id=self.location.id,
        )

        event_manager.add_event(event)

        # Update the agents to the new location
        self.location = location

        # emit the arrival to the db
        event = Event(
            timestamp=datetime.now(tz=pytz.utc),
            type=EventType.NON_MESSAGE,
            description=f"{self.full_name} arrived at location: {location.name}",
            location_id=self.location.id,
        )
        event_manager.add_event(event)

        # update the agents row in the db
        self._update_agent_row()

    def _reflect(self):
        recent_memories = sorted(
            self.memories, key=lambda memory: memory.last_accessed, reverse=True
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
        response = chat_llm.get_chat_completion(
            questions_prompter.prompt,
            loading_text="🤔 Thinking about what to reflect on...",
        )

        # Parse the response into an object
        parsed_questions_response: ReflectionQuestions = question_parser.parse(response)

        # For each question in the parsed questions...
        for question in parsed_questions_response.questions:
            # Get the related memories
            related_memories = self._related_memories(question, 20)

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
            response = chat_llm.get_chat_completion(
                reflection_prompter.prompt,
                loading_text=f"🤔 Reflecting on the following question: {question}",
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
                self._add_memory(
                    description=reflection_insight.insight,
                    type=MemoryType.REFLECTION,
                    related_memory_ids=related_memory_ids,
                )

    def _plan(self) -> list[SinglePlan]:
        self._log("Starting to Plan", LogColor.PLAN, "📝")

        low_temp_llm = ChatModel(DEFAULT_SMART_MODEL, temperature=0, streaming=True)

        # Make the plan parser
        plan_parser = OutputFixingParser.from_llm(
            parser=PydanticOutputParser(
                pydantic_object=LLMPlanResponse,
            ),
            llm=low_temp_llm.defaultModel,
        )

        print(plan_parser.get_format_instructions())

        # Get a summary of the recent activity
        recent_activity = self._summarize_activity()

        self._log("Recent Activity Summary", LogColor.PLAN, recent_activity)

        # Make the Plan prompter
        plan_prompter = Prompter(
            PromptString.MAKE_PLANS,
            {
                "time_window": PLAN_LENGTH,
                "location_descriptions": [
                    f"'id: {location.id}, name: {location.name}, description: {location.description}\n"
                    for location in self.allowed_locations
                ],
                "full_name": self.full_name,
                "bio": self.bio,
                "directives": str(self.directives),
                "recent_activity": recent_activity,
                "current_plans": [
                    f"{index}. {plan.description}"
                    for index, plan in enumerate(self.plans)
                ],
                "format_instructions": plan_parser.get_format_instructions(),
            },
        )

        chat_llm = ChatModel(
            DEFAULT_FAST_MODEL, temperature=0.5, streaming=True, request_timeout=600
        )

        # Get the plans
        response = chat_llm.get_chat_completion(
            plan_prompter.prompt,
            loading_text="🤔 Making plans...",
        )

        # Parse the response into an object
        parsed_plans_response: LLMPlanResponse = plan_parser.parse(response)

        print(
            "allowed_locations", self.allowed_locations, parsed_plans_response.plans[0]
        )

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
                f"The following locations are not in your allowed locations: {invalid_locations}",
            )

            # Get the plans
            response = chat_llm.get_chat_completion(
                plan_prompter.prompt
                + [
                    AIMessage(content=response),
                    HumanMessage(
                        content=f"Your response included the following invalid location_id: {invalid_locations}. Please try again."
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
                        if location.id == plan.location_id
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

    def _react(self, event_manager: EventManager) -> Reaction:
        """Get the recent activity and decide whether to replan to carry on"""

        # Pull in latest events
        new_events = event_manager.get_events_by_location(self.location)

        # Store them as observations for this agent
        for event in new_events:
            self._add_memory(event.description, MemoryType.OBSERVATION)

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
                "bio": self.bio,
                "directives": str(self.directives),
                "recent_activity": self._summarize_activity(),
                "current_plans": [
                    f"{index}. {plan.description}"
                    for index, plan in enumerate(self.plans)
                ],
                "event_descriptions": [
                    f"{index}. {event.description}"
                    for index, event in enumerate(new_events)
                ],
            },
        )

        # Get the reaction
        llm = ChatModel(DEFAULT_SMART_MODEL, temperature=0.5)
        response = llm.get_chat_completion(
            reaction_prompter.prompt,
            loading_text="🤔 Deciding how to react...",
        )

        # parse the reaction response
        parsed_reaction_response: LLMReactionResponse = reaction_parser.parse(response)

        self._log(
            "Reaction",
            LogColor.REACT,
            f"Decided to {parsed_reaction_response.reaction.value} given the recent events:\n"
            + "\n".join([event.description for event in new_events]),
        )

        return parsed_reaction_response

    def _do_first_plan(self, event_manager: EventManager) -> None:
        """Do the first plan in the list"""

        current_plan = None

        # If we do not have a plan state, consult the plans or plan something new
        # If we have no plans, make some
        if len(self.plans) == 0:
            plans = self._plan()
        # Otherwise, just use the existing plans
        else:
            plans = self.plans

        current_plan = plans[0]

        self._log("Acting on Plan", LogColor.ACT, f"{current_plan.description}")

        # If we are not in the right location, move to the new location
        if self.location.id != current_plan.location.id:
            self._move_to_location(current_plan.location, event_manager)
            return

        # Execute the plan

        # TODO: Tools are dependent on the location
        timeout = int(os.getenv("STEP_DURATION"))
        resp = run_executor(current_plan.description, timeout=timeout)

        if resp.status == ExecutorStatus.NEEDS_HELP:
            self._log(
                "Action Failed: Need help",
                LogColor.ACT,
                f"{current_plan.description} Error: {resp.output}",
            )
            # TODO: handle plan failure with a human
            return

        elif resp.status == ExecutorStatus.TIMED_OUT:
            self._log(
                "Action Failed: Timeout",
                LogColor.ACT,
                f"{current_plan.description} Error: {resp.output}",
            )
            return

        # If the plan is done, remove it from the list of plans
        elif resp.status == ExecutorStatus.COMPLETED:
            # TODO: make sure current_plan is indeed a plan from the list, and not a reconstruction of one.
            self.plans.remove(current_plan)
            self._log("Action Completed", LogColor.ACT, f"{current_plan.description}")

    def run_for_one_step(self, events_manager: EventManager):
        # First we decide if we need to reflect
        if self._should_reflect():
            self._reflect()

        # Generate a reaction to the latest events
        reaction = self._react(events_manager)

        # If the reaction calls for a new plan, make one
        if reaction == Reaction.REPLAN:
            self._plan()

        # Work through the plans
        self._do_first_plan(event_manager=events_manager)
