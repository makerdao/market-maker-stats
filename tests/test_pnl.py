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

from market_maker_stats.pnl import granularize_prices
from market_maker_stats.util import Price


def test_granularize_prices_fills_gaps():
    # given
    # 1518440700 = 2018-02-12 13:05:00 UTC
    prices = [Price(1518440700, 1.5, 1.4, 1.6, 10),
              Price(1518440760, 1.7, 1.6, 1.8, 14),
              Price(1518440880, 1.2, 1.1, 1.3, 18)]

    # when
    granularized_prices = granularize_prices(prices)

    # then
    print(granularized_prices)
    assert granularized_prices == [Price(1518440700, 1.5, 1.4, 1.6, 10),
                                   Price(1518440760, 1.7, 1.6, 1.8, 14),
                                   Price(1518440820, 0, 0, 0, 0),
                                   Price(1518440880, 1.2, 1.1, 1.3, 18)]
