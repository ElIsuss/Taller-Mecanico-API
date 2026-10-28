from contextlib import asynccontextmanager
from fastapi import FastAPI, status
from app.core.config import settings
from app.core.database import create_engine_and_session_maker


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create engine and session maker, store in app.state
    engine, async_session_maker = create_engine_and_session_maker()
    app.state.db_engine = engine
    app.state.async_session_maker = async_session_maker
    yield
    # Shutdown: dispose database engine
    await app.state.db_engine.dispose()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)


@app.get("/health/live", status_code=status.HTTP_200_OK)
async def liveness_probe():
    """Liveness probe to check if the application is running."""
    return {"status": "alive"}


@app.get("/health/ready", status_code=status.HTTP_200_OK)
async def readiness_probe():
    """Readiness probe to check application and database connection readiness."""
    try:
        async with app.state.db_engine.connect() as conn:
            await conn.run_sync(lambda sync_conn: None)
        db_status = "connected"
    except Exception as e:
        db_status = f"disconnected: {str(e)}"
    
    return {"status": "ready", "database": db_status}