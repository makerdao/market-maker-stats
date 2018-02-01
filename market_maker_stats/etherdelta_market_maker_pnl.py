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

from web3 import Web3, HTTPProvider

from market_maker_stats.etherdelta import etherdelta_trades
from market_maker_stats.pnl import get_approx_vwaps, pnl_text, pnl_chart
from market_maker_stats.util import sort_trades_for_pnl, get_gdax_prices, get_block_timestamp
from pymaker import Address
from pymaker.etherdelta import EtherDelta


class EtherDeltaMarketMakerPnl:
    """Tool to calculate profitability for the EtherDelta market maker keeper."""

    def __init__(self, args: list):
        parser = argparse.ArgumentParser(prog='etherdelta-market-maker-pnl')
        parser.add_argument("--rpc-host", help="JSON-RPC host (default: `localhost')", default="localhost", type=str)
        parser.add_argument("--rpc-port", help="JSON-RPC port (default: `8545')", default=8545, type=int)
        parser.add_argument("--rpc-timeout", help="JSON-RPC timeout (in seconds, default: 60)", type=int, default=60)
        parser.add_argument("--etherdelta-address", help="Ethereum address of the EtherDelta contract", required=True, type=str)
        parser.add_argument("--sai-address", help="Ethereum address of the SAI token", required=True, type=str)
        parser.add_argument("--eth-address", help="Ethereum address of the ETH token", required=True, type=str)
        parser.add_argument("--market-maker-address", help="Ethereum account of the market maker to analyze", required=True, type=str)
        parser.add_argument("--vwap-minutes", help="Rolling VWAP window size (default: 240)", type=int, default=240)
        parser.add_argument("--past-blocks", help="Number of past blocks to analyze", required=True, type=int)
        parser.add_argument("-o", "--output", help="Name of the filename to save to chart to."
                                                   " Will get displayed on-screen if empty", required=False, type=str)

        parser_mode = parser.add_mutually_exclusive_group(required=True)
        parser_mode.add_argument('--text', help="Show PnL as a text table", dest='text', action='store_true')
        parser_mode.add_argument('--chart', help="Show PnL on a cumulative graph", dest='chart', action='store_true')

        self.arguments = parser.parse_args(args)

        self.web3 = Web3(HTTPProvider(endpoint_uri=f"http://{self.arguments.rpc_host}:{self.arguments.rpc_port}",
                                      request_kwargs={'timeout': self.arguments.rpc_timeout}))
        self.infura = Web3(HTTPProvider(endpoint_uri=f"https://mainnet.infura.io/", request_kwargs={'timeout': 120}))
        self.sai_address = Address(self.arguments.sai_address)
        self.eth_address = Address(self.arguments.eth_address)
        self.market_maker_address = Address(self.arguments.market_maker_address)
        self.etherdelta = EtherDelta(web3=self.web3, address=Address(self.arguments.etherdelta_address))

        if self.arguments.chart and self.arguments.output:
            import matplotlib
            matplotlib.use('Agg')

        logging.basicConfig(format='%(asctime)-15s %(levelname)-8s %(message)s', level=logging.INFO)
        logging.getLogger("filelock").setLevel(logging.WARNING)

    def main(self):
        start_timestamp = get_block_timestamp(self.infura, self.web3.eth.blockNumber - self.arguments.past_blocks)
        end_timestamp = int(time.time())

        events = self.etherdelta.past_trade(self.arguments.past_blocks, {'get': self.market_maker_address.address})
        trades = etherdelta_trades(self.infura, self.market_maker_address, self.sai_address, self.eth_address, events)
        trades = sort_trades_for_pnl(trades)

        prices = get_gdax_prices(start_timestamp, end_timestamp)
        vwaps = get_approx_vwaps(prices, self.arguments.vwap_minutes)
        vwaps_start = prices[0].timestamp

        if self.arguments.text:
            pnl_text(trades, vwaps, vwaps_start)

        if self.arguments.chart:
            pnl_chart(start_timestamp, end_timestamp, prices, trades, vwaps, vwaps_start, self.arguments.output)


if __name__ == '__main__':
    EtherDeltaMarketMakerPnl(sys.argv[1:]).main()
