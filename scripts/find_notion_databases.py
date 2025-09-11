#!/usr/bin/env python3
"""
查找和列出所有可訪問的 Notion 數據庫
"""

import os
import sys
from notion_client import Client
from dotenv import load_dotenv

# 加載 .env 文件
load_dotenv()

def main():
    """查找可用的數據庫"""
    
    print("🔍 查找可訪問的 Notion 數據庫")
    print("="*50)
    
    notion_token = os.getenv('NOTION_TOKEN')
    
    if not notion_token:
        print("❌ NOTION_TOKEN 未設置")
        return
    
    try:
        client = Client(auth=notion_token)
        
        print("1️⃣ 搜索所有可訪問的頁面和數據庫...")
        
        # 搜索所有可訪問的內容
        search_results = client.search(
            query="",
            sort={"direction": "descending", "timestamp": "last_edited_time"},
            page_size=100
        )
        
        results = search_results.get('results', [])
        
        print(f"📊 找到 {len(results)} 個可訪問的項目")
        
        databases = []
        pages = []
        
        for item in results:
            if item.get('object') == 'database':
                databases.append(item)
            elif item.get('object') == 'page':
                pages.append(item)
        
        print(f"📚 數據庫: {len(databases)} 個")
        print(f"📄 頁面: {len(pages)} 個")
        
        if databases:
            print(f"\n📚 可用的數據庫:")
            print("="*50)
            
            for i, db in enumerate(databases, 1):
                db_id = db.get('id')
                title_list = db.get('title', [])
                db_title = title_list[0].get('plain_text', '未命名數據庫') if title_list else '未命名數據庫'
                created_time = db.get('created_time', 'N/A')
                last_edited = db.get('last_edited_time', 'N/A')
                
                print(f"{i}. {db_title}")
                print(f"   ID: {db_id}")
                print(f"   創建時間: {created_time[:10] if created_time != 'N/A' else 'N/A'}")
                print(f"   最後編輯: {last_edited[:10] if last_edited != 'N/A' else 'N/A'}")
                
                # 檢查是否包含「財商」或相關關鍵字
                if any(keyword in db_title for keyword in ['財商', '成長', '思維', 'financial', 'wisdom']):
                    print(f"   🎯 這可能是您要找的數據庫!")
                    
                    # 嘗試獲取更多信息
                    try:
                        db_details = client.databases.retrieve(database_id=db_id)
                        properties = db_details.get('properties', {})
                        
                        print(f"   📋 屬性 ({len(properties)} 個):")
                        for prop_name, prop_config in list(properties.items())[:5]:
                            prop_type = prop_config.get('type', 'unknown')
                            print(f"      • {prop_name} ({prop_type})")
                        
                        if len(properties) > 5:
                            print(f"      ... 還有 {len(properties) - 5} 個屬性")
                            
                    except Exception as e:
                        print(f"   ⚠️  無法獲取詳細信息: {e}")
                
                print()
        
        else:
            print(f"\n❌ 沒有找到任何數據庫")
            print(f"💡 可能的原因:")
            print(f"1. 您的集成還沒有被邀請到任何數據庫")
            print(f"2. 「財商成長思維」可能是一個頁面而不是數據庫")
        
        if pages:
            print(f"\n📄 可用的頁面 (前10個):")
            print("="*50)
            
            for i, page in enumerate(pages[:10], 1):
                page_id = page.get('id')
                title_list = page.get('properties', {}).get('title', {}).get('title', [])
                
                # 嘗試不同方式提取標題
                page_title = ""
                if title_list:
                    page_title = title_list[0].get('plain_text', '')
                
                if not page_title:
                    # 嘗試從其他屬性提取
                    properties = page.get('properties', {})
                    for prop_name, prop_data in properties.items():
                        if prop_data.get('type') == 'title':
                            title_entries = prop_data.get('title', [])
                            if title_entries:
                                page_title = title_entries[0].get('plain_text', '')
                                break
                
                if not page_title:
                    page_title = "未命名頁面"
                
                print(f"{i}. {page_title}")
                print(f"   ID: {page_id}")
                
                # 檢查是否包含「財商」關鍵字
                if any(keyword in page_title for keyword in ['財商', '成長', '思維']):
                    print(f"   🎯 這可能包含您要找的內容!")
                
                print()
        
        # 提供建議
        print(f"\n💡 建議:")
        print("="*50)
        print("1. 如果您看到了「財商成長思維」相關的數據庫，複製其 ID")
        print("2. 如果只看到頁面，檢查該頁面是否包含數據庫")
        print("3. 如果什麼都沒看到，請確保:")
        print("   a) 在 Notion 中邀請您的集成")
        print("   b) 給予集成適當的權限")
        print("   c) 確認數據庫確實存在")
        
    except Exception as e:
        print(f"❌ 搜索失敗: {e}")

if __name__ == "__main__":
    main()