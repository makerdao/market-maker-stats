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
import json
import logging
import sys
from typing import List

import numpy as np
import pytz
from texttable import Texttable
from web3 import Web3, HTTPProvider

import market_maker_stats
from market_maker_stats.oasis import Trade, oasis_trades
from market_maker_stats.util import format_timestamp
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
        parser.add_argument("--past-blocks", help="Number of past blocks to analyze", required=True, type=int)

        self.arguments = parser.parse_args(args)

        self.web3 = Web3(HTTPProvider(endpoint_uri=f"http://{self.arguments.rpc_host}:{self.arguments.rpc_port}",
                                      request_kwargs={'timeout': self.arguments.rpc_timeout}))
        self.sai_address = Address(self.arguments.sai_address)
        self.weth_address = Address(self.arguments.weth_address)
        self.market_maker_address = Address(self.arguments.market_maker_address)
        self.otc = SimpleMarket(web3=self.web3, address=Address(self.arguments.oasis_address))

        logging.basicConfig(format='%(asctime)-15s %(levelname)-8s %(message)s', level=logging.INFO)

    def token_pair(self):
        return "ETH/DAI"

    def base_token(self):
        return "ETH"

    def quote_token(self):
        return "DAI"

    def main(self):
        import matplotlib
        import matplotlib.pyplot as plt

        take_events = self.otc.past_take(self.arguments.past_blocks)
        trades = oasis_trades(self.market_maker_address, self.sai_address, self.weth_address, take_events)

        trades, prices, timestamps = market_maker_stats.util.parse_trades(trades)

        profits = market_maker_stats.util.calculate_pnl_vwap(trades, prices, timestamps, vwap_minutes=240)

        print("{}".format(np.sum(profits)))

        fig, ax = plt.subplots()
        ax2 = ax.twinx()

        dt_timestamps = [datetime.datetime.fromtimestamp(timestamp) for timestamp in timestamps]

        ax.plot(dt_timestamps[:len(profits)], np.cumsum(profits), color='green')
        ax2.plot(dt_timestamps[:len(profits)], prices[:len(profits)], color='blue')

        ax.set_ylabel('Cumulative PnL ($)')
        ax2.set_ylabel('ETH/USD price ($)')
        plt.show()


if __name__ == '__main__':
    OasisMarketMakerPnl(sys.argv[1:]).main()
