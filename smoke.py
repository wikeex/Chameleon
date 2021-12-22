import asyncio
import aiohttp
from random import choice
from log import logger
from aiohttp import ClientTimeout


class Smoke:
    def __init__(self):
        self.common_tasks_q = asyncio.queues.Queue(maxsize=1000)
        self.continuous_task_q = asyncio.queues.Queue(maxsize=100)
        self.user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36' \
                          ' (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36 Edg/96.0.1054.57'
        self.headers = {
            'user-agent': self.user_agent
        }
        self.urls = []

    async def _common_task(self):
        async with aiohttp.ClientSession(headers=self.headers, timeout=ClientTimeout(total=3)) as client:
            while True:
                url = 'https://' + await self.common_tasks_q.get()
                for times in range(10):
                    try:
                        async with client.get(url=url.strip()) as response:
                            if response.status != 200:
                                break
                            logger.debug(f'smoke _common_task request {url} success {times + 1} times')
                            await asyncio.sleep(1)
                    except Exception as e:
                        logger.info(f'smoke _common_task request {url} encounter an error: {e}')
                        break

    async def _continuous_task(self):
        async with aiohttp.ClientSession(headers=self.headers, timeout=ClientTimeout(total=3)) as client:
            while True:
                url = 'https://' + await self.continuous_task_q.get()
                while True:
                    try:
                        async with client.get(url=url.strip()) as response:
                            if response.status != 200:
                                break
                            logger.debug(f'smoke _continuous_task request {url} success')
                            await asyncio.sleep(1)
                    except Exception as e:
                        logger.info(f'smoke _continuous_task request {url} encounter an error: {e}')
                        break

    def _read_urls(self):
        with open('sites.txt', 'r') as f:
            self.urls = f.readlines()
            logger.info(f'read {len(self.urls)} sites')

    async def _q_put(self, q: asyncio.queues.Queue):
        while True:
            url = choice(self.urls)
            await q.put(url)

    async def release(self):
        self._read_urls()
        logger.info(f'releasing smoke...')
        await asyncio.gather(
            self._q_put(self.common_tasks_q),
            self._q_put(self.continuous_task_q),
            *[self._continuous_task() for _ in range(100)],
            *[self._common_task() for _ in range(1000)]
        )


if __name__ == '__main__':
    smoke = Smoke()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(smoke.release())
