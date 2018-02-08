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

from market_maker_stats.chart import initialize_charting, draw_chart
from market_maker_stats.util import get_file_prices, to_seconds, \
    initialize_logging
from pyexchange.gateio import GateIOApi


class GateIOMarketMakerChart:
    """Tool to generate a chart displaying the gate.io market maker keeper trades."""

    def __init__(self, args: list):
        parser = argparse.ArgumentParser(prog='gateio-market-maker-chart')
        parser.add_argument("--gateio-api-server", help="Address of the Gate.io API server (default: 'https://data.gate.io')", default="https://data.gate.io", type=str)
        parser.add_argument("--gateio-api-key", help="API key for the Gate.io API", required=True, type=str)
        parser.add_argument("--gateio-secret-key", help="Secret key for the Gate.io API", required=True, type=str)
        parser.add_argument("--gateio-timeout", help="Timeout for accessing the Gate.io API (in seconds, default: 9.5)", default=9.5, type=float)
        parser.add_argument("--price-history-file", help="File to use as the price history source", type=str)
        parser.add_argument("--alternative-price-history-file", help="File to use as the alternative price history source", type=str)
        parser.add_argument("--pair", help="Token pair to draw the chart for", required=True, type=str)
        parser.add_argument("--past", help="Past period of time for which to draw the chart for (e.g. 3d)", required=True, type=str)
        parser.add_argument("-o", "--output", help="Name of the filename to save to chart to."
                                                   " Will get displayed on-screen if empty", required=False, type=str)
        self.arguments = parser.parse_args(args)

        self.gateio_api = GateIOApi(api_server=self.arguments.gateio_api_server,
                                    api_key=self.arguments.gateio_api_key,
                                    secret_key=self.arguments.gateio_secret_key,
                                    timeout=self.arguments.gateio_timeout)

        initialize_charting(self.arguments.output)
        initialize_logging()

    def main(self):
        start_timestamp = int(time.time() - to_seconds(self.arguments.past))
        end_timestamp = int(time.time())

        trades = self.gateio_api.get_trades(self.arguments.pair, from_timestamp=start_timestamp, to_timestamp=end_timestamp)

        if self.arguments.price_history_file:
            prices = get_file_prices(self.arguments.price_history_file, start_timestamp, end_timestamp)
        else:
            prices = []

        if self.arguments.alternative_price_history_file:
            alternative_prices = get_file_prices(self.arguments.alternative_price_history_file, start_timestamp, end_timestamp)
        else:
            alternative_prices = []

        draw_chart(start_timestamp, end_timestamp, prices, alternative_prices, trades, self.arguments.output)


if __name__ == '__main__':
    GateIOMarketMakerChart(sys.argv[1:]).main()
