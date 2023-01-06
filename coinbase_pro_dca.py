#!/usr/bin/env python3

import argparse
import json
import logging
from time import sleep
from typing import Dict

import cbpro


class CoinbaseProDca:
    def __init__(self, config: Dict, logger: logging.Logger, dry_run: bool = False):
        # TODO add more fiat curencies, if there are any more that are supported
        self.IGNORED_CURRENCIES = ["USD", "EUR", "GBP"]

        self.config = config
        self.logger = logger
        self.dry_run = dry_run

        if dry_run:
            self.sandbox_msg = "DRY-RUN - "
            cbpro_config = self.config["coinbase_pro_sandbox"]
            api_url = "https://api-public.sandbox.pro.coinbase.com"

        else:
            self.sandbox_msg = ""
            cbpro_config = config["coinbase_pro"]
            api_url = "https://api.pro.coinbase.com"

        self.cbpro_api = cbpro.AuthenticatedClient(
            cbpro_config["api_key"],
            cbpro_config["api_secret"],
            cbpro_config["password"],
            api_url=api_url,
        )

    def deposit_funds(self):
        deposit_config = self.config["deposit"]
        order_sum = 0
        for order in self.config["orders"]:
            order_sum += order["amount"]
        usd_per_period = order_sum * deposit_config["purchases_per_period"]

        # TODO eliminate dependence on USD markets
        deposit_dict = {
            "payment_method_id": deposit_config["payment_method_id"],
            "amount": usd_per_period,
            "currency": "USD",
        }

        self.logger.info(f"{self.sandbox_msg}Depositing {deposit_dict['amount']}")
        # TODO add info of depositing acct
        # "from payment method X")
        #
        # we should call GET /payment-methods to get the payment method's name

        res = self.cbpro_api._send_message(
            "post", "/deposits/payment-method", data=json.dumps(deposit_dict)
        )

        if "message" in res:
            # Don't raise an exception, as we'd like to continue execution
            self.logger.error(
                f"{self.sandbox_msg}Error during deposit - {res['message']}"
            )

    def invest(self):
        issued_orders = list()
        for order in self.config["orders"]:
            res = self.cbpro_api.place_market_order(
                product_id=order["trading_pair"], side="buy", funds=str(order["amount"])
            )

            if "message" in res:
                # Don't raise an exception, as we'd like to continue trading
                self.logger.error(
                    f"{self.sandbox_msg}Error trading "
                    f"{order['trading_pair']} - {res['message']}"
                )

            else:
                self.logger.info(
                    f"{self.sandbox_msg}Successfully bought ${order['amount']:.2f} "
                    f"of {order['trading_pair'].split('-')[0]}"
                )
                issued_orders.append(res)

        # Block until all of our issued orders have settled
        #
        # This is non-optional, but the most recent order should be the one
        # to complete last, so at least there's that.
        #
        # This is assuming that we're only issuing market orders
        # which is a fair assumption for this tool

        # TODO make sleep times configurable
        for order in issued_orders[::-1]:
            last_settled = False
            for _ in range(10):
                order = self.cbpro_api.get_order(order["id"])
                if order.get("settled", False):
                    last_settled = True
                    break
                sleep(3)

            if not last_settled:
                self.logger.error(
                    f"{self.sandbox_msg}Order {order['id']} has not settled in 30 seconds"
                )

    def withdraw_funds(self):
        ext_wallets = self.config.get("external_wallets", dict())

        # return if we don't care about moving balances to ext wallets
        if not ext_wallets:
            return

        for acct in self.cbpro_api.get_accounts():
            wallet_conf = ext_wallets.get(acct["currency"], None)
            if wallet_conf is None:
                if (
                    float(acct["balance"]) >= self.config.get("minimum_nag_value", 100)
                    and acct["currency"] not in self.IGNORED_CURRENCIES
                ):
                    # let the user know that they don't have an ext wallet set up
                    # for this asset if its value is >= the "nag value"
                    self.logger.warning(
                        f"{self.sandbox_msg}"
                        "No external wallet set for currency "
                        "%s with balance %s"
                        % (acct["currency"], float(acct["balance"]))
                    )
                else:
                    # Skip empty or ignored accounts
                    continue

            else:
                # TODO eliminate dependence on *-USD markets
                try:
                    acct_balance_in_usd = float(acct["balance"]) * float(
                        self.cbpro_api.get_product_ticker(f"{acct['currency']}-USD")[
                            "price"
                        ]
                    )

                except KeyError:
                    self.logger.error(
                        f"{self.sandbox_msg}Error retrieving USD conversion "
                        f"rate for asset {acct['currency']} "
                        "- continuing"
                    )
                    continue

                if acct_balance_in_usd >= wallet_conf["max_value_before_move"]:
                    self.logger.info(
                        f"{self.sandbox_msg}Withdrawing {acct['balance']} "
                        f"{acct['currency']} to external wallet"
                    )

                    withdraw_dict = {
                        "currency": acct["currency"],
                        "amount": acct["available"],
                        "crypto_address": wallet_conf["destination_wallet"],
                    }

                    res = self.cbpro_api._send_message(
                        "post", "/withdrawals/crypto", data=json.dumps(withdraw_dict)
                    )
                    if "message" in res:
                        # Don't raise an exception,
                        # as we'd like to continue withdrawing funds
                        self.logger.error(
                            f"{self.sandbox_msg}Error withdrawing funds for "
                            f"currency {acct['currency']} - {res['message']}"
                        )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--action",
        type=str,
        choices=["deposit", "invest", "withdraw"],
        default="invest",
        help="Action to take for execution",
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config.json",
        help="The path to a configuration file. If absent, ./config.json is used",
    )
    parser.add_argument(
        "--sandbox",
        action="store_true",
        help="If true, utilize the Coinbase Pro Sandbox for testing purposes",
    )
    args = parser.parse_args()

    with open(args.config, "r") as f:
        config = json.load(f)

    # logging setup
    logger = logging.getLogger("coinbase_pro_dca")
    logging.basicConfig()

    logging_conf = config.get("logging", dict())
    logger.setLevel(logging_conf.get("log_level", logging.INFO))
    if "gotify" in logging_conf:
        from gotify_handler import GotifyHandler

        logger.addHandler(GotifyHandler(**logging_conf["gotify"]))

    dca = CoinbaseProDca(config, logger, args.sandbox)

    # check args.action here and switch based on it
    if args.action == "deposit":
        dca.deposit_funds()

    elif args.action == "invest":
        dca.invest()

    # regardless of the content of args.action,
    # check if we should withdraw funds to external wallets
    dca.withdraw_funds()


if __name__ == "__main__":
    main()
