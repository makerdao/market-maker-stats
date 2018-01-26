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

from web3 import Web3

from market_maker_stats.util import get_event_timestamp
from pymaker import Address
from pymaker.etherdelta import LogTrade
from pymaker.numeric import Wad


class Trade:
    def __init__(self, timestamp: int, price: Wad, amount: Wad, money: Wad, is_buy: bool, is_sell: bool, taker: Address):
        self.timestamp = timestamp
        self.price = price
        self.amount = amount
        self.money = money
        self.is_buy = is_buy
        self.is_sell = is_sell
        self.taker = taker


def etherdelta_trades(infura: Web3, market_maker_address: Address, sai_address: Address, eth_address: Address, past_trades: List[LogTrade]) -> list:
    assert(isinstance(infura, Web3))
    assert(isinstance(market_maker_address, Address))
    assert(isinstance(sai_address, Address))
    assert(isinstance(eth_address, Address))
    assert(isinstance(past_trades, list))

    def sell_trades() -> List[Trade]:
        return list(map(lambda log_trade: Trade(get_event_timestamp(infura, log_trade), log_trade.give_amount / log_trade.take_amount, log_trade.take_amount, log_trade.give_amount, False, True, log_trade.taker),
                    filter(lambda log_trade: log_trade.maker == market_maker_address and log_trade.buy_token == sai_address and log_trade.pay_token == eth_address, past_trades)))

    def buy_trades() -> List[Trade]:
        return list(map(lambda log_trade: Trade(get_event_timestamp(infura, log_trade), log_trade.take_amount / log_trade.give_amount, log_trade.give_amount, log_trade.take_amount, True, False, log_trade.taker),
                    filter(lambda log_trade: log_trade.maker == market_maker_address and log_trade.buy_token == eth_address and log_trade.pay_token == sai_address, past_trades)))

    trades = sell_trades() + buy_trades()
    return sorted(trades, key=lambda trade: trade.timestamp)
