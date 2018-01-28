import os
import sys
import json
import datetime
import numpy as np
import matplotlib.pyplot as plt

import market_maker_stats.util


OASIS_TRADES_FILE = '/Downloads/all_trades/oasis_server2__trades_some.json'

oasis_trades_json = json.load(open(OASIS_TRADES_FILE))
trades, prices, timestamps = market_maker_stats.util.parse_trades_json(oasis_trades_json)

profits = market_maker_stats.util.calculate_pnl_vwap(trades, prices, timestamps, vwap_minutes=240)

print("{}".format(np.sum(profits)))

fig, ax = plt.subplots()
ax2 = ax.twinx()

dt_timestamps = [datetime.datetime.fromtimestamp(timestamp) for timestamp in timestamps]

ax.plot(dt_timestamps[:len(profits)], np.cumsum(profits), color='green')
ax2.plot(dt_timestamps[:len(profits)], prices[:len(profits)], color='blue')

ax.set_ylabel('Cumulative PnL ($)')
ax2.set_ylabel('ETH/USD price ($)')
