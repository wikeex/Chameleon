import asyncio
import aiohttp
from aiohttp import ClientTimeout
from aiohttp_socks import ProxyConnector
from log import logger


async def check(proxy_address: str, username: str = '', password: str = '') -> bool:
    connector = ProxyConnector.from_url(f'socks5://{username}:{password}@{proxy_address}')
    url = 'https://www.google.com'
    try:
        async with aiohttp.ClientSession(connector=connector, timeout=ClientTimeout(total=5)) as session:
            async with session.get(url) as response:
                if response.status == 200:
                    logger.info(f'{proxy_address} 代理联通正常')
                    return True
                else:
                    logger.error(f'无法通过代理{proxy_address}连接{url}，响应状态：{response.status}')
                    return False
    except asyncio.TimeoutError:
        logger.error(f'检查代理超时，代理地址：{proxy_address}')
        return False
    except Exception as e:
        logger.error(f'检查代理连通性时发生错误：{e}')
        return False


async def forwarding(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    try:
        while not reader.at_eof():
            data = await reader.read(2048)
            writer.write(data)
    except Exception as e:
        logger.error(f'转发时发生错误：{e}')
    finally:
        writer.close()


async def handler(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    forwarding_reader, forwarding_writer = await asyncio.open_connection('127.0.0.1', 1080)
    await asyncio.gather(forwarding(reader, forwarding_writer), forwarding(forwarding_reader, writer))


async def forwarding_server():
    server = await asyncio.start_server(
        handler, '127.0.0.1', 8888)

    address = server.sockets[0].getsockname()
    logger.info(f'Serving on {address}')

    async with server:
        await server.serve_forever()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(forwarding_server())
