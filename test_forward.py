import pytest
from forward import check, forwarding_server


@pytest.mark.asyncio
async def test_check():
    result = await check(proxy_address='127.0.0.1:8888')
    assert result is True


@pytest.mark.asyncio
async def test_forwarding_server():
    await forwarding_server()
