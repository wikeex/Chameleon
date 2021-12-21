

class Monitor:
    def __init__(self, interval: int = 30):
        self.internal = interval

    async def monitor(self):
        raise NotImplementedError

    async def _alert(self, message: str):
        raise NotImplementedError

