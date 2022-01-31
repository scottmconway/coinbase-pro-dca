# (Yet another) Coinbase Pro DCA Tool
This tool provides a way to accomplish the following tasks programatically:
* Deposit a programatically-determined amount of fiat for a given period into Coinbase Pro
* Place user-defined purchase (market) orders
* Withdraw cyrptocurrencies into external wallets once their values exceed a user-defined amount

## Requirements
* python3
* cbpro
* gotify-handler (optional - required only if you'd like to log to gotify)

## Usage
`python3 coinbase_pro_dca.py --action {deposit, invest, withdraw}`

For more information on these arguments, see the below "Arguments" section.

I intend to use this program in the following way - maybe you will as well.
The following read as crontab entries.

At the first of each month, I'll invest the sum of all orders I wish to place in the span of a month (as defined in the config file - `deposit->purchases_per_period`).

`0 0 1 * * python3 coinbase_pro_dca.py --deposit`

Note that if you're going to programatically invest each month (or another span of time with an indeterminate amount of time), you should be sure to "lie" about the `purchases_per_period` value. In my config, I set it to `31`, since I'll deposit every month, and some months have 31 days.

Every day, I'll invest as per the `orders` section.

`0 0 * * * python3 coinbase_pro_dca.py --invest`

Note that whichever action you take (deposit, invest, or withdraw),
each action will trigger a withdraw action at the end of execution.
This might be changed in the future if it's found to be a nuisance.

## Arguments
|Name|Type|Description|
|-|-|-|
|`--action`|`str`|Action to take for execution - deposit, invest, or withdraw|
|`--config`|`str`|The path to a configuration file. If absent, `./config.json` is used|
|`--sandbox`|`bool`|If set, utilize the Coinbase Pro Sandbox, for testing purposes|

## Configuration
See config.json.example for an example configuration.

You can also invoke `python3 config_wizard.py` for a guided process to create a configuration file.

`deposit->payment_method_id` is the `id` of a payment method from Coinbase Pro. I can't find this value in the Web UI, but it can be retrieved through this [API endpoint](https://docs.cloud.coinbase.com/exchange/reference/exchangerestapi_getpaymentmethods) in Coinbase Pro. At some point I'll add a wizard to make the initial config generation less painful.

`deposit->purchases_per_period` defines the number of purchases that you intend to make per `deposit` period. For example - for investing each day for a month with a deposit each month, the value should be set to 31. This value is multiplied by the sum of all orders to determine how much money to deposit from the selected payment method when the `deposit` action is used.

`orders` contains a list of order objects, which contain a trading pair and the amount to purchase in a market order, in USD.
eg. with the example config, the program will purchase $100 USD of BTC and $100 of ETH when the `invest` action is taken.

`external_wallets` specifies a few notes for the `withdraw` action.
Each key is a valid cryptocurrency ticker, as defined by coinbase (BTC, ETH, etc.).
`max_value_before_move` is the lowest amount of USD value the cryptocurrency's account that should trigger it to be withdrawn to an external wallet.
`destination_wallet` contains a valid wallet address for the given cryptocurrency.

`coinbase_pro` contains all attributes required for your API key.
If you wish to use the `deposit` and/or `withdraw` actions, it will need the `transfer` scope.
If you wish to use the `invest` action, it'll need the `trade` scope.

**If you have the `transfer` scope enabled, you should enable address whitelisting**.

Address whitelisting can be enabled [here](https://pro.coinbase.com/profile/address-book).
If you do not, if your API credentials were to be compromised, an attacker could withdraw your funds to cryptocurrency wallets that you do not control.
Additionally, if possible, you should enable the `IP Whitelist` section when creating an API key.

`coinbase_pro_sandbox` contains the same parameters as `coinbase_pro`, but for a coinbase pro sandbox account. This section is utilized when the `--sandbox` argument is passed to `coinbase_pro_dca.py`.

`logging` specifies the logging level, and optionally, a configuration to log to a gotify server, utilizing [gotify-handler](https://github.com/scottmconway/gotify-handler).
