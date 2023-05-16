import re
from enum import Enum

from langchain.schema import BaseMessage, SystemMessage
from pydantic import BaseModel


class Examples(Enum):
    PLAN_EXAMPLES = [""]


class PromptString(Enum):
    REFLECTION_QUESTIONS = "Here are a list of statements:\n{memory_descriptions}\n\nGiven only the information above, what are 3 most salient high-level questions we can answer about the subjects in the statements?\n\n{format_instructions}"

    REFLECTION_INSIGHTS = "\n{memory_strings}\nWhat 5 high-level insights can you infer from the above statements?\nWhen referring to people, always specify their name.\n\n{format_instructions}"

    IMPORTANCE = "You are a memory importance AI. Given the character's profile and the memory description, rate the importance of the memory on a scale of 1 to 10, where 1 is purely mundane (e.g., brushing teeth, making bed) and 10 is extremely poignant (e.g., a break up, college acceptance). Be sure to make your rating relative to the character's personality and concerns.\n\nExample #1:\nName: Jojo\nBio: Jojo is a professional ice-skater who loves specialty coffee. She hopes to compete in the olympics one day.\nMemory: Jojo sees a new coffee shop\n\n Your Response: '{{\"rating\": 3}}'\n\nExample #2:\nName: Skylar\nBio: Skylar is a product marketing manager. She works at a growth-stage tech company that makes autonomous cars. She loves cats.\nMemory: Skylar sees a new coffee shop\n\n Your Response: '{{\"rating\": 1}}'\n\nExample #3:\nName: Bob\nBio: Bob is a plumber living in the lower east side of New York City. He's been working as a plumber for 20 years. On the weekends he enjoys taking long walks with his wife. \nMemory: Bob's wife slaps him in the face.\n\n Your Response: '{{\"rating\": 9}}'\n\nExample #4:\nName: Thomas\nBio: Thomas is a police officer in Minneapolis. He joined the force only 6 months ago, and having a hard time at work because of his inexperience.\nMemory: Thomas accidentally spills his drink on a stranger\n\n Your Response: '{{\"rating\": 6}}'\n\nExample #5:\nName: Laura\nBio: Laura is a marketing specialist who works at a large tech company. She loves traveling and trying new foods. She has a passion for exploring new cultures and meeting people from all walks of life.\nMemory: Laura arrived at the meeting room\n\n Your Response: '{{\"rating\": 1}}'\n\n{format_instructions} Let's Begin! \n\n Name: {full_name}\nBio: {private_bio}\nMemory:{memory_description}\n\n"

    RECENT_ACTIIVITY = "Given the following memories, generate a short summary of what {full_name} has been doing lately. Do not make up details that are not specified in the memories. For any conversations, be sure to mention if the conversations are finished or still ongoing.\n\nMemories: {memory_descriptions}"

    MAKE_PLANS = 'You are a plan generating AI, and your job is to help characters make new plans based on new information. Given the character\'s info (bio, goals, recent activity, current plans, and location context) and the character\'s current thought process, generate a new set of plans for them to carry out, such that the final set of plans include at least {time_window} of activity and include no more than 5 individual plans. The plan list should be numbered in the order in which they should be performed, with each plan containing a description, location, start time, stop condition, and max duration.\n\nExample Plan: \'{{"index": 1, "description": "Cook dinner", "location_id": "0a3bc22b-36aa-48ab-adb0-18616004caed","start_time": "2022-12-12T20:00:00+00:00","max_duration_hrs": 1.5, "stop_condition": "Dinner is fully prepared"}}\'\n\nFor each plan, pick the most reasonable location_name ONLY from this list: {allowed_location_descriptions}\n\n{format_instructions}\n\nAlways prioritize finishing any pending conversations before doing other things.\n\nLet\'s Begin!\n\nName: {full_name}\nBio: {private_bio}\nGoals: {directives}\nLocation Context: {location_context}\nCurrent Plans: {current_plans}\nRecent Activity: {recent_activity}\nThought Process: {thought_process}\nImportant: Encourage the character to collaborate with other characters in their plan.\n\n'

    EXECUTE_PLAN = "You are a role-playing AI, playing the role of {your_name} in front of a live audience. Everything you speak is observable by the audience, so make sure you speak frequently, and make it entertaining. You cannot interact with the audience directly.\n\nGiven the following context and tools, proceed as if you were {your_name}. Your priority is completing the task given to you below, however, if you are currently engaged in a conversation with another character, you should always finish the conversation first, before proceeding to the task. Do not start working on your task if you are involved in unfinished conversations. Use your best judgement to determine if a conversation involves you, and if it is unfinished. You do not need to respond to every message you get.\n\nHere is your character's bio:\n{your_private_bio}\n\nHere is your location and a description of the other characters nearby, with whom you can speak:\n\n{location_context}\n\nHere are some relevant memories:\n```\n{relevant_memories}\n```\n\nHere is some relevant conversation history:\n```\n{conversation_history}\n```\n\nHere are the tools you have access to:\n{tools}\n\nYour response should use the following format:\n\nTask: the task you must complete\nThought: your thoughts about what you should do\nAction: the action to take, which must be one of these words: [{tool_names}]\nAction Input: the input to the action\nObservation: the result of the action\n... (this Thought/Action/Action Input/Observation can repeated N times)\nThought: 'I have completed the task'\nFinal Response: the final response to the task\n\nIf you are not ready with a final response, then you must take an action.\n\nIf you determine that you are incapable of completing the task with the tools you have been given, return 'Final Response: Need Help', however, if you are in dialog with another character, responses such as 'I don't know' are valid responses. When in dialog, you should never, under any circumstance, break character, or admit that you are an AI.\nIf the task is complete and no specific response is needed, return 'Final Response: Done'\nBegin!\n\nTask: {input}\n\n{agent_scratchpad}"

    REACT = "You are a role-playing AI, playing the role of {full_name}.\n\nGiven the following information about your character and their current context, decide how they should proceed with their current plan. Your decision must be one of: [\"postpone\", \"continue\", or \"cancel\"]. If your character's current plan is no longer relevant to the context, you should cancel them. If your character's current plan is still relevant to the context, but something new has happened that takes priority, you should decide to postpone, so you can do something else first, and then return to the current plan later. In all other cases, you should continue.\n\nResponding to other characters should always take priority when a response is necessary. A response is considered necessary if it would rude not to respond. For example, let's say your current plan is to read a book, and Sally asks 'what are you reading?'. In this situation, you should postpone your current plan (reading) so that you can respond to the inbound message, because in this context, it would be rude not to respond to Sally. In cases where your current plan involves a dialog with another character, you don't need to postpone to respond to that character. For example, let's say your current plan is to talk to Sally, and then Sally says hello to you. In this situation, you should continue your current plan (talk to sally). In cases where no verbal response is needed from you, you should continue. For example, let's say your current plan is to take a walk and you've just said 'Bye' to Sally, then Sally says 'Bye' back to you. In this case, no verbal response is necessary, and you should continue with your plan.\n\nAlways include a thought process in addition to your decision, and in cases where you choose to postpone your current plan, include the specifications of the new plan.\n\n{format_instructions}\n\nHere's some information about your character:\n\nName: {full_name}\n\nBio: {private_bio}\n\nGoals: {directives}\n\nHere's some context about your character at this moment:\n\nLocation Context: {location_context}\n\nRecent Activity: {recent_activity}\n\nConversation History: {conversation_history}\n\nHere is your characters current plan: {current_plan}\n\nHere are the new events that have occured sincce your character made this plan: {event_descriptions}.\n"

    GOSSIP = "You are {full_name}. \n{memory_descriptions}\n\nBased on the above statements, say one or two sentences that are interesting to others present at your location: {other_agent_names}.\nWhen referring to others, always specify their name."

    HAS_HAPPENED = "Given the following character's observations and a description of what they are waiting for, state whether or not the event has been witnessed by the character.\n{format_instructions}\n\nExample:\n\nObservations:\nJoe walked into the office @ 2023-05-04 08:00:00+00:00\nJoe said hi to Sally @ 2023-05-04 08:05:00+00:00\nSally said hello to Joe @ 2023-05-04 08:05:30+00:00\nRebecca started doing work @ 2023-05-04 08:10:00+00:00\nJoe made some breakfast @ 2023-05-04 08:15:00+00:00\n\nWaiting For: Sally responded to Joe\n\n Your Response: '{{\"has_happened\": true, \"date_occured\": 2023-05-04 08:05:30+00:00}}'\n\nLet's Begin!\n\nObservations:\n{memory_descriptions}\n\nWaiting For: {event_description}\n"

    OUTPUT_FORMAT = "\n\n(Remember! Make sure your output always conforms to one of the following two formats:\n\nA. If you are done with the task:\nThought: 'I have completed the task'\nFinal Response: <str>\n\nB. If you are not done with the task:\nThought: <str>\nAction: <str>\nAction Input: <str>\nObservation: <str>)\n"


class Prompter(BaseModel):
    template: str
    inputs: dict

    def __init__(self, template: PromptString | str, inputs: dict) -> None:
        if isinstance(template, PromptString):
            template = template.value

        super().__init__(inputs=inputs, template=template)

        # Find all variables in the template string
        input_names = set(re.findall(r"{(\w+)}", self.template))

        # Check that all variables are present in the inputs dictionary
        missing_vars = input_names - set(self.inputs.keys())
        if missing_vars:
            raise ValueError(f"Missing inputs: {missing_vars}")

    @property
    def prompt(self) -> list[BaseMessage]:
        final_string = self.template.format(**self.inputs)
        messages = [SystemMessage(content=final_string)]
        return messages
