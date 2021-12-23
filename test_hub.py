import pytest
from hub import check, Hub


@pytest.mark.asyncio
async def test_check():
    result = await check('localhost', 8888)
    assert result is True


@pytest.mark.asyncio
async def test_run_server():
    hub = Hub('localhost', 8888, [('localhost', 1080)])
    await hub.run()
