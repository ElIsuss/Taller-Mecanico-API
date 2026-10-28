from contextlib import asynccontextmanager
from fastapi import FastAPI
import app.core.models  # noqa: F401  (registra todos los modelos y relaciones)
from app.core.config import settings
from app.core.database import create_engine_and_session_maker
from app.core.exceptions import register_exception_handlers
from app.modules.clientes.router import router as clientes_router
from app.modules.clientes.router import router_vehiculos
from app.modules.health.router import router as health_router
from app.modules.ordenes.router import router as ordenes_router
from app.modules.ordenes.router import router_estados
from app.modules.repuestos.router import router as repuestos_router


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

register_exception_handlers(app)

app.include_router(clientes_router)
app.include_router(router_vehiculos)
app.include_router(repuestos_router)
app.include_router(ordenes_router)
app.include_router(router_estados)
app.include_router(health_router)