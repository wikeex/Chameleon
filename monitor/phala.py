from monitor.base import Monitor


class PhalaMonitor(Monitor):

    def __init__(self, host: str, port: int, work):
        self.rpc_endpoint = f'http://{host}:{port}'
        self.substrate = None
        self.worker_pid =

    async def _fetch(self):
        result = self.substrate.query(
            module='phalaMining',
            storage_function='miners',
            params=[f'{}{}']
        )

    async def monitor(self):
        pass

    async def _alert(self, message: str):
        pass