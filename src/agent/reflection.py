from pydantic import BaseModel, Field


class ReflectionQuestions(BaseModel):
    questions: tuple[str, str, str] = Field(description="The questions we can answer")


class ReflectionInsight(BaseModel):
    insight: str = Field(description="The insight")
    related_statements: list[int] = Field(
        description="A list of the statement numbers that support the insight"
    )


class ReflectionResponse(BaseModel):
    insights: list[ReflectionInsight] = Field(
        description="A list of insights and the statement numbers that support them."
    )
