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
from typing import Optional

from pymaker import Wad


class AllTrade:
    def __init__(self, pair: str, timestamp: int, is_sell: Optional[bool], amount: Wad, price: Wad):
        assert(isinstance(pair, str))
        assert(isinstance(is_sell, bool) or (is_sell is None))
        assert(isinstance(timestamp, int))
        assert(isinstance(amount, Wad))
        assert(isinstance(price, Wad))

        self.timestamp = timestamp
        self.is_sell = is_sell
        self.amount = amount
        self.amount_symbol = pair.split("-")[0]
        self.price = price
        self.money = amount * price
        self.money_symbol = pair.split("-")[1]
