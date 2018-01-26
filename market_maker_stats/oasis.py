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

from pymaker import Address
from pymaker.numeric import Wad
from pymaker.oasis import LogTake


class Trade:
    def __init__(self, timestamp: int, price: Wad, value_in_sai: Wad, is_buy: bool, is_sell: bool):
        self.timestamp = timestamp
        self.price = price
        self.value_in_sai = value_in_sai
        self.is_buy = is_buy
        self.is_sell = is_sell


def oasis_trades(market_maker_address: Address, sai_address: Address, weth_address: Address, past_takes: List[LogTake]):
    assert(isinstance(market_maker_address, Address))
    assert(isinstance(sai_address, Address))
    assert(isinstance(weth_address, Address))
    assert(isinstance(past_takes, list))

    def sell_trades() -> List[Trade]:
        regular = map(lambda log_take: Trade(log_take.timestamp, log_take.give_amount / log_take.take_amount, log_take.give_amount, False, True),
                      filter(lambda log_take: log_take.maker == market_maker_address and log_take.buy_token == sai_address and log_take.pay_token == weth_address, past_takes))
        matched = map(lambda log_take: Trade(log_take.timestamp, log_take.take_amount / log_take.give_amount, log_take.take_amount, False, True),
                      filter(lambda log_take: log_take.taker == market_maker_address and log_take.buy_token == weth_address and log_take.pay_token == sai_address, past_takes))
        return list(regular) + list(matched)

    def buy_trades() -> List[Trade]:
        regular = map(lambda log_take: Trade(log_take.timestamp, log_take.take_amount / log_take.give_amount, log_take.take_amount, True, False),
                      filter(lambda log_take: log_take.maker == market_maker_address and log_take.buy_token == weth_address and log_take.pay_token == sai_address, past_takes))
        matched = map(lambda log_take: Trade(log_take.timestamp, log_take.give_amount / log_take.take_amount, log_take.give_amount, True, False),
                      filter(lambda log_take: log_take.taker == market_maker_address and log_take.buy_token == sai_address and log_take.pay_token == weth_address, past_takes))
        return list(regular) + list(matched)

    return sell_trades() + buy_trades()
