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
from functools import reduce
from pprint import pformat

import filelock
import pytz
import re
import requests
import os
import time
import numpy as np
from typing import List, Optional

from appdirs import user_cache_dir
from web3 import Web3

import trade_client
from market_maker_stats.model import AllTrade
from pymaker.numeric import Wad

SIZE_MIN = 5
SIZE_MAX = 100
SIZE_PRICE_MAX = 30000


class Price:
    def __init__(self, timestamp: int, price: Optional[float], buy_price: Optional[float], sell_price: Optional[float], volume: Optional[float]):
        self.timestamp = timestamp
        self.price = price
        self.buy_price = buy_price
        self.sell_price = sell_price
        self.volume = volume

    def inverse(self):
        def inv_optional(x: Optional[float]):
            return 1/x if x is not None else None

        return Price(timestamp=self.timestamp,
                     price=inv_optional(self.price),
                     buy_price=inv_optional(self.buy_price),
                     sell_price=inv_optional(self.sell_price),
                     volume=self.volume)

    def __eq__(self, other):
        assert(isinstance(other, Price))
        return self.timestamp == other.timestamp and \
               self.price == other.price and \
               self.buy_price == other.buy_price and \
               self.sell_price == other.sell_price and \
               self.volume == other.volume

    def __hash__(self):
        return hash((self.timestamp,
                     self.price,
                     self.buy_price,
                     self.sell_price,
                     self.volume))

    def __repr__(self):
        return pformat(vars(self))


class OrderHistoryItem:
    def __init__(self, timestamp: int, orders: list):
        self.timestamp = timestamp
        self.orders = orders

    def closest_sell_price(self) -> Optional[Wad]:
        return min(self.sell_prices(), default=None)

    def closest_buy_price(self) -> Optional[Wad]:
        return max(self.buy_prices(), default=None)

    def sell_orders(self) -> list:
        return list(filter(lambda order: order['type'] == 'sell', self.orders))

    def sell_prices(self) -> List[Wad]:
        return list(map(lambda order: Wad.from_number(order['price']), self.sell_orders()))

    def buy_orders(self) -> list:
        return list(filter(lambda order: order['type'] == 'buy', self.orders))

    def buy_prices(self) -> List[Wad]:
        return list(map(lambda order: Wad.from_number(order['price']), self.buy_orders()))


def to_seconds(string: str) -> int:
    assert(isinstance(string, str))
    seconds_per_unit = {"s": 1, "m": 60, "h": 3600, "d": 86400, "w": 604800}
    return int(string[:-1]) * seconds_per_unit[string[-1]]


def amount_to_size(trade: AllTrade):
    ETH_IN_USD = Wad.from_number(500)
    MKR_IN_USD = Wad.from_number(500)

    if trade.pair.endswith("-DAI"):
        amount_in_usd = trade.amount * trade.price
    elif trade.pair.startswith("DAI-"):
        amount_in_usd = trade.amount
    elif trade.pair.endswith("-USDT") or trade.pair.endswith("-USD") or trade.pair.endswith("-TUSD"):
        amount_in_usd = trade.amount * trade.price
    elif trade.pair.startswith("USDT-") or trade.pair.startswith("USD-") or trade.pair.startswith("TUSD-"):
        amount_in_usd = trade.amount
    elif trade.pair.startswith("ETH-"):
        amount_in_usd = trade.amount * ETH_IN_USD
    elif trade.pair.startswith("-ETH"):
        amount_in_usd = trade.amount * trade.price * ETH_IN_USD
    elif trade.pair.startswith("MKR-"):
        amount_in_usd = trade.amount * MKR_IN_USD
    elif trade.pair.startswith("-MKR"):
        amount_in_usd = trade.amount * trade.price * MKR_IN_USD
    else:
        raise Exception("Don't know how to calculate amount in USD for chart size")

    return amount_in_usd_to_size(amount_in_usd)


def amount_in_usd_to_size(amount_in_usd: Wad):
    return max(min(float(amount_in_usd) / float(SIZE_PRICE_MAX) * SIZE_MAX, SIZE_MAX), SIZE_MIN)


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


def get_trades(endpoint: Optional[str], start_timestamp: int, end_timestamp: int):
    if endpoint is not None:
        trades = trade_client.get_trades(endpoint, start_timestamp, end_timestamp, 60.5)

        return list(map(lambda item: AllTrade(exchange=item.exchange,
                                              maker=item.maker,
                                              pair=item.pair,
                                              timestamp=item.timestamp,
                                              is_sell=item.is_sell,
                                              amount=item.amount,
                                              price=item.price), trades))
    else:
        return []


def get_prices(gdax_price: Optional[str], price_feed: Optional[str], price_history_file: Optional[str], start_timestamp: int, end_timestamp: int):
    if price_feed:
        return get_price_feed(price_feed, start_timestamp, end_timestamp)
    elif price_history_file:
        return get_file_prices(price_history_file, start_timestamp, end_timestamp)
    elif gdax_price:
        return get_gdax_prices(gdax_price, start_timestamp, end_timestamp)
    else:
        return []


