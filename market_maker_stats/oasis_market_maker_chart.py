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
import datetime
import logging
import sys
import time
from functools import reduce
from typing import List, Optional

from web3 import Web3, HTTPProvider

from market_maker_stats.oasis import oasis_trades, Trade
from market_maker_stats.util import amount_in_usd_to_size, get_gdax_prices, iso_8601, Price
from pymaker import Address
from pymaker.numeric import Wad
from pymaker.oasis import SimpleMarket, Order, LogMake, LogTake, LogKill


class State:
    def __init__(self, timestamp: int, order_book: List[Order], market_price: Wad, sai_address: Address, weth_address: Address):
        self.timestamp = timestamp
        self.order_book = order_book
        self.market_price = market_price
        self.sai_address = sai_address
        self.weth_address = weth_address

    def closest_sell_price(self) -> Optional[Wad]:
        return min(self.sell_prices(), default=None)

    def closest_buy_price(self) -> Optional[Wad]:
        return max(self.buy_prices(), default=None)

    def sell_orders(self) -> List[Order]:
        return list(filter(lambda order: order.buy_token == self.sai_address and
                                         order.pay_token == self.weth_address, self.order_book))

    def sell_prices(self) -> List[Wad]:
        return list(map(lambda order: order.buy_to_sell_price, self.sell_orders()))

    def buy_orders(self) -> List[Order]:
        return list(filter(lambda order: order.buy_token == self.weth_address and
                                         order.pay_token == self.sai_address, self.order_book))

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
        parser.add_argument("--sai-address", help="Ethereum address of the SAI token", required=True, type=str)
        parser.add_argument("--weth-address", help="Ethereum address of the WETH token", required=True, type=str)
        parser.add_argument("--market-maker-address", help="Ethereum account of the market maker to analyze", required=True, type=str)
        parser.add_argument("--past-blocks", help="Number of past blocks to analyze", required=True, type=int)
        parser.add_argument("-o", "--output", help="Name of the filename to save to chart to."
                                                   " Will get displayed on-screen if empty", required=False, type=str)
        self.arguments = parser.parse_args(args)

        self.web3 = Web3(HTTPProvider(endpoint_uri=f"http://{self.arguments.rpc_host}:{self.arguments.rpc_port}",
                                      request_kwargs={'timeout': self.arguments.rpc_timeout}))
        self.sai_address = Address(self.arguments.sai_address)
        self.weth_address = Address(self.arguments.weth_address)
        self.market_maker_address = Address(self.arguments.market_maker_address)
        self.otc = SimpleMarket(web3=self.web3, address=Address(self.arguments.oasis_address))

        if self.arguments.output:
            import matplotlib
            matplotlib.use('Agg')

        logging.basicConfig(format='%(asctime)-15s %(levelname)-8s %(message)s', level=logging.INFO)

    def main(self):
        past_make = self.otc.past_make(self.arguments.past_blocks)
        past_take = self.otc.past_take(self.arguments.past_blocks)
        past_kill = self.otc.past_kill(self.arguments.past_blocks)

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
                                   market_price=None,
                                   sai_address=self.sai_address,
                                   weth_address=self.weth_address)]

        event_timestamps = sorted(set(map(lambda event: event.timestamp, past_make + past_take + past_kill)))
        oasis_states = reduce(reduce_func, event_timestamps, [])
        gdax_states = self.get_gdax_states(event_timestamps)

        states = sorted(oasis_states + gdax_states, key=lambda state: state.timestamp)
        states = self.consolidate_states(states)

        trades = oasis_trades(self.market_maker_address, self.sai_address, self.weth_address, past_take)

        self.draw(states, trades)

    def consolidate_states(self, states):
        last_market_price = None
        last_order_book = []
        for i in range(0, len(states)):
            state = states[i]

            if state.order_book is None:
                state.order_book = last_order_book
            if state.market_price is None:
                state.market_price = last_market_price

            last_order_book = state.order_book
            last_market_price = state.market_price

        return states

    def get_gdax_states(self, timestamps: List[int]):
        start_timestamp = timestamps[0]
        end_timestamp = max(timestamps[-1], int(time.time()))
        prices = get_gdax_prices(start_timestamp, end_timestamp)

        return list(map(lambda price: State(timestamp=price.timestamp,
                                            order_book=None,
                                            market_price=price.market_price,
                                            sai_address=self.sai_address,
                                            weth_address=self.weth_address), prices))

    def convert_timestamp(self, timestamp):
        from matplotlib.dates import date2num

        return date2num(datetime.datetime.fromtimestamp(timestamp))

    def to_size(self, trade: Trade):
        return amount_in_usd_to_size(trade.money)

    def draw(self, states: List[State], trades: List[Trade]):
        import matplotlib.dates as md
        import matplotlib.pyplot as plt

        plt.subplots_adjust(bottom=0.2)
        plt.xticks(rotation=25)
        ax=plt.gca()
        ax.xaxis.set_major_formatter(md.DateFormatter('%Y-%m-%d %H:%M:%S'))

        if len(trades) == 0:
            ax.set_title('(no trades found in this block range)')

        timestamps = list(map(self.convert_timestamp, map(lambda state: state.timestamp, states)))
        closest_sell_prices = list(map(lambda state: state.closest_sell_price(), states))
        closest_buy_prices = list(map(lambda state: state.closest_buy_price(), states))
        market_prices = list(map(lambda state: state.market_price, states))

        plt.plot_date(timestamps, closest_sell_prices, 'b-', zorder=1)
        plt.plot_date(timestamps, closest_buy_prices, 'g-', zorder=1)
        plt.plot_date(timestamps, market_prices, 'r-', zorder=1)

        sell_trades = list(filter(lambda trade: trade.is_sell, trades))
        sell_x = list(map(self.convert_timestamp, map(lambda trade: trade.timestamp, sell_trades)))
        sell_y = list(map(lambda trade: trade.price, sell_trades))
        sell_s = list(map(self.to_size, sell_trades))
        plt.scatter(x=sell_x, y=sell_y, s=sell_s, c='blue', zorder=2)

        buy_trades = list(filter(lambda trade: trade.is_buy, trades))
        buy_x = list(map(self.convert_timestamp, map(lambda trade: trade.timestamp, buy_trades)))
        buy_y = list(map(lambda trade: trade.price, buy_trades))
        buy_s = list(map(self.to_size, buy_trades))
        plt.scatter(x=buy_x, y=buy_y, s=buy_s, c='green', zorder=2)

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
