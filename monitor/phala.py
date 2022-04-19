import asyncio
from concurrent.futures import ThreadPoolExecutor

import aiohttp
from substrateinterface import SubstrateInterface

from log import logger
from monitor.base import Monitor
from typing import List, Tuple, Union, Any
import docker

from utils import exception_catch


class PhalaMonitor(Monitor):

    def __init__(self, workers: Union[List[str], Tuple[str]],
                 prb_host: str,
                 node_host: str,
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
        self.prb_host = prb_host
        self.node_host = node_host
        self.prb_fetcher_working = True
        self.prb_fetcher_block = 0

    @staticmethod
    async def _post(url: str, *, data: Any = None, **kwargs: Any):
        try:
            headers = {"Content-Type": "application/json"}
            async with aiohttp.ClientSession() as session:
                async with session.post(url, data=data, headers=headers, **kwargs) as response:
                    return await response.json()
        except Exception as e:
            logger.error(f'向{url}发送post请求发生错误：{e}', exc_info=True)

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
        loop = asyncio.new_event_loop()
        while True:
            loop.run_until_complete(asyncio.sleep(self.internal))
            for worker in self.workers:
                try:
                    result = self._fetch_worker_status(worker)
                    if result['state'] not in ['MiningIdle', 'Mining']:
                        logger.error(f'substrate worker {worker} is abnormal, current state: {result["state"]}')
                        loop.run_until_complete(self._alert(f'substrate worker {worker} 非正常工作状态，请检查！'))
                    else:
                        logger.info(f'substrate worker {worker} state is {result["state"]}')
                except Exception as e:
                    logger.error(f'fetch substrate worker {worker} status encounter an error: {e}', exc_info=True)
                    loop.run_until_complete(self._alert(f'获取worker状态失败，请检查网络或节点状态！'))

    async def monitor(self):
        pool = ThreadPoolExecutor(max_workers=10)
        worker_task = asyncio.get_event_loop().run_in_executor(pool, self._worker_monitor)
        await asyncio.gather(
            worker_task,
            self._prb_fetcher_status(),
            self._prb_monitor()
        )

    async def _alert(self, message: str):
        print(message)

    async def _prb_fetcher_status(self):
        prb_monitor_url = f'{self.prb_host}/api/query_fetcher'
        prb_monitor_req_data = {
            'callOnlineFetcher': {}
        }
        while True:
            await asyncio.sleep(20)
            prb_monitor_data = await self._post(prb_monitor_url, json=prb_monitor_req_data)
            if not prb_monitor_data:
                logger.error(f'获取prb fetch状态错误：{prb_monitor_data}')
                continue
            fetcher_state = prb_monitor_data['content']['fetcherStateUpdate']

            logger.info(f'fetch是否已经同步synched：{fetcher_state["synched"]}')
            if fetcher_state['synched'] is False:
                sync_diff = fetcher_state['paraBlobHeight'] - self.prb_fetcher_block
                logger.info(f'上次同步到的高度：{self.prb_fetcher_block}，本次同步到的高度：{fetcher_state["paraBlobHeight"]}')
                self.prb_fetcher_working = False if sync_diff < 1 else True
            else:
                self.prb_fetcher_working = True

            self.prb_fetcher_block = fetcher_state['paraBlobHeight']

    @exception_catch
    async def _prb_monitor(self):
        watching_names = ['node', 'fetch', 'lifecycle', 'trade']

        while True:
            await asyncio.sleep(self.internal)
            try:
                client = docker.from_env()
            except Exception as e:
                logger.error(f'获取docker环境错误：{e}', exc_info=True)
                continue

            containers = {}
            # 监控各个docker容器的状态
            for container in client.containers.list(all=True):
                containers[container.name] = container

            logger.info(f'当前监控的docker镜像：{containers.keys()}')
            for name in watching_names:
                container = containers.get(name)
                if container is None:
                    logger.error(f'监控的docker容器不存在：{name}')
                    await self._alert(f'监控的docker容器不存在：{name}')
                if container.status != 'running':
                    logger.error(f'监控的docker容器状态异常! name: {name}, status: {container.status}')
                    await self._alert(f'监控的docker容器状态异常! name: {name}, status: {container.status}')
                    container.restart()

            # 监控khala节点的高度
            khala_node_req = {"id": 1, "jsonrpc": "2.0", "method": "system_syncState", "params": []}
            khala_node_data = await self._post(self.node_host, json=khala_node_req)
            if not khala_node_data:
                logger.error(f'获取khala节点高度错误：{khala_node_data}', exc_info=True)
                continue

            current_height = khala_node_data['result']['currentBlock']
            highest_height = khala_node_data['result']['highestBlock']
            logger.info(f'检查node同步高度，当前同步高度：{current_height}，链上高度：{highest_height}')

            if highest_height - current_height > 8:
                logger.info(f'当前同步高度落后于链上高度：{highest_height - current_height}，开始重启node')
                containers['node'].stop()
                containers['node'].start()
                containers['fetch'].start()
                containers['lifecycle'].start()
                containers['trade'].start()
                # 重启过后不能继续执行，下面的服务可能还没准备好，重新开启循环
                continue

            # 监控fetch运行状态
            logger.info(f'prb fetch当前运行状态：{self.prb_fetcher_working}')
            if self.prb_fetcher_working is not True:
                logger.info(f'prb fetch当前未正常运行，现在重启。')
                containers['fetch'].restart()

            # 监控worker同步状态
            # 首先获取各个worker的uuid
            worker_url = f'{self.prb_host}/api/query_manager'
            worker_req = {"callOnlineLifecycleManager": {}}

            workers_data = await self._post(worker_url, json=worker_req)
            workers = workers_data['content']['lifecycleManagerStateUpdate']['workers']
            workers = [worker for worker in workers if not worker['deleted'] and worker['enabled']]
            logger.info(f'当前监控的所有worker：{workers}')

            workers_state_req = {"queryWorkerState": {"ids": [{'uuid': worker['uuid']} for worker in workers]}}
            workers_state_data = await self._post(worker_url, json=workers_state_req)

            for worker in workers_state_data['content']['workerStateUpdate']['workerStates']:
                logger.info(f'worker {worker["worker"]["name"]}当前同步状态：{worker["status"]}')
                if worker['status'] == 'S_ERROR':
                    restart_worker_req = {
                        "requestStartWorkerLifecycle": {"requests": [{"id": {"uuid": worker['worker']['uuid']}}]}
                    }
                    headers = {"Content-Type": "application/json"}
                    async with aiohttp.ClientSession() as session:
                        async with session.post(worker_url, json=restart_worker_req, headers=headers) as response:
                            if response.status != 200:
                                logger.error(f'重启worker时发生错误，http状态码：{response.status}')


if __name__ == '__main__':
    phala = PhalaMonitor(
        [
            '0xfce4d9fed94760c944b0c9bcbcf8d64b2a37137c6e1408568a7206b15d02b658',
            '0x520bbce00afab260ec99dbeaff70d1726482126aff28bfac94ad5d4d09df8a55'
        ],
        prb_host='http://127.0.0.1:3000',
        node_host='http://127.0.0.1:9933'
    )
    asyncio.get_event_loop().run_until_complete(phala.monitor())
