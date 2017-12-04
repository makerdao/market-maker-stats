#!/bin/sh

PYTHONPATH=$PYTHONPATH:./lib/pymaker py.test --cov=market_maker_stats --cov-report=term --cov-append tests/
