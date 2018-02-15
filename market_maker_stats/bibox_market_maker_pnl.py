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

from market_maker_stats.pnl import get_approx_vwaps, pnl_text, pnl_chart
from market_maker_stats.util import to_seconds, get_gdax_prices, sort_trades_for_pnl
from pyexchange.bibox import BiboxApi


class BiboxMarketMakerPnl:
    """Tool to calculate profitability for the Bibox market maker keeper."""

    def __init__(self, args: list):
        parser = argparse.ArgumentParser(prog='bibox-market-maker-pnl')
        parser.add_argument("--bibox-api-server", help="Address of the Bibox API server (default: 'https://api.bibox.com')", default="https://api.bibox.com", type=str)
        parser.add_argument("--bibox-api-key", help="API key for the Bibox API", required=True, type=str)
        parser.add_argument("--bibox-secret", help="Secret for the Bibox API", required=True, type=str)
        parser.add_argument("--bibox-timeout", help="Timeout for accessing the Bibox API", default=9.5, type=float)
        parser.add_argument("--bibox-retry-count", help="Retry count for accessing the Bibox API (default: 20)", default=20, type=int)
        parser.add_argument("--gdax-price", help="GDAX product (ETH-USD, BTC-USD) to use as the price history source", required=True, type=str)
        parser.add_argument("--vwap-minutes", help="Rolling VWAP window size (default: 240)", type=int, default=240)
        parser.add_argument("--pair", help="Token pair to get the past trades for", required=True, type=str)
        parser.add_argument("--past", help="Past period of time for which to get the trades for (e.g. 3d)", required=True, type=str)
        parser.add_argument("-o", "--output", help="Name of the filename to save to chart to."
                                                   " Will get displayed on-screen if empty", required=False, type=str)

        parser_mode = parser.add_mutually_exclusive_group(required=True)
        parser_mode.add_argument('--text', help="Show PnL as a text table", dest='text', action='store_true')
        parser_mode.add_argument('--chart', help="Show PnL on a cumulative graph", dest='chart', action='store_true')

        self.arguments = parser.parse_args(args)

        self.bibox_api = BiboxApi(api_server=self.arguments.bibox_api_server,
                                  api_key=self.arguments.bibox_api_key,
                                  secret=self.arguments.bibox_secret,
                                  timeout=self.arguments.bibox_timeout)

        if self.arguments.chart and self.arguments.output:
            import matplotlib
            matplotlib.use('Agg')

        logging.basicConfig(format='%(asctime)-15s %(levelname)-8s %(message)s', level=logging.INFO)
        logging.getLogger("filelock").setLevel(logging.WARNING)

    def main(self):
        start_timestamp = int(time.time() - to_seconds(self.arguments.past))
        end_timestamp = int(time.time())
        trades = self.bibox_api.get_trades(self.arguments.pair, True, self.arguments.bibox_retry_count, from_timestamp=start_timestamp)
        trades = sort_trades_for_pnl(trades)

        prices = get_gdax_prices(self.arguments.gdax_price, start_timestamp, end_timestamp)
        vwaps = get_approx_vwaps(prices, self.arguments.vwap_minutes)
        vwaps_start = prices[0].timestamp

        if self.arguments.text:
            pnl_text(trades, vwaps, vwaps_start)

        if self.arguments.chart:
            pnl_chart(start_timestamp, end_timestamp, prices, trades, vwaps, vwaps_start, self.arguments.output)


if __name__ == '__main__':
    BiboxMarketMakerPnl(sys.argv[1:]).main()
