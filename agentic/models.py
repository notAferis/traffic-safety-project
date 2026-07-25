from pydantic import BaseModel, ConfigDict, Field


class IncidentVerdict(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    observations: str = Field(
        min_length=1,
        max_length=1000,
        description=(
            "Literal observations from the image only. "
            "Describe visible vehicles, positions, damage, debris, smoke, fire, people, "
            "and road conditions. Do not speculate."
        ),
    )

    confidence_score: float = Field(
        ge=0,
        le=1,
        description="Confidence that the image depicts a real traffic accident.",
    )

    is_accident: bool = Field(
        description=(
            "True only when concrete visual evidence of a traffic accident is present. "
            "False for ordinary traffic, parked vehicles, congestion, or uncertain scenes."
        ),
    )