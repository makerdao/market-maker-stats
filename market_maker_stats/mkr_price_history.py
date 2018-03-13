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
import json
import logging
import operator
import sys
import time

from typing import List, Optional
from web3 import Web3, HTTPProvider

from market_maker_stats.oasis import oasis_trades
from market_maker_stats.pnl import get_approx_vwaps, pnl_text, pnl_chart
from market_maker_stats.util import get_gdax_prices, sort_trades_for_pnl, get_block_timestamp, Price
from pymaker import Address
from pymaker.oasis import SimpleMarket


class MkrPriceHistory:
    """Tool to dump archival MKR price history from Oasis for MKR market making PnL calculation."""

    def __init__(self, args: list):
        parser = argparse.ArgumentParser(prog='mkr-price-history')
        parser.add_argument("--rpc-host", help="JSON-RPC host (default: `localhost')", default="localhost", type=str)
        parser.add_argument("--rpc-port", help="JSON-RPC port (default: `8545')", default=8545, type=int)
        parser.add_argument("--rpc-timeout", help="JSON-RPC timeout (in seconds, default: 60)", type=int, default=60)
        parser.add_argument("--oasis-address", help="Ethereum address of the OasisDEX contract", required=True, type=str)
        parser.add_argument("--mkr-address", help="Ethereum address of the MKR token", required=True, type=str)
        parser.add_argument("--weth-address", help="Ethereum address of the WETH token", required=True, type=str)
        parser.add_argument("--past-blocks", help="Number of past blocks to analyze", required=True, type=int)
        parser.add_argument("--target-mkr-eth-history-file", type=str, help="Target file for the MKR/ETH price history")
        parser.add_argument("--target-mkr-btc-history-file", type=str, help="Target file for the MKR/BTC price history")
        parser.add_argument("--target-mkr-usd-history-file", type=str, help="Target file for the MKR/USD price history")

        self.arguments = parser.parse_args(args)

        self.web3 = Web3(HTTPProvider(endpoint_uri=f"http://{self.arguments.rpc_host}:{self.arguments.rpc_port}",
                                      request_kwargs={'timeout': self.arguments.rpc_timeout}))
        self.mkr_address = Address(self.arguments.mkr_address)
        self.weth_address = Address(self.arguments.weth_address)
        self.otc = SimpleMarket(web3=self.web3, address=Address(self.arguments.oasis_address))

        logging.basicConfig(format='%(asctime)-15s %(levelname)-8s %(message)s', level=logging.INFO)
        logging.getLogger("filelock").setLevel(logging.WARNING)

    def main(self):
        # Get Oasis take events from which we will get the main MKR/ETH price source
        takes = self.otc.past_take(self.arguments.past_blocks)
        start_timestamp = min(map(lambda log_take: log_take.timestamp, takes))
        end_timestamp = max(map(lambda log_take: log_take.timestamp, takes))

        # Get auxiliary prices (ETH/USD and BTC/USD)
        prices_eth_usd = get_gdax_prices('ETH-USD', start_timestamp, end_timestamp)
        prices_btc_usd = get_gdax_prices('BTC-USD', start_timestamp, end_timestamp)

        prices_mkr_eth = self.get_mkr_eth_prices(takes)
        prices_mkr_usd = self.convert_prices(prices_mkr_eth, prices_eth_usd, operator.mul)
        prices_mkr_btc = self.convert_prices(prices_mkr_usd, prices_btc_usd, operator.truediv)

        self.save_prices(prices_mkr_eth, self.arguments.target_mkr_eth_history_file)
        self.save_prices(prices_mkr_btc, self.arguments.target_mkr_btc_history_file)
        self.save_prices(prices_mkr_usd, self.arguments.target_mkr_usd_history_file)

    def get_mkr_eth_prices(self, takes):
        takes_1 = filter(lambda log_take: log_take.buy_token == self.mkr_address and log_take.pay_token == self.weth_address, takes)
        takes_2 = filter(lambda log_take: log_take.buy_token == self.weth_address and log_take.pay_token == self.mkr_address, takes)

        prices_mkr_eth = list(map(lambda log_take: Price(timestamp=log_take.timestamp,
                                                         market_price=float(log_take.take_amount / log_take.give_amount),
                                                         volume=float(log_take.give_amount)), takes_1)) \
                         + list(map(lambda log_take: Price(timestamp=log_take.timestamp,
                                                           market_price=float(log_take.give_amount / log_take.take_amount),
                                                           volume=float(log_take.take_amount)), takes_2))

        return prices_mkr_eth

    def convert_prices(self, source: List[Price], target: List[Price], operator):
        result = []
        for price in source:
            matching_target = next(filter(lambda target_price: target_price.timestamp >= price.timestamp, target), None)
            if matching_target is not None:
                result.append(Price(timestamp=price.timestamp,
                                    market_price=operator(price.market_price, matching_target.market_price),
                                    volume=price.volume))
            else:
                logging.warning(f"No matching price found at {price.timestamp}")

        return result

    def save_prices(self, prices: List[Price], filename: Optional[str]):
        if filename is not None:
            with open(filename, "w") as file:
                for price in prices:
                    file.write(json.dumps({"timestamp": price.timestamp,
                                           "price": float(price.market_price),
                                           "volume": float(price.volume)}) + "\n")


if __name__ == '__main__':
    MkrPriceHistory(sys.argv[1:]).main()
