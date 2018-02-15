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
from market_maker_stats.etherdelta import etherdelta_trades
from market_maker_stats.util import get_gdax_prices, get_block_timestamp, initialize_logging
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
        parser.add_argument("--gdax-price", help="GDAX product (ETH-USD, BTC-USD) to use as the price history source", required=True, type=str)
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

        initialize_charting(self.arguments.output)
        initialize_logging()

    def main(self):
        start_timestamp = get_block_timestamp(self.infura, self.web3.eth.blockNumber - self.arguments.past_blocks)
        end_timestamp = int(time.time())

        events = self.etherdelta.past_trade(self.arguments.past_blocks, {'get': self.market_maker_address.address})
        trades = etherdelta_trades(self.infura, self.market_maker_address, self.sai_address, self.eth_address, events)

        prices = get_gdax_prices(self.arguments.gdax_price, start_timestamp, end_timestamp)

        draw_chart(start_timestamp, end_timestamp, prices, [], trades, self.arguments.output)


if __name__ == '__main__':
    EtherDeltaMarketMakerChart(sys.argv[1:]).main()
