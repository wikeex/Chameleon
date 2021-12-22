import asyncio

from monitor.base import Monitor
from log import logger
import aiohttp
import ssl


class ChiaMonitor(Monitor):
    def __init__(self, ca_file, cert_file, key_file, plots_count: int,
                 host: str = 'localhost', port: int = 8560, interval: int = 30):
        super().__init__(interval)
        self.url = f'https://{host}:{port}/get_plots'
        self.plots_count = plots_count
        self.ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH, cafile=ca_file)
        self.ssl_context.verify_mode = ssl.CERT_REQUIRED
        self.ssl_context.load_cert_chain(cert_file, key_file)
        self.headers = {
            'Content-Type': 'application/json'
        }

    async def _fetch(self):
        async with aiohttp.ClientSession(headers=self.headers, trust_env=True) as session:
            async with session.post(self.url, ssl=self.ssl_context, json={}) as response:
                if response.status == 200:
                    return await response.json()

    async def monitor(self):
        while True:
            try:
                result = await self._fetch()
                current_plots_count = len(result['plots'])
                if current_plots_count < self.plots_count:
                    logger.error(
                        f'quantity of plots is abnormal, current: {current_plots_count}, except: {self.plots_count}'
                    )
                    await self._alert(f'plots数量异常，当前数量：{current_plots_count}，预期数量：{self.plots_count}')
                else:
                    logger.info(f'chia status is normal.')
            except Exception as e:
                logger.error(f'fetch chia status encounter an error: {e}')
                await self._alert(f'获取plots数量失败，请检查网络和服务！')

    async def _alert(self, message: str):
        pass


if __name__ == '__main__':
    chia = ChiaMonitor(
        ca_file='/home/wikeex/.chia/mainnet/config/ssl/ca/private_ca.crt',
        cert_file='/home/wikeex/.chia/mainnet/config/ssl/full_node/private_full_node.crt',
        key_file='/home/wikeex/.chia/mainnet/config/ssl/full_node/private_full_node.key',
        plots_count=60
    )
    asyncio.get_event_loop().run_until_complete(chia._fetch())
