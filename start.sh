#!/bin/bash
pip3 install fastapi uvicorn aiohttp pylxd psutil
 
/home/`whoami`/.local/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000