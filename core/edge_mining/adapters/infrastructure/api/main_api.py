"""Initializes the FastAPI application for the Edge Mining system."""

from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from edge_mining.__version__ import __version__
from edge_mining.adapters.domain.climate.fast_api.router import router as climate_router
from edge_mining.adapters.domain.energy.fast_api.router import router as energy_router
from edge_mining.adapters.domain.forecast.fast_api.router import router as forecast_router
from edge_mining.adapters.domain.home_load.fast_api.router import router as home_load_router
from edge_mining.adapters.domain.miner.fast_api.router import router as miner_router
from edge_mining.adapters.domain.notification.fast_api.router import router as notification_router
from edge_mining.adapters.domain.optimization_unit.fast_api.router import router as optimization_unit_router
from edge_mining.adapters.domain.performance.fast_api.router import router as performance_router
from edge_mining.adapters.domain.policy.fast_api.router import router as policy_router

# Import dependency injection setup functions
from edge_mining.adapters.infrastructure.api.setup import get_logger, get_optimization_service, get_service_container
from edge_mining.adapters.infrastructure.external_services.fast_api.router import router as external_services_router
from edge_mining.adapters.infrastructure.rule_engine.fast_api.router import router as rule_engine_router
from edge_mining.adapters.infrastructure.websocket.router import router as ws_router
from edge_mining.application.services.optimization_service import OptimizationService
from edge_mining.shared.logging.port import LoggerPort


@asynccontextmanager
async def app_lifespan(api_app: FastAPI):
    """Application lifespan - startup and shutdown logic."""
    # Startup
    try:
        container = await get_service_container()
        if not container.is_initialized():
            # This should not happen if properly initialized in main
            raise RuntimeError("Services not initialized before FastAPI startup!")

        container.logger.info("FastAPI application started successfully")

        # We can add other startup logic here
        # e.g., database connections, external service checks, etc.

    except Exception as e:
        print(f"Failed to start FastAPI application: {e}")
        raise

    yield  # Application is running

    # Shutdown
    try:
        container.logger.info("FastAPI application shutting down...")
        # Add cleanup logic here if needed
    except Exception as e:
        print(f"Error during shutdown: {e}")


app = FastAPI(
    title="Edge Mining Core API",
    description="Core API for managing and monitoring the bitcoin mining energy optimization system.",
    version=__version__,
    lifespan=app_lifespan,
)

# TODO: set only localhost origins
origins = ["*"]

# User CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(energy_router, prefix="/api/v1", tags=["energy"])
app.include_router(miner_router, prefix="/api/v1", tags=["mining"])
app.include_router(policy_router, prefix="/api/v1", tags=["policy"])
app.include_router(optimization_unit_router, prefix="/api/v1", tags=["optimization_unit"])
app.include_router(external_services_router, prefix="/api/v1", tags=["external_services"])
app.include_router(rule_engine_router, prefix="/api/v1", tags=["rule_engine"])
app.include_router(notification_router, prefix="/api/v1", tags=["notification"])
app.include_router(forecast_router, prefix="/api/v1", tags=["forecast"])
app.include_router(home_load_router, prefix="/api/v1", tags=["home_load"])
app.include_router(performance_router, prefix="/api/v1", tags=["performance"])
app.include_router(climate_router, prefix="/api/v1", tags=["climate"])
app.include_router(ws_router, tags=["websocket"])
# Add more routers here (e.g., for configuration)


@app.get("/health", tags=["system"])
async def health_check():
    """Basic health check endpoint."""
    return {"status": "ok"}


@app.get("/api/version", tags=["system"])
async def get_version():
    """Get the current version of the Edge Mining software."""
    return {
        "version": __version__,
        "name": "Edge Mining",
    }


# Example endpoint using dependency injection
@app.post("/api/v1/evaluate", tags=["system"])
async def trigger_evaluation(
    logger: Annotated[LoggerPort, Depends(get_logger)],  # Inject logger
    optimization_service: Annotated[OptimizationService, Depends(get_optimization_service)],  # Inject service
):
    """Manually run all enabled optimization units."""
    logger.info("API run all enabled optimization units...")
    try:
        await optimization_service.run_all_enabled_units()
        return {"message": "All optimization units run successfully."}
    except Exception as e:
        logger.error("Error during API run optimization units.")
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {e}") from e


# --- To run this API (after setting up services): ---
# uvicorn edge_mining.adapters.infrastructure.api.main_api:app --reload
