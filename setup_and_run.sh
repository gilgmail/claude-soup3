#!/bin/bash

# 財商成長思維平台 - 設置和運行腳本
# Financial Wisdom Platform - Setup and Run Script

echo "=== 設置虛擬環境和依賴 ==="

# 檢查是否已存在虛擬環境
if [ ! -d "venv" ]; then
    echo "創建虛擬環境..."
    python3 -m venv venv
fi

# 啟動虛擬環境
echo "啟動虛擬環境..."
source venv/bin/activate

# 安裝依賴
echo "安裝依賴套件..."
pip install -r requirements.txt

echo "=== 啟動服務器 ==="
echo "服務器將在 http://localhost:8000 運行"
echo "按 Ctrl+C 停止服務器"

# 啟動服務器
python simple_main.py