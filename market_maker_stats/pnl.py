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

import datetime
from itertools import groupby

import numpy as np
import pytz
from texttable import Texttable
from typing import List, Optional

from market_maker_stats.util import get_day, sum_wads, Price, timestamp_to_x
from pymaker import Wad


def rolling_window(a, window):
    shape = a.shape[:-1] + (a.shape[-1] - window + 1, window)
    strides = a.strides + (a.strides[-1],)
    return np.lib.stride_tricks.as_strided(a, shape=shape, strides=strides)


# prices can have gaps, but for PnL calculation we need minute-by-minute data, that's why we fill the gaps.
# zero price and zero volume is fine, this way it won't count towards vwap as we don't know what was there anyway
# in case there is more than one sample per minute, we only leave the first one
def granularize_prices(prices: list) -> list:
    def get_minute(ts):
        return int(ts/60)

    granular_prices = []
    last_timestamp = -1
    for price in prices:
        if last_timestamp != -1:
            minute_increment = get_minute(price.timestamp) - get_minute(last_timestamp)
            for i in range(0, minute_increment-1):
                granular_prices.append(Price(last_timestamp + 60*(i+1), 0.0, 0.0, 0.0, 0.0))

            if minute_increment > 0:
                granular_prices.append(price)

        else:
            granular_prices.append(price)

        last_timestamp = price.timestamp

    return granular_prices


def get_approx_vwaps(prices: list, vwap_minutes: int):
    granular_prices = granularize_prices(prices)

    # approximates historical vwap_minutes VWAPs from GDAX by querying historical at minimal
    # (60 second) granularity, using (low+high)/2 as price for each bucket, then weighting by volume
    # traded in each bucket. Might not be that accurate, consider applying smoothing on top of this
    granular_prices_avg = np.array(list(map(lambda price: price.price, granular_prices)))
    granular_volumes = np.array(list(map(lambda price: price.volume, granular_prices)))

    rolling_volumes = rolling_window(granular_volumes, vwap_minutes)
    rolling_prices = rolling_window(granular_prices_avg, vwap_minutes)
    weighted_prices = rolling_prices * rolling_volumes

    vwaps = np.sum(weighted_prices, axis=1) / np.sum(rolling_volumes, axis=1)

    return vwaps


def to_direction(x):
    if x:
        return 1.
    else:
        return -1.


def prepare_trades_for_pnl(trades: list):
    trades = sorted(trades, key=lambda trade: trade.timestamp)

    # assumes the pair is ETH/DAI or BTC/DAI, so buying is +ETH_or_BTC -DAI
    # trades is a 2-column array where each row is (delta_ETH_or_BTC, delta_DAI)
    deals = np.array([(to_direction(not trade.is_sell)*float(trade.amount), to_direction(trade.is_sell)*float(trade.money)) for trade in trades])
    prices = np.array([float(trade.price) for trade in trades])
    timestamps = np.array([trade.timestamp for trade in trades])

    return deals, prices, timestamps


def calculate_pnl(pnl_trades, pnl_prices, pnl_timestamps, vwaps, vwaps_start):
    if len(pnl_trades) == 0:
        return np.array([])

    # first 3 arguments are output of parse_trades_json
    # put timestamps into (forward-looking) minute buckets starting at 0
    # this means we must exclude trades from the last vwap_minutes minutes
    rel_minutes = np.ceil((pnl_timestamps - vwaps_start) / 60).astype('int')
    where_overshoot = np.where(rel_minutes >= len(vwaps))[0]
    if where_overshoot.size == 0:
        end = len(rel_minutes)
    else:
        end = where_overshoot[0]

    trade_market_vwaps = vwaps[rel_minutes[:end]]
    profits = (trade_market_vwaps - pnl_prices[:end]) * pnl_trades[:, 0][:end]

    # profits for each trade in period from timestamps[0] to timestamps[end_row-1]
    # use np.sum(profits) to get total PnL over period
    # and np.cumsum(profits) to get cumulative PnLs over period, for plotting
    return profits


