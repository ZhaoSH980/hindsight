"""Domain schemas: claims, memo, run config. Spec §3.3."""
from __future__ import annotations

from enum import Enum
from typing import Literal, Union

from pydantic import BaseModel, Field, model_validator


class ClaimType(str, Enum):
    direction = "direction"
    magnitude = "magnitude"
    volatility = "volatility"


class GradeStatus(str, Enum):
    hit = "hit"
    miss = "miss"
    ungradable = "ungradable"


class DirectionPrediction(BaseModel):
    direction: Literal["up", "down"]
    threshold_pct: float = Field(gt=0)


class MagnitudePrediction(BaseModel):
    low_pct: float
    high_pct: float

    @model_validator(mode="after")
    def _ordered(self) -> "MagnitudePrediction":
        if self.low_pct > self.high_pct:
            raise ValueError("low_pct must be <= high_pct")
        return self


class VolatilityPrediction(BaseModel):
    relation: Literal["above", "below"]
    percentile: float = Field(ge=0, le=100)


Prediction = Union[DirectionPrediction, MagnitudePrediction, VolatilityPrediction]

_PREDICTION_FOR_TYPE = {
    ClaimType.direction: DirectionPrediction,
    ClaimType.magnitude: MagnitudePrediction,
    ClaimType.volatility: VolatilityPrediction,
}


class Claim(BaseModel):
    claim_id: str
    statement: str
    type: ClaimType
    ticker: str
    horizon_days: int = Field(gt=0)
    prediction: Prediction
    confidence: float = Field(ge=0, le=1)
    evidence: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def _prediction_matches_type(self) -> "Claim":
        expected = _PREDICTION_FOR_TYPE[self.type]
        if not isinstance(self.prediction, expected):
            raise ValueError(
                f"claim type {self.type.value} requires {expected.__name__}, "
                f"got {type(self.prediction).__name__}"
            )
        return self


class Memo(BaseModel):
    background: str
    bull_case: str
    bear_case: str
    conclusion: str
    claims: list[Claim] = Field(min_length=1)


class RunConfig(BaseModel):
    model: str = ""
    temperature: float = 0.2
    max_steps: int = Field(default=8, gt=0)
    memory_on: bool = False
    context_budget: int = Field(default=8000, gt=0)
    retrieval_top_k: int = Field(default=5, gt=0)
