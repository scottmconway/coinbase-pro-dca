# (Yet another) Coinbase Pro DCA Tool
## Requirements
* python3
* cbpro
* gotify-handler

## Usage
`python3 coinbase_pro_dca.py --config $PATH_TO_CONFIG_FILE`

If `--config` is not provided, the local file `./config.json` is read.

## Configuration
See config.json.example for an example configuration.

A coinbase pro API key with the "trade" (and eventually "transfer") scopes is required.
Its key, secret, and password must be provided in the `coinbase_pro` section of the config.

`orders` contains a list of order objects, which contain a trading pair and the amount to purchase in a market order, in USD.

eg. with the example config, the program will purchase $100 USD of BTC and $100 of ETH.
