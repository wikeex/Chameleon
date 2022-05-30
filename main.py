import asyncio
from hub import Hub
from smoke import Smoke
from monitor.chia import ChiaMonitor
from monitor.nbminer import NBMinerMonitor
from monitor.phala.prbv0 import PrbV0Monitor
from monitor.phala.substrate import SubstrateMonitor
from config import config


async def main():
    proxies = [tuple(proxy.strip().split(':')) for proxy in config.get('hub', 'proxies').split(',')]
    # hub = Hub(
    #     serv_host=config.get('hub', 'host'),
    #     serv_port=int(config.get('hub', 'port')),
    #     proxies=proxies
    # )
    #
    # smoke = Smoke()
    # chia_monitor = ChiaMonitor(
    #     ca_file=config.get('chia', 'ca_file'),
    #     cert_file=config.get('chia', 'cert_file'),
    #     key_file=config.get('chia', 'key_file'),
    #     plots_quantity=int(config.get('chia', 'plots_quantity'))
    # )
    # nbminer_monitor = NBMinerMonitor(
    #     host=config.get('nbminer', 'host'),
    #     port=int(config.get('nbminer', 'port')),
    #     alert_limit=float(config.get('nbminer', 'alert_limit'))
    # )
    workers = [worker.strip() for worker in config.get('phala', 'workers').split(',')]
    prb_host = config.get('phala', 'prb_host')
    khala_node_host = config.get('phala', 'khala_node_host')
    substrate_monitor = SubstrateMonitor(workers, interval=120)
    prb_monitor = PrbV0Monitor(prb_host, khala_node_host, interval=120)

    await asyncio.gather(
        # hub.run(),
        # smoke.release(),
        # chia_monitor.monitor(),
        # nbminer_monitor.monitor(),
        prb_monitor.monitor(),
        substrate_monitor.monitor()
    )


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
