# This file is part of Maker Keeper Framework.
#
# Copyright (C) 2017 reverendus
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

import matplotlib
matplotlib.use('Agg')

import argparse
import datetime
import sys
import time
from typing import List

import matplotlib.dates as md
import matplotlib.pyplot as plt
import pytz
import requests
from matplotlib.dates import date2num

from pymaker.bibox import BiboxApi
from pymaker.numeric import Wad


class Price:
    def __init__(self, timestamp: int, market_price: Wad):
        self.timestamp = timestamp
        self.market_price = market_price


class Trade:
    def __init__(self, timestamp: int, price: Wad, is_buy: bool, is_sell: bool):
        self.timestamp = timestamp
        self.price = price
        self.is_buy = is_buy
        self.is_sell = is_sell


class BiboxMarketMakerChart:
    """Tool to analyze the Bibox Market Maker keeper performance."""

    def __init__(self, args: list):
        parser = argparse.ArgumentParser(prog='bibox-market-maker-chart')
        parser.add_argument("--bibox-api-server", help="Address of the Bibox API server (default: 'https://api.bibox.com')", default="https://api.bibox.com", type=str)
        parser.add_argument("--bibox-api-key", help="API key for the Bibox API", required=True, type=str)
        parser.add_argument("--bibox-secret", help="Secret for the Bibox API", required=True, type=str)
        parser.add_argument("--past-trades", help="Number of past trades to fetch and display", required=True, type=int)
        parser.add_argument("-o", "--output", help="Name of the filename to save to chart to."
                                                   " Will get displayed on-screen if empty", required=False, type=str)
        self.arguments = parser.parse_args(args)

        self.bibox_api = BiboxApi(api_server=self.arguments.bibox_api_server,
                                  api_key=self.arguments.bibox_api_key,
                                  secret=self.arguments.bibox_secret)

    def main(self):
        trades = self.bibox_api.get_trade_history('ETH_DAI', self.arguments.past_trades, retry=True)

        start_timestamp = min(trades, key=lambda trade: trade.timestamp).timestamp
        end_timestamp = int(time.time())
        prices = self.get_gdax_prices(start_timestamp, end_timestamp)

        self.draw(prices, trades)

    def get_gdax_prices(self, start_timestamp: int, end_timestamp: int):
        prices = []
        timestamp = start_timestamp
        while timestamp <= end_timestamp:
            timestamp_range_start = timestamp
            timestamp_range_end = int((datetime.datetime.fromtimestamp(timestamp) + datetime.timedelta(hours=3)).timestamp())
            prices = prices + list(filter(lambda state: state.timestamp >= start_timestamp and state.timestamp <= end_timestamp,
                                          self.get_gdax_partial(timestamp_range_start, timestamp_range_end)))
            timestamp = timestamp_range_end

        return sorted(prices, key=lambda price: price.timestamp)

    def get_gdax_partial(self, timestamp_range_start: int, timestamp_range_end: int):
        start = datetime.datetime.fromtimestamp(timestamp_range_start, pytz.UTC)
        end = datetime.datetime.fromtimestamp(timestamp_range_end, pytz.UTC)

        url = f"https://api.gdax.com/products/ETH-USD/candles?" \
              f"start={self.iso_8601(start)}&" \
              f"end={self.iso_8601(end)}&" \
              f"granularity=60"

        print(f"Downloading: {url}")

        # data is: [[ time, low, high, open, close, volume ], [...]]
        try:
            data = requests.get(url).json()
        except:
            print("GDAX API network error, waiting 10 secs...")
            time.sleep(10)
            return self.get_gdax_partial(timestamp_range_start, timestamp_range_end)

        if 'message' in data:
            print("GDAX API rate limiting, slowing down for 2 secs...")
            time.sleep(2)
            return self.get_gdax_partial(timestamp_range_start, timestamp_range_end)
        else:
            return list(map(lambda array: Price(timestamp=array[0],
                                                market_price=array[3]), data))  # array[3] is 'open'

    @staticmethod
    def iso_8601(tm) -> str:
        return tm.isoformat().replace('+00:00', 'Z')

    def convert_timestamp(self, timestamp):
        return date2num(datetime.datetime.fromtimestamp(timestamp))

    def draw(self, prices: List[Price], trades: List[Trade]):
        plt.subplots_adjust(bottom=0.2)
        plt.xticks(rotation=25)
        ax=plt.gca()
        ax.xaxis.set_major_formatter(md.DateFormatter('%Y-%m-%d %H:%M:%S'))

        timestamps = list(map(self.convert_timestamp, map(lambda price: price.timestamp, prices)))
        market_prices = list(map(lambda price: price.market_price, prices))
        plt.plot_date(timestamps, market_prices, 'r-')

        sell_trades = list(filter(lambda trade: trade.is_sell, trades))
        buy_trades = list(filter(lambda trade: not trade.is_sell, trades))
        plt.plot_date(list(map(self.convert_timestamp, map(lambda trade: trade.timestamp, sell_trades))),
                      list(map(lambda trade: trade.price, sell_trades)), 'b*')
        plt.plot_date(list(map(self.convert_timestamp, map(lambda trade: trade.timestamp, buy_trades))),
                      list(map(lambda trade: trade.price, buy_trades)), 'g*')

        if self.arguments.output:
            plt.savefig(fname=self.arguments.output, dpi=300, bbox_inches='tight', pad_inches=0)
        else:
            plt.show()


if __name__ == '__main__':
    BiboxMarketMakerChart(sys.argv[1:]).main()
