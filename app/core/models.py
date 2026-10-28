"""Import every model module so SQLModel.metadata is fully populated.

Alembic and the application import this module before configuring mappers, so
cross-module relationships (declared with string forward references) resolve.
"""

from app.modules.auth.models import (  # noqa: F401
    AsignacionRol,
    EventoSeguridad,
    IntentoAcceso,
    Usuario,
)
from app.modules.clientes.models import Cliente  # noqa: F401
from app.modules.ordenes.models import (  # noqa: F401
    EstadoOrden,
    HistorialEstadoOrden,
    HistorialPrecioRepuesto,
    ItemOrden,
    MovimientoStock,
    OrdenTrabajo,
)
from app.modules.repuestos.models import Repuesto  # noqa: F401
from app.modules.vehiculos.models import Vehiculo  # noqa: F401
