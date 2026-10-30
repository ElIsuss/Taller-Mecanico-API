import pytest
from app.core.security import hash_password, verify_password, constant_time_verify


@pytest.mark.asyncio
async def test_hash_and_verify_password():
    password = "test-password-123"
    hashed = await hash_password(password)
    
    # Verify correct password
    assert await verify_password(password, hashed) is True
    
    # Verify incorrect password
    assert await verify_password("wrong-password", hashed) is False


@pytest.mark.asyncio
async def test_constant_time_verify_with_existing_user():
    password = "test-password-123"
    hashed = await hash_password(password)
    
    assert await constant_time_verify(password, hashed) is True
    assert await constant_time_verify("wrong-password", hashed) is False


@pytest.mark.asyncio
async def test_constant_time_verify_with_nonexistent_user():
    """RN-09: Responds the same whether email exists or not (constant time)."""
    password = "test-password-123"
    
    # Should not raise and should return False
    result = await constant_time_verify(password, None)
    assert result is False
    
    # Also test with wrong password
    result = await constant_time_verify("wrong-password", None)
    assert result is False