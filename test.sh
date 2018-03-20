#!/bin/sh

PYTHONPATH=$PYTHONPATH:./lib/pymaker:./lib/pyexchange:./lib/trade-client py.test --cov=market_maker_stats --cov-report=term --cov-append tests/
