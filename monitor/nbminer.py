import asyncio
from log import logger
from monitor.base import Monitor
import aiohttp


class NBMinerMonitor(Monitor):

    def __init__(self, host: str, port: int, alert_limit: float, interval: int = 30):
        super().__init__(interval)
        self.url = f'http://{host}:{port}/api/v1/status'
        self.alert_limit = alert_limit
        self.interval = interval

    async def _fetch(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(self.url) as response:
                return await response.json()

    async def monitor(self):
        while True:
            try:
                result = await self._fetch()
                local_hash_rate = float(result['miner']['total_hashrate'].strip('M '))
                if local_hash_rate < self.alert_limit:
                    logger.error(
                        f'NBMiner hash rate is too low, current: {local_hash_rate}M, except: {self.alert_limit}M'
                    )
                    await self._alert(f'NBMiner hash率过低，当前hash率：{local_hash_rate}M，警戒线：{self.alert_limit}M')
                else:
                    logger.info(f'NBMiner hash rate is normal, current: {local_hash_rate}, except: {self.alert_limit}M')
            except Exception as e:
                logger.error(f'fetch NBMiner status encounter an error: {e}', exc_info=True)
                await self._alert(f'连接NBMiner api发生错误，请检查服务')
            await asyncio.sleep(self.interval)

    async def _alert(self, message: str):
        ...
