#!/bin/bash

# 创建日志目录
mkdir -p logs

# 安装依赖
pip install -r requirements.txt

# 启动 Gunicorn
gunicorn -c gunicorn.conf.py app:app 