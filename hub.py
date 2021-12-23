import asyncio
from typing import List, Tuple

import aiohttp
from aiohttp import ClientTimeout
from aiohttp_socks import ProxyConnector

from common import alert
from log import logger
from random import choice


async def forwarding(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    try:
        while not reader.at_eof():
            data = await reader.read(2048)
            writer.write(data)
    except Exception as e:
        logger.error(f'转发时发生错误：{e}')
    finally:
        writer.close()


async def check(host: str, port: int, username: str = '', password: str = '') -> bool:
    connector = ProxyConnector.from_url(f'socks5://{username}:{password}@{host}:{port}')
    url = 'https://www.google.com'
    try:
        async with aiohttp.ClientSession(connector=connector, timeout=ClientTimeout(total=5)) as session:
            async with session.get(url) as response:
                if response.status == 200:
                    logger.info(f'{host}:{port} 代理联通正常')
                    return True
                else:
                    logger.error(f'无法通过代理{host}:{port}连接{url}，响应状态：{response.status}')
                    return False
    except asyncio.TimeoutError:
        logger.error(f'检查代理超时，代理地址：{host}:{port}')
        return False
    except Exception as e:
        logger.error(f'检查代理{host}:{port}连通性时发生错误：{e}', exc_info=True)
        return False


class Hub:
    def __init__(self, serv_host: str, serv_port: int, proxies: List[Tuple], check_interval: int = 30):
        self.proxies = proxies
        self.serv_host = serv_host
        self.serv_port = serv_port
        self.check_interval = check_interval
        self.valid_proxies = []
        self.chosen_proxy = None

    async def _check(self):
        while True:
            for proxy in self.proxies:
                is_connectable = await check(*proxy)
                if is_connectable is True:
                    if proxy not in self.valid_proxies:
                        self.valid_proxies.append(proxy)
                else:
                    if proxy in self.valid_proxies:
                        self.valid_proxies.remove(proxy)
                if len(self.valid_proxies) <= 0:
                    logger.error(f'No connectable proxy.')
                    await alert(f'无可用代理')
            logger.info(f'Connectable proxy: {self.valid_proxies}')
            await asyncio.sleep(self.check_interval)

    async def _handler(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        if len(self.valid_proxies) > 0:
            proxy = choice(self.valid_proxies)
            logger.debug(f'chosen {proxy} proxy')
            forwarding_reader, forwarding_writer = await asyncio.open_connection(proxy[0], proxy[1])
            await asyncio.gather(forwarding(reader, forwarding_writer), forwarding(forwarding_reader, writer))

    async def _run_server(self):
        server = await asyncio.start_server(
            self._handler, self.serv_host, self.serv_port)

        address = server.sockets[0].getsockname()
        logger.info(f'Serving on {address}')

        async with server:
            await server.serve_forever()

    async def run(self):
        await asyncio.gather(self._check(), self._run_server())
