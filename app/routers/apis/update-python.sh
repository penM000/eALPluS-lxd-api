#!/bin/bash
pip3 list -o --format columns|  cut -d' ' -f1|xargs -n1 pip3 install -U