#!/usr/bin/env python3
"""
診斷 Notion 連接問題
"""

import os
import sys
from notion_client import Client
from dotenv import load_dotenv

# 加載 .env 文件
load_dotenv()

def main():
    """診斷連接問題"""
    
    print("🔬 Notion 連接診斷")
    print("="*50)
    
    # 檢查環境變數
    notion_token = os.getenv('NOTION_TOKEN')
    database_id = os.getenv('NOTION_DATABASE_ID')
    
    print(f"📋 配置檢查:")
    print(f"   NOTION_TOKEN: {'✅ 已設置' if notion_token else '❌ 未設置'}")
    if notion_token:
        print(f"   Token 開頭: {notion_token[:10]}...")
        print(f"   Token 長度: {len(notion_token)} 字符")
    
    print(f"   NOTION_DATABASE_ID: {'✅ 已設置' if database_id else '❌ 未設置'}")
    if database_id:
        print(f"   Database ID: {database_id}")
    
    if not notion_token or not database_id:
        print("\n❌ 配置不完整，請檢查 .env 文件")
        return
    
    try:
        print(f"\n🔧 測試 Notion API 連接...")
        client = Client(auth=notion_token)
        
        # 測試 1: 檢查 Token 有效性
        print("1️⃣ 測試 API Token...")
        try:
            users = client.users.list()
            print("   ✅ Token 有效")
            print(f"   👥 找到 {len(users.get('results', []))} 個用戶")
        except Exception as e:
            print(f"   ❌ Token 無效: {e}")
            return
        
        # 測試 2: 嘗試訪問數據庫
        print("2️⃣ 測試數據庫訪問...")
        try:
            database = client.databases.retrieve(database_id=database_id)
            print("   ✅ 數據庫訪問成功!")
            
            # 提取數據庫標題
            title_list = database.get('title', [])
            db_title = title_list[0].get('plain_text', '未命名數據庫') if title_list else '未命名數據庫'
            print(f"   📊 數據庫名稱: {db_title}")
            
        except Exception as e:
            print(f"   ❌ 數據庫訪問失敗: {e}")
            
            # 提供詳細的解決方案
            print(f"\n💡 解決方案:")
            print(f"1. 確認數據庫 ID 正確:")
            print(f"   當前 ID: {database_id}")
            print(f"   請檢查這是否是正確的數據庫 ID")
            
            print(f"\n2. 授權集成訪問數據庫:")
            print(f"   a) 打開您的「財商成長思維」Notion 頁面")
            print(f"   b) 點擊右上角的「Share」或「分享」按鈕") 
            print(f"   c) 點擊「Invite」或「邀請」")
            print(f"   d) 搜索並選擇您的集成")
            print(f"   e) 授予「Can edit」權限")
            
            print(f"\n3. 檢查數據庫是否為 Database 而非 Page:")
            print(f"   確保您分享的是數據庫，而不是普通頁面")
            
            return
        
        # 測試 3: 嘗試查詢數據
        print("3️⃣ 測試數據查詢...")
        try:
            pages_result = client.databases.query(
                database_id=database_id,
                page_size=5
            )
            
            pages = pages_result.get('results', [])
            print(f"   ✅ 查詢成功!")
            print(f"   📄 找到 {len(pages)} 個條目")
            
            if pages:
                print(f"   📋 數據庫屬性:")
                properties = database.get('properties', {})
                for prop_name, prop_config in properties.items():
                    prop_type = prop_config.get('type', 'unknown')
                    print(f"      • {prop_name} ({prop_type})")
            
        except Exception as e:
            print(f"   ❌ 查詢失敗: {e}")
            return
        
        print(f"\n🎉 診斷完成 - 所有測試通過!")
        print(f"您的 Notion 集成配置正確，可以正常使用。")
        
    except Exception as e:
        print(f"❌ 連接失敗: {e}")
        print(f"\n💡 請檢查:")
        print(f"1. Token 是否正確複製")
        print(f"2. 網路連接是否正常")
        print(f"3. Notion 服務是否可用")

if __name__ == "__main__":
    main()