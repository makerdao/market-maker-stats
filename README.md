# market-maker-stats

A set of tools for collecting data from the `market-maker-keeper`
(<https://github.com/makerdao/market-maker-keeper>) keepers.

The following tools are currently present:
* `oasis-market-maker-chart`,
* `oasis-market-maker-trades`,
* `etherdelta-market-maker-chart`,
* `etherdelta-market-maker-trades`,
* `radarrelay-market-maker-chart`,
* `bibox-market-maker-chart`,
* `bibox-market-maker-trades`.

<https://chat.makerdao.com/channel/keeper>


## oasis-market-maker-chart

Draws a chart with the historical GDAX ETH/USD price, closest `oasis-market-maker-keeper` bids and asks
(represented as lines) and trades taking place with the keeper (represented as dots).
The size of the dots depends on the trade volume. This way we can clearly spot
if the keeper is not creating dangerous arbitrage opportunities.

Example result:

![](https://s10.postimg.org/qzzbyuzxl/oasis_server1_1.png)

### Usage

```
usage: oasis-market-maker-chart [-h] [--rpc-host RPC_HOST]
                                [--rpc-port RPC_PORT] --oasis-address
                                OASIS_ADDRESS --sai-address SAI_ADDRESS
                                --weth-address WETH_ADDRESS
                                --market-maker-address MARKET_MAKER_ADDRESS
                                --past-blocks PAST_BLOCKS [-o OUTPUT]

optional arguments:
  -h, --help            show this help message and exit
  --rpc-host RPC_HOST   JSON-RPC host (default: `localhost')
  --rpc-port RPC_PORT   JSON-RPC port (default: `8545')
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


## etherdelta-market-maker-chart

Draws a chart with the historical GDAX ETH/USD price and trades taking place with the keeper
(represented as dots). The size of the dots depends on the trade volume. This way we can clearly spot
if the keeper is not creating dangerous arbitrage opportunities.

Example result:

![](https://s10.postimg.org/u83tbvjmh/etherdelta_server1_1.png)

### Usage

```
usage: etherdelta-market-maker-chart [-h] [--rpc-host RPC_HOST]
                                     [--rpc-port RPC_PORT]
                                     --etherdelta-address ETHERDELTA_ADDRESS
                                     --sai-address SAI_ADDRESS --eth-address
                                     ETH_ADDRESS --market-maker-address
                                     MARKET_MAKER_ADDRESS --past-blocks
                                     PAST_BLOCKS [-o OUTPUT]

optional arguments:
  -h, --help            show this help message and exit
  --rpc-host RPC_HOST   JSON-RPC host (default: `localhost')
  --rpc-port RPC_PORT   JSON-RPC port (default: `8545')
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


## radarrelay-market-maker-chart

Draws a chart with the historical GDAX ETH/USD price and trades taking place with the keeper
(represented as dots). The size of the dots depends on the trade volume. This way we can clearly spot
if the keeper is not creating dangerous arbitrage opportunities.

Example result:

![](https://s10.postimg.org/u83tbvjmh/etherdelta_server1_1.png)

### Usage

```
usage: radarrelay-market-maker-chart [-h] [--rpc-host RPC_HOST]
                                     [--rpc-port RPC_PORT] --exchange-address
                                     EXCHANGE_ADDRESS --sai-address
                                     SAI_ADDRESS --weth-address WETH_ADDRESS
                                     --market-maker-address
                                     MARKET_MAKER_ADDRESS --past-blocks
                                     PAST_BLOCKS [-o OUTPUT]

optional arguments:
  -h, --help            show this help message and exit
  --rpc-host RPC_HOST   JSON-RPC host (default: `localhost')
  --rpc-port RPC_PORT   JSON-RPC port (default: `8545')
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

Draws a chart with either the historical GDAX ETH/USD price or the price history read from a file, and trades
taking place with the keeper (represented as dots). The size of the dots depends on the trade volume.
This way we can clearly spot if the keeper is not creating dangerous arbitrage opportunities.

Price history files can be supplied using `--price-history-file` and `--alternative-price-history-file`
arguments. If they are, it is expected that each line of them will be a simple JSON document with `timestamp`
and `price` properties. If no `--price-history-file` argument is supplied, historical GDAX ETH/USD price
will be displayed.

Example result:

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


## License

See [COPYING](https://github.com/makerdao/market-maker-stats/blob/master/COPYING) file.
