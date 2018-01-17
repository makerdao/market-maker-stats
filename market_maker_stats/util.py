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

from pymaker.numeric import Wad

SIZE_MIN = 30
SIZE_MAX = 100
SIZE_PRICE_MAX = 5000

class Price:
    def __init__(self, timestamp: int, market_price: Wad, market_price_min: Wad, market_price_max: Wad):
        self.timestamp = timestamp
        self.market_price = market_price
        self.market_price_min = market_price_min
        self.market_price_max = market_price_max

def amount_in_sai_to_size(amount_in_sai):
    return max(min(float(amount_in_sai) / float(SIZE_PRICE_MAX) * SIZE_MAX, SIZE_MAX), SIZE_MIN)

def get_gdax_prices(self, start_timestamp: int, end_timestamp: int):
    prices = []
    timestamp = start_timestamp
    while timestamp <= end_timestamp:
        timestamp_range_start = timestamp
        timestamp_range_end = int((datetime.datetime.fromtimestamp(timestamp) + datetime.timedelta(hours=3)).timestamp())
        prices = prices + list(filter(lambda state: state.timestamp >= start_timestamp and state.timestamp <= end_timestamp,
                                      self.get_gdax_partial(timestamp_range_start, timestamp_range_end)))
        timestamp = timestamp_range_end

    return sorted(prices, key=lambda price: price.timestamp)

def get_gdax_partial(self, timestamp_range_start: int, timestamp_range_end: int):
    start = datetime.datetime.fromtimestamp(timestamp_range_start, pytz.UTC)
    end = datetime.datetime.fromtimestamp(timestamp_range_end, pytz.UTC)

    url = f"https://api.gdax.com/products/ETH-USD/candles?" \
          f"start={iso_8601(start)}&" \
          f"end={iso_8601(end)}&" \
          f"granularity=60"

    print(f"Downloading: {url}")

    # data is: [[ time, low, high, open, close, volume ], [...]]
    try:
        data = requests.get(url).json()
    except:
        print("GDAX API network error, waiting 10 secs...")
        time.sleep(10)
        return self.get_gdax_partial(timestamp_range_start, timestamp_range_end)

    if 'message' in data:
        print("GDAX API rate limiting, slowing down for 2 secs...")
        time.sleep(2)
        return self.get_gdax_partial(timestamp_range_start, timestamp_range_end)
    else:
        return list(map(lambda array: Price(timestamp=array[0],
                                            market_price=(array[1]+array[2])/2,
                                            market_price_min=array[1],
                                            market_price_max=array[2]), data))


@staticmethod
def iso_8601(tm) -> str:
    return tm.isoformat().replace('+00:00', 'Z')

