"""
FastAPI application entry point for the Parcel Feasibility Engine.

This module initializes the FastAPI app, registers routers, and configures
middleware for the enterprise-grade parcel analysis system.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import time
import logging

from app.api import analyze, rules, metadata, autocomplete
from app.core.config import settings
from app.utils.logging import setup_logging, get_logger

# Setup logging
setup_logging()
logger = get_logger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.DESCRIPTION,
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests with timing information."""
    start_time = time.time()

    # Log request
    logger.info(
        "Request started",
        extra={
            "method": request.method,
            "path": request.url.path,
            "client_host": request.client.host if request.client else None,
        }
    )

    # Process request
    response = await call_next(request)

    # Calculate duration
    duration = time.time() - start_time

    # Log response
    logger.info(
        "Request completed",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": round(duration * 1000, 2),
        }
    )

    return response


# Register routers
app.include_router(analyze.router, prefix=settings.API_V1_STR, tags=["Analysis"])
app.include_router(rules.router, prefix=settings.API_V1_STR, tags=["Rules"])
app.include_router(metadata.router, prefix=settings.API_V1_STR, tags=["Metadata"])
app.include_router(autocomplete.router)

# Rent control endpoint - TEMPORARILY DISABLED due to cloudscraper timeout issues
# from app.services.rent_control_api import lookup_mar, get_mar_summary, RentControlLookupError
# from fastapi import Query, HTTPException
#
# @app.get("/api/v1/rent-control")
# async def get_rent_control_data(
#     streetNumber: str = Query(..., description="Street number (e.g., '624')"),
#     streetName: str = Query(..., description="Street name (e.g., 'Lincoln Blvd')")
# ):
#     """
#     Query Santa Monica's Maximum Allowable Rent (MAR) database.
#
#     Returns rent control data for all units at the specified address,
#     including maximum allowable rent, tenancy dates, and unit details.
#     """
#     try:
#         units = lookup_mar(streetNumber, streetName)
#         return {
#             "address": f"{streetNumber} {streetName}",
#             "units": units,
#             "total_units": len(units)
#         }
#     except RentControlLookupError as e:
#         raise HTTPException(status_code=404, detail=str(e))
#     except Exception as e:
#         logger.error(f"Rent control lookup error: {e}")
#         raise HTTPException(status_code=500, detail="Failed to query rent control database")


@app.get("/health")
async def health_check():
    """
    Health check endpoint with feature flag status.

    Returns the health status of the API along with enabled features
    and configuration information.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "features": {
            "ab2011": settings.ENABLE_AB2011,
            "sb35": settings.ENABLE_SB35,
            "density_bonus": settings.ENABLE_DENSITY_BONUS,
            "sb9": settings.ENABLE_SB9,
            "ab2097": settings.ENABLE_AB2097,
        },
        "services": {
            "gis_services_configured": bool(settings.SANTA_MONICA_PARCEL_SERVICE_URL),
            "narrative_generation": settings.ENABLE_NARRATIVE_GENERATION,
            "database": settings.DATABASE_URL.split("@")[-1] if "@" in settings.DATABASE_URL else "configured",
        }
    }


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "description": settings.DESCRIPTION,
        "docs_url": "/docs",
        "health_check": "/health",
    }
