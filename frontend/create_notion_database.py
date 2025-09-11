#!/usr/bin/env python3
"""
創建Notion資料庫用於儲存金融智慧文章
"""

import os
from notion_client import Client
import sys

def create_articles_database(notion_token, parent_page_id):
    """
    創建文章資料庫
    
    Args:
        notion_token: Notion API token
        parent_page_id: 父頁面ID（資料庫將在此頁面下創建）
    
    Returns:
        str: 創建的資料庫ID
    """
    notion = Client(auth=notion_token)
    
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
        "可讀性評分": {
            "number": {
                "format": "number_with_commas"
            }
        },
        "參與度評分": {
            "number": {
                "format": "number_with_commas"
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
                    {"name": "房地產", "color": "brown"},
                    {"name": "理性投資", "color": "default"},
                    {"name": "長期價值", "color": "blue"},
                    {"name": "風險控制", "color": "red"}
                ]
            }
        },
        "狀態": {
            "select": {
                "options": [
                    {"name": "草稿", "color": "gray"},
                    {"name": "已發布", "color": "green"},
                    {"name": "存檔", "color": "red"}
                ]
            }
        }
    }
    
    try:
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

def main():
    """主函數"""
    print("🚀 創建Notion金融智慧文章資料庫")
    print("=" * 50)
    
    # 檢查環境變數
    notion_token = os.getenv('NOTION_TOKEN')
    parent_page_id = os.getenv('NOTION_PARENT_PAGE_ID')
    
    if not notion_token:
        print("❌ 錯誤: NOTION_TOKEN環境變數未設定")
        print("\n請按照以下步驟設定:")
        print("1. 前往 https://www.notion.so/my-integrations")
        print("2. 點擊 'New integration' 創建新的集成")
        print("3. 複製 Internal Integration Token")
        print("4. 設定環境變數: export NOTION_TOKEN=your_token_here")
        sys.exit(1)
    
    if not parent_page_id:
        print("❌ 錯誤: NOTION_PARENT_PAGE_ID環境變數未設定")
        print("\n請按照以下步驟獲取頁面ID:")
        print("1. 在Notion中創建一個新頁面（或使用現有頁面）")
        print("2. 點擊右上角的 'Share' 按鈕")
        print("3. 點擊 'Copy link' 獲取頁面連結")
        print("4. 從URL中提取頁面ID（32字符的字符串）")
        print("5. 設定環境變數: export NOTION_PARENT_PAGE_ID=your_page_id")
        print("6. 記得要將集成添加到該頁面的訪問權限中!")
        sys.exit(1)
    
    print(f"📝 使用的Token: {notion_token[:10]}...")
    print(f"📄 父頁面ID: {parent_page_id}")
    
    # 創建資料庫
    database_id = create_articles_database(notion_token, parent_page_id)
    
    if database_id:
        print(f"\n🎉 設定完成!")
        print(f"請設定以下環境變數以在應用中使用:")
        print(f"export NOTION_DATABASE_ID={database_id}")
        print(f"\n您現在可以使用notion_config.py來管理文章了!")
    else:
        print(f"\n❌ 設定失敗，請檢查:")
        print(f"1. Notion Token是否正確")
        print(f"2. 父頁面ID是否正確")
        print(f"3. 集成是否有權限訪問該頁面")

if __name__ == "__main__":
    main()