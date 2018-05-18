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

import pytz

from market_maker_stats.util import Price, amount_to_size, timestamp_to_x, amount_in_usd_to_size, OrderHistoryItem


def initialize_charting(output: Optional[str]):
    if output:
        import matplotlib
        matplotlib.use('Agg')


# If there is a gap in the price feed history, pyplot by default links it with a straight like.
# In order to avoid it, we add an empty price # between all values which are at least `price_gap_size` minutes apart.
# This way a nice visual gap will be seen in the chart as well.
def prepare_prices_for_charting(prices: List[Price], price_gap_size: int) -> List[Price]:
    if len(prices) == 0:
        return prices

    result = [prices[0]]
    for i in range(1, len(prices)):
        if prices[i].timestamp - prices[i-1].timestamp > price_gap_size:
            result.append(Price(prices[i-1].timestamp + 1, None, None, None, None))

        result.append(prices[i])

    return result


# Same for order history actually.
def prepare_order_history_for_charting(items: List[OrderHistoryItem]) -> List[OrderHistoryItem]:
    if len(items) == 0:
        return items

    result = [items[0]]
    for i in range(1, len(items)):
        if items[i].timestamp - items[i - 1].timestamp > 180:
            result.append(OrderHistoryItem(items[i - 1].timestamp + 1, []))

        result.append(items[i])

    return result


def draw_chart(start_timestamp: int,
               end_timestamp: int,
               prices: List[Price],
               alternative_prices: List[Price],
               price_gap_size: int,
               order_history: list,
               our_trades: list,
               all_trades: list,
               output: Optional[str]):
    import matplotlib.dates as md
    import matplotlib.pyplot as plt

    plt.subplots_adjust(bottom=0.2)
    plt.xticks(rotation=25)
    ax=plt.gca()
    ax.set_xlim(left=timestamp_to_x(start_timestamp), right=timestamp_to_x(end_timestamp))
    ax.xaxis.set_major_formatter(md.DateFormatter('%d-%b %H:%M', tz=pytz.UTC))

    timestamps = list(map(timestamp_to_x, map(lambda item: item.timestamp, order_history)))
    closest_sell_prices = list(map(lambda item: item.closest_sell_price(), order_history))
    closest_buy_prices = list(map(lambda item: item.closest_buy_price(), order_history))

    plt.plot_date(timestamps, closest_sell_prices, 'b-', zorder=2, linewidth=1)
    plt.plot_date(timestamps, closest_buy_prices, 'g-', zorder=2, linewidth=1)

    draw_prices(prices, alternative_prices, price_gap_size)
    draw_trades(our_trades, all_trades)

    if output:
        plt.savefig(fname=output, dpi=300, bbox_inches='tight', pad_inches=0)
    else:
        plt.show()


def draw_prices(prices, alternative_prices, price_gap_size):
    import matplotlib.pyplot as plt

    if len(prices) > 0:
        prices = prepare_prices_for_charting(prices, price_gap_size)
        timestamps = list(map(lambda price: timestamp_to_x(price.timestamp), prices))
        buy_prices = list(map(lambda price: price.buy_price if price.buy_price is not None else price.price, prices))
        sell_prices = list(map(lambda price: price.sell_price if price.sell_price is not None else price.price, prices))

        plt.plot_date(timestamps, buy_prices, 'c-', zorder=2)
        plt.plot_date(timestamps, sell_prices, 'r-', zorder=2)

    if len(alternative_prices) > 0:
        alternative_prices = prepare_prices_for_charting(alternative_prices, price_gap_size)
        timestamps = list(map(lambda price: timestamp_to_x(price.timestamp), alternative_prices))
        buy_prices = list(map(lambda price: price.buy_price if price.buy_price is not None else price.price, alternative_prices))
        sell_prices = list(map(lambda price: price.sell_price if price.sell_price is not None else price.price, alternative_prices))

        plt.plot_date(timestamps, buy_prices, 'y-', zorder=1)
        plt.plot_date(timestamps, sell_prices, 'y-', zorder=1)


def draw_trades(our_trades, all_trades):
    import matplotlib.pyplot as plt

    def to_timestamp(price_or_trade):
        return timestamp_to_x(price_or_trade.timestamp)

    def to_price(trade):
        return trade.price

    def to_size(trade):
        try:
            return amount_to_size(trade.money_symbol, trade.money)
        except:
            return amount_in_usd_to_size(trade.money)

    sell_trades = list(filter(lambda trade: trade.is_sell is True, our_trades))
    sell_x = list(map(to_timestamp, sell_trades))
    sell_y = list(map(to_price, sell_trades))
    sell_s = list(map(to_size, sell_trades))
    plt.scatter(x=sell_x, y=sell_y, s=sell_s, c='blue', zorder=4)

    buy_trades = list(filter(lambda trade: trade.is_sell is False, our_trades))
    buy_x = list(map(to_timestamp, buy_trades))
    buy_y = list(map(to_price, buy_trades))
    buy_s = list(map(to_size, buy_trades))
    plt.scatter(x=buy_x, y=buy_y, s=buy_s, c='green', zorder=4)

    all_x = list(map(to_timestamp, all_trades))
    all_y = list(map(to_price, all_trades))
    all_s = list(map(to_size, all_trades))
    plt.scatter(x=all_x, y=all_y, s=all_s, c='#ff00e5', zorder=3)
