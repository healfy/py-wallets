"""
Script to create platform wallets
"""
import os
import asyncio
from wallets import objects
from wallets.common.models import Wallet


async def create_wallets():
    await objects.create(
        Wallet,
        address=os.environ.get(
            'EXCHANGER_BTC_ADDRESS', 'mtQGkRpBVRDdRBwVkCbtGArdCYmiqkQrB1'
        ).lower(),
        external_id=os.environ.get('BTC_ID', 23),
        is_platform=True,
        currency_slug=os.environ.get('BTC_SLUG', 'bitcoin').lower()
    )

    await objects.create(
        Wallet,
        address=os.environ.get(
            'EXCHANGER_ETH_ADDRESS',
            '0xF6E4709341426Dee13c9e9EaB6e4779b299CE2F7'
        ).lower(),
        external_id=os.environ.get('ETH_ID', 24),
        is_platform=True,
        currency_slug=os.environ.get('ETH_SLUG', 'ethereum').lower()
    )


async def create_tokens_main_net():
    slugs = ['usd-coin'
             'trueusd',
             'omisego',
             'basic-attention-token',
             'holo',
             'chainlink',
             'zilliqa'
             ]
    for slug in slugs:
        await objects.create(
            Wallet,
            address=os.environ.get(
                'EXCHANGER_ETH_ADDRESS',
                '0xF6E4709341426Dee13c9e9EaB6e4779b299CE2F7'
            ).lower(),
            external_id=os.environ.get('ETH_ID', 24),
            is_platform=True,
            currency_slug=slug)


async def create_test_token():

    await objects.create(
        Wallet,
        address=os.environ.get(
            'EXCHANGER_ETH_ADDRESS',
            '0xF6E4709341426Dee13c9e9EaB6e4779b299CE2F7'
        ).lower(),
        external_id=os.environ.get('ETH_ID', 24),
        is_platform=True,
        currency_slug='binance-coin'
    )


def main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(create_wallets())
    loop.run_until_complete(create_test_token())

