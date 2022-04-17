import docker
import pytest
from substrateinterface import SubstrateInterface

from monitor.phala import PhalaMonitor


def test_substrate():
    substrate = SubstrateInterface(
        url="wss://khala.api.onfinality.io/public-ws",
        ss58_format=42,
        type_registry_preset='kusama'
    )
    # 获取worker绑定的账户
    account = substrate.query(
        module='PhalaMining',
        storage_function='WorkerBindings',
        params=[f'0xd6edac6c588244402e8a256927f99be6519ca5578e0ca9760a4e8537b0e5d275']
    )
    print(account.value)

    # 使用worker绑定的账户查询worker的状态
    result = substrate.query(
        module='PhalaMining',
        storage_function='Miners',
        params=[account.value]
    )
    print(result)


@pytest.fixture
def phala():
    return PhalaMonitor(['0xfce4d9fed94760c944b0c9bcbcf8d64b2a37137c6e1408568a7206b15d02b658'])


@pytest.mark.asyncio
async def test_monitor(phala):
    await phala.monitor()


def test_restart(phala):
    phala.restart()


def test_docker():
    client = docker.from_env()
    containers = {}

    for container in client.containers.list(all=True):
        containers[container.name] = container

        print(container.status)