def get_order_history(endpoint: Optional[str], start_timestamp: int, end_timestamp: int):
    if endpoint is None:
        return []

    result = requests.get(f"{endpoint}?min={start_timestamp}&max={end_timestamp}", timeout=15.5)

    # This trick is only here so we can still generate charts for keepers which haven't started
    # operating yet. Without it, the 500 will make the tool abort and not generate any chart.
    if result.status_code == 500:
        print("!!! Received 500 from the order history endpoint, assuming empty history")
        return []

    if not result.ok:
        raise Exception(f"Unable to fetch order history from the endpoint: {result.status_code} {result.reason}")

    return list(map(lambda item: OrderHistoryItem(timestamp=int(item['timestamp']),
                                                  orders=list(item['orders'])), result.json()['items']))


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
                                        price=price,
                                        buy_price=None,
                                        sell_price=None,
                                        volume=record['volume'] if 'volume' in record else None))
            except:
                pass

    return sorted(prices, key=lambda price: price.timestamp)


def get_price_feed(endpoint: str, start_timestamp: int, end_timestamp: int):

    if endpoint.startswith("fixed:"):
        price = float(endpoint.replace("fixed:", ""))

        result = []
        for timestamp in range(start_timestamp, end_timestamp, 60):
            result.append(Price(timestamp=timestamp, price=price, buy_price=price, sell_price=price, volume=1.0))

        return result

    result = requests.get(f"{endpoint}?min={start_timestamp}&max={end_timestamp}", timeout=15.5)
    if not result.ok:
        raise Exception(f"Failed to fetch price feed history: {result.status_code} {result.reason}")

    return list(map(lambda item: Price(timestamp=item['timestamp'],
                                       price=float(item['data']['price']) if 'price' in item['data'] else None,
                                       buy_price=float(item['data']['buyPrice']) if 'buyPrice' in item['data'] else None,
                                       sell_price=float(item['data']['sellPrice']) if 'sellPrice' in item['data'] else None,
                                       volume=None), result.json()['items']))


def get_gdax_prices(product: str, start_timestamp: int, end_timestamp: int):
    prices = []
    timestamp = gdax_batch_begin(start_timestamp)
    while timestamp <= end_timestamp:
        timestamp_range_start = timestamp
        timestamp_range_end = gdax_batch_end(timestamp)
        prices = prices + get_gdax_partial(product, timestamp_range_start, timestamp_range_end)
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
        data = requests.get(url, timeout=30.5).json()
    except:
        logging.info("GDAX API network error, waiting 10 secs...")
        time.sleep(10)
        return gdax_fetch(url)

    if 'message' in data:
        logging.info("GDAX API rate limiting, slowing down for 2 secs...")
        time.sleep(2)
        return gdax_fetch(url)

    return data


def get_gdax_partial(product: str, timestamp_range_start: int, timestamp_range_end: int) -> List[Price]:
    assert(isinstance(product, str))
    assert(isinstance(timestamp_range_start, int))
    assert(isinstance(timestamp_range_end, int))

    if product == 'USD-ETH':
        return list(map(lambda price: price.inverse(), get_gdax_partial('ETH-USD', timestamp_range_start, timestamp_range_end)))

    if product == 'USD-BTC':
        return list(map(lambda price: price.inverse(), get_gdax_partial('BTC-USD', timestamp_range_start, timestamp_range_end)))

    # We only cache batches if their end timestamp is at least one hour in the past.
    # There is no good reason for choosing exactly one hour as the cutoff time.
    can_cache = timestamp_range_end < int(time.time()) - 3600
    cache_file = os.path.join(cache_folder(), f'gdax_{product.upper()}_{timestamp_range_start}_{timestamp_range_end}_60.json')

    start = datetime.datetime.fromtimestamp(timestamp_range_start, pytz.UTC)
    end = datetime.datetime.fromtimestamp(timestamp_range_end, pytz.UTC)
    url = f"https://api.gdax.com/products/{product.upper()}/candles?" \
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
                                          price=(array[1] + array[2]) / 2,
                                          buy_price=None,
                                          sell_price=None,
                                          volume=array[5]), data))

    return list(filter(lambda price: timestamp_range_start <= price.timestamp <= timestamp_range_end, prices))


def get_day(timestamp: int):
    assert(isinstance(timestamp, int))
    transaction_timestamp = datetime.datetime.fromtimestamp(timestamp, tz=pytz.UTC)
    return transaction_timestamp.replace(hour=0, minute=0, second=0, microsecond=0)


def iso_8601(tm) -> str:
    return tm.isoformat().replace('+00:00', 'Z')


def format_timestamp(timestamp: int):
    assert(isinstance(timestamp, int))
    return datetime.datetime.fromtimestamp(timestamp, pytz.UTC).strftime('%Y-%m-%d %H:%M:%S %Z')


def timestamp_to_x(timestamp):
    from matplotlib.dates import date2num
    return date2num(datetime.datetime.fromtimestamp(int(timestamp), tz=pytz.UTC))


def sort_trades(trades: list) -> list:
    return sorted(trades, key=lambda trade: trade.timestamp, reverse=True)


def sort_trades_for_pnl(trades: list) -> list:
    return sorted(trades, key=lambda trade: trade.timestamp)


def sum_wads(iterable):
    return reduce(lambda x, y: x + y, iterable, Wad(0))


def initialize_logging():
    logging.basicConfig(format='%(asctime)-15s %(levelname)-8s %(message)s', level=logging.INFO)
    logging.getLogger("filelock").setLevel(logging.WARNING)
