"""
Script to create platform wallets
"""
import os
from wallets import db
from wallets.common.models import Wallet


def create_wallets():
    wallet_btc = Wallet(
        address=os.environ.get('EXCHANGER_BTC_ADDRESS',
                               'mtQGkRpBVRDdRBwVkCbtGArdCYmiqkQrB1'),
        external_id=os.environ.get('BTC_ID', 23),
        is_platform=True,
        currency_slug=os.environ.get('BTC_SLUG', 'bitcoin')
    )

    wallet_eth = Wallet(
        address=os.environ.get('EXCHANGER_ETH_ADDRESS',
                               '0xF6E4709341426Dee13c9e9EaB6e4779b299CE2F7'),
        external_id=os.environ.get('ETH_ID', 24),
        is_platform=True,
        currency_slug=os.environ.get('ETH_SLUG', 'ethereum')
    )

    db.session.add(wallet_btc)
    db.session.add(wallet_eth)
    db.session.commit()


def create_tokens_main_net():
    slugs = ['usd-coin'
             'trueusd',
             'omisego',
             'basic-attention-token',
             'holo',
             'chainlink',
             'zilliqa'
             ]
    wallets = [
        Wallet(
            address=os.environ.get('EXCHANGER_ETH_ADDRESS',
                                   '0xF6E4709341426Dee13c9e9EaB6e4779b299CE2F7'),
            external_id=os.environ.get('ETH_ID', 24),
            is_platform=True,
            currency_slug=slug
        ) for slug in slugs
    ]
    db.session.add_all(wallets)
    db.session.commit()


def create_test_token():

    wallet = Wallet(
        address=os.environ.get('EXCHANGER_ETH_ADDRESS',
                               '0xF6E4709341426Dee13c9e9EaB6e4779b299CE2F7'),
        external_id=os.environ.get('ETH_ID', 24),
        is_platform=True,
        currency_slug='binance-coin'
    )
    db.session.add(wallet)
    db.session.commit()
