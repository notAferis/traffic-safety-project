from pydantic import BaseModel, ConfigDict, Field


class IncidentVerdict(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    observations: str = Field(
        min_length=1,
        max_length=1000,
        description=(
            "Literal, detailed physical observations visible in the image frame. "
            "Describe specific vehicles (types, colors), orientations, structural damage, "
            "collision contact points, scattered debris, smoke/fire, people, and road blockage. "
            "Do not copy or repeat the input user prompt."
        ),
    )

    sms_report: str = Field(
        default="",
        description=(
            "A concise, detailed emergency dispatch SMS summary specifying scene facts: "
            "vehicle types/colors, impact severity, visible hazards (smoke/fire/debris), and road blockage. "
            "Example: 'Red sedan and white truck in collision. Heavy front damage, debris blocking left lane, smoke visible.'"
        ),
    )

    confidence_score: float = Field(
        ge=0,
        le=1,
        description="Confidence (0.0 to 1.0) that the image depicts a real traffic accident.",
    )

    is_accident: bool = Field(
        description=(
            "True ONLY when concrete visual evidence of a traffic accident is present. "
            "False for ordinary traffic, parked vehicles, congestion, or non-crash scenes."
        ),
    )