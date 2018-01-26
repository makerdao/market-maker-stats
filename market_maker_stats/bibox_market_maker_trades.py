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

from pyexchange.bibox import BiboxApi, Trade


class BiboxMarketMakerTrades:
    """Tool to list historical trades for the Bibox market maker keeper."""

    def __init__(self, args: list):
        parser = argparse.ArgumentParser(prog='bibox-market-maker-trades')
        parser.add_argument("--bibox-api-server", help="Address of the Bibox API server (default: 'https://api.bibox.com')", default="https://api.bibox.com", type=str)
        parser.add_argument("--bibox-api-key", help="API key for the Bibox API", required=True, type=str)
        parser.add_argument("--bibox-secret", help="Secret for the Bibox API", required=True, type=str)
        parser.add_argument("--bibox-timeout", help="Timeout for accessing the Bibox API", default=9.5, type=float)
        parser.add_argument("--bibox-retry-count", help="Retry count for accessing the Bibox API (default: 20)", default=20, type=int)
        parser.add_argument("--pair", help="Token pair to get the past trades for", required=True, type=str)
        parser.add_argument("--past-trades", help="Number of past trades to fetch and show", required=True, type=int)

        parser_mode = parser.add_mutually_exclusive_group(required=True)
        parser_mode.add_argument('--text', help="List trades as a text table", dest='text', action='store_true')
        parser_mode.add_argument('--json', help="List trades as a JSON document", dest='json', action='store_true')

        self.arguments = parser.parse_args(args)

        self.bibox_api = BiboxApi(api_server=self.arguments.bibox_api_server,
                                  api_key=self.arguments.bibox_api_key,
                                  secret=self.arguments.bibox_secret,
                                  timeout=self.arguments.bibox_timeout)

        logging.basicConfig(format='%(asctime)-15s %(levelname)-8s %(message)s', level=logging.INFO)

    def token_pair(self):
        return self.arguments.pair.replace("_", "/").upper()

    def base_token(self):
        return self.arguments.pair.split('_')[0].upper()

    def quote_token(self):
        return self.arguments.pair.split('_')[1].upper()

    def main(self):
        trades = self.bibox_api.get_trades(pair=self.arguments.pair,
                                           number_of_trades=self.arguments.past_trades,
                                           retry=True,
                                           retry_count=self.arguments.bibox_retry_count)

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
                'datetime': self.format_timestamp(trade.timestamp),
                'timestamp': trade.timestamp,
                'type': "Sell" if trade.is_sell else "Buy",
                'price': float(trade.price),
                'amount': float(trade.amount),
                'amount_symbol': trade.amount_symbol.upper(),
                'money': float(trade.money),
                'money_symbol': trade.money_symbol.upper()
            }

        print(json.dumps(list(map(build_item, trades)), indent=True))

    def text_trades(self, trades: List[Trade]):
        assert(isinstance(trades, list))

        def table_row(trade: Trade) -> list:
            assert(trade.amount_symbol.upper() == self.base_token())
            assert(trade.money_symbol.upper() == self.quote_token())

            return [self.format_timestamp(trade.timestamp),
                    "Sell" if trade.is_sell else "Buy",
                    format(float(trade.price), '.8f'),
                    format(float(trade.amount), '.8f'),
                    format(float(trade.money), '.8f')]

        table = Texttable(max_width=250)
        table.set_deco(Texttable.HEADER)
        table.set_cols_dtype(['t', 't', 't', 't', 't'])
        table.set_cols_align(['l', 'l', 'r', 'r', 'r'])
        table.add_rows([["Date/time",
                         "Type",
                         "Price",
                         f"Amount in {self.base_token()}",
                         f"Value in {self.quote_token()}"]] + list(map(table_row, trades)))

        print(f"Trade history on the {self.token_pair()} pair:")
        print(f"")
        print(table.draw())
        print(f"")
        print(f"Buy  = Somebody bought {self.quote_token()} from the keeper")
        print(f"Sell = Somebody sold {self.quote_token()} to the keeper")
        print(f"")
        print(f"Number of trades: {len(trades)}")
        print(f"Generated at: {datetime.datetime.now(tz=pytz.UTC).strftime('%Y.%m.%d %H:%M:%S %Z')}")

    @staticmethod
    def format_timestamp(timestamp: int):
        assert(isinstance(timestamp, int))
        return datetime.datetime.fromtimestamp(timestamp, pytz.UTC).strftime('%Y-%m-%d %H:%M:%S %Z')


if __name__ == '__main__':
    BiboxMarketMakerTrades(sys.argv[1:]).main()
