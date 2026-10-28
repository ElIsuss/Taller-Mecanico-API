"""Tests for app.modules.usuarios.models (C-02 task 2.1)."""

from sqlmodel import SQLModel

import app.modules.usuarios.models as usuarios_models


def test_auth_module_imports_without_errors():
    """The usuarios models module must import cleanly (task 2.1 acceptance)."""
    assert usuarios_models is not None


def test_usuario_model_has_expected_columns():
    """usuario: id, email, nombre, password_hash, activo, flags y password_cambiada_en."""
    columns = set(SQLModel.metadata.tables["usuario"].c.keys())
    expected = {
        "id",
        "email",
        "nombre",
        "password_hash",
        "activo",
        "debe_cambiar_password",
        "password_cambiada_en",
    }
    assert expected <= columns, f"usuario missing columns: {sorted(expected - columns)}"


def test_usuario_email_is_unique_and_not_nullable():
    """Usuario.email es unico (UNIQUE simple, RN-02) y obligatorio."""
    col = SQLModel.metadata.tables["usuario"].c.email
    assert col.unique is True
    assert col.nullable is False


def test_usuario_password_cambiada_en_is_timezone_aware_and_nullable():
    """password_cambiada_en es timestamptz y nullable."""
    col = SQLModel.metadata.tables["usuario"].c.password_cambiada_en
    assert col.type.timezone is True
    assert col.nullable is True


def test_asignacion_rol_has_fks_and_vigencia_columns():
    """asignacion_rol: usuario_id, rol, desde, vence_en, revocada_en, otorgada_por."""
    table = SQLModel.metadata.tables["asignacion_rol"]
    expected = {
        "id",
        "usuario_id",
        "rol",
        "desde",
        "vence_en",
        "revocada_en",
        "otorgada_por",
    }
    assert expected <= set(table.c.keys())

    targets = {fk.target_fullname for fk in table.foreign_keys}
    assert "usuario.id" in targets
    assert any(fk.column.table.name == "usuario" for fk in table.foreign_keys)


def test_asignacion_rol_rol_check_constraint():
    """asignacion_rol.rol solo admite ADMIN/RECEPCION/MECANICO/CLIENTE."""
    table = SQLModel.metadata.tables["asignacion_rol"]
    checks = {c.name: str(c.sqltext) for c in table.constraints if c.__class__.__name__ == "CheckConstraint"}
    assert "ck_asignacion_rol_rol_valido" in checks
    sqltext = checks["ck_asignacion_rol_rol_valido"].upper()
    for rol in ("ADMIN", "RECEPCION", "MECANICO", "CLIENTE"):
        assert rol in sqltext


def test_asignacion_rol_partial_unique_index():
    """Un usuario no puede tener el mismo rol activo dos veces (RN-03)."""
    index = next(
        ix
        for ix in SQLModel.metadata.tables["asignacion_rol"].indexes
        if ix.name == "ix_asignacion_rol_usuario_rol_uc"
    )
    assert index.unique is True
    where = index.dialect_options["postgresql"].get("where")
    assert where is not None
    assert "REVOCADA_EN IS NULL" in str(where).upper()


def test_intento_acceso_columns_and_index():
    """intento_acceso registra email/ip/cuando/exito con indice compuesto."""
    table = SQLModel.metadata.tables["intento_acceso"]
    assert {"id", "cuando", "email", "ip", "exito"} <= set(table.c.keys())
    index_names = {ix.name for ix in table.indexes}
    assert "ix_intento_acceso_email_ip_cuando" in index_names


def test_evento_seguridad_columns():
    """evento_seguridad: id, cuando, actor, accion."""
    table = SQLModel.metadata.tables["evento_seguridad"]
    assert {"id", "cuando", "actor", "accion"} <= set(table.c.keys())


def test_auth_relationships_are_declared():
    """Usuario expone cliente, asignaciones_rol y relaciones hacia ordenes."""
    Usuario = usuarios_models.Usuario
    AsignacionRol = usuarios_models.AsignacionRol
    for attr in (
        "cliente",
        "asignaciones_rol",
        "roles_otorgados",
        "ordenes_asignadas",
        "historiales_estado",
        "movimientos_stock",
        "historiales_precio",
    ):
        assert hasattr(Usuario, attr), f"Usuario missing relationship: {attr}"
    assert hasattr(AsignacionRol, "usuario")
    assert hasattr(AsignacionRol, "otorgante")


def test_todas_las_fks_de_usuario_tienen_indice():
    """Cada FK de las tablas de auth tiene indice (regla del proyecto)."""
    table = SQLModel.metadata.tables["asignacion_rol"]
    indexed_columns = {tuple(col.name for col in ix.columns) for ix in table.indexes}
    assert ("usuario_id",) in indexed_columns
    assert ("otorgada_por",) in indexed_columns
