"""Tests for app.modules.auth.models (C-02 task 2.1)."""

from sqlalchemy import inspect
from sqlmodel import SQLModel

import app.modules.auth.models as auth_models


def test_auth_module_imports_without_errors():
    """The auth models module must import cleanly (task 2.1 acceptance)."""
    assert auth_models is not None


def test_usuario_model_has_expected_columns_and_fk():
    """usuario: email, password_hash, password_cambiada_en, fecha_alta/fecha_baja, cliente_id FK."""
    inspector = inspect(SQLModel.metadata.tables["usuario"])
    columns = {c.name: c for c in inspector.columns}
    for col in ("id", "email", "password_hash", "password_cambiada_en", "fecha_alta", "fecha_baja", "cliente_id"):
        assert col in columns, f"usuario missing column: {col}"

    fks = {fk.name for fk in inspector.foreign_keys}
    assert any("cliente" in str(fk) for fk in inspector.foreign_keys), "usuario.cliente_id must FK to cliente.id"


def test_usuario_password_cambiada_en_is_timezone_aware():
    """password_cambiada_en must be DateTime(timezone=True)."""
    col = SQLModel.metadata.tables["usuario"].c.password_cambiada_en
    assert col.type.timezone is True


def test_rol_model_has_catalog_columns():
    """rol: id, nombre, fecha_alta, fecha_baja."""
    table = SQLModel.metadata.tables["rol"]
    for col in ("id", "nombre", "fecha_alta", "fecha_baja"):
        assert col in table.c, f"rol missing column: {col}"


def test_rol_asignacion_has_fks_and_vigencia_columns():
    """rol_asignacion: usuario_id FK, rol_id FK, fecha_desde, fecha_hasta, fecha_alta."""
    table = SQLModel.metadata.tables["rol_asignacion"]
    for col in ("id", "usuario_id", "rol_id", "fecha_desde", "fecha_hasta", "fecha_alta"):
        assert col in table.c, f"rol_asignacion missing column: {col}"

    fk_targets = {str(fk) for fk in table.foreign_keys}
    assert any("usuario" in t for t in fk_targets), "rol_asignacion.usuario_id must FK to usuario.id"
    assert any("rol" in t for t in fk_targets), "rol_asignacion.rol_id must FK to rol.id"


def test_relationships_defined():
    """Relationships must be declared on the ORM classes."""
    Usuario = auth_models.Usuario
    Rol = auth_models.Rol
    RolAsignacion = auth_models.RolAsignacion

    assert hasattr(Usuario, "rol_asignaciones") or hasattr(Usuario, "rol_asignacion")
    assert hasattr(RolAsignacion, "usuario")
    assert hasattr(RolAsignacion, "rol")
