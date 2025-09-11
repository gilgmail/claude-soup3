#!/usr/bin/env python3
"""
設置現有「財商成長思維」Notion 數據庫的集成
不創建新數據庫，只是檢查和配置現有數據庫
"""

import os
import sys
from notion_client import Client

def main():
    """主設置流程"""
    
    print("🔧 設置現有 Notion 數據庫集成")
    print("="*60)
    
    # Step 1: 檢查 Notion Token
    print("1️⃣ 檢查 Notion Token...")
    notion_token = os.getenv('NOTION_TOKEN')
    
    if not notion_token:
        print("❌ NOTION_TOKEN 環境變數未設定")
        print("\n請按照以下步驟設置:")
        print("1. 前往 https://www.notion.so/my-integrations")
        print("2. 創建新集成或使用現有集成")
        print("3. 複製 Integration Token")
        print("4. 設置環境變數:")
        print("   export NOTION_TOKEN='secret_your_token_here'")
        return False
    else:
        print(f"✅ NOTION_TOKEN 已設定 (...{notion_token[-8:]})")
    
    # Step 2: 檢查數據庫 ID
    print("\n2️⃣ 檢查數據庫 ID...")
    database_id = os.getenv('NOTION_DATABASE_ID')
    
    if not database_id:
        print("❌ NOTION_DATABASE_ID 環境變數未設定")
        print("\n請按照以下步驟獲取數據庫 ID:")
        print("1. 打開您的「財商成長思維」Notion 頁面")
        print("2. 點擊右上角的「...」按鈕")
        print("3. 選擇「Copy link」")
        print("4. 從 URL 中提取數據庫 ID（32位字符串）")
        print("5. 設置環境變數:")
        print("   export NOTION_DATABASE_ID='your_database_id_here'")
        
        # 互動式輸入
        user_input = input("\n您可以現在輸入數據庫 ID 進行測試 (或按 Enter 跳過): ").strip()
        if user_input:
            database_id = user_input
            print(f"✅ 使用提供的數據庫 ID: {database_id[:8]}...")
        else:
            return False
    else:
        print(f"✅ NOTION_DATABASE_ID 已設定 ({database_id[:8]}...)")
    
    # Step 3: 測試連接
    print("\n3️⃣ 測試連接...")
    
    try:
        client = Client(auth=notion_token)
        
        # 測試 Token 有效性
        users = client.users.list()
        print("✅ Notion Token 有效")
        
        # 測試數據庫訪問
        database = client.databases.retrieve(database_id=database_id)
        
        # 提取數據庫標題
        title_list = database.get('title', [])
        database_title = title_list[0].get('plain_text', '未命名數據庫') if title_list else '未命名數據庫'
        
        print(f"✅ 數據庫訪問成功")
        print(f"   數據庫名稱: {database_title}")
        print(f"   數據庫 ID: {database_id}")
        print(f"   屬性數量: {len(database.get('properties', {}))}")
        
    except Exception as e:
        print(f"❌ 連接測試失敗: {e}")
        print("\n可能的問題:")
        print("1. Token 無效或已過期")
        print("2. 數據庫 ID 錯誤")
        print("3. 集成沒有訪問數據庫的權限")
        print("\n解決方案:")
        print("1. 檢查 Token 是否正確複製")
        print("2. 確認數據庫 ID 是否正確")
        print("3. 在 Notion 頁面中邀請您的集成並給予權限")
        return False
    
    # Step 4: 檢查數據庫結構
    print("\n4️⃣ 分析數據庫結構...")
    
    try:
        properties = database.get('properties', {})
        
        print(f"發現 {len(properties)} 個屬性:")
        
        for prop_name, prop_config in properties.items():
            prop_type = prop_config.get('type', 'unknown')
            print(f"  • {prop_name} ({prop_type})")
            
            # 顯示選項
            if prop_type == 'select':
                options = prop_config.get('select', {}).get('options', [])
                if options:
                    option_names = [opt['name'] for opt in options[:5]]
                    print(f"    選項: {option_names}{'...' if len(options) > 5 else ''}")
            elif prop_type == 'multi_select':
                options = prop_config.get('multi_select', {}).get('options', [])
                if options:
                    option_names = [opt['name'] for opt in options[:5]]
                    print(f"    選項: {option_names}{'...' if len(options) > 5 else ''}")
        
    except Exception as e:
        print(f"⚠️  結構分析失敗: {e}")
    
    # Step 5: 生成配置建議
    print("\n5️⃣ 配置建議...")
    
    print("\n建議添加到 .env 文件:")
    print(f"NOTION_TOKEN={notion_token}")
    print(f"NOTION_DATABASE_ID={database_id}")
    
    print("\n或設置為環境變數:")
    print(f"export NOTION_TOKEN='{notion_token}'")
    print(f"export NOTION_DATABASE_ID='{database_id}'")
    
    # Step 6: 測試數據寫入（可選）
    print("\n6️⃣ 可選: 創建測試條目")
    create_test = input("是否創建一個測試條目來驗證寫入功能? (y/N): ").strip().lower()
    
    if create_test == 'y':
        try:
            from datetime import datetime
            
            # 構建測試屬性
            test_properties = {}
            
            for prop_name, prop_config in properties.items():
                prop_type = prop_config.get('type')
                
                if prop_type == 'title':
                    test_properties[prop_name] = {
                        "title": [{"text": {"content": f"測試條目 - {datetime.now().strftime('%Y-%m-%d %H:%M')}"}}]
                    }
                elif prop_type == 'rich_text':
                    test_properties[prop_name] = {
                        "rich_text": [{"text": {"content": "這是一個測試條目，用於驗證數據庫寫入功能。"}}]
                    }
                elif prop_type == 'select':
                    options = prop_config.get('select', {}).get('options', [])
                    if options:
                        test_properties[prop_name] = {"select": {"name": options[0]['name']}}
                elif prop_type == 'number':
                    test_properties[prop_name] = {"number": 8.0}
                elif prop_type == 'checkbox':
                    test_properties[prop_name] = {"checkbox": True}
                elif prop_type == 'date':
                    test_properties[prop_name] = {"date": {"start": datetime.now().isoformat()}}
            
            # 創建測試頁面
            page = client.pages.create(
                parent={"database_id": database_id},
                properties=test_properties
            )
            
            page_id = page["id"]
            page_url = page.get("url", f"https://notion.so/{page_id.replace('-', '')}")
            
            print(f"✅ 測試條目創建成功!")
            print(f"   頁面 ID: {page_id}")
            print(f"   頁面 URL: {page_url}")
            
        except Exception as e:
            print(f"❌ 測試條目創建失敗: {e}")
    
    # 完成
    print("\n" + "="*60)
    print("🎉 設置完成!")
    print("="*60)
    
    print("現在您可以:")
    print("1. 使用 Python 腳本測試集成:")
    print("   python3 scripts/test_existing_notion.py")
    print("2. 啟動 API 服務器:")
    print("   uvicorn app.api.main:app --reload")
    print("3. 測試 API 端點:")
    print("   curl http://localhost:8000/api/v1/articles/health")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)