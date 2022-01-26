#!/usr/bin/env python3

import argparse
import json
import logging
from time import sleep

import cbpro


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        type=str,
        default="config.json",
        help="The path to a configuration file for this program",
    )
    parser.add_argument(
        "--sandbox",
        action='store_true',
        help="If true, use public.sandbox.pro.coinbase.com "
        "instead of api.pro.coinbase.com"
    )
    args = parser.parse_args()

    with open(args.config, "r") as f:
        config = json.load(f)

    logger = logging.getLogger("coinbase_pro_dca")
    logging.basicConfig()

    logging_conf = config.get("logging", dict())
    logger.setLevel(logging_conf.get("log_level", logging.INFO))
    if "gotify" in logging_conf:
        from gotify_handler import GotifyHandler
        logger.addHandler(GotifyHandler(**logging_conf["gotify"]))

    # init coinbase session
    if args.sandbox:
        sandbox_msg = "DRY-RUN -"
        cbpro_config = config["coinbase_pro_sandbox"]
        coinbase_api = cbpro.AuthenticatedClient(
            cbpro_config["api_key"],
            cbpro_config["api_secret"],
            cbpro_config["password"],
            api_url="https://api-public.sandbox.pro.coinbase.com"
        )

    else:
        sandbox_msg = ""
        cbpro_config = config["coinbase_pro"]
        coinbase_api = cbpro.AuthenticatedClient(
            cbpro_config["api_key"],
            cbpro_config["api_secret"],
            cbpro_config["password"])

    issued_orders = list()
    for order in config["orders"]:
        # Don't raise an exception, as we'd like to continue trading
        res = coinbase_api.place_market_order(product_id=order["trading_pair"],
                                              side="buy",
                                              funds=str(order["amount"]))

        if "message" in res:
            logger.error(f"{sandbox_msg} Error trading "
                         f"{order['trading_pair']} - {res['message']}")

        else:
            logger.info(
                f"{sandbox_msg} Successfully bought ${order['amount']} "
                f"of {order['trading_pair'].split('-')[0]}")
            issued_orders.append(res)

    # Exit now if we don't care about moving balances to ext wallets
    if not config.get('currency_wallets', dict()):
        return

    # Block until all of our issued orders have settled
    #
    # This is non-optional, but the most recent order should be the one
    # to complete last, so at least there's that.
    #
    # This is assuming that we're only issuing market orders
    # which is a fair assumption for this tool
    for order in issued_orders[::-1]:
        while not order['settled']:
            order = coinbase_api.get_order(order["id"])
            sleep(1)
    # Now that all of our orders have settled, check out our accounts
    for acct in coinbase_api.get_accounts():
        wallet_conf = config['currency_wallets'].get(acct['currency'], None)
        if wallet_conf is not None:
            # TODO this assumes that there's a X-USD market,
            # which there doesn't have to be
            acct_balance_in_usd = acct['balance'] * float(coinbase_api.get_product_ticker(f"{acct['currency']}-USD")['price'])
            if acct_balance_in_usd >= wallet_conf['max_amount_before_move']:
                # TODO init a transfer to wallet_conf['destination_wallet']
                logger.info(f"{sandbox_msg} Withdrawing {acct['balance']} "
                            f"{acct['currency']} to external wallet")


if __name__ == "__main__":
    main()
