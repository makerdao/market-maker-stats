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
import json
import logging

import errno

import filelock
import pytz
import requests
import os
import time
import numpy as np
from typing import List

from appdirs import user_cache_dir
from web3 import Web3

from pymaker.numeric import Wad

SIZE_MIN = 5
SIZE_MAX = 100
SIZE_PRICE_MAX = 30000


class Price:
    def __init__(self, timestamp: int, market_price: Wad, market_price_min: Wad, market_price_max: Wad, volume: Wad):
        self.timestamp = timestamp
        self.market_price = market_price
        self.market_price_min = market_price_min
        self.market_price_max = market_price_max
        self.volume = volume


def to_seconds(string: str) -> int:
    assert(isinstance(string, str))
    seconds_per_unit = {"s": 1, "m": 60, "h": 3600, "d": 86400, "w": 604800}
    return int(string[:-1]) * seconds_per_unit[string[-1]]


def amount_to_size(symbol: str, amount: Wad):
    if symbol.upper() == 'DAI':
        amount_in_usd = amount
    elif symbol.upper() in ['USD', 'USDT']:
        amount_in_usd = amount
    elif symbol.upper() == 'BTC':
        amount_in_usd = amount * 10000
    elif symbol.upper() == 'ETH':
        amount_in_usd = amount * 1000
    else:
        raise Exception("Don't know how to calculate amount in USD for chart size")

    return amount_in_usd_to_size(amount_in_usd)


def amount_in_usd_to_size(amount_in_usd: Wad):
    return max(min(float(amount_in_usd) / float(SIZE_PRICE_MAX) * SIZE_MAX, SIZE_MAX), SIZE_MIN)


def get_file_prices(filename: str, start_timestamp: int, end_timestamp: int):
    prices = []
    with open(filename, "r") as file:
        for line in file:
            try:
                record = json.loads(line)
                timestamp = record['timestamp']
                price = record['price']

                if start_timestamp <= timestamp <= end_timestamp:
                    prices.append(Price(timestamp=timestamp,
                                        market_price=price,
                                        market_price_min=None,
                                        market_price_max=None,
                                        volume=None))
            except:
                pass

    return sorted(prices, key=lambda price: price.timestamp)


def get_block_timestamp(infura: Web3, block_number):
    return infura.eth.getBlock(block_number).timestamp


def get_event_timestamp(infura: Web3, event):
    return infura.eth.getBlock(event.raw['blockHash']).timestamp


def cache_folder():
    db_folder = user_cache_dir("market-maker-stats", "maker")

    try:
        os.makedirs(db_folder)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise

    return db_folder


def get_gdax_prices(start_timestamp: int, end_timestamp: int):
    prices = []
    timestamp = gdax_batch_begin(start_timestamp)
    while timestamp <= end_timestamp:
        timestamp_range_start = timestamp
        timestamp_range_end = gdax_batch_end(timestamp)
        prices = prices + get_gdax_partial(timestamp_range_start, timestamp_range_end)
        timestamp = timestamp_range_end

    prices = list(filter(lambda price: start_timestamp <= price.timestamp <= end_timestamp, prices))
    return sorted(prices, key=lambda price: price.timestamp)


def gdax_batch_begin(start_timestamp):
    return int(datetime.datetime.fromtimestamp(start_timestamp).replace(hour=0, minute=0, second=0, microsecond=0).timestamp())


def gdax_batch_end(batch_begin):
    # TODO what about leap seconds...?
    return int((datetime.datetime.fromtimestamp(batch_begin) + datetime.timedelta(hours=4)).timestamp())


def gdax_fetch(url):
    try:
        data = requests.get(url).json()
    except:
        logging.info("GDAX API network error, waiting 10 secs...")
        time.sleep(10)
        return gdax_fetch(url)

    if 'message' in data:
        logging.info("GDAX API rate limiting, slowing down for 2 secs...")
        time.sleep(2)
        return gdax_fetch(url)

    return data


def get_gdax_partial(timestamp_range_start: int, timestamp_range_end: int) -> List[Price]:
    assert(isinstance(timestamp_range_start, int))
    assert(isinstance(timestamp_range_end, int))

    # We only cache batches if their end timestamp is at least one hour in the past.
    # There is no good reason for choosing exactly one hour as the cutoff time.
    can_cache = timestamp_range_end < int(time.time()) - 3600
    cache_file = os.path.join(cache_folder(), f'gdax_ETH-USD_{timestamp_range_start}_{timestamp_range_end}_60.json')

    start = datetime.datetime.fromtimestamp(timestamp_range_start, pytz.UTC)
    end = datetime.datetime.fromtimestamp(timestamp_range_end, pytz.UTC)
    url = f"https://api.gdax.com/products/ETH-USD/candles?" \
          f"start={iso_8601(start)}&" \
          f"end={iso_8601(end)}&" \
          f"granularity=60"

    # Try do get data from cache
    data_from_cache = None
    if can_cache:
        with filelock.FileLock(cache_file + ".lock"):
            try:
                if os.path.isfile(cache_file):
                    with open(cache_file, 'r') as infile:
                        data_from_cache = json.load(infile)
            except:
                pass

    if data_from_cache is None:
        data_from_server = gdax_fetch(url)

        if can_cache:
            with filelock.FileLock(cache_file + ".lock"):
                try:
                    with open(cache_file, 'w') as outfile:
                        json.dump(data_from_server, outfile)
                except:
                    pass

    # data is: [[ time, low, high, open, close, volume ], [...]]
    data = data_from_cache if data_from_cache is not None else data_from_server
    prices = list(map(lambda array: Price(timestamp=array[0],
                                          market_price=(array[1]+array[2])/2,
                                          market_price_min=array[1],
                                          market_price_max=array[2],
                                          volume=array[5]), data))

    return list(filter(lambda price: timestamp_range_start <= price.timestamp <= timestamp_range_end, prices))


def iso_8601(tm) -> str:
    return tm.isoformat().replace('+00:00', 'Z')


def format_timestamp(timestamp: int):
    assert(isinstance(timestamp, int))
    return datetime.datetime.fromtimestamp(timestamp, pytz.UTC).strftime('%Y-%m-%d %H:%M:%S %Z')


def timestamp_to_x(timestamp: int):
    assert(isinstance(timestamp, int))

    from matplotlib.dates import date2num
    return date2num(datetime.datetime.fromtimestamp(timestamp))


def sort_trades(trades: list) -> list:
    return sorted(trades, key=lambda trade: trade.timestamp, reverse=True)


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
