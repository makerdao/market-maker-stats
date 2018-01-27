# market-maker-stats

A set of tools for collecting data from the `market-maker-keeper`
(<https://github.com/makerdao/market-maker-keeper>) keepers.

The following tools are available in this repository:
* `oasis-market-maker-chart`,
* `oasis-market-maker-trades`,
* `etherdelta-market-maker-chart`,
* `etherdelta-market-maker-trades`,
* `radarrelay-market-maker-chart`,
* `bibox-market-maker-chart`,
* `bibox-market-maker-trades`,
* `gateio-market-maker-chart`,
* `gateio-market-maker-trades`.

<https://chat.makerdao.com/channel/keeper>


## Installation

This project uses *Python 3.6.2*.

In order to clone the project and install required third-party packages please execute:
```
git clone https://github.com/makerdao/market-maker-keeper.git
git submodule update --init --recursive
pip3 install -r requirements.txt
```

For some known macOS issues see the [pymaker](https://github.com/makerdao/pymaker) README.


## oasis-market-maker-chart

Draws a chart with the historical GDAX ETH/USD price, closest `oasis-market-maker-keeper` bids and asks
(represented as lines) and recent trades which took place with the keeper (represented as dots).
The size of the dots depends on the trade volume. This way we can clearly spot
if the keeper is not creating dangerous arbitrage opportunities.

Sample result:

![](https://s10.postimg.org/qzzbyuzxl/oasis_server1_1.png)

### Usage

```
usage: oasis-market-maker-chart [-h] [--rpc-host RPC_HOST]
                                [--rpc-port RPC_PORT]
                                [--rpc-timeout RPC_TIMEOUT] --oasis-address
                                OASIS_ADDRESS --sai-address SAI_ADDRESS
                                --weth-address WETH_ADDRESS
                                --market-maker-address MARKET_MAKER_ADDRESS
                                --past-blocks PAST_BLOCKS [-o OUTPUT]

optional arguments:
  -h, --help            show this help message and exit
  --rpc-host RPC_HOST   JSON-RPC host (default: `localhost')
  --rpc-port RPC_PORT   JSON-RPC port (default: `8545')
  --rpc-timeout RPC_TIMEOUT
                        JSON-RPC timeout (in seconds, default: 60)
  --oasis-address OASIS_ADDRESS
                        Ethereum address of the OasisDEX contract
  --sai-address SAI_ADDRESS
                        Ethereum address of the SAI token
  --weth-address WETH_ADDRESS
                        Ethereum address of the WETH token
  --market-maker-address MARKET_MAKER_ADDRESS
                        Ethereum account of the market maker to analyze
  --past-blocks PAST_BLOCKS
                        Number of past blocks to analyze
  -o OUTPUT, --output OUTPUT
                        Name of the filename to save to chart to. Will get
                        displayed on-screen if empty
```


## oasis-market-maker-trades

Exports the list of recent trades which took place with the keeper, either as a text table (if invoked
with `--text`) or as a JSON document (if invoked with `--json`).

Example text output:

```
Trade history on the ETH/DAI pair:

       Date/time          Type       Price       Amount in ETH   Value in DAI                      Taker
===========================================================================================================================
2018-01-01 10:00:00 UTC   Buy     990.57615003      5.85517832   5800.00000000   0x8eb07c216cc1a46f135eb67d9ce9c7465893ccf9
2018-01-02 11:30:00 UTC   Sell    990.57615003      6.14822530   6090.28534500   0x78e134c3da7fb2b1b0e04e1bb3cdeb67d14e7a6d

Buy  = Somebody bought DAI from the keeper
Sell = Somebody sold DAI to the keeper

Number of trades: 2
Generated at: 2018.01.02 11:36:18 UTC
```

Example JSON output:
```
[
 {
  "datetime": "2018-01-01 10:00:00 UTC",
  "timestamp": 1516712345,
  "type": "Buy",
  "price": 990.57615003,
  "amount": 5.85517832,
  "amount_symbol": "ETH",
  "money": 5800.00000000,
  "money_symbol": "DAI",
  "taker": "0x8eb07c216cc1a46f135eb67d9ce9c7465893ccf9"
 },
 {
  "datetime": "2018-01-01 11:30:00 UTC",
  "timestamp": 1516812345,
  "type": "Sell",
  "price": 990.57615003,
  "amount": 6.14822530,
  "amount_symbol": "ETH",
  "money": 6090.28534500,
  "money_symbol": "DAI",
  "taker": "0x78e134c3da7fb2b1b0e04e1bb3cdeb67d14e7a6d"
 }
]
```

### Usage

```
usage: oasis-market-maker-trades [-h] [--rpc-host RPC_HOST]
                                 [--rpc-port RPC_PORT]
                                 [--rpc-timeout RPC_TIMEOUT] --oasis-address
                                 OASIS_ADDRESS --sai-address SAI_ADDRESS
                                 --weth-address WETH_ADDRESS
                                 --market-maker-address MARKET_MAKER_ADDRESS
                                 --past-blocks PAST_BLOCKS (--text | --json)

optional arguments:
  -h, --help            show this help message and exit
  --rpc-host RPC_HOST   JSON-RPC host (default: `localhost')
  --rpc-port RPC_PORT   JSON-RPC port (default: `8545')
  --rpc-timeout RPC_TIMEOUT
                        JSON-RPC timeout (in seconds, default: 60)
  --oasis-address OASIS_ADDRESS
                        Ethereum address of the OasisDEX contract
  --sai-address SAI_ADDRESS
                        Ethereum address of the SAI token
  --weth-address WETH_ADDRESS
                        Ethereum address of the WETH token
  --market-maker-address MARKET_MAKER_ADDRESS
                        Ethereum account of the market maker to analyze
  --past-blocks PAST_BLOCKS
                        Number of past blocks to analyze
  --text                List trades as a text table
  --json                List trades as a JSON document
```

## etherdelta-market-maker-chart

Draws a chart with the historical GDAX ETH/USD price and recent trades which took place with the keeper
(represented as dots). The size of the dots depends on the trade volume. This way we can clearly spot
if the keeper is not creating dangerous arbitrage opportunities.

Sample result:

![](https://s10.postimg.org/u83tbvjmh/etherdelta_server1_1.png)

### Usage

```
usage: etherdelta-market-maker-chart [-h] [--rpc-host RPC_HOST]
                                     [--rpc-port RPC_PORT]
                                     [--rpc-timeout RPC_TIMEOUT]
                                     --etherdelta-address ETHERDELTA_ADDRESS
                                     --sai-address SAI_ADDRESS --eth-address
                                     ETH_ADDRESS --market-maker-address
                                     MARKET_MAKER_ADDRESS --past-blocks
                                     PAST_BLOCKS [-o OUTPUT]

optional arguments:
  -h, --help            show this help message and exit
  --rpc-host RPC_HOST   JSON-RPC host (default: `localhost')
  --rpc-port RPC_PORT   JSON-RPC port (default: `8545')
  --rpc-timeout RPC_TIMEOUT
                        JSON-RPC timeout (in seconds, default: 60)
  --etherdelta-address ETHERDELTA_ADDRESS
                        Ethereum address of the EtherDelta contract
  --sai-address SAI_ADDRESS
                        Ethereum address of the SAI token
  --eth-address ETH_ADDRESS
                        Ethereum address of the ETH token
  --market-maker-address MARKET_MAKER_ADDRESS
                        Ethereum account of the market maker to analyze
  --past-blocks PAST_BLOCKS
                        Number of past blocks to analyze
  -o OUTPUT, --output OUTPUT
                        Name of the filename to save to chart to. Will get
                        displayed on-screen if empty
```


## etherdelta-market-maker-trades

Exports the list of recent trades which took place with the keeper, either as a text table (if invoked
with `--text`) or as a JSON document (if invoked with `--json`).

For sample text and JSON output, see the `oasis-market-maker-trades` above.

### Usage

```
usage: etherdelta-market-maker-trades [-h] [--rpc-host RPC_HOST]
                                      [--rpc-port RPC_PORT]
                                      [--rpc-timeout RPC_TIMEOUT]
                                      --etherdelta-address ETHERDELTA_ADDRESS
                                      --sai-address SAI_ADDRESS --eth-address
                                      ETH_ADDRESS --market-maker-address
                                      MARKET_MAKER_ADDRESS --past-blocks
                                      PAST_BLOCKS (--text | --json)

optional arguments:
  -h, --help            show this help message and exit
  --rpc-host RPC_HOST   JSON-RPC host (default: `localhost')
  --rpc-port RPC_PORT   JSON-RPC port (default: `8545')
  --rpc-timeout RPC_TIMEOUT
                        JSON-RPC timeout (in seconds, default: 60)
  --etherdelta-address ETHERDELTA_ADDRESS
                        Ethereum address of the EtherDelta contract
  --sai-address SAI_ADDRESS
                        Ethereum address of the SAI token
  --eth-address ETH_ADDRESS
                        Ethereum address of the ETH token
  --market-maker-address MARKET_MAKER_ADDRESS
                        Ethereum account of the market maker to analyze
  --past-blocks PAST_BLOCKS
                        Number of past blocks to analyze
  --text                List trades as a text table
  --json                List trades as a JSON document
```


## radarrelay-market-maker-chart

Draws a chart with the historical GDAX ETH/USD price and recent trades which took place with the keeper
(represented as dots). The size of the dots depends on the trade volume. This way we can clearly spot
if the keeper is not creating dangerous arbitrage opportunities.

Sample result:

![](https://s10.postimg.org/u83tbvjmh/etherdelta_server1_1.png)

### Usage

```
usage: radarrelay-market-maker-chart [-h] [--rpc-host RPC_HOST]
                                     [--rpc-port RPC_PORT]
                                     [--rpc-timeout RPC_TIMEOUT]
                                     --exchange-address EXCHANGE_ADDRESS
                                     --sai-address SAI_ADDRESS --weth-address
                                     WETH_ADDRESS --market-maker-address
                                     MARKET_MAKER_ADDRESS --past-blocks
                                     PAST_BLOCKS [-o OUTPUT]

optional arguments:
  -h, --help            show this help message and exit
  --rpc-host RPC_HOST   JSON-RPC host (default: `localhost')
  --rpc-port RPC_PORT   JSON-RPC port (default: `8545')
  --rpc-timeout RPC_TIMEOUT
                        JSON-RPC timeout (in seconds, default: 60)
  --exchange-address EXCHANGE_ADDRESS
                        Ethereum address of the 0x contract
  --sai-address SAI_ADDRESS
                        Ethereum address of the SAI token
  --weth-address WETH_ADDRESS
                        Ethereum address of the WETH token
  --market-maker-address MARKET_MAKER_ADDRESS
                        Ethereum account of the market maker to analyze
  --past-blocks PAST_BLOCKS
                        Number of past blocks to analyze
  -o OUTPUT, --output OUTPUT
                        Name of the filename to save to chart to. Will get
                        displayed on-screen if empty
```


## bibox-market-maker-chart

Draws a chart with either the historical GDAX ETH/USD price or the price history read from a file, and recent
trades which took place with the keeper (represented as dots). The size of the dots depends on the trade volume.
This way we can clearly spot if the keeper is not creating dangerous arbitrage opportunities.

Price history files can be supplied using `--price-history-file` and `--alternative-price-history-file`
arguments. If they are, it is expected that each line of them will be a simple JSON document with `timestamp`
and `price` properties. If no `--price-history-file` argument is supplied, historical GDAX ETH/USD price
will be displayed.

Sample result:

![](https://s10.postimg.org/g1o2gvteh/bibox_server1_2.png)

### Usage

```
usage: bibox-market-maker-chart [-h] [--bibox-api-server BIBOX_API_SERVER]
                                --bibox-api-key BIBOX_API_KEY --bibox-secret
                                BIBOX_SECRET [--bibox-timeout BIBOX_TIMEOUT]
                                [--bibox-retry-count BIBOX_RETRY_COUNT]
                                [--price-history-file PRICE_HISTORY_FILE]
                                [--alternative-price-history-file ALTERNATIVE_PRICE_HISTORY_FILE]
                                --pair PAIR --past-trades PAST_TRADES
                                [-o OUTPUT]

optional arguments:
  -h, --help            show this help message and exit
  --bibox-api-server BIBOX_API_SERVER
                        Address of the Bibox API server (default:
                        'https://api.bibox.com')
  --bibox-api-key BIBOX_API_KEY
                        API key for the Bibox API
  --bibox-secret BIBOX_SECRET
                        Secret for the Bibox API
  --bibox-timeout BIBOX_TIMEOUT
                        Timeout for accessing the Bibox API
  --bibox-retry-count BIBOX_RETRY_COUNT
                        Retry count for accessing the Bibox API (default: 20)
  --price-history-file PRICE_HISTORY_FILE
                        File to use as the price history source
  --alternative-price-history-file ALTERNATIVE_PRICE_HISTORY_FILE
                        File to use as the alternative price history source
  --pair PAIR           Token pair to draw the chart for
  --past-trades PAST_TRADES
                        Number of past trades to fetch and display
  -o OUTPUT, --output OUTPUT
                        Name of the filename to save to chart to. Will get
                        displayed on-screen if empty
```


## bibox-market-maker-trades

Exports the list of recent trades which took place with the keeper, either as a text table (if invoked
with `--text`) or as a JSON document (if invoked with `--json`).

For sample text and JSON output, see the `oasis-market-maker-trades` above.

### Usage

```
usage: bibox-market-maker-trades [-h] [--bibox-api-server BIBOX_API_SERVER]
                                 --bibox-api-key BIBOX_API_KEY --bibox-secret
                                 BIBOX_SECRET [--bibox-timeout BIBOX_TIMEOUT]
                                 [--bibox-retry-count BIBOX_RETRY_COUNT]
                                 --pair PAIR --past-trades PAST_TRADES
                                 (--text | --json)

optional arguments:
  -h, --help            show this help message and exit
  --bibox-api-server BIBOX_API_SERVER
                        Address of the Bibox API server (default:
                        'https://api.bibox.com')
  --bibox-api-key BIBOX_API_KEY
                        API key for the Bibox API
  --bibox-secret BIBOX_SECRET
                        Secret for the Bibox API
  --bibox-timeout BIBOX_TIMEOUT
                        Timeout for accessing the Bibox API
  --bibox-retry-count BIBOX_RETRY_COUNT
                        Retry count for accessing the Bibox API (default: 20)
  --pair PAIR           Token pair to get the past trades for
  --past-trades PAST_TRADES
                        Number of past trades to fetch and show
  --text                List trades as a text table
  --json                List trades as a JSON document
```


## gateio-market-maker-chart

Draws a chart with price history read from a file and recent trades which took place with the keeper
(represented as dots). The size of the dots depends on the trade volume. This way we can clearly spot
if the keeper is not creating dangerous arbitrage opportunities.

Price history files can be supplied using `--price-history-file` and `--alternative-price-history-file`
arguments. If they are, it is expected that each line of them will be a simple JSON document with `timestamp`
and `price` properties. If neither `--price-history-file` not `--alternative-price-history-file` arguments
are supplied, only the trades will be displayed on the chart.

### Usage

```
usage: gateio-market-maker-chart [-h] [--gateio-api-server GATEIO_API_SERVER]
                                 --gateio-api-key GATEIO_API_KEY
                                 --gateio-secret-key GATEIO_SECRET_KEY
                                 [--gateio-timeout GATEIO_TIMEOUT]
                                 [--price-history-file PRICE_HISTORY_FILE]
                                 [--alternative-price-history-file ALTERNATIVE_PRICE_HISTORY_FILE]
                                 --pair PAIR [-o OUTPUT]

optional arguments:
  -h, --help            show this help message and exit
  --gateio-api-server GATEIO_API_SERVER
                        Address of the Gate.io API server (default:
                        'https://data.gate.io')
  --gateio-api-key GATEIO_API_KEY
                        API key for the Gate.io API
  --gateio-secret-key GATEIO_SECRET_KEY
                        Secret key for the Gate.io API
  --gateio-timeout GATEIO_TIMEOUT
                        Timeout for accessing the Gate.io API (in seconds,
                        default: 9.5)
  --price-history-file PRICE_HISTORY_FILE
                        File to use as the price history source
  --alternative-price-history-file ALTERNATIVE_PRICE_HISTORY_FILE
                        File to use as the alternative price history source
  --pair PAIR           Token pair to draw the chart for
  -o OUTPUT, --output OUTPUT
                        Name of the filename to save to chart to. Will get
                        displayed on-screen if empty
```


## gateio-market-maker-trades

Exports the list of recent trades which took place with the keeper, either as a text table (if invoked
with `--text`) or as a JSON document (if invoked with `--json`).

For sample text and JSON output, see the `oasis-market-maker-trades` above.

### Usage

```
usage: gateio-market-maker-trades [-h] [--gateio-api-server GATEIO_API_SERVER]
                                  --gateio-api-key GATEIO_API_KEY
                                  --gateio-secret-key GATEIO_SECRET_KEY
                                  [--gateio-timeout GATEIO_TIMEOUT] --pair
                                  PAIR (--text | --json)

optional arguments:
  -h, --help            show this help message and exit
  --gateio-api-server GATEIO_API_SERVER
                        Address of the Gate.io API server (default:
                        'https://data.gate.io')
  --gateio-api-key GATEIO_API_KEY
                        API key for the Gate.io API
  --gateio-secret-key GATEIO_SECRET_KEY
                        Secret key for the Gate.io API
  --gateio-timeout GATEIO_TIMEOUT
                        Timeout for accessing the Gate.io API (in seconds,
                        default: 9.5)
  --pair PAIR           Token pair to get the past trades for
  --text                List trades as a text table
  --json                List trades as a JSON document
```


## License

See [COPYING](https://github.com/makerdao/market-maker-stats/blob/master/COPYING) file.
