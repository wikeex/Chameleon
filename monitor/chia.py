import asyncio

from monitor.base import Monitor
import aiohttp
import ssl


class ChiaMonitor(Monitor):
    def __init__(self, ca_file, cert_file, key_file, host: str = 'localhost', port: int = 8560, interval: int = 30):
        super().__init__(interval)
        self.url = f'https://{host}:{port}/get_plots'
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
        pass

    async def _alert(self, message: str):
        pass


if __name__ == '__main__':
    chia = ChiaMonitor(
        ca_file='/home/wikeex/.chia/mainnet/config/ssl/ca/private_ca.crt',
        cert_file='/home/wikeex/.chia/mainnet/config/ssl/full_node/private_full_node.crt',
        key_file='/home/wikeex/.chia/mainnet/config/ssl/full_node/private_full_node.key'
    )
    asyncio.get_event_loop().run_until_complete(chia._fetch())
