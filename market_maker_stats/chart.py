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

from typing import List, Optional

from market_maker_stats.util import Price, amount_to_size, timestamp_to_x, amount_in_usd_to_size


def initialize_charting(output: Optional[str]):
    if output:
        import matplotlib
        matplotlib.use('Agg')


def draw_chart(start_timestamp: int,
               end_timestamp: int,
               prices: List[Price],
               alternative_prices: List[Price],
               trades: list,
               output: Optional[str]):
    import matplotlib.dates as md
    import matplotlib.pyplot as plt

    def to_timestamp(price_or_trade):
        return timestamp_to_x(price_or_trade.timestamp)

    def to_price(trade):
        return trade.price

    def to_size(trade):
        try :
            return amount_to_size(trade.money_symbol, trade.money)
        except:
            return amount_in_usd_to_size(trade.money)

    plt.subplots_adjust(bottom=0.2)
    plt.xticks(rotation=25)
    ax=plt.gca()
    ax.set_xlim(left=timestamp_to_x(start_timestamp), right=timestamp_to_x(end_timestamp))
    ax.xaxis.set_major_formatter(md.DateFormatter('%Y-%m-%d %H:%M:%S'))

    if len(prices) > 0:
        timestamps = list(map(to_timestamp, prices))
        market_prices = list(map(lambda price: price.market_price, prices))
        plt.plot_date(timestamps, market_prices, 'r-', zorder=2)

    if len(alternative_prices) > 0:
        timestamps = list(map(to_timestamp, alternative_prices))
        market_prices = list(map(lambda price: price.market_price, alternative_prices))
        plt.plot_date(timestamps, market_prices, 'y-', zorder=1)

    if False:
        market_prices_min = list(map(lambda price: price.market_price_min, prices))
        market_prices_max = list(map(lambda price: price.market_price_max, prices))
        plt.plot_date(timestamps, market_prices_min, 'y-', zorder=1)
        plt.plot_date(timestamps, market_prices_max, 'y-', zorder=1)

    sell_trades = list(filter(lambda trade: trade.is_sell, trades))
    sell_x = list(map(to_timestamp, sell_trades))
    sell_y = list(map(to_price, sell_trades))
    sell_s = list(map(to_size, sell_trades))
    plt.scatter(x=sell_x, y=sell_y, s=sell_s, c='blue', zorder=3)

    buy_trades = list(filter(lambda trade: not trade.is_sell, trades))
    buy_x = list(map(to_timestamp, buy_trades))
    buy_y = list(map(to_price, buy_trades))
    buy_s = list(map(to_size, buy_trades))
    plt.scatter(x=buy_x, y=buy_y, s=buy_s, c='green', zorder=3)

    if output:
        plt.savefig(fname=output, dpi=300, bbox_inches='tight', pad_inches=0)
    else:
        plt.show()
