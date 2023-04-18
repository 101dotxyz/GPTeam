import datetime
import json
import os
from typing import Optional
from uuid import UUID, uuid4

from colorama import Fore
from langchain.output_parsers import OutputFixingParser, PydanticOutputParser
from pydantic import BaseModel

from ..memory.base import MemoryType, SingleMemory
from ..utils.database import supabase
from ..utils.formatting import print_to_console
from ..utils.models import ChatModel, ChatModelName
from ..utils.parameters import DEFAULT_LOCATION_ID, PLAN_LENGTH, REFLECTION_MEMORY_COUNT
from ..utils.prompt import Prompter, PromptString
from ..world.base import Event, EventType, Location
from .executor import run_executor
from .importance import ImportanceRatingResponse
from .plans import LLMPlanResponse, LLMSinglePlan, SinglePlan
from .reflection import ReflectionQuestions, ReflectionResponse


class RelatedMemory(BaseModel):
    memory: SingleMemory
    relevance: float

    def __str__(self) -> str:
        return f"SingleMemory: {self.memory.description}, Relevance: {self.relevance}"


class AgentState(BaseModel):
    plan_id: Optional[UUID]
    location_id: UUID

    def __init__(self, location_id: UUID | str, plan_id: Optional[UUID | str] = None):
        if plan_id is None:
            print("none")
        if isinstance(plan_id, str):
            plan_id = UUID(plan_id)
        if isinstance(location_id, str):
            location_id = UUID(location_id)

        super().__init__(location_id=location_id, plan_id=plan_id)

    def db_dict(self) -> dict:
        return {"plan_id": str(self.plan_id), "location_id": str(self.location_id)}


