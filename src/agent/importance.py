from pydantic import BaseModel, Field, validator


class ImportanceRatingResponse(BaseModel):
    rating: int = Field(description="Importance integer from 1 to 10")

    @validator("rating")
    def validate_cron_jobs(cls, rating):
        if rating < 1 or rating > 10:
            raise ValueError(f"rating must be between 1 and 10. Got: {rating}")

        return rating
