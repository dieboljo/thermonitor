#!/bin/bash

set -m

node js/app.js &

python3 py/thermonitor.py
