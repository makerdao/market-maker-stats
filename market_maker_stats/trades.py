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
from typing import Optional

import pytz
from texttable import Texttable


def json_trades(trades: list, output: Optional[str], include_taker: bool = False):
    assert(isinstance(trades, list))
    assert(isinstance(include_taker, bool))

    def build_item(trade) -> dict:
        item = {
            'exchange': trade.exchange,
            'pair': trade.pair,
            'datetime': format_timestamp(trade.timestamp),
            'timestamp': trade.timestamp,
            'type': "Sell" if trade.is_sell is True else "Buy" if trade.is_sell is False else "n/a",
            'price': float(trade.price),
            'amount': float(trade.amount),
            'money': float(trade.money)
        }

        if trade.maker is not None:
            item['maker'] = str(trade.maker)

        if include_taker:
            item['taker'] = str(trade.taker)

        return item

    result = json.dumps(list(map(build_item, trades)), indent=True)

    if output is not None:
        with open(output, "w") as file:
            file.write(result)

    else:
        print(result)


def text_trades(buy_token, sell_token, trades, output: Optional[str], include_taker: bool = False):
    assert(isinstance(buy_token, str) or (buy_token is None))
    assert(isinstance(sell_token, str) or (sell_token is None))
    assert(isinstance(trades, list))
    assert(isinstance(include_taker, bool))

    def amount_symbol(trade):
        return trade.pair.split("-")[0]

    def money_symbol(trade):
        return trade.pair.split("-")[1]

    def table_row(trade) -> list:
        return [format_timestamp(trade.timestamp),
                trade.exchange,
                trade.maker if trade.maker is not None else "n/a",
                trade.pair,
                "Sell" if trade.is_sell is True else "Buy" if trade.is_sell is False else "n/a",
                format(float(trade.price), '.8f'),
                ' '*5 + format(float(trade.amount), '.8f') + ' ' + amount_symbol(trade),
                ' '*3 + format(float(trade.money), '.8f') + ' ' + money_symbol(trade)] + ([str(trade.taker)] if include_taker else [])

    table = Texttable(max_width=250)
    table.set_deco(Texttable.HEADER)
    table.set_cols_dtype(['t', 't', 't', 't', 't', 't', 't', 't'] + (['t'] if include_taker else []))
    table.set_cols_align(['l', 'l', 'l', 'l', 'l', 'r', 'r', 'r'] + (['l'] if include_taker else []))
    table.add_rows([["Date/time",
                     "Exchange",
                     "Maker",
                     "Pair",
                     "Type",
                     "Price",
                     f"Amount",
                     f"Value"] + (["Taker"] if include_taker else [])] + list(map(table_row, trades)))

    result = table.draw() + "\n\n" + \
             f"Number of trades: {len(trades)}" + "\n" + \
             f"Generated at: {datetime.datetime.now(tz=pytz.UTC).strftime('%Y.%m.%d %H:%M:%S %Z')}"

    if output is not None:
        with open(output, "w") as file:
            file.write(result)

    else:
        print(result)


def format_timestamp(timestamp: int):
    assert(isinstance(timestamp, int))
    return datetime.datetime.fromtimestamp(timestamp, pytz.UTC).strftime('%Y-%m-%d %H:%M:%S %Z')
