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

from market_maker_stats.oasis import Trade, oasis_trades
from market_maker_stats.util import format_timestamp
from pymaker import Address
from pymaker.oasis import SimpleMarket


class OasisMarketMakerTrades:
    """Tool to list historical trades for the OasisDEX market maker keeper."""

    def __init__(self, args: list):
        parser = argparse.ArgumentParser(prog='oasis-market-maker-trades')
        parser.add_argument("--rpc-host", help="JSON-RPC host (default: `localhost')", default="localhost", type=str)
        parser.add_argument("--rpc-port", help="JSON-RPC port (default: `8545')", default=8545, type=int)
        parser.add_argument("--rpc-timeout", help="JSON-RPC timeout (in seconds, default: 60)", type=int, default=60)
        parser.add_argument("--oasis-address", help="Ethereum address of the OasisDEX contract", required=True, type=str)
        parser.add_argument("--sai-address", help="Ethereum address of the SAI token", required=True, type=str)
        parser.add_argument("--weth-address", help="Ethereum address of the WETH token", required=True, type=str)
        parser.add_argument("--market-maker-address", help="Ethereum account of the market maker to analyze", required=True, type=str)
        parser.add_argument("--past-blocks", help="Number of past blocks to analyze", required=True, type=int)

        parser_mode = parser.add_mutually_exclusive_group(required=True)
        parser_mode.add_argument('--text', help="List trades as a text table", dest='text', action='store_true')
        parser_mode.add_argument('--json', help="List trades as a JSON document", dest='json', action='store_true')

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
        take_events = self.otc.past_take(self.arguments.past_blocks)
        trades = oasis_trades(self.market_maker_address, self.sai_address, self.weth_address, take_events)

        if self.arguments.text:
            self.text_trades(trades)
        elif self.arguments.json:
            self.json_trades(trades)
        else:
            raise Exception("Unknown output mode")

    def json_trades(self, trades: List[Trade]):
        assert(isinstance(trades, list))

        def build_item(trade: Trade) -> dict:
            return {
                'datetime': format_timestamp(trade.timestamp),
                'timestamp': trade.timestamp,
                'type': "Sell" if trade.is_sell else "Buy",
                'price': float(trade.price),
                'amount': float(trade.amount),
                'amount_symbol': self.base_token(),
                'money': float(trade.money),
                'money_symbol': self.quote_token(),
                'taker': str(trade.taker)
            }

        print(json.dumps(list(map(build_item, trades)), indent=True))

    def text_trades(self, trades: List[Trade]):
        assert(isinstance(trades, list))

        def table_row(trade: Trade) -> list:
            return [format_timestamp(trade.timestamp),
                    "Sell" if trade.is_sell else "Buy",
                    format(float(trade.price), '.8f'),
                    format(float(trade.amount), '.8f'),
                    format(float(trade.money), '.8f'),
                    str(trade.taker)]

        table = Texttable(max_width=250)
        table.set_deco(Texttable.HEADER)
        table.set_cols_dtype(['t', 't', 't', 't', 't', 't'])
        table.set_cols_align(['l', 'l', 'r', 'r', 'r', 'l'])
        table.add_rows([["Date/time",
                         "Type",
                         "Price",
                         f"Amount in {self.base_token()}",
                         f"Value in {self.quote_token()}",
                         f"Taker"]] + list(map(table_row, trades)))

        print(f"Trade history on the {self.token_pair()} pair:")
        print(f"")
        print(table.draw())
        print(f"")
        print(f"Buy  = Somebody bought {self.quote_token()} from the keeper")
        print(f"Sell = Somebody sold {self.quote_token()} to the keeper")
        print(f"")
        print(f"Number of trades: {len(trades)}")
        print(f"Generated at: {datetime.datetime.now(tz=pytz.UTC).strftime('%Y.%m.%d %H:%M:%S %Z')}")


if __name__ == '__main__':
    OasisMarketMakerTrades(sys.argv[1:]).main()
