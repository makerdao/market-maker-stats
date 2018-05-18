# This file is part of Maker Keeper Framework.
#
# Copyright (C) 2017-2018 reverendus
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import argparse
import logging
import sys
import time
from typing import List

from web3 import Web3, HTTPProvider

from market_maker_stats.chart import initialize_charting, draw_chart, prepare_order_history_for_charting
from market_maker_stats.zrx import zrx_trades, Trade
from market_maker_stats.util import amount_in_usd_to_size, get_gdax_prices, Price, get_block_timestamp, \
    timestamp_to_x, initialize_logging, get_order_history, get_prices
from pymaker import Address
from pymaker.zrx import ZrxExchange


class ZrxMarketMakerChart:
    """Tool to generate a chart displaying the 0x market maker keeper trades."""

    def __init__(self, args: list):
        parser = argparse.ArgumentParser(prog='0x-market-maker-chart')
        parser.add_argument("--rpc-host", help="JSON-RPC host (default: `localhost')", default="localhost", type=str)
        parser.add_argument("--rpc-port", help="JSON-RPC port (default: `8545')", default=8545, type=int)
        parser.add_argument("--rpc-timeout", help="JSON-RPC timeout (in seconds, default: 60)", type=int, default=60)
        parser.add_argument("--exchange-address", help="Ethereum address of the 0x contract", required=True, type=str)
        parser.add_argument("--buy-token-address", help="Ethereum address of the buy token", required=True, type=str)
        parser.add_argument("--sell-token-address", help="Ethereum address of the sell token", required=True, type=str)
        parser.add_argument("--old-sell-token-address", help="Ethereum address of the old sell token", required=False, type=str)
        parser.add_argument("--market-maker-address", help="Ethereum account of the market maker to analyze", required=True, type=str)
        parser.add_argument("--gdax-price", help="GDAX product (ETH-USD, BTC-USD) to use as the price history source", type=str)
        parser.add_argument("--price-feed", help="Price endpoint to use as the price history source", type=str)
        parser.add_argument("--alternative-price-feed", help="Price endpoint to use as the alternative price history source", type=str)
        parser.add_argument("--order-history", help="Order history endpoint from which to fetch our order history", type=str)
        parser.add_argument("--past-blocks", help="Number of past blocks to analyze", required=True, type=int)
        parser.add_argument("-o", "--output", help="Name of the filename to save to chart to."
                                                   " Will get displayed on-screen if empty", required=False, type=str)
        self.arguments = parser.parse_args(args)

        self.web3 = Web3(HTTPProvider(endpoint_uri=f"http://{self.arguments.rpc_host}:{self.arguments.rpc_port}",
                                      request_kwargs={'timeout': self.arguments.rpc_timeout}))
        self.infura = Web3(HTTPProvider(endpoint_uri=f"https://mainnet.infura.io/", request_kwargs={'timeout': 120}))
        self.buy_token_address = Address(self.arguments.buy_token_address)
        self.sell_token_address = Address(self.arguments.sell_token_address)
        self.old_sell_token_address = Address(self.arguments.old_sell_token_address) if self.arguments.old_sell_token_address else None
        self.market_maker_address = Address(self.arguments.market_maker_address)
        self.exchange = ZrxExchange(web3=self.web3, address=Address(self.arguments.exchange_address))

        initialize_charting(self.arguments.output)
        initialize_logging()

    def main(self):
        start_timestamp = get_block_timestamp(self.infura, self.web3.eth.blockNumber - self.arguments.past_blocks)
        end_timestamp = int(time.time())

        events = self.exchange.past_fill(self.arguments.past_blocks, {'maker': self.market_maker_address.address})
        trades = zrx_trades(self.infura, self.market_maker_address, self.buy_token_address, [self.sell_token_address, self.old_sell_token_address], events, '-')

        prices = get_prices(self.arguments.gdax_price, self.arguments.price_feed, None, start_timestamp, end_timestamp)
        alternative_prices = get_prices(None, self.arguments.alternative_price_feed, None, start_timestamp, end_timestamp)

        order_history = get_order_history(self.arguments.order_history, start_timestamp, end_timestamp)
        order_history = prepare_order_history_for_charting(order_history)

        draw_chart(start_timestamp, end_timestamp, prices, alternative_prices, 180, order_history, trades, [], self.arguments.output)


if __name__ == '__main__':
    ZrxMarketMakerChart(sys.argv[1:]).main()
