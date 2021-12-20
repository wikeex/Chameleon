import pytest
from substrateinterface import SubstrateInterface


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