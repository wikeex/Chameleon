import pytest

from smoke import Smoke


@pytest.fixture(scope='module')
def smoke():
    return Smoke()


@pytest.mark.asyncio
async def test_release(smoke):
    await smoke.release()
