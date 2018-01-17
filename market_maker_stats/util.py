# This file is part of Maker Keeper Framework.
#
# Copyright (C) 2017 reverendus
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
import pytz
import requests
import time
import numpy as np

from pymaker.numeric import Wad

SIZE_MIN = 30
SIZE_MAX = 100
SIZE_PRICE_MAX = 5000

class Price:
    def __init__(self, timestamp: int, market_price: Wad, market_price_min: Wad, market_price_max: Wad, volume: Wad):
        self.timestamp = timestamp
        self.market_price = market_price
        self.market_price_min = market_price_min
        self.market_price_max = market_price_max
        self.volume = volume

def amount_in_sai_to_size(amount_in_sai):
    return max(min(float(amount_in_sai) / float(SIZE_PRICE_MAX) * SIZE_MAX, SIZE_MAX), SIZE_MIN)

def get_gdax_prices(start_timestamp: int, end_timestamp: int):
    prices = []
    timestamp = start_timestamp
    while timestamp <= end_timestamp:
        timestamp_range_start = timestamp
        timestamp_range_end = int((datetime.datetime.fromtimestamp(timestamp) + datetime.timedelta(hours=3)).timestamp())
        prices = prices + list(filter(lambda state: state.timestamp >= start_timestamp and state.timestamp <= end_timestamp,
                                      get_gdax_partial(timestamp_range_start, timestamp_range_end)))
        timestamp = timestamp_range_end

    return sorted(prices, key=lambda price: price.timestamp)

def get_gdax_partial(timestamp_range_start: int, timestamp_range_end: int):
    start = datetime.datetime.fromtimestamp(timestamp_range_start, pytz.UTC)
    end = datetime.datetime.fromtimestamp(timestamp_range_end, pytz.UTC)

    url = f"https://api.gdax.com/products/ETH-USD/candles?" \
          f"start={iso_8601(start)}&" \
          f"end={iso_8601(end)}&" \
          f"granularity=60"

    #print(f"Downloading: {url}")

    # data is: [[ time, low, high, open, close, volume ], [...]]
    try:
        data = requests.get(url).json()
    except:
        print("GDAX API network error, waiting 10 secs...")
        time.sleep(10)
        return get_gdax_partial(timestamp_range_start, timestamp_range_end)

    if 'message' in data:
        print("GDAX API rate limiting, slowing down for 2 secs...")
        time.sleep(2)
        return get_gdax_partial(timestamp_range_start, timestamp_range_end)
    else:
        return list(map(lambda array: Price(timestamp=array[0],
                                            market_price=(array[1]+array[2])/2,
                                            market_price_min=array[1],
                                            market_price_max=array[2],
                                            volume=array[5]), data))

def iso_8601(tm) -> str:
    return tm.isoformat().replace('+00:00', 'Z')

def rolling_window(a, window):
    shape = a.shape[:-1] + (a.shape[-1] - window + 1, window)
    strides = a.strides + (a.strides[-1],)
    return np.lib.stride_tricks.as_strided(a, shape=shape, strides=strides)

def get_approx_vwaps(start_timestamp_ int, end_timestamp: int, vwap_minutes: int):
    # approximates historical vwap_minutes VWAPs from GDAX by querying historical at minimal
    # (60 second) granularity, using (low+high)/2 as price for each bucket, then weighting by volume
    # traded in each bucket. Might not be that accurate, consider applying smoothing on top of this
    granular_prices = get_gdax_prices(start_timestamp, end_timestamp)
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

def parse_trades_json(trades_json: list):
    trades_json = sorted(trades_json, key=lambda trade: trade['timestamp'])
    # assumes the pair is ETH/DAI, so buying is +ETH -DAI
    # trades is a 2-column array where each row is (delta_ETH, delta_DAI)
    trades = np.array([(to_direction(trade['type'] == 'Buy')*trade['amountETH'], to_direction(trade['type'] == 'Sell')*trade['amountDAI']) for trade in trades_json])
    prices = np.array([trade['price'] for trade in trades_json])
    timestamps = np.array([trade['timestamp'] for trade in trades_json])
    
    return trades, prices, timestamps

def calculate_pnl_vwap(trades, prices, timestamps, vwap_minutes=60):
    # first 3 arguments are output of parse_trades_json
    vwaps = get_approx_vwaps(timestamps[0], timestamps[-1], vwap_minutes)
    # put timestamps into (forward-looking) minute buckets starting at 0
    # this means we must exclude trades from the last vwap_minutes minutes
    rel_minutes = np.ceil((timestamps - timestamps[0])/60).astype('int')
    where_overshoot = np.where(rel_minutes >= len(vwaps))[0]
    if where_overshoot.size == 0:
        end = len(rel_minutes)
    else:
        end = where_overshoot[0]
    
    trade_market_vwaps = vwaps[rel_minutes[:end]]
    profits = (trade_market_vwaps - prices[:end])*trades[:, 0][:end]

    # profits for each trade in period from timestamps[0] to timestamps[end_row-1]
    # use np.sum(profits) to get total PnL over period
    # and np.cumsum(profits) to get cumulative PnLs over period, for plotting
    return profits
