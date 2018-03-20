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
from market_maker_stats.util import get_gdax_prices, get_file_prices, to_seconds, initialize_logging, get_prices, \
    get_trades
from pyexchange.paradex import ParadexApi
from pymaker import Address
from pymaker.zrx import ZrxExchange


class ParadexMarketMakerChart:
    """Tool to generate a chart displaying the Paradex market maker keeper trades."""

    def __init__(self, args: list):
        parser = argparse.ArgumentParser(prog='paradex-market-maker-chart')
        parser.add_argument("--paradex-api-server", help="Address of the Paradex API server (default: 'https://api.paradex.io/consumer')", default='https://api.paradex.io/consumer', type=str)
        parser.add_argument("--paradex-api-key", help="API key for the Paradex API", required=True, type=str)
        parser.add_argument("--paradex-api-timeout", help="Timeout for accessing the Paradex API", default=9.5, type=float)
        parser.add_argument("--gdax-price", help="GDAX product (ETH-USD, BTC-USD) to use as the price history source", type=str)
        parser.add_argument("--price-feed", help="Price endpoint to use as the price history source", type=str)
        parser.add_argument("--alternative-price-feed", help="Price endpoint to use as the alternative price history source", type=str)
        parser.add_argument("--all-trades", help="Trades endpoint from which to fetch all market trades", type=str)
        parser.add_argument("--pair", help="Token pair to draw the chart for", required=True, type=str)
        parser.add_argument("--past", help="Past period of time for which to draw the chart for (e.g. 3d)", required=True, type=str)
        parser.add_argument("-o", "--output", help="Name of the filename to save to chart to."
                                                   " Will get displayed on-screen if empty", required=False, type=str)
        self.arguments = parser.parse_args(args)

        self.paradex_api = ParadexApi(None,
                                      self.arguments.paradex_api_server,
                                      self.arguments.paradex_api_key,
                                      self.arguments.paradex_api_timeout)

        initialize_charting(self.arguments.output)
        initialize_logging()

    def main(self):
        start_timestamp = int(time.time() - to_seconds(self.arguments.past))
        end_timestamp = int(time.time())

        our_trades = self.paradex_api.get_trades(pair=self.arguments.pair, from_timestamp=start_timestamp, to_timestamp=end_timestamp)
        all_trades = get_trades(self.arguments.all_trades, start_timestamp, end_timestamp)

        prices = get_prices(self.arguments.gdax_price, self.arguments.price_feed, None, start_timestamp, end_timestamp)
        alternative_prices = get_prices(None, self.arguments.alternative_price_feed, None, start_timestamp, end_timestamp)

        draw_chart(start_timestamp, end_timestamp, prices, alternative_prices, our_trades, all_trades, self.arguments.output)


if __name__ == '__main__':
    ParadexMarketMakerChart(sys.argv[1:]).main()
