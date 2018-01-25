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
import datetime
import logging
import sys
from typing import List

from market_maker_stats.util import amount_to_size
from pyexchange.gateio import GateIOApi, Trade


class GateIOMarketMakerChart:
    """Tool to generate a chart displaying the gate.io market maker keeper trades."""

    def __init__(self, args: list):
        parser = argparse.ArgumentParser(prog='gateio-market-maker-chart')
        parser.add_argument("--gateio-api-server", help="Address of the Gate.io API server (default: 'https://data.gate.io')", default="https://data.gate.io", type=str)
        parser.add_argument("--gateio-api-key", help="API key for the Gate.io API", required=True, type=str)
        parser.add_argument("--gateio-secret-key", help="Secret key for the Gate.io API", required=True, type=str)
        parser.add_argument("--gateio-timeout", help="Timeout for accessing the Gate.io API (in seconds, default: 9.5)", default=9.5, type=float)
        parser.add_argument("--pair", help="Token pair to draw the chart for", required=True, type=str)
        parser.add_argument("-o", "--output", help="Name of the filename to save to chart to."
                                                   " Will get displayed on-screen if empty", required=False, type=str)
        self.arguments = parser.parse_args(args)

        self.gateio_api = GateIOApi(api_server=self.arguments.gateio_api_server,
                                    api_key=self.arguments.gateio_api_key,
                                    secret_key=self.arguments.gateio_secret_key,
                                    timeout=self.arguments.gateio_timeout)

        if self.arguments.output:
            import matplotlib
            matplotlib.use('Agg')

        logging.basicConfig(format='%(asctime)-15s %(levelname)-8s %(message)s', level=logging.INFO)

    def main(self):
        trades = self.gateio_api.get_trades(self.arguments.pair)
        self.draw(trades)

    def to_timestamp(self, price_or_trade):
        from matplotlib.dates import date2num

        return date2num(datetime.datetime.fromtimestamp(price_or_trade.timestamp))

    def to_price(self, trade: Trade):
        return trade.price

    def to_size(self, trade: Trade):
        return amount_to_size(trade.money_symbol, trade.money)

    def draw(self, trades: List[Trade]):
        import matplotlib.dates as md
        import matplotlib.pyplot as plt

        plt.subplots_adjust(bottom=0.2)
        plt.xticks(rotation=25)
        ax=plt.gca()
        ax.xaxis.set_major_formatter(md.DateFormatter('%Y-%m-%d %H:%M:%S'))

        sell_trades = list(filter(lambda trade: trade.is_sell, trades))
        sell_x = list(map(self.to_timestamp, sell_trades))
        sell_y = list(map(self.to_price, sell_trades))
        sell_s = list(map(self.to_size, sell_trades))
        plt.scatter(x=sell_x, y=sell_y, s=sell_s, c='blue', zorder=2)

        buy_trades = list(filter(lambda trade: not trade.is_sell, trades))
        buy_x = list(map(self.to_timestamp, buy_trades))
        buy_y = list(map(self.to_price, buy_trades))
        buy_s = list(map(self.to_size, buy_trades))
        plt.scatter(x=buy_x, y=buy_y, s=buy_s, c='green', zorder=2)

        if self.arguments.output:
            plt.savefig(fname=self.arguments.output, dpi=300, bbox_inches='tight', pad_inches=0)
        else:
            plt.show()


if __name__ == '__main__':
    GateIOMarketMakerChart(sys.argv[1:]).main()
