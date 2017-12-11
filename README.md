# market-maker-stats

A set of tools for collecting data from the `market-maker-keeper` keepers.

<https://chat.makerdao.com/channel/keeper>

## oasis-market-maker-chart

Draws a chart with the GDAX price and closest `oasis-market-maker-keeper` bid and asks.
This way we can clearly spot if we are not creating dangerous arbitrage opportunities:

Example result:

![](https://s18.postimg.org/vkj0jgag9/image.png)

### Usage

```
usage: oasis-market-maker-chart [-h] [--rpc-host RPC_HOST]
                                [--rpc-port RPC_PORT] --oasis-address
                                OASIS_ADDRESS --sai-address SAI_ADDRESS
                                --weth-address WETH_ADDRESS
                                --market-maker-address MARKET_MAKER_ADDRESS
                                --past-blocks PAST_BLOCKS

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
```

## License

See [COPYING](https://github.com/makerdao/market-maker-stats/blob/master/COPYING) file.