class Agent(BaseModel):
    id: UUID
    full_name: str
    bio: str
    directives: Optional[list[str]] = None
    memories: Optional[list[SingleMemory]] = []
    ordered_plan_ids: Optional[list[UUID]] = []
    state: Optional[AgentState] = None

    def __init__(
        self,
        full_name: str,
        bio: str,
        directives: list[str] = None,
        memories: list[SingleMemory] = [],
        ordered_plan_ids: list[UUID] = [],
        state: AgentState = None,
        id: Optional[str | UUID] = None,
    ):
        if id is None:
            id = uuid4()
        elif isinstance(id, str):
            id = UUID(id)

        # if the state is None, put them into the default location
        if state is None:
            state = AgentState(location_id=DEFAULT_LOCATION_ID)
        elif isinstance(state, dict):
            state = AgentState(**state)

        super().__init__(
            id=id,
            full_name=full_name,
            bio=bio,
            directives=directives,
            memories=memories,
            ordered_plan_ids=ordered_plan_ids,
            state=state,
        )

        print_to_console("Agent: ", Fore.GREEN, self.full_name)

    @property
    def allowed_locations(self) -> list[Location]:
        """Get locations that this agent is allowed to be in."""
        data, count = (
            supabase.table("Locations")
            .select("*")
            .contains("allowed_agent_ids", [str(self.id)])
            .execute()
        )
        return [Location(**location) for location in data[1]]

    @property
    def ordered_plans(self) -> list[SinglePlan]:
        """Get the full plans for this agent."""
        return [SinglePlan.from_id(id) for id in self.ordered_plan_ids]

    @classmethod
    def from_json_profile(cls, id: str):
        path = os.path.dirname(os.path.abspath(__file__)) + f"/profiles/{id}.json"
        f = open(path, "r")
        profile = json.load(f)
        f.close()

        return cls(**profile)

    @classmethod
    def from_id(cls, id: UUID):
        data, count = supabase.table("Agents").select("*").eq("id", str(id)).execute()
        print(data[1][0])
        return cls(**data[1][0])

    # private
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
            importance=self.calculate_importance(description),
            related_memory_ids=related_memory_ids,
        )
        print("made new memory ", memory.id)

        self.memories.append(memory)

        # add to database
        data, count = supabase.table("Memories").insert(memory.db_dict()).execute()

        print_to_console("New Memory: ", Fore.BLUE, f"{memory}")

        return memory

    # private
    def _update_agent_row(self):
        row = {
            "full_name": self.full_name,
            "bio": self.bio,
            "directives": self.directives,
            "ordered_plan_ids": [str(plan_id) for plan_id in self.ordered_plan_ids],
            "state": self.state.db_dict(),
        }
        print("Updated ", self.full_name, " in db.")
        return supabase.table("Agents").update(row).eq("id", str(self.id)).execute()

    # private
    def _add_plan_rows(self, plans: list[SinglePlan]):
        for plan in plans:
            row = {
                "id": str(plan.id),
                "description": plan.description,
                "max_duration_hrs": plan.max_duration_hrs,
                "agent_id": str(self.id),
                "created_at": plan.created_at.isoformat(),
                "stop_condition": plan.stop_condition,
            }
            print("Added plan to db.")
            return supabase.table("Plans").insert(row).execute()

    def db_dict(self):
        return {
            "id": str(self.id),
            "full_name": self.full_name,
            "bio": self.bio,
            "directives": self.directives,
            "ordered_plan_ids": [str(plan_id) for plan_id in self.ordered_plan_ids],
            "state": self.state.db_dict(),
        }

    def add_observation_strings(self, memory_strings: list[str]):
        for memory_string in memory_strings:
            self._add_memory(memory_string, MemoryType.OBSERVATION)

    def related_memories(self, query: str, k: int = 5) -> list[RelatedMemory]:
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

    def summarize_activity(self, k: int = 20) -> str:
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

        low_temp_llm = ChatModel(ChatModelName.GPT4, temperature=0)

        response = low_temp_llm.get_chat_completion(
            summary_prompter.prompt,
            loading_text="🤔 Summarizing recent activity...",
        )

        return response

    def calculate_importance(self, memory_description: str) -> int:
        # Set up a complex chat model
        complex_llm = ChatModel(ChatModelName.GPT4, temperature=0)

        importance_parser = OutputFixingParser.from_llm(
            parser=PydanticOutputParser(pydantic_object=ImportanceRatingResponse),
            llm=complex_llm,
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

    def move_to_location(self, location_id: UUID):
        """Move the agents state, send event to Events table"""

        # first emit the depature event to the db
        event = Event(
            timestamp=datetime.datetime.now(),
            type=EventType.NON_MESSAGE,
            description=f"{self.full_name} left location: {Location.from_id(location_id).name}",
            location_id=self.state.location_id,
            witness_ids=Location.from_id(self.state.location_id).local_agent_ids,
        )

        data, count = supabase.table("Events").insert(event.db_dict()).execute()

        # Update the agents state to the new location
        self.state.location_id = location_id

        print_to_console(
            "Moved to ", Fore.BLUE, f"{Location.from_id(location_id).name}"
        )

        # emit the arrival to the db
        event = Event(
            timestamp=datetime.datetime.now(),
            type=EventType.NON_MESSAGE,
            description=f"{self.full_name} arrived at location: {Location.from_id(location_id).name}",
            location_id=self.state.location_id,
            witness_ids=Location.from_id(self.state.location_id).local_agent_ids,
        )

        data, count = supabase.table("Events").insert(event.db_dict()).execute()

        # update the agents row in the db
        self._update_agent_row()

    def reflect(self):
        recent_memories = sorted(
            self.memories, key=lambda memory: memory.last_accessed, reverse=True
        )[:REFLECTION_MEMORY_COUNT]

        print_to_console("Starting Reflection", Fore.CYAN, "🤔")

        # Set up a complex chat model
        chat_llm = ChatModel(ChatModelName.GPT4, temperature=0)

        # Set up the parser
        question_parser = OutputFixingParser.from_llm(
            parser=PydanticOutputParser(pydantic_object=ReflectionQuestions),
            llm=chat_llm,
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
            related_memories = self.related_memories(question, 20)

            # Format them into a string
            memory_strings = [
                f"{index}. {related_memory.memory.description}"
                for index, related_memory in enumerate(related_memories, start=1)
            ]

            # Make the reflection parser
            reflection_parser = OutputFixingParser.from_llm(
                parser=PydanticOutputParser(pydantic_object=ReflectionResponse),
                llm=chat_llm,
            )

            print_to_console("Reflecting on Question", Fore.GREEN, f"{question}")

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

    def plan(self) -> list[SinglePlan]:
        print_to_console("Starting to Plan", Fore.YELLOW, "📝")

        low_temp_llm = ChatModel(ChatModelName.GPT4, temperature=0)

        # Make the plan parser
        plan_parser = OutputFixingParser.from_llm(
            parser=PydanticOutputParser(pydantic_object=LLMPlanResponse),
            llm=low_temp_llm,
        )

        # Get a summary of the recent activity
        recent_activity = self.summarize_activity()

        print_to_console("Summarized Recent Activity", Fore.YELLOW, recent_activity)

        # Make the Plan prompter
        plan_prompter = Prompter(
            PromptString.MAKE_PLANS,
            {
                "time_window": PLAN_LENGTH,
                "location_descriptions": [
                    f"'{location.name}' - {location.description}\n"
                    for location in self.allowed_locations
                ],
                "full_name": self.full_name,
                "bio": self.bio,
                "directives": str(self.directives),
                "recent_activity": recent_activity,
                "current_plans": [
                    f"{index}. {plan.description}"
                    for index, plan in enumerate(self.ordered_plans)
                ],
                "format_instructions": plan_parser.get_format_instructions(),
            },
        )

        # Set up a complex chat model
        chat_llm = ChatModel(ChatModelName.GPT4, temperature=0.5)

        # Get the plans
        response = chat_llm.get_chat_completion(
            plan_prompter.prompt,
            loading_text="🤔 Making plans...",
        )

        # Parse the response into an object
        parsed_plans_response: LLMPlanResponse = plan_parser.parse(response)

        # Delete existing plans
        self.ordered_plan_ids = []

        # Make a bunch of new plan objects, put em into a list
        new_plans: list[SinglePlan] = []
        ordered_plan_ids = []
        for plan in parsed_plans_response.plans:
            new_plan = SinglePlan(
                description=plan.description,
                location_id=Location.from_name(plan.location_name).id,
                max_duration_hrs=plan.max_duration_hrs,
                agent_id=self.id,
                stop_condition=plan.stop_condition,
            )
            new_plans.append(new_plan)
            ordered_plan_ids.append(new_plan.id)

        # update the local agent object
        self.ordered_plan_ids = ordered_plan_ids

        # update the db agent row
        data, count = self._update_agent_row()

        # add the plans to the plan table
        data, count = self._add_plan_rows(new_plans)

        # Loop through each plan and print it to the console
        for index, plan in enumerate(new_plans):
            print_to_console(
                "Plan ",
                Fore.YELLOW,
                f"#{index}: {plan.description} @ {plan.location_id} (<{plan.max_duration_hrs} hrs) [Stop Condition: {plan.stop_condition}]",
            )

        return new_plans

    def run(self, steps: int = 1) -> None:
        step_duration = 0
        while step_duration < steps:
            current_plan = None

            # If we do not have a plan state, consult the plans or plan something new
            if self.state.plan_id is None:
                # If we have no plans, make some
                if len(self.ordered_plan_ids) == 0:
                    plans = self.plan()

                # Otherwise, just use the existing plans
                else:
                    plans = [
                        SinglePlan.from_id(plan_id) for plan_id in self.ordered_plan_ids
                    ]

                # Set the agent state
                self.state = AgentState(
                    plan_id=plans[0].id, location_id=plans[0].location_id
                )

                current_plan = plans[0]

            # Get the current plan
            current_plan = (
                SinglePlan.from_id(self.state.plan_id)
                if current_plan is None
                else current_plan
            )

            print_to_console(
                "Acting on Plan", Fore.YELLOW, f"{current_plan.description}"
            )

            # If we are not in the right location, move to the new location
            if self.state.location_id != current_plan.location_id:
                self.move_to_location(current_plan.location_id)

            # Execute the plan
            steps_left = steps - step_duration  # TODO: stop executor when this is 0

            # TODO: Tools are dependent on the location
            output = run_executor(current_plan.description)

            if "Final Response: Task Failed" in output:
                print_to_console("Plan Failed", Fore.RED, f"{current_plan.description}")
                # TODO: handle plan failure with a human
                return

            # If the plan is done, remove it from the list of plans
            elif "Final Response" in output:
                self.ordered_plan_ids.remove(current_plan.id)
                self.state = AgentState(plan_id=None, location_id=None)
