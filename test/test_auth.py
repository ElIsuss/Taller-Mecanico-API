"""Integration tests for C-04 / C-07 auth endpoints and intento_acceso isolation.

Requires TEST_DATABASE_URL to be set with a PostgreSQL connection string.
"""

from datetime import datetime, timezone
import pytest
from sqlmodel import select

from app.core.security import hash_password
from app.main import app
from app.modules.usuarios.models import AsignacionRol, IntentoAcceso, Usuario
from app.modules.usuarios.service import registrar_intento_acceso


@pytest.fixture
async def auth_user(seed):
    """Crea un usuario de prueba con credenciales válidas y rol CLIENTE."""
    hashed = await hash_password("test-password-123")
    async with app.state.async_session_maker() as session:
        async with session.begin():
            user = Usuario(
                email="auth.user@test.com",
                nombre="Auth User Test",
                password_hash=hashed,
                activo=True,
                debe_cambiar_password=False,
            )
            session.add(user)
            await session.flush()
            rol = AsignacionRol(
                usuario_id=user.id,
                rol="CLIENTE",
            )
            session.add(rol)
            await session.flush()
            return user


@pytest.mark.asyncio
async def test_login_exitoso(client, auth_user):
    """Login con credenciales válidas.

    - Retorna 200 OK
    - Cookie `access_token` con HttpOnly, SameSite=lax, Max-Age
    - Body contiene los datos del usuario (sin password_hash)
    """
    response = await client.post(
        "/auth/login",
        json={"email": auth_user.email, "password": "test-password-123"},
    )
    assert response.status_code == 200, f"Esperaba 200, got {response.status_code}: {response.text}"

    cookie = response.cookies.get("access_token")
    assert cookie is not None, "Cookie access_token no incluida en respuesta"
    set_cookie = str(response.headers.get("set-cookie", ""))
    assert "HttpOnly" in set_cookie or "httponly" in set_cookie.lower()

    data = response.json()
    assert data["id"] == auth_user.id
    assert data["email"] == auth_user.email
    assert data["rol"] == "CLIENTE"
    assert "password_hash" not in str(data)


@pytest.mark.asyncio
async def test_login_invalido(client, auth_user):
    """Login con credenciales inválidas.

    - Retorna 401 Unauthorized
    - Mismo mensaje aunque el email no exista (RN-09)
    """
    response = await client.post(
        "/auth/login",
        json={"email": auth_user.email, "password": "password_incorrecta"},
    )
    assert response.status_code == 401
    assert response.json().get("detail") == "Invalid credentials"

    # Con email inexistente
    response_no_user = await client.post(
        "/auth/login",
        json={"email": "noexiste@test.com", "password": "password_incorrecta"},
    )
    assert response_no_user.status_code == 401
    assert response_no_user.json().get("detail") == "Invalid credentials"


@pytest.mark.asyncio
async def test_perfil_con_token_valido(client, auth_user):
    """Perfil del usuario autenticado con cookie válida."""
    login_resp = await client.post(
        "/auth/login",
        json={"email": auth_user.email, "password": "test-password-123"},
    )
    assert login_resp.status_code == 200
    token = login_resp.cookies.get("access_token")
    assert token is not None

    response = await client.get("/auth/yo", cookies={"access_token": token})
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == auth_user.id
    assert data["email"] == auth_user.email
    assert data["rol"] == "CLIENTE"
    assert "password_hash" not in str(data)


@pytest.mark.asyncio
async def test_perfil_sin_token(client):
    """Perfil sin cookie o con token inválido retorna 401."""
    response = await client.get("/auth/yo")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_logout(client, auth_user):
    """Logout invalida la cookie de sesión."""
    login_resp = await client.post(
        "/auth/login",
        json={"email": auth_user.email, "password": "test-password-123"},
    )
    assert login_resp.status_code == 200

    logout_resp = await client.post("/auth/logout")
    assert logout_resp.status_code == 204
    set_cookie = logout_resp.headers.get("set-cookie", "")
    assert "Max-Age=0" in set_cookie or "max-age=0" in set_cookie.lower()


