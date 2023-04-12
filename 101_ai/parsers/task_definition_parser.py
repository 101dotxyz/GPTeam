# Define your desired data structure.
from sys import implementation
from typing import Optional

from langchain.chat_models import ChatOpenAI
from langchain.output_parsers import OutputFixingParser, PydanticOutputParser
from pydantic import BaseModel, Field, validator

from ..utils.models import ChatModel, get_chat_model


class BackendEndpointDefinition(BaseModel):
    endpoint: str = Field(description="The endpoint url e.g. /endpoint-url")
    pseudocode: str = Field(description="The pseudocode for this endpoint in plain english")

class CronJobDefinition(BaseModel):
    cron: str = Field(description="The cron definition e.g. 0 0 * * *")
    url: str = Field(description="The backend endpoint url to trigger e.g. /endpoint-url")
class TaskDefinition(BaseModel):
    backend_endpoints: list[BackendEndpointDefinition] = Field(description="A list of endpoints for the backend web-server that will be triggered by cron tasks or frontend interactions")
    cron_jobs: list[CronJobDefinition] = Field(description="A list of necessary cron jobs and which functions they call")
    env_variables: list[str] = Field(description="A list of all necessary environment variables.")
    implementation_notes: str = Field(description="Any notes for the developer about how to implement the application")
    # tables: str = Field(description="A list of database tables with schema for each table")
    # frontend: str = Field(description="list of necessary frontend components")

    

def get_task_definition_parser(fix_output: bool = True) -> PydanticOutputParser:
  parser = PydanticOutputParser(pydantic_object=TaskDefinition)

  if not fix_output:
    return parser
  
  llm = get_chat_model(model=ChatModel.TURBO)
    
  return OutputFixingParser.from_llm(parser=parser, llm=llm)