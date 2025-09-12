import pytest
from unittest.mock import AsyncMock, patch
import redis.asyncio as aioredis
from src.services import redis_service


class TestRedisClient:
    """A collection of tests for the redis_service.get_redis_client function."""

    @pytest.mark.asyncio
    async def test_returns_client(self):
        """Tests that the function returns a Redis object."""
        client = await redis_service.get_redis_client()
        assert client is not None
        assert isinstance(client, aioredis.Redis)

    @pytest.mark.asyncio
    async def test_mocked_client(self):
        """Tests the function with a mocked redis_client at the module level."""
        fake_client = AsyncMock()
        with patch("src.services.redis_service.redis_client", fake_client):
            client = await redis_service.get_redis_client()
            assert client == fake_client
