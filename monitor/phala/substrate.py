import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Union, List, Tuple

from substrateinterface import SubstrateInterface
from websocket import WebSocketConnectionClosedException
from log import logger
from monitor.base import Monitor


class SubstrateMonitor(Monitor):

    def __init__(self, workers: Union[List[str], Tuple[str]],
                 substrate_url: str = f'wss://khala.api.onfinality.io/public-ws',
                 interval: int = 30
                 ):
        super().__init__(interval=interval)
        self.substrate_url = substrate_url
        self.workers = workers
        self.substrate = SubstrateInterface(
            url=self.substrate_url,
            ss58_format=42,
            type_registry_preset='kusama'
        )

    def _fetch_worker_status(self, worker_public_hash):
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

    def _worker_monitor(self):
        """
        在substrate上获取worker挖矿状态
        :return:
        """
        while True:
            time.sleep(self.internal)
            for worker in self.workers:
                try:
                    result = self._fetch_worker_status(worker)
                    if result['state'] not in ['MiningIdle', 'Mining']:
                        logger.error(f'substrate worker {worker} is abnormal, current state: {result["state"]}')
                        self._alert(f'substrate worker {worker} 非正常工作状态，请检查！')
                    else:
                        logger.info(f'substrate worker {worker} state is {result["state"]}')
                except (WebSocketConnectionClosedException, BrokenPipeError) as e:
                    logger.info(f'fetch substrate worker {worker} status encounter a network error: {e}')
                except Exception as e:
                    logger.info(f'fetch substrate worker {worker} status encounter a unknown error: {e}', exc_info=True)

    async def monitor(self):
        pool = ThreadPoolExecutor(max_workers=10)
        await asyncio.get_event_loop().run_in_executor(pool, self._worker_monitor)

    def _alert(self, message: str):
        pass
