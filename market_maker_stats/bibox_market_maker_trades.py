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
import sys
import time
from typing import List

import pytz
from texttable import Texttable

from market_maker_stats.trades import text_trades, json_trades
from market_maker_stats.util import to_seconds, sort_trades, initialize_logging
from pyexchange.bibox import BiboxApi, Trade


class BiboxMarketMakerTrades:
    """Tool to list historical trades for the Bibox market maker keeper."""

    def __init__(self, args: list):
        parser = argparse.ArgumentParser(prog='bibox-market-maker-trades')
        parser.add_argument("--bibox-api-server", help="Address of the Bibox API server (default: 'https://api.bibox.com')", default="https://api.bibox.com", type=str)
        parser.add_argument("--bibox-api-key", help="API key for the Bibox API", required=True, type=str)
        parser.add_argument("--bibox-secret", help="Secret for the Bibox API", required=True, type=str)
        parser.add_argument("--bibox-timeout", help="Timeout for accessing the Bibox API", default=9.5, type=float)
        parser.add_argument("--bibox-retry-count", help="Retry count for accessing the Bibox API (default: 20)", default=20, type=int)
        parser.add_argument("--pair", help="Token pair to get the past trades for", required=True, type=str)
        parser.add_argument("--past", help="Past period of time for which to get the trades for (e.g. 3d)", required=True, type=str)

        parser_mode = parser.add_mutually_exclusive_group(required=True)
        parser_mode.add_argument('--text', help="List trades as a text table", dest='text', action='store_true')
        parser_mode.add_argument('--json', help="List trades as a JSON document", dest='json', action='store_true')

        self.arguments = parser.parse_args(args)

        self.bibox_api = BiboxApi(api_server=self.arguments.bibox_api_server,
                                  api_key=self.arguments.bibox_api_key,
                                  secret=self.arguments.bibox_secret,
                                  timeout=self.arguments.bibox_timeout)

        initialize_logging()

    def token_pair(self):
        return self.arguments.pair.replace("_", "/").upper()

    def base_token(self):
        return self.arguments.pair.split('_')[0].upper()

    def quote_token(self):
        return self.arguments.pair.split('_')[1].upper()

    def main(self):
        start_timestamp = int(time.time() - to_seconds(self.arguments.past))
        trades = self.bibox_api.get_trades(self.arguments.pair, True, self.arguments.bibox_retry_count, from_timestamp=start_timestamp)
        trades = sort_trades(trades)

        if self.arguments.text:
            text_trades(self.token_pair(), self.base_token(), self.quote_token(), trades)

        if self.arguments.json:
            json_trades(trades)


if __name__ == '__main__':
    BiboxMarketMakerTrades(sys.argv[1:]).main()
