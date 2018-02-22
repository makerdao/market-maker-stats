# market-maker-stats

[![Build Status](https://travis-ci.org/makerdao/market-maker-stats.svg?branch=master)](https://travis-ci.org/makerdao/market-maker-stats)
[![codecov](https://codecov.io/gh/makerdao/market-maker-stats/branch/master/graph/badge.svg)](https://codecov.io/gh/makerdao/market-maker-stats)

A set of tools for collecting data from the `market-maker-keeper`
(<https://github.com/makerdao/market-maker-keeper>) keepers.

The following tools are available in this repository:
* `oasis-market-maker-chart` (trade chart tool for OasisDEX),
* `oasis-market-maker-pnl` (profitability calculation tool for OasisDEX),
* `oasis-market-maker-trades` (trade history dumping tool for OasisDEX),
* `etherdelta-market-maker-chart` (trade chart tool for EtherDelta),
* `etherdelta-market-maker-pnl` (profitability calculation tool for EtherDelta),
* `etherdelta-market-maker-trades` (trade history dumping tool for EtherDelta),
* `0x-market-maker-chart` (trade chart tool for 0x exchanges),
* `0x-market-maker-pnl` (profitability calculation tool for 0x exchanges),
* `0x-market-maker-trades` (trade history dumping tool for 0x exchanges),
* `paradex-market-maker-chart` (trade chart tool for Paradex),
* `paradex-market-maker-pnl` (profitability calculation tool for Paradex),
* `paradex-market-maker-trades` (trade history dumping tool for Paradex),
* `bibox-market-maker-chart` (trade chart tool for Bibox),
* `bibox-market-maker-pnl` (profitability calculation tool for Bibox),
* `bibox-market-maker-trades` (trade history dumping tool for Bibox),
* `gateio-market-maker-chart` (trade chart tool for gate.io),
* `gateio-market-maker-trades` (trade history dumping tool for gate.io).

<https://chat.makerdao.com/channel/keeper>


## Installation

This project uses *Python 3.6.2*.

In order to clone the project and install required third-party packages please execute:
```
git clone https://github.com/makerdao/market-maker-stats.git
git submodule update --init --recursive
pip3 install -r requirements.txt
```

For some known macOS issues see the [pymaker](https://github.com/makerdao/pymaker) README.


## Trade chart tools

These tools draw a chart with either the historical GDAX ETH/USD price, the historical GDAX BTC/USD price,
or any other price which history is present in a disk file, and recent trades which took place with the keeper
(represented as dots). The size of the dots depends on the trade volume. This way we can clearly
spot if the keeper is not creating dangerous arbitrage opportunities.

Price history files can be supplied using `--price-history-file` and `--alternative-price-history-file`
arguments. If they are, it is expected that each line of them will be a simple JSON document with `timestamp`
and `price` properties. If no `--price-history-file` argument is supplied, the `--gdax-price` argument
can be used to make the tools use historical GDAX price data. The value of this argument is the GDAX
product identifier, it only currently makes sense to use `ETH-USD` or `BTC-USD`.

In case of OasisDEX (the `oasis-market-maker-chart` tool), closest bids and asks will also be shown
in the chart (represented as lines).

Sample result for OasisDEX:

![](https://s10.postimg.org/qzzbyuzxl/oasis_server1_1.png)

Sample result for some other exchange:

![](https://s10.postimg.org/u83tbvjmh/etherdelta_server1_1.png)


## Profitability calculation tools

These tools perform profitability calculation of ETH/DAI or BTC/DAI keepers.

Sample text output:

```
PnL report for DAI market-making:

    Day       # transactions           Bought                 Sold                    Net bought                Cumulative net               Profit          
                                                                                                                    bought                                   
=============================================================================================================================================================
2017-12-29                 16          19,785.70 DAI        20,230.31 DAI                      -444.61 DAI         326,188.03 DAI                  337.93 USD
2017-12-30                 43          74,652.49 DAI        58,584.57 DAI                    16,067.92 DAI         342,255.95 DAI                2,292.57 USD
2017-12-31                 23          41,964.14 DAI            14.50 DAI                    41,949.64 DAI         384,205.59 DAI                  429.15 USD

The first and the last day of the report may not contain all trades.
As a rolling VWAP window is used, last window of trades is excluded from profit calculation.

Number of trades: 82
Total profit: 2,771.40 USD
Generated at: 2018.01.01 11:32:00 UTC
```


## Trade history dumping tools

These tools export the list of recent trades which took place with the keeper, either as a text table
(if invoked with `--text`) or as a JSON document (if invoked with `--json`).

Taker address is only present for OasisDEX.

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


## License

See [COPYING](https://github.com/makerdao/market-maker-stats/blob/master/COPYING) file.
