#!/bin/bash
# スクリプトの場所に移動
cd `dirname $0`
pip3 install fastapi uvicorn aiohttp pylxd psutil apscheduler Jinja2
 
~/.local/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --log-level debug --proxy-headers