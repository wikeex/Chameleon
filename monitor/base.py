

class Monitor:
    async def monitor(self):
        raise NotImplementedError

    async def _alert(self, message: str):
        raise NotImplementedError

