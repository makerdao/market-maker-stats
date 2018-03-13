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
    prices = [Price(1518440700, 1.5, 10),
              Price(1518440760, 1.7, 14),
              Price(1518440880, 1.2, 18)]

    # when
    granularized_prices = granularize_prices(prices)

    # then
    assert granularized_prices == [Price(1518440700, 1.5, 10),
                                   Price(1518440760, 1.7, 14),
                                   Price(1518440820, 0, 0),
                                   Price(1518440880, 1.2, 18)]



def test_granularize_prices_fills_gaps_even_if_seconds_are_uneven():
    # given
    # 1518440700 = 2018-02-12 13:05:00 UTC
    prices = [Price(1518440759, 1.5, 10),
              Price(1518440760, 1.7, 14),
              Price(1518440851, 1.2, 18)]

    # when
    granularized_prices = granularize_prices(prices)

    # then
    assert granularized_prices == [Price(1518440759, 1.5, 10),
                                   Price(1518440760, 1.7, 14),
                                   Price(1518440851, 1.2, 18)]


def test_granularize_prices_removes_duplicates():
    # given
    # 1518440700 = 2018-02-12 13:05:00 UTC
    prices = [Price(1518440700, 1.5, 10),
              Price(1518440730, 1.51, 11),
              Price(1518440740, 1.52, 12),
              Price(1518440759, 1.53, 13),
              Price(1518440760, 1.7, 14),
              Price(1518440885, 1.2, 18),
              Price(1518440910, 1.1, 29),]

    # when
    granularized_prices = granularize_prices(prices)

    # then
    assert granularized_prices == [Price(1518440700, 1.5, 10),
                                   Price(1518440760, 1.7, 14),
                                   Price(1518440820, 0, 0),
                                   Price(1518440885, 1.2, 18)]
