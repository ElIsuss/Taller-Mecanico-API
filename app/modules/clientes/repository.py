"""Client-domain repository definitions."""

from app.core.repository import SoftDeleteRepository
from app.modules.clientes.models import Cliente, Vehiculo


class ClienteRepository(SoftDeleteRepository[Cliente]):
    model = Cliente


class VehiculoRepository(SoftDeleteRepository[Vehiculo]):
    model = Vehiculo


__all__ = ["ClienteRepository", "VehiculoRepository"]
