#!/usr/bin/env python3

import json
import logging

import cbpro

API_SETUP_MSG = 'Set up a Coinbase Pro API key here: https://pro.coinbase.com/profile/api\nThe "View" scope is required. If you wish to utilize deposits and/or withdrawals, grant the "Transfer" scope. If you wish to utilize investing, grant the "Trade" scope.\nIf possible, consider setting a restrictive IP whitelist.'


def main():
    final_config = {
        "deposit": dict(),
        "orders": list(),
        "external_wallets": dict(),
        "coinbase_pro": dict(),
        "logging": {"log_level": logging.INFO},
    }

    # ask user to set up coinbase API key
    print(API_SETUP_MSG)

    cbpro_settings = dict()
    cbpro_settings["api_key"] = input("Enter API key: ")
    cbpro_settings["api_secret"] = input("Enter API secret: ")
    cbpro_settings["password"] = input("Enter API passphrase: ")
    final_config["coinbase_pro"] = cbpro_settings

    # init CBPro client with above info
    cbpro_api = cbpro.AuthenticatedClient(
        cbpro_settings["api_key"],
        cbpro_settings["api_secret"],
        cbpro_settings["password"],
    )

    # configure deposit method
    res = cbpro_api._send_message("get", "/payment-methods")

    # err-check the CBPro auth
    if isinstance(res, dict) and 'message' in res:
        print(f"API error - {res['message']}. Please try running this program again with valid API credentials.")

    payment_methods = list()
    for index, payment_method in enumerate(res):
        payment_methods.append(f"{index} - {payment_method['name']}")

    print("\n".join(["Payment methods:"] + payment_methods))

    payment_method_index = input(
        "Enter the index of the payment method you'd like to deposit from in the future: "
    )
    final_config["deposit"]["payment_method_id"] = res[int(payment_method_index)]["id"]

    per_period = input(
        "Enter the number of purcahses that will be made per period (31): "
    )
    if per_period == "":
        per_period = 31
    else:
        per_period = int(per_period)

    final_config["deposit"]["purchases_per_period"] = per_period

    # configure orders
    first_order = True
    while first_order or input("Enter another order? (y/N): ").lower() == "y":
        order_info = dict()
        order_info["trading_pair"] = input(
            "Enter order trading pair (eg. BTC-USD): "
        ).upper()
        order_info["amount"] = float(input("Enter trading amount in USD: "))
        final_config["orders"].append(order_info)

        first_order = False

    # configure withdrawal settings

    # TODO if coinbase ever adds support for it,
    # check out the address book to source default addresses
    # and yell at them if they don't have address whitelisting enabled

    wallet_config = dict()
    first_wallet = True
    while first_wallet or input("Enter another withdrawal configuration? (y/N): ").lower() == "y":
        first_wallet = False
        ticker = input("Enter the asset's ticker symbol (eg. BTC): ").upper()
        wallet_config[ticker] = dict()
        wallet_config[ticker]['max_value_before_move'] = float(input("Enter the lowest value in USD that should initiate a withdrawal: "))
        wallet_config[ticker]['destination_wallet'] = input(f"Enter a destination {ticker} address: ")

    final_config['external_wallets'] = wallet_config

    config_filename = input("Enter file name to write configuration (config.json): ")
    if config_filename == "":
        config_filename = "config.json"

    with open(config_filename, "w") as f:
        json.dump(final_config, f, indent=4)


if __name__ == "__main__":
    main()
