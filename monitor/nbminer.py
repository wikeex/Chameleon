import asyncio

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
                    await self._alert(f'NBMiner hash率过低，当前hash率：{local_hash_rate}M，警戒线：{self.alert_limit}M')
            except Exception as e:
                print(e)
                await self._alert(f'无法连接NBMiner api，请检查服务')
            await asyncio.sleep(self.interval)

    async def _alert(self, message: str):
        ...
