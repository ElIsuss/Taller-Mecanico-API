"""Unit tests for C-04 Auth: schemas, tokens, cookies, and security functions."""

from datetime import datetime, timezone
import pytest
from pydantic import ValidationError
from starlette.responses import Response

from app.core.security import (
    constant_time_verify,
    create_access_token,
    decode_access_token,
    delete_access_token_cookie,
    hash_password,
    set_access_token_cookie,
    verify_password,
)
from app.modules.usuarios.schemas import Login, Me, Register, TokenData


def test_login_schema_valid():
    data = Login(email="TEST@DOMAIN.COM ", password="password123")
    assert data.email == "test@domain.com"
    assert data.password == "password123"


def test_login_schema_extra_forbid():
    with pytest.raises(ValidationError):
        Login(email="user@test.com", password="pwd", extra_field="forbidden")


def test_login_schema_password_limit():
    long_pwd = "a" * 73
    with pytest.raises(ValidationError):
        Login(email="user@test.com", password=long_pwd)


def test_register_schema_valid():
    data = Register(
        email="NewUser@Test.com ",
        nombre="Juan Perez",
        password="securePassword",
        documento="12345678",
        telefono="555-1234",
    )
    assert data.email == "newuser@test.com"
    assert data.nombre == "Juan Perez"


def test_register_schema_extra_forbid():
    with pytest.raises(ValidationError):
        Register(
            email="user@test.com",
            nombre="Juan",
            password="pwd",
            documento="123",
            rol="ADMIN",  # Forbidden field
        )


def test_register_schema_password_limit():
    long_pwd = "b" * 73
    with pytest.raises(ValidationError):
        Register(
            email="user@test.com",
            nombre="Juan",
            password=long_pwd,
            documento="123",
        )


def test_me_schema():
    me = Me(
        id=1,
        email="user@test.com",
        nombre="Test User",
        rol="CLIENTE",
        iat=1234567890,
    )
    assert me.id == 1
    assert me.rol == "CLIENTE"


def test_jwt_token_create_and_decode():
    data = {"sub": "42", "roles": ["ADMIN", "CLIENTE"]}
    token = create_access_token(data, expires_delta=3600)
    assert isinstance(token, str)

    payload = decode_access_token(token)
    assert payload["sub"] == "42"
    assert payload["roles"] == ["ADMIN", "CLIENTE"]
    assert "iat" in payload
    assert "exp" in payload
    assert payload["exp"] > payload["iat"]


def test_cookie_utilities():
    response = Response()
    token = "fake-jwt-token"
    set_access_token_cookie(response, token, max_age=1800, secure=False)

    cookie_header = response.headers.get("set-cookie", "")
    assert "access_token=fake-jwt-token" in cookie_header
    assert "httponly" in cookie_header.lower()
    assert "samesite=lax" in cookie_header.lower()
    assert "max-age=1800" in cookie_header.lower()

    del_response = Response()
    delete_access_token_cookie(del_response)
    del_cookie_header = del_response.headers.get("set-cookie", "")
    assert "Max-Age=0" in del_cookie_header or "expires=0" in del_cookie_header.lower()


@pytest.mark.asyncio
async def test_hash_password_length_check():
    with pytest.raises(ValueError, match="72 bytes"):
        await hash_password("x" * 73)
