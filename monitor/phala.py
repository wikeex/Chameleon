import asyncio
from concurrent.futures import ThreadPoolExecutor

from substrateinterface import SubstrateInterface

from log import logger
from monitor.base import Monitor
from typing import List, Tuple, Union


class PhalaMonitor(Monitor):

    def __init__(self, workers: Union[List[str], Tuple[str]],
                 substrate_url: str = f'wss://khala.api.onfinality.io/public-ws',
                 interval: int = 30
                 ):
        super().__init__(interval=interval)
        self.substrate_url = substrate_url
        self.workers = workers
        self.substrate = SubstrateInterface(
            url="wss://khala.api.onfinality.io/public-ws",
            ss58_format=42,
            type_registry_preset='kusama'
        )

    def _fetch(self, worker_public_hash):
        # 获取worker绑定的账户
        account = self.substrate.query(
            module='PhalaMining',
            storage_function='WorkerBindings',
            params=[worker_public_hash]
        )

        # 使用worker绑定的账户查询worker的状态
        result = self.substrate.query(
            module='PhalaMining',
            storage_function='Miners',
            params=[account.value]
        )
        return result.value

    def _monitor(self):
        loop = asyncio.new_event_loop()
        while True:
            for worker in self.workers:
                try:
                    result = self._fetch(worker)
                    if result['state'] not in ['MiningIdle', 'Mining']:
                        logger.error(f'phala worker {worker} is abnormal, current state: {result["state"]}')
                        loop.run_until_complete(self._alert(f'phala worker {worker} 非正常工作状态，请检查！'))
                    else:
                        logger.info(f'phala worker {worker} state is {{result["state"]}}')
                except Exception as e:
                    logger.error(f'fetch phala worker {worker} status encounter an error: {e}')
                    loop.run_until_complete(self._alert(f'获取worker状态失败，请检查网络或节点状态！'))
                loop.run_until_complete(asyncio.sleep(self.internal))

    async def monitor(self):
        pool = ThreadPoolExecutor(max_workers=10)
        await asyncio.get_event_loop().run_in_executor(pool, self._monitor)

    async def _alert(self, message: str):
        print(message)


if __name__ == '__main__':
    phala = PhalaMonitor(['0xd6edac6c588244402e8a256927f99be6519ca5578e0ca9760a4e8537b0e5d275'])
    asyncio.get_event_loop().run_until_complete(phala.monitor())