from pydantic import BaseModel, Field
import datetime


class SinglePlan(BaseModel):
    index: int = Field(description="The plan number")
    description: str = Field(description="A description of the plan")
    duration: float = Field(description="The duration of the plan in hours")
    start_time: datetime.datetime = Field(description="The starting time, using this strftime format string: '%H:%M - %m/%d/%y'")


class PlanningResponse(BaseModel):
    plans: list[SinglePlan] = Field(description="A numbered list of plans")
