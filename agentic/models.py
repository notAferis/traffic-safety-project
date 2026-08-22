from pydantic import BaseModel, ConfigDict, Field


class IncidentVerdict(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    vehicles_involved: str = Field(
        default="",
        description=(
            "Exact breakdown of vehicles visible in the scene: vehicle types (sedan, SUV, truck, bus, motorcycle), "
            "colors, estimated count, relative positions, and orientations (e.g. '1 red sedan flipped on side, 1 white truck rear-ended')."
        ),
    )

    damage_and_hazards: str = Field(
        default="",
        description=(
            "Physical structural damage, collision contact points, crushed bodywork, broken glass, deployed airbags, "
            "visible smoke, active fire, spilled fluids, or scattered debris fields."
        ),
    )

    road_blockage_status: str = Field(
        default="",
        description=(
            "Road blockage status: specific lanes blocked, off-road vehicle position, curb barrier collision, or traffic queuing severity."
        ),
    )

    observations: str = Field(
        min_length=1,
        max_length=1500,
        description=(
            "Comprehensive, literal physical observations visible in the image frame. "
            "Describe specific vehicles (types, colors), orientations, structural damage, "
            "collision contact points, scattered debris, smoke/fire, people/bystanders, and road blockage. "
            "Do not copy or repeat the input user prompt."
        ),
    )

    sms_report: str = Field(
        default="",
        description=(
            "A structured, highly detailed emergency dispatch SMS summary compiling all visual facts. "
            "Must follow the format: 'VEHICLES: <details> | DAMAGE: <details> | HAZARDS: <details> | ROAD: <details>'. "
            "Provide maximum visual detail for emergency responders."
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