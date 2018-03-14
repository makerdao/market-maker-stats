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

from typing import List

from market_maker_stats.model import AllTrade
from pymaker import Address
from pymaker.numeric import Wad
from pymaker.oasis import LogTake


class Trade:
    def __init__(self, timestamp: int, price: Wad, amount: Wad, money: Wad, is_sell: bool, taker: Address):
        self.timestamp = timestamp
        self.price = price
        self.amount = amount
        self.money = money
        self.is_sell = is_sell
        self.taker = taker


def our_oasis_trades(market_maker_address: Address, buy_token_address: Address, sell_token_address: Address, past_takes: List[LogTake]) -> list:
    assert(isinstance(market_maker_address, Address))
    assert(isinstance(buy_token_address, Address))
    assert(isinstance(sell_token_address, Address))
    assert(isinstance(past_takes, list))

    def sell_trades() -> List[Trade]:
        regular = map(lambda log_take: Trade(log_take.timestamp, log_take.give_amount / log_take.take_amount, log_take.take_amount, log_take.give_amount, True, log_take.taker),
                      filter(lambda log_take: log_take.maker == market_maker_address and log_take.buy_token == buy_token_address and log_take.pay_token == sell_token_address, past_takes))
        matched = map(lambda log_take: Trade(log_take.timestamp, log_take.take_amount / log_take.give_amount, log_take.give_amount, log_take.take_amount, True, log_take.maker),
                      filter(lambda log_take: log_take.taker == market_maker_address and log_take.buy_token == sell_token_address and log_take.pay_token == buy_token_address, past_takes))
        return list(regular) + list(matched)

    def buy_trades() -> List[Trade]:
        regular = map(lambda log_take: Trade(log_take.timestamp, log_take.take_amount / log_take.give_amount, log_take.give_amount, log_take.take_amount, False, log_take.taker),
                      filter(lambda log_take: log_take.maker == market_maker_address and log_take.buy_token == sell_token_address and log_take.pay_token == buy_token_address, past_takes))
        matched = map(lambda log_take: Trade(log_take.timestamp, log_take.give_amount / log_take.take_amount, log_take.take_amount, log_take.give_amount, False, log_take.maker),
                      filter(lambda log_take: log_take.taker == market_maker_address and log_take.buy_token == buy_token_address and log_take.pay_token == sell_token_address, past_takes))
        return list(regular) + list(matched)

    trades = sell_trades() + buy_trades()
    return sorted(trades, key=lambda trade: trade.timestamp)


def all_oasis_trades(buy_token_address: Address, sell_token_address: Address, past_takes: List[LogTake]) -> List[AllTrade]:
    assert(isinstance(buy_token_address, Address))
    assert(isinstance(sell_token_address, Address))
    assert(isinstance(past_takes, list))

    regular = map(lambda log_take: AllTrade('-', float(log_take.timestamp), log_take.take_amount, log_take.give_amount / log_take.take_amount),
                  filter(lambda log_take: log_take.buy_token == buy_token_address and log_take.pay_token == sell_token_address, past_takes))

    matched = map(lambda log_take: AllTrade('-', float(log_take.timestamp), log_take.give_amount, log_take.take_amount / log_take.give_amount),
                  filter(lambda log_take: log_take.buy_token == sell_token_address and log_take.pay_token == buy_token_address, past_takes))

    return sorted(list(regular) + list(matched), key=lambda trade: trade.timestamp)
