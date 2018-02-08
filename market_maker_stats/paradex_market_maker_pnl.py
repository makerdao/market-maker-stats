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

from market_maker_stats.pnl import get_approx_vwaps, pnl_text, pnl_chart
from market_maker_stats.util import to_seconds, get_gdax_prices, sort_trades_for_pnl, initialize_logging, read_password
from pyexchange.paradex import ParadexApi


class ParadexMarketMakerPnl:
    """Tool to calculate profitability for the Paradex market maker keeper."""

    def __init__(self, args: list):
        parser = argparse.ArgumentParser(prog='paradex-market-maker-pnl')
        parser.add_argument("--eth-key-file", help="File with the private key file for the Ethereum account", required=True, type=str)
        parser.add_argument("--eth-password-file", help="File with the private key password for the Ethereum account", required=True, type=str)
        parser.add_argument("--paradex-api-server", help="Address of the Paradex API server (default: 'https://api.paradex.io/consumer')", default='https://api.paradex.io/consumer', type=str)
        parser.add_argument("--paradex-api-key", help="API key for the Paradex API", required=True, type=str)
        parser.add_argument("--paradex-api-timeout", help="Timeout for accessing the Paradex API", default=9.5, type=float)
        parser.add_argument("--vwap-minutes", help="Rolling VWAP window size (default: 240)", type=int, default=240)
        parser.add_argument("--pair", help="Token pair to get the past trades for", required=True, type=str)
        parser.add_argument("--past", help="Past period of time for which to get the trades for (e.g. 3d)", required=True, type=str)
        parser.add_argument("-o", "--output", help="Name of the filename to save to chart to."
                                                   " Will get displayed on-screen if empty", required=False, type=str)

        parser_mode = parser.add_mutually_exclusive_group(required=True)
        parser_mode.add_argument('--text', help="Show PnL as a text table", dest='text', action='store_true')
        parser_mode.add_argument('--chart', help="Show PnL on a cumulative graph", dest='chart', action='store_true')

        self.arguments = parser.parse_args(args)

        self.paradex_api = ParadexApi(None,
                                      self.arguments.paradex_api_server,
                                      self.arguments.paradex_api_key,
                                      self.arguments.paradex_api_timeout,
                                      self.arguments.eth_key_file,
                                      read_password(self.arguments.eth_password_file))

        if self.arguments.chart and self.arguments.output:
            import matplotlib
            matplotlib.use('Agg')

        initialize_logging()

    def main(self):
        start_timestamp = int(time.time() - to_seconds(self.arguments.past))
        end_timestamp = int(time.time())
        trades = self.paradex_api.get_trades(self.arguments.pair, from_timestamp=start_timestamp)
        trades = sort_trades_for_pnl(trades)

        prices = get_gdax_prices(start_timestamp, end_timestamp)
        vwaps = get_approx_vwaps(prices, self.arguments.vwap_minutes)
        vwaps_start = prices[0].timestamp

        if self.arguments.text:
            pnl_text(trades, vwaps, vwaps_start)

        if self.arguments.chart:
            pnl_chart(start_timestamp, end_timestamp, prices, trades, vwaps, vwaps_start, self.arguments.output)


if __name__ == '__main__':
    ParadexMarketMakerPnl(sys.argv[1:]).main()
