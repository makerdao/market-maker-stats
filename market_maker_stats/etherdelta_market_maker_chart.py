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
import time
from typing import List

from web3 import Web3, HTTPProvider

from market_maker_stats.etherdelta import Trade, etherdelta_trades
from market_maker_stats.util import amount_in_usd_to_size, get_gdax_prices, Price
from pymaker import Address
from pymaker.etherdelta import EtherDelta


class EtherDeltaMarketMakerChart:
    """Tool to generate a chart displaying the EtherDelta market maker keeper trades."""

    def __init__(self, args: list):
        parser = argparse.ArgumentParser(prog='etherdelta-market-maker-chart')
        parser.add_argument("--rpc-host", help="JSON-RPC host (default: `localhost')", default="localhost", type=str)
        parser.add_argument("--rpc-port", help="JSON-RPC port (default: `8545')", default=8545, type=int)
        parser.add_argument("--rpc-timeout", help="JSON-RPC timeout (in seconds, default: 60)", type=int, default=60)
        parser.add_argument("--etherdelta-address", help="Ethereum address of the EtherDelta contract", required=True, type=str)
        parser.add_argument("--sai-address", help="Ethereum address of the SAI token", required=True, type=str)
        parser.add_argument("--eth-address", help="Ethereum address of the ETH token", required=True, type=str)
        parser.add_argument("--market-maker-address", help="Ethereum account of the market maker to analyze", required=True, type=str)
        parser.add_argument("--past-blocks", help="Number of past blocks to analyze", required=True, type=int)
        parser.add_argument("-o", "--output", help="Name of the filename to save to chart to."
                                                   " Will get displayed on-screen if empty", required=False, type=str)
        self.arguments = parser.parse_args(args)

        self.web3 = Web3(HTTPProvider(endpoint_uri=f"http://{self.arguments.rpc_host}:{self.arguments.rpc_port}",
                                      request_kwargs={'timeout': self.arguments.rpc_timeout}))
        self.infura = Web3(HTTPProvider(endpoint_uri=f"https://mainnet.infura.io/", request_kwargs={'timeout': 120}))
        self.sai_address = Address(self.arguments.sai_address)
        self.eth_address = Address(self.arguments.eth_address)
        self.market_maker_address = Address(self.arguments.market_maker_address)
        self.etherdelta = EtherDelta(web3=self.web3, address=Address(self.arguments.etherdelta_address))

        if self.arguments.output:
            import matplotlib
            matplotlib.use('Agg')

        logging.basicConfig(format='%(asctime)-15s %(levelname)-8s %(message)s', level=logging.INFO)

    def main(self):
        past_trades = self.etherdelta.past_trade(self.arguments.past_blocks)
        trades = etherdelta_trades(self.infura, self.market_maker_address, self.sai_address, self.eth_address, past_trades)

        start_timestamp = trades[0].timestamp
        end_timestamp = int(time.time())
        prices = get_gdax_prices(start_timestamp, end_timestamp)

        self.draw(prices, trades)

    def convert_timestamp(self, timestamp):
        from matplotlib.dates import date2num

        return date2num(datetime.datetime.fromtimestamp(timestamp))

    def to_size(self, trade: Trade):
        return amount_in_usd_to_size(trade.money)

    def draw(self, prices: List[Price], trades: List[Trade]):
        import matplotlib.dates as md
        import matplotlib.pyplot as plt

        plt.subplots_adjust(bottom=0.2)
        plt.xticks(rotation=25)
        ax=plt.gca()
        ax.xaxis.set_major_formatter(md.DateFormatter('%Y-%m-%d %H:%M:%S'))

        timestamps = list(map(self.convert_timestamp, map(lambda price: price.timestamp, prices)))
        market_prices = list(map(lambda price: price.market_price, prices))
        plt.plot_date(timestamps, market_prices, 'r-', zorder=1)

        sell_trades = list(filter(lambda trade: trade.is_sell, trades))
        sell_x = list(map(self.convert_timestamp, map(lambda trade: trade.timestamp, sell_trades)))
        sell_y = list(map(lambda trade: trade.price, sell_trades))
        sell_s = list(map(self.to_size, sell_trades))
        plt.scatter(x=sell_x, y=sell_y, s=sell_s, c='blue', zorder=2)

        buy_trades = list(filter(lambda trade: trade.is_buy, trades))
        buy_x = list(map(self.convert_timestamp, map(lambda trade: trade.timestamp, buy_trades)))
        buy_y = list(map(lambda trade: trade.price, buy_trades))
        buy_s = list(map(self.to_size, buy_trades))
        plt.scatter(x=buy_x, y=buy_y, s=buy_s, c='green', zorder=2)

        if self.arguments.output:
            plt.savefig(fname=self.arguments.output, dpi=300, bbox_inches='tight', pad_inches=0)
        else:
            plt.show()


if __name__ == '__main__':
    EtherDeltaMarketMakerChart(sys.argv[1:]).main()
