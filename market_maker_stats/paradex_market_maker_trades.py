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

from market_maker_stats.trades import text_trades, json_trades
from market_maker_stats.util import to_seconds, sort_trades, initialize_logging
from pyexchange.paradex import ParadexApi


class ParadexMarketMakerTrades:
    """Tool to list historical trades for the Paradex market maker keeper."""

    def __init__(self, args: list):
        parser = argparse.ArgumentParser(prog='paradex-market-maker-trades')
        parser.add_argument("--paradex-api-server", help="Address of the Paradex API server (default: 'https://api.paradex.io/consumer')", default='https://api.paradex.io/consumer', type=str)
        parser.add_argument("--paradex-api-key", help="API key for the Paradex API", required=True, type=str)
        parser.add_argument("--paradex-api-timeout", help="Timeout for accessing the Paradex API", default=9.5, type=float)
        parser.add_argument("--pair", help="Token pair to get the past trades for", required=True, type=str)
        parser.add_argument("--past", help="Past period of time for which to get the trades for (e.g. 3d)", required=True, type=str)
        parser.add_argument("-o", "--output", help="File to save the table or the JSON to", required=False, type=str)

        parser_mode = parser.add_mutually_exclusive_group(required=True)
        parser_mode.add_argument('--text', help="List trades as a text table", dest='text', action='store_true')
        parser_mode.add_argument('--json', help="List trades as a JSON document", dest='json', action='store_true')

        self.arguments = parser.parse_args(args)

        self.paradex_api = ParadexApi(None,
                                      self.arguments.paradex_api_server,
                                      self.arguments.paradex_api_key,
                                      self.arguments.paradex_api_timeout)

        initialize_logging()

    def sell_token(self):
        return self.arguments.pair.split('/')[0].upper()

    def buy_token(self):
        return self.arguments.pair.split('/')[1].upper()

    def main(self):
        start_timestamp = int(time.time() - to_seconds(self.arguments.past))
        trades = self.paradex_api.get_trades(self.arguments.pair, from_timestamp=start_timestamp)
        trades = sort_trades(trades)

        if self.arguments.text:
            text_trades(self.buy_token(), self.sell_token(), trades, self.arguments.output)

        if self.arguments.json:
            json_trades(trades, self.arguments.output)


if __name__ == '__main__':
    ParadexMarketMakerTrades(sys.argv[1:]).main()
