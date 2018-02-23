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

import json
import datetime

import pytz
from texttable import Texttable


def json_trades(trades: list):
    assert(isinstance(trades, list))

    def build_item(trade) -> dict:
        return {
            'datetime': format_timestamp(trade.timestamp),
            'timestamp': trade.timestamp,
            'type': "Sell" if trade.is_sell else "Buy",
            'price': float(trade.price),
            'amount': float(trade.amount),
            'money': float(trade.money)
        }

    print(json.dumps(list(map(build_item, trades)), indent=True))


def text_trades(pair, base_token, quote_token, trades):
    assert(isinstance(trades, list))

    def table_row(trade) -> list:
        return [format_timestamp(trade.timestamp),
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
                     f"Amount in {base_token}",
                     f"Value in {quote_token}"]] + list(map(table_row, trades)))

    print(f"Trade history on the {pair} pair:")
    print(f"")
    print(table.draw())
    print(f"")
    print(f"Buy  = Somebody bought {quote_token} from the keeper")
    print(f"Sell = Somebody sold {quote_token} to the keeper")
    print(f"")
    print(f"Number of trades: {len(trades)}")
    print(f"Generated at: {datetime.datetime.now(tz=pytz.UTC).strftime('%Y.%m.%d %H:%M:%S %Z')}")


def format_timestamp(timestamp: int):
    assert(isinstance(timestamp, int))
    return datetime.datetime.fromtimestamp(timestamp, pytz.UTC).strftime('%Y-%m-%d %H:%M:%S %Z')
