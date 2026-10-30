"""Import every model module so SQLModel.metadata is fully populated.

Alembic and the application import this module before configuring mappers, so
cross-module relationships (declared with string forward references) resolve.
"""

from app.modules.clientes.models import Cliente, Vehiculo  # noqa: F401
from app.modules.ordenes.models import (  # noqa: F401
    EstadoOrden,
    HistorialEstadoOrden,
    ItemOrden,
    OrdenTrabajo,
)
from app.modules.repuestos.models import (  # noqa: F401
    HistorialPrecioRepuesto,
    MovimientoStock,
    Repuesto,
)
from app.modules.usuarios.models import (  # noqa: F401
    AsignacionRol,
    EventoSeguridad,
    IntentoAcceso,
    Usuario,
)
