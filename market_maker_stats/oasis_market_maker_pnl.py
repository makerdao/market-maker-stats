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
from itertools import groupby
from typing import List

import numpy as np
import pytz
from texttable import Texttable
from web3 import Web3, HTTPProvider

from market_maker_stats.oasis import oasis_trades, Trade
from market_maker_stats.pnl import calculate_pnl, prepare_trades_for_pnl, get_approx_vwaps
from market_maker_stats.util import get_gdax_prices, timestamp_to_x, Price, get_day, sum_wads
from pymaker import Address
from pymaker.numeric import Wad
from pymaker.oasis import SimpleMarket


class OasisMarketMakerPnl:
    """Tool to calculate profitability for the OasisDEX market maker keeper."""

    def __init__(self, args: list):
        parser = argparse.ArgumentParser(prog='oasis-market-maker-pnl')
        parser.add_argument("--rpc-host", help="JSON-RPC host (default: `localhost')", default="localhost", type=str)
        parser.add_argument("--rpc-port", help="JSON-RPC port (default: `8545')", default=8545, type=int)
        parser.add_argument("--rpc-timeout", help="JSON-RPC timeout (in seconds, default: 60)", type=int, default=60)
        parser.add_argument("--oasis-address", help="Ethereum address of the OasisDEX contract", required=True, type=str)
        parser.add_argument("--sai-address", help="Ethereum address of the SAI token", required=True, type=str)
        parser.add_argument("--weth-address", help="Ethereum address of the WETH token", required=True, type=str)
        parser.add_argument("--market-maker-address", help="Ethereum account of the market maker to analyze", required=True, type=str)
        parser.add_argument("--vwap-minutes", help="Rolling VWAP window size (default: 240)", type=int, default=240)
        parser.add_argument("--past-blocks", help="Number of past blocks to analyze", required=True, type=int)
        parser.add_argument("-o", "--output", help="Name of the filename to save to chart to."
                                                   " Will get displayed on-screen if empty", required=False, type=str)

        parser_mode = parser.add_mutually_exclusive_group(required=True)
        parser_mode.add_argument('--text', help="Show PnL as a text table", dest='text', action='store_true')
        parser_mode.add_argument('--chart', help="Show PnL on a cumulative graph", dest='chart', action='store_true')

        self.arguments = parser.parse_args(args)

        self.web3 = Web3(HTTPProvider(endpoint_uri=f"http://{self.arguments.rpc_host}:{self.arguments.rpc_port}",
                                      request_kwargs={'timeout': self.arguments.rpc_timeout}))
        self.sai_address = Address(self.arguments.sai_address)
        self.weth_address = Address(self.arguments.weth_address)
        self.market_maker_address = Address(self.arguments.market_maker_address)
        self.otc = SimpleMarket(web3=self.web3, address=Address(self.arguments.oasis_address))

        logging.basicConfig(format='%(asctime)-15s %(levelname)-8s %(message)s', level=logging.INFO)
        logging.getLogger("filelock").setLevel(logging.WARNING)

    def main(self):
        events = self.otc.past_take(self.arguments.past_blocks)
        trades = oasis_trades(self.market_maker_address, self.sai_address, self.weth_address, events)
        start_timestamp = trades[0].timestamp
        end_timestamp = int(time.time())

        prices = get_gdax_prices(start_timestamp, end_timestamp)
        vwaps = get_approx_vwaps(prices, self.arguments.vwap_minutes)
        vwaps_start = start_timestamp

        if self.arguments.text:
            self.text(trades, vwaps, vwaps_start)

        if self.arguments.chart:
            self.chart(start_timestamp, end_timestamp, prices, trades, vwaps, vwaps_start)

    def text(self, trades: List[Trade], vwaps: list, vwaps_start: int):
        data = []
        total_dai_net = Wad(0)
        total_profit = 0
        for day, day_trades in groupby(trades, lambda trade: get_day(trade.timestamp)):
            day_trades = list(day_trades)

            pnl_trades, pnl_prices, pnl_timestamps = prepare_trades_for_pnl(day_trades)
            pnl_profits = calculate_pnl(pnl_trades, pnl_prices, pnl_timestamps, vwaps, vwaps_start)

            day_dai_bought = sum_wads(map(lambda trade: trade.money, filter(lambda trade: not trade.is_sell, day_trades)))
            day_dai_sold = sum_wads(map(lambda trade: trade.money, filter(lambda trade: trade.is_sell, day_trades)))
            day_dai_net = day_dai_bought - day_dai_sold
            day_profit = np.sum(pnl_profits)

            total_dai_net += day_dai_net
            total_profit += day_profit

            data.append([day.strftime('%Y-%m-%d'),
                         len(day_trades),
                         "{:,.2f} DAI".format(float(day_dai_bought)),
                         "{:,.2f} DAI".format(float(day_dai_sold)),
                         "{:,.2f} DAI".format(float(day_dai_net)),
                         "{:,.2f} DAI".format(float(total_dai_net)),
                         "{:,.2f} USD".format(day_profit)])

        table = Texttable(max_width=250)
        table.set_deco(Texttable.HEADER)
        table.set_cols_dtype(['t', 't', 't', 't', 't', 't', 't'])
        table.set_cols_align(['l', 'r', 'r', 'r', 'r', 'r', 'r'])
        table.set_cols_width([11, 15, 20, 18, 30, 20, 25])
        table.add_rows([["Day", "# transactions", "Bought", "Sold", "Net bought", "Cumulative net bought", "Profit"]] + data)

        print(f"")
        print(f"PnL report for market-making on the ETH/DAI pair:")
        print(f"")
        print(table.draw())
        print(f"")
        print(f"The first and the last day of the report may not contain all trades.")
        print(f"As a rolling VWAP window is used, last {self.arguments.vwap_minutes} minutes of trades are excluded"
              f" from profit calculation.")
        print(f"")
        print(f"Number of trades: {len(trades)}")
        print(f"Total profit: " + "{:,.2f} USD".format(total_profit))
        print(f"Generated at: {datetime.datetime.now(tz=pytz.UTC).strftime('%Y.%m.%d %H:%M:%S %Z')}")

    def chart(self, start_timestamp: int, end_timestamp: int, prices: List[Price], trades: List[Trade], vwaps: list, vwaps_start: int):
        import matplotlib.dates as md
        import matplotlib.pyplot as plt

        pnl_trades, pnl_prices, pnl_timestamps = prepare_trades_for_pnl(trades)
        pnl_profits = calculate_pnl(pnl_trades, pnl_prices, pnl_timestamps, vwaps, vwaps_start)

        fig, ax = plt.subplots()
        ax.set_xlim(left=timestamp_to_x(start_timestamp), right=timestamp_to_x(end_timestamp))
        ax.xaxis.set_major_formatter(md.DateFormatter('%Y-%m-%d %H:%M:%S'))
        plt.subplots_adjust(bottom=0.2)
        plt.xticks(rotation=25)
        ax2 = ax.twinx()

        ax.set_zorder(ax2.get_zorder()+1)
        ax.patch.set_visible(False)

        dt_timestamps = [datetime.datetime.fromtimestamp(timestamp) for timestamp in pnl_timestamps]
        ax.plot(dt_timestamps[:len(pnl_profits)], np.cumsum(pnl_profits), color='green')

        ax2.plot(list(map(lambda price: timestamp_to_x(price.timestamp), prices)),
                 list(map(lambda price: price.market_price, prices)), color='red')

        ax.set_ylabel('Cumulative PnL ($)')
        ax2.set_ylabel('ETH/USD price ($)')
        plt.title("Profit: {:,.2f} USD".format(np.sum(pnl_profits)))

        if self.arguments.output:
            plt.savefig(fname=self.arguments.output, dpi=300, bbox_inches='tight', pad_inches=0)
        else:
            plt.show()


if __name__ == '__main__':
    OasisMarketMakerPnl(sys.argv[1:]).main()