@pytest.mark.asyncio
async def test_register_exitoso(client):
    """Registro atómico de cliente."""
    response = await client.post(
        "/auth/register",
        json={
            "email": "nuevo.cliente@test.com",
            "nombre": "Nuevo Cliente",
            "password": "Password123",
            "documento": "12345678-A",
            "telefono": "555-0100",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "nuevo.cliente@test.com"
    assert data["rol"] == "CLIENTE"
    assert "password_hash" not in str(data)
    assert "access_token" in response.cookies


@pytest.mark.asyncio
async def test_register_duplicado_email(client):
    """Registro con email duplicado retorna 409."""
    data = {
        "email": "duplicado@test.com",
        "nombre": "Duplicado",
        "password": "Password123",
        "documento": "87654321-B",
        "telefono": "555-0100",
    }
    r1 = await client.post("/auth/register", json=data)
    assert r1.status_code == 201

    r2 = await client.post(
        "/auth/register",
        json={**data, "documento": "99999999-Z"},
    )
    assert r2.status_code == 409


@pytest.mark.asyncio
async def test_rn08_intento_registrado_en_db(client, auth_user):
    """RN-08: Se registra un intento fallido en intento_acceso."""
    response = await client.post(
        "/auth/login",
        json={"email": auth_user.email, "password": "password_equivocada"},
    )
    assert response.status_code == 401

    async with app.state.async_session_maker() as session:
        result = await session.execute(
            select(IntentoAcceso).where(
                IntentoAcceso.email == auth_user.email,
                IntentoAcceso.exito == False,  # noqa: E712
            )
        )
        intentos = result.scalars().all()
        assert len(intentos) >= 1, "Debe registrarse al menos un intento fallido en intento_acceso"


@pytest.mark.asyncio
async def test_rn08_bloqueo_segun_intentos(client, auth_user):
    """RN-08: Se bloquea después de 5 intentos fallidos en 60s."""
    for _ in range(5):
        resp = await client.post(
            "/auth/login",
            json={"email": auth_user.email, "password": "password_equivocada"},
        )
        assert resp.status_code == 401

    # El sexto intento debe responder 429 con Retry-After
    resp6 = await client.post(
        "/auth/login",
        json={"email": auth_user.email, "password": "password_equivocada"},
    )
    assert resp6.status_code == 429
    assert "retry-after" in resp6.headers or "Retry-After" in resp6.headers


@pytest.mark.asyncio
async def test_rn08_login_correcto_reinicia_conteo(client, auth_user):
    """RN-08: Un login correcto reinicia el conteo efectivo de fallos."""
    for _ in range(3):
        resp = await client.post(
            "/auth/login",
            json={"email": auth_user.email, "password": "password_equivocada"},
        )
        assert resp.status_code == 401

    # Login correcto
    resp_ok = await client.post(
        "/auth/login",
        json={"email": auth_user.email, "password": "test-password-123"},
    )
    assert resp_ok.status_code == 200

    # Siguiente intento fallido no debe estar bloqueado (retorna 401, no 429)
    resp_next = await client.post(
        "/auth/login",
        json={"email": auth_user.email, "password": "password_equivocada"},
    )
    assert resp_next.status_code == 401


@pytest.mark.asyncio
async def test_rn08_intentos_perduran_rollback(client):
    """Task 2.2: Los intentos quedan registrados aunque la sesión principal sufra un rollback."""
    session_maker = app.state.async_session_maker
    async with session_maker() as main_session:
        # Abrir transacción en la sesión principal
        await main_session.begin()

        # Registrar intento de acceso
        await registrar_intento_acceso(
            main_session,
            "rollback_test@test.com",
            "192.168.1.50",
            exito=False,
        )

        # Forzar rollback explícito de la sesión principal
        await main_session.rollback()

    # Verificar en una sesión limpia e independiente que el intento persistió
    async with session_maker() as verify_session:
        result = await verify_session.execute(
            select(IntentoAcceso).where(
                IntentoAcceso.email == "rollback_test@test.com"
            )
        )
        intento = result.scalar_one_or_none()
        assert intento is not None, (
            "El intento de acceso debe persistir en la base de datos a pesar del rollback de la sesión principal"
        )
        assert intento.exito is False
        assert intento.ip == "192.168.1.50"
