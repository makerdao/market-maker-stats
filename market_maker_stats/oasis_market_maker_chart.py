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

import argparse
import sys
import time
from functools import reduce
from typing import List, Optional

from web3 import Web3, HTTPProvider

from market_maker_stats.chart import initialize_charting, prepare_prices_for_charting, draw_prices, draw_trades
from market_maker_stats.oasis import oasis_trades, Trade
from market_maker_stats.util import amount_in_usd_to_size, get_block_timestamp, \
    timestamp_to_x, initialize_logging, get_prices, Price
from pymaker import Address
from pymaker.numeric import Wad
from pymaker.oasis import SimpleMarket, Order, LogMake, LogTake, LogKill


class State:
    def __init__(self, timestamp: int, order_book: List[Order], buy_token_address: Address, sell_token_address: Address):
        self.timestamp = timestamp
        self.order_book = order_book
        self.buy_token_address = buy_token_address
        self.sell_token_address = sell_token_address

    def closest_sell_price(self) -> Optional[Wad]:
        return min(self.sell_prices(), default=None)

    def closest_buy_price(self) -> Optional[Wad]:
        return max(self.buy_prices(), default=None)

    def sell_orders(self) -> List[Order]:
        return list(filter(lambda order: order.buy_token == self.buy_token_address and
                                         order.pay_token == self.sell_token_address, self.order_book))

    def sell_prices(self) -> List[Wad]:
        return list(map(lambda order: order.buy_to_sell_price, self.sell_orders()))

    def buy_orders(self) -> List[Order]:
        return list(filter(lambda order: order.buy_token == self.sell_token_address and
                                         order.pay_token == self.buy_token_address, self.order_book))

    def buy_prices(self) -> List[Wad]:
        return list(map(lambda order: order.sell_to_buy_price, self.buy_orders()))


