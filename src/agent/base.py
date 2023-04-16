from pydantic import BaseModel
from colorama import Fore
from langchain.output_parsers import OutputFixingParser, PydanticOutputParser
from typing import Optional
import json
import os

from .importance import ImportanceRatingResponse
from .reflection import ReflectionQuestions, ReflectionResponse
from ..memory.base import SingleMemory, MemoryType
from .plans import SinglePlan, PlanningResponse
from ..utils.parameters import REFLECTION_MEMORY_COUNT, PLAN_LENGTH
from ..utils.formatting import print_to_console
from ..utils.models import ChatModel, ChatModelName
from ..utils.prompt import Prompter, PromptString
from ..utils.supabase_client import supabase

class RelatedMemory(BaseModel):
    memory: SingleMemory
    relevance: float

    def __str__(self) -> str:
        return f"SingleMemory: {self.memory.description}, Relevance: {self.relevance}"


class AgentState(BaseModel):
    description: str


class Agent(BaseModel):
    id: str
    name: str
    bio: str
    memories: Optional[list[SingleMemory]] = []
    directives: Optional[list[str]] = None
    plans: Optional[list[SinglePlan]] = []
    state: Optional[AgentState]

    def __init__(
            self,
            id: str,
            name: str,
            bio: str,
            directives: list[str] = None,
            memories: list[SingleMemory] = [],
            plans: list[SinglePlan] = [], 
            state: AgentState = None
        ):
        
        super().__init__(
            id=id,
            name=name,
            bio=bio,
            directives=directives,
            memories=memories,
            plans=plans,
            state=state
        )

        print_to_console("New Agent Initialized: ", Fore.GREEN, self.bio) 
  
    @classmethod
    def from_json_profile(cls, id: str):
        path = os.path.dirname(os.path.abspath(__file__)) + f"/profiles/{id}.json"
        f = open(path, "r")
        profile = json.load(f)
        f.close()

        return cls(**profile)

    @classmethod
    def from_db(cls, id: str):
        pass

    # private
    def _add_memory(
        self, 
        description: str,
        type: MemoryType = MemoryType.OBSERVATION,
        related_memory_ids: list[str] = []
    ) -> SingleMemory:

        memory = SingleMemory(
            description=description,
            type=type,
            related_memory_ids=related_memory_ids,
            importance=self.calculate_importance(description)
        )
    
        self.memories.append(memory)

        print_to_console(
            "New Memory: ", Fore.BLUE, f"{memory}"
        )

        return memory

    def update_state(self, description: str):
        self.state = AgentState(description=description)

    def add_observation_strings(self, memory_strings: list[str]):
        for memory_string in memory_strings:
            self._add_memory(
                memory_string,
                MemoryType.OBSERVATION
            )
    
    def related_memories(self, query: str, k: int = 5) ->  list[RelatedMemory]:

        # Calculate relevance for each memory and store it in a list of dictionaries
        memories_with_relevance = [
            RelatedMemory(
                memory=memory,
                relevance=memory.relevance(query)
            )
            for memory in self.memories
        ]

        # Sort the list of dictionaries based on the 'relevance' key in descending order
        sorted_memories = sorted(
            memories_with_relevance, key=lambda x: x.relevance, reverse=True
        )

        return sorted_memories[:k]

    def summarize_activity(self, k: int = 20) -> str:

        recent_memories = sorted(
            self.memories, key=lambda memory: memory.created, reverse=True
        )[:k]

        summary_prompter = Prompter(
            PromptString.RECENT_ACTIIVITY,
            { 
                "name": self.name,
                "memory_descriptions": str([memory.description for memory in recent_memories]) 
            }
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
                "name": self.name,
                "bio": self.bio,
                "memory_description": memory_description,
                "format_instructions": importance_parser.get_format_instructions()
            }
        )

        response = complex_llm.get_chat_completion(
            importance_prompter.prompt,
            loading_text="🤔 Calculating memory importance...",
        )

        parsed_response: ImportanceRatingResponse = importance_parser.parse(response)

        rating = parsed_response.rating

        return rating

    def reflect(self):
        recent_memories = sorted(
            self.memories, key=lambda memory: memory.lastAccessed, reverse=True
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
                "format_instructions": question_parser.get_format_instructions()
            }
        )

        # Get the reflection questions
        response = chat_llm.get_chat_completion(
            questions_prompter.prompt, 
            loading_text="🤔 Thinking about what to reflect on..."
        )

        # Parse the response into an object
        parsed_questions_response: ReflectionQuestions = question_parser.parse(
            response
        )

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
                    "name": self.name, 
                    "memory_strings": str(memory_strings),
                    "format_instructions": reflection_parser.get_format_instructions(),
                }
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

    def plan(self):

        print_to_console("Starting Planning", Fore.YELLOW, "📝")

        low_temp_llm = ChatModel(ChatModelName.GPT4, temperature=0)

        # Make the plan parser
        plan_parser = OutputFixingParser.from_llm(
            parser=PydanticOutputParser(pydantic_object=PlanningResponse),
            llm=low_temp_llm,
        )

        # Get a summary of the recent activity
        recent_activity = self.summarize_activity()

        print_to_console(
            "Summarized Recent Activity",
            Fore.YELLOW,
            recent_activity
        )

        # Make the Plan prompter
        plan_prompter = Prompter(
            PromptString.MAKE_PLANS,
            {
                "time_window": '15 minutes', # PLAN_LENGTH,
                "name": self.name,
                "bio": self.bio,
                "directives": str(self.directives),
                "recent_activity": recent_activity,
                "current_plans": str(self.plans),
                "format_instructions": plan_parser.get_format_instructions()
            }
        )

        # Set up a complex chat model
        chat_llm = ChatModel(ChatModelName.GPT4, temperature=0.5)

        # Get the plans
        response = chat_llm.get_chat_completion(
            plan_prompter.prompt,
            loading_text="🤔 Making plans...",
        )

        # Parse the response into an object
        parsed_plans_response: PlanningResponse = plan_parser.parse(response)

        # Replace existing plans with the new ones
        self.plans = parsed_plans_response.plans

        # Loop through each plan and print it to the console
        for plan in self.plans:
            print_to_console("Plan ", Fore.YELLOW, f"#{plan.index}: {plan.description} ({str(plan.duration)} hrs)")








