"""
Pydantic models for the Parcel Feasibility Engine.
"""
from app.models.parcel import ParcelBase, ParcelCreate, Parcel
from app.models.analysis import (
    AnalysisRequest,
    AnalysisResponse,
    DevelopmentScenario,
    AnalysisSummary,
    RentControlData,
    RentControlUnit,
)
from app.models.economic_feasibility import (
    EconomicAssumptions,
    ConstructionInputs,
    ConstructionCostEstimate,
    RevenueInputs,
    RevenueProjection,
    TimelineInputs,
    CashFlow,
    FinancialMetrics,
    SensitivityInput,
    TornadoResult,
    MonteCarloInputs,
    MonteCarloResult,
    SensitivityAnalysis,
    FeasibilityAnalysis,
    FeasibilityRequest,
)
from app.models.user import (
    User,
    UserCreate,
    UserUpdate,
    UserResponse,
    Token,
    TokenPayload,
    LoginRequest,
)
from app.models.subscription import (
    Subscription,
    SubscriptionStatus,
    SubscriptionPlan,
    SubscriptionResponse,
    APIUsage,
    UsageStats,
)

__all__ = [
    # Parcel models
    "ParcelBase",
    "ParcelCreate",
    "Parcel",
    # Analysis models
    "AnalysisRequest",
    "AnalysisResponse",
    "DevelopmentScenario",
    "AnalysisSummary",
    "RentControlData",
    "RentControlUnit",
    # Economic feasibility models
    "EconomicAssumptions",
    "ConstructionInputs",
    "ConstructionCostEstimate",
    "RevenueInputs",
    "RevenueProjection",
    "TimelineInputs",
    "CashFlow",
    "FinancialMetrics",
    "SensitivityInput",
    "TornadoResult",
    "MonteCarloInputs",
    "MonteCarloResult",
    "SensitivityAnalysis",
    "FeasibilityAnalysis",
    "FeasibilityRequest",
    # User and auth models
    "User",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "Token",
    "TokenPayload",
    "LoginRequest",
    # Subscription and payment models
    "Subscription",
    "SubscriptionStatus",
    "SubscriptionPlan",
    "SubscriptionResponse",
    "APIUsage",
    "UsageStats",
]
