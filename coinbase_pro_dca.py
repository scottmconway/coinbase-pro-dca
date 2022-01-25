#!/usr/bin/env python3

import argparse
import json
import logging

import cbpro
from gotify_handler import GotifyHandler


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        type=str,
        default="config.json",
        help="The path to a configuration file for this program",
    )
    args = parser.parse_args()

    with open(args.config, "r") as f:
        config = json.load(f)

    logger = logging.getLogger("coinbase_pro_dca")
    logging.basicConfig()

    logging_conf = config.get("logging", dict())
    logger.setLevel(logging_conf.get("log_level", logging.INFO))
    if "gotify" in logging_conf:
        logger.addHandler(GotifyHandler(**logging_conf["gotify"]))

    # init coinbase session
    cbpro_config = config["coinbase_pro"]
    coinbase_api = cbpro.AuthenticatedClient(
        cbpro_config["api_key"],
        cbpro_config["api_secret"],
        cbpro_config["password"])

    for order in config["orders"]:
        res = coinbase_api.place_market_order(product_id=order["trading_pair"],
                                              side="buy",
                                              funds=str(order["amount"]))

        if "message" in res:
            logger.error(f"Error trading {order['trading_pair']} - "
                         f"{res['message']}")

        else:
            logger.info(
                f"Successfully bought ${order['amount']} "
                f"of {order['trading_pair'].split('-')[0]}")

        # TODO save the order ID and block while it hasn't settled

        # TODO once the order has resolved, check if we should move the
        # funds to an external address specified in the config


if __name__ == "__main__":
    main()
