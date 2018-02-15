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
import sys
import time

from web3 import Web3, HTTPProvider

from market_maker_stats.chart import initialize_charting, draw_chart
from market_maker_stats.util import get_gdax_prices, get_file_prices, to_seconds, initialize_logging
from pyexchange.paradex import ParadexApi
from pymaker import Address
from pymaker.zrx import ZrxExchange


class ParadexMarketMakerChart:
    """Tool to generate a chart displaying the Paradex market maker keeper trades."""

    def __init__(self, args: list):
        parser = argparse.ArgumentParser(prog='paradex-market-maker-chart')
        parser.add_argument("--rpc-host", help="JSON-RPC host (default: `localhost')", default="localhost", type=str)
        parser.add_argument("--rpc-port", help="JSON-RPC port (default: `8545')", default=8545, type=int)
        parser.add_argument("--rpc-timeout", help="JSON-RPC timeout (in seconds, default: 60)", type=int, default=60)
        parser.add_argument("--paradex-api-server", help="Address of the Paradex API server (default: 'https://api.paradex.io/consumer')", default='https://api.paradex.io/consumer', type=str)
        parser.add_argument("--paradex-api-key", help="API key for the Paradex API", required=True, type=str)
        parser.add_argument("--paradex-api-timeout", help="Timeout for accessing the Paradex API", default=9.5, type=float)
        parser.add_argument("--exchange-address", help="Ethereum address of the 0x contract", required=True, type=str)
        parser.add_argument("--market-maker-address", help="Ethereum account of the trading account", required=True, type=str)
        parser.add_argument("--gdax-price", help="GDAX product (ETH-USD, BTC-USD) to use as the price history source", type=str)
        parser.add_argument("--price-history-file", help="File to use as the price history source", type=str)
        parser.add_argument("--alternative-price-history-file", help="File to use as the alternative price history source", type=str)
        parser.add_argument("--pair", help="Token pair to draw the chart for", required=True, type=str)
        parser.add_argument("--past", help="Past period of time for which to draw the chart for (e.g. 3d)", required=True, type=str)
        parser.add_argument("-o", "--output", help="Name of the filename to save to chart to."
                                                   " Will get displayed on-screen if empty", required=False, type=str)
        self.arguments = parser.parse_args(args)

        self.web3 = Web3(HTTPProvider(endpoint_uri=f"http://{self.arguments.rpc_host}:{self.arguments.rpc_port}",
                                      request_kwargs={'timeout': self.arguments.rpc_timeout}))
        self.web3.eth.defaultAccount = self.arguments.market_maker_address

        self.exchange = ZrxExchange(web3=self.web3, address=Address(self.arguments.exchange_address))
        self.paradex_api = ParadexApi(self.exchange,
                                      self.arguments.paradex_api_server,
                                      self.arguments.paradex_api_key,
                                      self.arguments.paradex_api_timeout)

        initialize_charting(self.arguments.output)
        initialize_logging()

    def main(self):
        start_timestamp = int(time.time() - to_seconds(self.arguments.past))
        end_timestamp = int(time.time())

        trades = self.paradex_api.get_trades(pair=self.arguments.pair,
                                             from_timestamp=start_timestamp,
                                             to_timestamp=end_timestamp)

        if self.arguments.price_history_file:
            prices = get_file_prices(self.arguments.price_history_file, start_timestamp, end_timestamp)
        elif self.arguments.gdax_price:
            prices = get_gdax_prices(self.arguments.gdax_price, start_timestamp, end_timestamp)
        else:
            prices = []

        if self.arguments.alternative_price_history_file:
            alternative_prices = get_file_prices(self.arguments.alternative_price_history_file, start_timestamp, end_timestamp)
        else:
            alternative_prices = []

        draw_chart(start_timestamp, end_timestamp, prices, alternative_prices, trades, self.arguments.output)


if __name__ == '__main__':
    ParadexMarketMakerChart(sys.argv[1:]).main()
