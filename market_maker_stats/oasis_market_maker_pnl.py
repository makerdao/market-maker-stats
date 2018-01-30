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

import numpy as np
from web3 import Web3, HTTPProvider

from market_maker_stats.oasis import oasis_trades
from market_maker_stats.pnl import calculate_pnl, prepare_trades_for_pnl, get_approx_vwaps
from market_maker_stats.util import get_gdax_prices, timestamp_to_x
from pymaker import Address
from pymaker.oasis import SimpleMarket


class OasisMarketMakerPnl:
    """Tool to calculate profitability for the OasisDEX market maker keeper."""

    def __init__(self, args: list):
        parser = argparse.ArgumentParser(prog='oasis-market-maker-pnl')
        parser.add_argument("--rpc-host", help="JSON-RPC host (default: `localhost')", default="localhost", type=str)
        parser.add_argument("--rpc-port", help="JSON-RPC port (default: `8545')", default=8545, type=int)
        parser.add_argument("--rpc-timeout", help="JSON-RPC timeout (in seconds, default: 60)", type=int, default=60)
        parser.add_argument("--oasis-address", help="Ethereum address of the OasisDEX contract", required=True, type=str)
        parser.add_argument("--sai-address", help="Ethereum address of the SAI token", required=True, type=str)
        parser.add_argument("--weth-address", help="Ethereum address of the WETH token", required=True, type=str)
        parser.add_argument("--market-maker-address", help="Ethereum account of the market maker to analyze", required=True, type=str)
        parser.add_argument("--vwap-minutes", help="Rolling VWAP window size (default: 240)", type=int, default=240)
        parser.add_argument("--past-blocks", help="Number of past blocks to analyze", required=True, type=int)

        parser_mode = parser.add_mutually_exclusive_group(required=True)
        parser_mode.add_argument('--text', help="Show PnL as a text table", dest='text', action='store_true')
        parser_mode.add_argument('--chart', help="Show PnL on a cumulative graph", dest='chart', action='store_true')

        self.arguments = parser.parse_args(args)

        self.web3 = Web3(HTTPProvider(endpoint_uri=f"http://{self.arguments.rpc_host}:{self.arguments.rpc_port}",
                                      request_kwargs={'timeout': self.arguments.rpc_timeout}))
        self.sai_address = Address(self.arguments.sai_address)
        self.weth_address = Address(self.arguments.weth_address)
        self.market_maker_address = Address(self.arguments.market_maker_address)
        self.otc = SimpleMarket(web3=self.web3, address=Address(self.arguments.oasis_address))

        logging.basicConfig(format='%(asctime)-15s %(levelname)-8s %(message)s', level=logging.INFO)
        logging.getLogger("filelock").setLevel(logging.WARNING)

    def token_pair(self):
        return "ETH/DAI"

    def base_token(self):
        return "ETH"

    def quote_token(self):
        return "DAI"

    def main(self):
        import matplotlib.dates as md
        import matplotlib.pyplot as plt

        events = self.otc.past_take(self.arguments.past_blocks)
        trades = oasis_trades(self.market_maker_address, self.sai_address, self.weth_address, events)
        start_timestamp = trades[0].timestamp
        end_timestamp = int(time.time())

        prices = get_gdax_prices(start_timestamp, end_timestamp)
        vwaps = get_approx_vwaps(prices, self.arguments.vwap_minutes)
        vwaps_start = start_timestamp

        pnl_trades, pnl_prices, pnl_timestamps = prepare_trades_for_pnl(trades)
        profits = calculate_pnl(pnl_trades, pnl_prices, pnl_timestamps, vwaps, vwaps_start)

        print("{}".format(np.sum(profits)))

        fig, ax = plt.subplots()
        ax.set_xlim(left=timestamp_to_x(start_timestamp), right=timestamp_to_x(end_timestamp))
        ax.xaxis.set_major_formatter(md.DateFormatter('%Y-%m-%d %H:%M:%S'))
        ax2 = ax.twinx()

        ax.set_zorder(ax2.get_zorder()+1)
        ax.patch.set_visible(False)

        dt_timestamps = [datetime.datetime.fromtimestamp(timestamp) for timestamp in pnl_timestamps]

        ax.plot(dt_timestamps[:len(profits)], np.cumsum(profits), color='green')
        ax2.plot(list(map(lambda price: timestamp_to_x(price.timestamp), prices)),
                 list(map(lambda price: price.market_price, prices)), color='red')

        ax.set_ylabel('Cumulative PnL ($)')
        ax2.set_ylabel('ETH/USD price ($)')
        plt.show()


if __name__ == '__main__':
    OasisMarketMakerPnl(sys.argv[1:]).main()
