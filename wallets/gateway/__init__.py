currencies_service_gw = None
blockchain_service_gw = None
transactions_service_gw = None
exchanger_service_gw = None


def start_remote_gateways():
    """Create remote services gateway instances with clients."""
    from wallets import currencies_gateway, bgw_gateway, \
        transactions_gateway, exchanger_gateway

    global currencies_service_gw, blockchain_service_gw, \
        transactions_service_gw, exchanger_service_gw

    currencies_service_gw = currencies_gateway.CurrenciesServiceGateway()
    blockchain_service_gw = bgw_gateway.BlockChainServiceGateWay()
    transactions_service_gw = transactions_gateway.TransactionsServiceGateway()
    exchanger_service_gw = exchanger_gateway.ExchangerServiceGateway()

    return currencies_service_gw, blockchain_service_gw, \
           transactions_service_gw, exchanger_service_gw

