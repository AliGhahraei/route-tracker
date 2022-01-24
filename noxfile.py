#!/usr/bin/env python3
from nox_tools import config, linting, tests, typing

config.module = 'route_tracker'
config.sessions = [linting, tests, typing]