def pnl_text(trades: list, vwaps: list, vwaps_start: int, buy_token: str, sell_token: str, vwap_minutes: int, output: Optional[str]):
    if buy_token.upper() in ['DAI', 'USD', 'USDT']:
        amount_format = "{:,.2f} " + buy_token.upper()
    else:
        amount_format = "{:,.4f} " + buy_token.upper()

    data = []
    total_volume = Wad(0)
    total_net = Wad(0)
    total_profit = 0
    for day, day_trades in groupby(trades, lambda trade: get_day(trade.timestamp)):
        day_trades = list(day_trades)

        if vwaps_start != -1:
            pnl_trades, pnl_prices, pnl_timestamps = prepare_trades_for_pnl(day_trades)
            pnl_profits = calculate_pnl(pnl_trades, pnl_prices, pnl_timestamps, vwaps, vwaps_start)

            # 'pnl_profits' will contain NaN for these trades where missing price information
            # made profit calculation impossible. we count number of these in `missing_profits`
            pnl_profits_len_before = len(pnl_profits)
            pnl_profits = pnl_profits[~np.isnan(pnl_profits)]
            missing_profits = len(pnl_profits) != pnl_profits_len_before
            calculated_profits = True

        else:
            pnl_profits = np.array([])
            missing_profits = False
            calculated_profits = False

        day_volume = sum_wads(map(lambda trade: trade.money, day_trades))
        day_bought = sum_wads(map(lambda trade: trade.money, filter(lambda trade: trade.is_sell, day_trades)))
        day_sold = sum_wads(map(lambda trade: trade.money, filter(lambda trade: not trade.is_sell, day_trades)))
        day_net = day_bought - day_sold
        day_profit = np.sum(pnl_profits)

        total_volume += day_volume
        total_net += day_net
        total_profit += day_profit

        data.append([day.strftime('%Y-%m-%d'),
                     len(day_trades),
                     amount_format.format(float(day_volume)),
                     amount_format.format(float(day_bought)),
                     amount_format.format(float(day_sold)),
                     amount_format.format(float(day_net)),
                     amount_format.format(float(total_net)),
                     amount_format.format(day_profit) if calculated_profits else "n/a",
                     "*" if missing_profits else ""])

    table = Texttable(max_width=250)
    table.set_deco(Texttable.HEADER)
    table.set_cols_dtype(['t', 't', 't', 't', 't', 't', 't', 't', 't'])
    table.set_cols_align(['l', 'r', 'r', 'r', 'r', 'r', 'r', 'r', 'l'])
    table.set_cols_width([11, 9, 18, 22, 18, 26, 20, 25, 10])
    table.add_rows([["Day", "# trades", "Volume", "Bought", "Sold", "Net bought", "Cumulative net bought", "Profit", "Remarks"]] + data)

    result = f"PnL report for {sell_token}/{buy_token} market-making:" + "\n" + \
             f"" + "\n" + \
             table.draw() + "\n" + \
             f"" + "\n" + \
             f"The first and the last day of the report may not contain all trades." + "\n"

    if vwaps_start != -1:
        result = result + \
                 f"The last window of {vwap_minutes} minutes of trades is excluded from profit calculation." + "\n" + \
                 f"" + "\n" + \
                 f"Remarks:" + "\n" + \
                 f"*) Profit calculation for that day incomplete due to missing price information." + "\n"

    result = result + \
             f"" + "\n" + \
             f"Total number of trades: {len(trades)}" + "\n" + \
             f"Total volume: " + amount_format.format(float(total_volume)) + "\n"

    if vwaps_start != -1:
        result = result + \
               f"Total profit: " + amount_format.format(total_profit) + "\n"

    result = result + \
             f"" + "\n" + \
             f"Generated at: {datetime.datetime.now(tz=pytz.UTC).strftime('%Y.%m.%d %H:%M:%S %Z')}"

    if output is not None:
        with open(output, "w") as file:
            file.write(result)

    else:
        print(result)


def pnl_chart(start_timestamp: int, end_timestamp: int, prices: List[Price], trades: list, vwaps: list, vwaps_start: int, buy_token: str, sell_token: str, output: Optional[str]):
    import matplotlib.dates as md
    import matplotlib.pyplot as plt

    pnl_trades, pnl_prices, pnl_timestamps = prepare_trades_for_pnl(trades)
    pnl_profits = calculate_pnl(pnl_trades, pnl_prices, pnl_timestamps, vwaps, vwaps_start)
    pnl_profits = pnl_profits[~np.isnan(pnl_profits)]

    fig, ax = plt.subplots()
    ax.set_xlim(left=timestamp_to_x(start_timestamp), right=timestamp_to_x(end_timestamp))
    ax.xaxis.set_major_formatter(md.DateFormatter('%d-%b %H:%M', tz=pytz.UTC))
    plt.subplots_adjust(bottom=0.2)
    plt.xticks(rotation=25)
    ax2 = ax.twinx()

    ax.set_zorder(ax2.get_zorder()+1)
    ax.patch.set_visible(False)

    dt_timestamps = [datetime.datetime.fromtimestamp(timestamp) for timestamp in pnl_timestamps]
    ax.plot(dt_timestamps[:len(pnl_profits)], np.cumsum(pnl_profits), color='green')

    ax2.plot(list(map(lambda price: timestamp_to_x(price.timestamp), prices)),
             list(map(lambda price: price.price, prices)), color='red')

    ax.set_ylabel(f"Cumulative PnL ({buy_token})")
    ax2.set_ylabel(f"{sell_token} price in {buy_token}")
    plt.title("Profit: {:,.2f} {}".format(np.sum(pnl_profits), buy_token))

    if output:
        plt.savefig(fname=output, dpi=300, bbox_inches='tight', pad_inches=0)
    else:
        plt.show()
