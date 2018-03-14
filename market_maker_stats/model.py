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

from pymaker import Wad


class AllTrade:
    def __init__(self, pair: str, timestamp: float, amount: Wad, price: Wad):
        assert(isinstance(pair, str))
        assert(isinstance(timestamp, float))
        assert(isinstance(amount, Wad))
        assert(isinstance(price, Wad))

        self.timestamp = timestamp
        self.amount = amount
        self.amount_symbol = pair.split("-")[0]
        self.price = price
        self.money_symbol = pair.split("-")[1]

    @property
    def money(self) -> Wad:
        return self.amount * self.price
