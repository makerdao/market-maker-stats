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

import pytz
from texttable import Texttable
from web3 import Web3, HTTPProvider

from market_maker_stats.etherdelta import etherdelta_trades, Trade
from market_maker_stats.trades import text_trades, json_trades
from market_maker_stats.util import format_timestamp, sort_trades
from pymaker import Address
from pymaker.etherdelta import EtherDelta


class EtherDeltaMarketMakerTrades:
    """Tool to list historical trades for the EtherDelta market maker keeper."""

    def __init__(self, args: list):
        parser = argparse.ArgumentParser(prog='etherdelta-market-maker-trades')
        parser.add_argument("--rpc-host", help="JSON-RPC host (default: `localhost')", default="localhost", type=str)
        parser.add_argument("--rpc-port", help="JSON-RPC port (default: `8545')", default=8545, type=int)
        parser.add_argument("--rpc-timeout", help="JSON-RPC timeout (in seconds, default: 60)", type=int, default=60)
        parser.add_argument("--etherdelta-address", help="Ethereum address of the EtherDelta contract", required=True, type=str)
        parser.add_argument("--sai-address", help="Ethereum address of the SAI token", required=True, type=str)
        parser.add_argument("--eth-address", help="Ethereum address of the ETH token", required=True, type=str)
        parser.add_argument("--market-maker-address", help="Ethereum account of the market maker to analyze", required=True, type=str)
        parser.add_argument("--past-blocks", help="Number of past blocks to analyze", required=True, type=int)
        parser.add_argument("-o", "--output", help="File to save the table or the JSON to", required=False, type=str)

        parser_mode = parser.add_mutually_exclusive_group(required=True)
        parser_mode.add_argument('--text', help="List trades as a text table", dest='text', action='store_true')
        parser_mode.add_argument('--json', help="List trades as a JSON document", dest='json', action='store_true')

        self.arguments = parser.parse_args(args)

        self.web3 = Web3(HTTPProvider(endpoint_uri=f"http://{self.arguments.rpc_host}:{self.arguments.rpc_port}",
                                      request_kwargs={'timeout': self.arguments.rpc_timeout}))
        self.infura = Web3(HTTPProvider(endpoint_uri=f"https://mainnet.infura.io/", request_kwargs={'timeout': 120}))
        self.sai_address = Address(self.arguments.sai_address)
        self.eth_address = Address(self.arguments.eth_address)
        self.market_maker_address = Address(self.arguments.market_maker_address)
        self.etherdelta = EtherDelta(web3=self.web3, address=Address(self.arguments.etherdelta_address))

        logging.basicConfig(format='%(asctime)-15s %(levelname)-8s %(message)s', level=logging.INFO)
        logging.getLogger("filelock").setLevel(logging.WARNING)

    def sell_token(self):
        return "ETH"

    def buy_token(self):
        return "DAI"

    def main(self):
        past_trades = self.etherdelta.past_trade(self.arguments.past_blocks, {'get': self.market_maker_address.address})
        trades = etherdelta_trades(self.infura, self.market_maker_address, self.sai_address, self.eth_address, past_trades)
        trades = sort_trades(trades)

        if self.arguments.text:
            text_trades(self.buy_token(), self.sell_token(), trades, self.arguments.output, include_taker=True)

        if self.arguments.json:
            json_trades(trades, self.arguments.output, include_taker=True)


if __name__ == '__main__':
    EtherDeltaMarketMakerTrades(sys.argv[1:]).main()
