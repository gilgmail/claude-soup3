#!/usr/bin/env python3
"""
Notion 設定助手 - 自動設定和測試 Notion 整合
"""

import os
import sys
from notion_client import Client

# 設定 Notion Token
NOTION_TOKEN = "ntn_zZ1417634396Ir4Cf2trq919QYp8kJMjeIrPL4Mt7065pD"
PARENT_PAGE_NAME = "財商成長思維"

def find_page_by_name(notion, page_name):
    """
    通過名稱搜索 Notion 頁面
    
    Args:
        notion: Notion client
        page_name: 頁面名稱
        
    Returns:
        str: 頁面ID，如果找不到返回None
    """
    try:
        print(f"🔍 搜索頁面: {page_name}")
        
        # 搜索頁面
        search_response = notion.search(
            query=page_name,
            filter={
                "property": "object",
                "value": "page"
            }
        )
        
        results = search_response.get('results', [])
        print(f"📄 找到 {len(results)} 個結果")
        
        for result in results:
            if result['object'] == 'page':
                page_id = result['id']
                print(f"   - 找到頁面 ID: {page_id}")
                
                # 檢查標題 - 先嘗試不同的方式獲取標題
                title = "未知標題"
                
                # 方法1: 從 properties.title 獲取
                title_property = result.get('properties', {}).get('title', {})
                if title_property:
                    title_text = title_property.get('title', [{}])
                    if title_text and len(title_text) > 0:
                        title = title_text[0].get('plain_text', '')
                
                # 方法2: 直接從頁面對象獲取
                if not title or title == "未知標題":
                    if 'title' in result:
                        if isinstance(result['title'], list) and len(result['title']) > 0:
                            title = result['title'][0].get('plain_text', '')
                        elif isinstance(result['title'], str):
                            title = result['title']
                
                print(f"   - 頁面標題: '{title}'")
                print(f"   - 搜索目標: '{page_name}'")
                
                # 寬鬆的匹配條件
                if (page_name in title or 
                    title in page_name or 
                    page_name.lower() in title.lower() or
                    title.lower() in page_name.lower()):
                    print(f"   ✅ 匹配成功!")
                    return page_id
                
                # 如果只找到一個結果，直接使用它
                if len(results) == 1:
                    print(f"   ✅ 只有一個結果，使用此頁面")
                    return page_id
        
        return None
        
    except Exception as e:
        print(f"❌ 搜索頁面失敗: {e}")
        return None

def create_database_in_page(notion, parent_page_id):
    """
    在指定頁面中創建資料庫
    """
    try:
        print(f"🗄️ 在頁面中創建資料庫...")
        
        # 定義資料庫結構
        database_properties = {
            "標題": {
                "title": {}
            },
            "主題分類": {
                "select": {
                    "options": [
                        {"name": "投資理財", "color": "blue"},
                        {"name": "數字貨幣投資", "color": "purple"},
                        {"name": "科技股投資", "color": "green"},
                        {"name": "房地產", "color": "orange"},
                        {"name": "投資理念", "color": "yellow"},
                        {"name": "風險管理", "color": "red"},
                        {"name": "ESG投資", "color": "pink"}
                    ]
                }
            },
            "內容風格": {
                "select": {
                    "options": [
                        {"name": "實用智慧", "color": "default"},
                        {"name": "哲學思考", "color": "gray"},
                        {"name": "勵志財經", "color": "brown"},
                        {"name": "歷史洞察", "color": "red"}
                    ]
                }
            },
            "品質評分": {
                "number": {
                    "format": "number_with_commas"
                }
            },
            "字數統計": {
                "number": {
                    "format": "number"
                }
            },
            "創建時間": {
                "date": {}
            },
            "關鍵字": {
                "multi_select": {
                    "options": [
                        {"name": "投資", "color": "blue"},
                        {"name": "理財", "color": "green"},
                        {"name": "基金", "color": "yellow"},
                        {"name": "股票", "color": "red"},
                        {"name": "風險管理", "color": "purple"},
                        {"name": "ESG", "color": "pink"},
                        {"name": "數字貨幣", "color": "orange"},
                        {"name": "人工智能", "color": "gray"},
                        {"name": "房地產", "color": "brown"}
                    ]
                }
            }
        }
        
        # 創建資料庫
        response = notion.databases.create(
            parent={
                "type": "page_id",
                "page_id": parent_page_id
            },
            title=[
                {
                    "type": "text",
                    "text": {
                        "content": "金融智慧文章資料庫",
                        "link": None
                    }
                }
            ],
            properties=database_properties
        )
        
        database_id = response["id"]
        print(f"✅ 資料庫創建成功!")
        print(f"   資料庫ID: {database_id}")
        print(f"   資料庫URL: {response.get('url')}")
        
        return database_id
        
    except Exception as e:
        print(f"❌ 資料庫創建失敗: {e}")
        return None

def test_connection(notion, database_id=None):
    """測試 Notion 連接"""
    try:
        print("🧪 測試 Notion 連接...")
        
        # 測試基本連接
        users = notion.users.list()
        print(f"✅ 基本連接成功，找到 {len(users.get('results', []))} 個用戶")
        
        # 如果有資料庫ID，測試資料庫訪問
        if database_id:
            database = notion.databases.retrieve(database_id=database_id)
            db_title = database.get('title', [{}])[0].get('plain_text', '未知')
            print(f"✅ 資料庫訪問成功: {db_title}")
            
            return True, database_id
        
        return True, None
        
    except Exception as e:
        print(f"❌ 連接測試失敗: {e}")
        return False, None

def main():
    """主函數"""
    print("🚀 自動設定 Notion 整合")
    print("=" * 50)
    
    # 初始化 Notion client
    try:
        notion = Client(auth=NOTION_TOKEN)
        print(f"✅ Notion 客戶端初始化成功")
    except Exception as e:
        print(f"❌ Notion 客戶端初始化失敗: {e}")
        return
    
    # 步驟1: 搜索頁面
    parent_page_id = find_page_by_name(notion, PARENT_PAGE_NAME)
    
    if not parent_page_id:
        print(f"❌ 找不到頁面 '{PARENT_PAGE_NAME}'")
        print("請確保:")
        print("1. 頁面名稱正確")
        print("2. 集成有權限訪問該頁面")
        print("3. 在頁面中邀請了您的集成")
        return
    
    print(f"✅ 找到頁面ID: {parent_page_id}")
    
    # 步驟2: 創建資料庫
    database_id = create_database_in_page(notion, parent_page_id)
    
    if not database_id:
        print("❌ 資料庫創建失敗")
        return
    
    # 步驟3: 測試連接
    success, _ = test_connection(notion, database_id)
    
    if success:
        print("\n🎉 Notion 整合設定完成!")
        print("請設定以下環境變數:")
        print(f"export NOTION_TOKEN=\"{NOTION_TOKEN}\"")
        print(f"export NOTION_DATABASE_ID=\"{database_id}\"")
        
        # 保存到配置文件
        config_content = f"""# Notion 配置
export NOTION_TOKEN="{NOTION_TOKEN}"
export NOTION_DATABASE_ID="{database_id}"
export NOTION_PARENT_PAGE_ID="{parent_page_id}"
"""
        
        with open('.notion_config.sh', 'w') as f:
            f.write(config_content)
        
        print("\n配置已保存到 .notion_config.sh")
        print("運行以下命令加載配置:")
        print("source .notion_config.sh")
        
    else:
        print("❌ 整合設定失敗")

if __name__ == "__main__":
    main()