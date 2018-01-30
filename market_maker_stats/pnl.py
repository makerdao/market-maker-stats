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

import numpy as np


def rolling_window(a, window):
    shape = a.shape[:-1] + (a.shape[-1] - window + 1, window)
    strides = a.strides + (a.strides[-1],)
    return np.lib.stride_tricks.as_strided(a, shape=shape, strides=strides)


def get_approx_vwaps(granular_prices: list, vwap_minutes: int):
    # approximates historical vwap_minutes VWAPs from GDAX by querying historical at minimal
    # (60 second) granularity, using (low+high)/2 as price for each bucket, then weighting by volume
    # traded in each bucket. Might not be that accurate, consider applying smoothing on top of this
    granular_prices_avg = np.array(list(map(lambda price: price.market_price, granular_prices)))
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

    # assumes the pair is ETH/DAI, so buying is +ETH -DAI
    # trades is a 2-column array where each row is (delta_ETH, delta_DAI)
    deals = np.array([(to_direction(not trade.is_sell)*float(trade.amount), to_direction(trade.is_sell)*float(trade.money)) for trade in trades])
    prices = np.array([float(trade.price) for trade in trades])
    timestamps = np.array([trade.timestamp for trade in trades])

    return deals, prices, timestamps


def calculate_pnl(pnl_trades, pnl_prices, pnl_timestamps, vwaps, vwaps_start):
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