class OasisMarketMakerChart:
    """Tool to generate a chart displaying the OasisDEX market maker keeper trades."""

    def __init__(self, args: list):
        parser = argparse.ArgumentParser(prog='oasis-market-maker-chart')
        parser.add_argument("--rpc-host", help="JSON-RPC host (default: `localhost')", default="localhost", type=str)
        parser.add_argument("--rpc-port", help="JSON-RPC port (default: `8545')", default=8545, type=int)
        parser.add_argument("--rpc-timeout", help="JSON-RPC timeout (in seconds, default: 60)", type=int, default=60)
        parser.add_argument("--oasis-address", help="Ethereum address of the OasisDEX contract", required=True, type=str)
        parser.add_argument("--buy-token-address", help="Ethereum address of the buy token", required=True, type=str)
        parser.add_argument("--sell-token-address", help="Ethereum address of the sell token", required=True,type=str)
        parser.add_argument("--market-maker-address", help="Ethereum account of the market maker to analyze", required=True, type=str)
        parser.add_argument("--gdax-price", help="GDAX product (ETH-USD, BTC-USD) to use as the price history source", type=str)
        parser.add_argument("--price-feed", help="Price endpoint to use as the price history source", type=str)
        parser.add_argument("--price-history-file", help="File to use as the price history source", type=str)
        parser.add_argument("--alternative-price-feed", help="Price endpoint to use as the alternative price history source", type=str)
        parser.add_argument("--alternative-price-history-file", help="File to use as the alternative price history source", type=str)
        parser.add_argument("--past-blocks", help="Number of past blocks to analyze", required=True, type=int)
        parser.add_argument("-o", "--output", help="Name of the filename to save to chart to."
                                                   " Will get displayed on-screen if empty", required=False, type=str)
        self.arguments = parser.parse_args(args)

        self.web3 = Web3(HTTPProvider(endpoint_uri=f"http://{self.arguments.rpc_host}:{self.arguments.rpc_port}",
                                      request_kwargs={'timeout': self.arguments.rpc_timeout}))
        self.infura = Web3(HTTPProvider(endpoint_uri=f"https://mainnet.infura.io/", request_kwargs={'timeout': 120}))
        self.buy_token_address = Address(self.arguments.buy_token_address)
        self.sell_token_address = Address(self.arguments.sell_token_address)
        self.market_maker_address = Address(self.arguments.market_maker_address)
        self.otc = SimpleMarket(web3=self.web3, address=Address(self.arguments.oasis_address))

        initialize_charting(self.arguments.output)
        initialize_logging()

    def main(self):
        start_timestamp = get_block_timestamp(self.infura, self.web3.eth.blockNumber - self.arguments.past_blocks)
        end_timestamp = int(time.time())

        # If we only fetch log events from the last `past_blocks` blocks, the left hand side of the chart
        # will have some bid and ask lines missing as these orders were very likely created some blocks
        # earlier. So we also retrieve events from the blocks from the 24h before in order to minimize
        # the chance of it happening.
        block_lookback = 15*60*24

        past_make = self.otc.past_make(self.arguments.past_blocks + block_lookback)
        past_take = self.otc.past_take(self.arguments.past_blocks + block_lookback)
        past_kill = self.otc.past_kill(self.arguments.past_blocks + block_lookback)

        def reduce_func(states, timestamp):
            if len(states) == 0:
                order_book = []
            else:
                order_book = states[-1].order_book

            # apply all LogMake events having this timestamp
            for log_make in filter(lambda log_make: log_make.timestamp == timestamp, past_make):
                order_book = self.apply_make(order_book, log_make)
                order_book = list(filter(lambda order: order.maker == self.market_maker_address, order_book))

            # apply all LogTake events having this timestamp
            for log_take in filter(lambda log_take: log_take.timestamp == timestamp, past_take):
                order_book = self.apply_take(order_book, log_take)

            # apply all LogKill events having this timestamp
            for log_kill in filter(lambda log_kill: log_kill.timestamp == timestamp, past_kill):
                order_book = self.apply_kill(order_book, log_kill)

            return states + [State(timestamp=timestamp,
                                   order_book=order_book,
                                   buy_token_address=self.buy_token_address,
                                   sell_token_address=self.sell_token_address)]

        event_timestamps = sorted(set(map(lambda event: event.timestamp, past_make + past_take + past_kill)))
        states_timestamps = self.tighten_timestamps(event_timestamps) + [end_timestamp]
        states = list(filter(lambda state: state.timestamp >= start_timestamp, reduce(reduce_func, states_timestamps, [])))
        states = sorted(states, key=lambda state: state.timestamp)

        prices = get_prices(self.arguments.gdax_price, self.arguments.price_feed, self.arguments.price_history_file, start_timestamp, end_timestamp)
        alternative_prices = get_prices(None, self.arguments.alternative_price_feed, self.arguments.alternative_price_history_file, start_timestamp, end_timestamp)

        trades = oasis_trades(self.market_maker_address, self.buy_token_address, self.sell_token_address,
                              list(filter(lambda log_take: log_take.timestamp >= start_timestamp, past_take)))

        self.draw(start_timestamp, end_timestamp, states, trades, prices, alternative_prices)

    def tighten_timestamps(self, timestamps: list) -> list:
        if len(timestamps) == 0:
            return []

        result = [timestamps[0]]
        for index in range(1, len(timestamps)):
            last_ts = timestamps[index-1]
            while True:
                last_ts += 60
                if last_ts >= timestamps[index]:
                    break
                result.append(last_ts)

            result.append(timestamps[index])

        return result

    def draw(self, start_timestamp: int, end_timestamp: int, states: List[State], trades: List[Trade], prices: List[Price], alternative_prices: List[Price]):
        import matplotlib.dates as md
        import matplotlib.pyplot as plt

        plt.subplots_adjust(bottom=0.2)
        plt.xticks(rotation=25)
        ax=plt.gca()
        ax.set_xlim(left=timestamp_to_x(start_timestamp), right=timestamp_to_x(end_timestamp))
        ax.xaxis.set_major_formatter(md.DateFormatter('%Y-%m-%d %H:%M:%S'))

        timestamps = list(map(timestamp_to_x, map(lambda state: state.timestamp, states)))
        closest_sell_prices = list(map(lambda state: state.closest_sell_price(), states))
        closest_buy_prices = list(map(lambda state: state.closest_buy_price(), states))

        plt.plot_date(timestamps, closest_sell_prices, 'b-', zorder=2)
        plt.plot_date(timestamps, closest_buy_prices, 'g-', zorder=2)

        draw_prices(prices, alternative_prices)
        draw_trades(trades)

        if self.arguments.output:
            plt.savefig(fname=self.arguments.output, dpi=300, bbox_inches='tight', pad_inches=0)
        else:
            plt.show()

    def apply_make(self, order_book: List[Order], log_make: LogMake) -> List[Order]:
        return order_book + [Order(self.otc,
                                   order_id=log_make.order_id,
                                   pay_amount=log_make.pay_amount,
                                   pay_token=log_make.pay_token,
                                   buy_amount=log_make.buy_amount,
                                   buy_token=log_make.buy_token,
                                   maker=log_make.maker,
                                   timestamp=log_make.timestamp)]

    def apply_take(self, order_book: List[Order], log_take: LogTake):
        this_order = next(filter(lambda order: order.order_id == log_take.order_id, order_book), None)

        if this_order is not None:
            assert this_order.pay_token == log_take.pay_token
            assert this_order.buy_token == log_take.buy_token

            remaining_orders = list(filter(lambda order: order.order_id != log_take.order_id, order_book))
            this_order = Order(self.otc,
                               order_id=this_order.order_id,
                               pay_amount=this_order.pay_amount - log_take.take_amount,
                               pay_token=this_order.pay_token,
                               buy_amount=this_order.buy_amount - log_take.give_amount,
                               buy_token=this_order.buy_token,
                               maker=this_order.maker,
                               timestamp=this_order.timestamp)

            if this_order.pay_amount > Wad(0) and this_order.buy_amount > Wad(0):
                return remaining_orders + [this_order]
            else:
                return remaining_orders
        else:
            return order_book

    def apply_kill(self, order_book: List[Order], log_kill: LogKill) -> List[Order]:
        return list(filter(lambda order: order.order_id != log_kill.order_id, order_book))


if __name__ == '__main__':
    OasisMarketMakerChart(sys.argv[1:]).main()
