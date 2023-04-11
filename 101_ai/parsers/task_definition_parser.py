# Define your desired data structure.
from typing import Optional

from langchain.chat_models import ChatOpenAI
from langchain.output_parsers import OutputFixingParser, PydanticOutputParser
from pydantic import BaseModel, Field, validator

from ..utils.models import ChatModel, get_chat_model


class TaskDefinition(BaseModel):
    backend_endpoints: str = Field(description="list of endpoints and corresponding detailed pseudocode for the backend web-server that will be triggered by cron tasks or frontend interactions")
    tables: str = Field(description="list of database tables with schema for each table")
    cron_jobs: str = Field(description="list of necessary cron jobs and which functions they call")
    env_variables: str = Field(description="list all necessary environment variables")
    frontend: str = Field(description="list of necessary frontend components")

    

def get_task_definition_parser(fix_output: bool = True) -> PydanticOutputParser:
  parser = PydanticOutputParser(pydantic_object=TaskDefinition)

  if not fix_output:
    return parser
  
  llm = get_chat_model(model=ChatModel.TURBO)
    
  return OutputFixingParser.from_llm(parser=parser, llm=llm)