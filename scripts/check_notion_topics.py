#!/usr/bin/env python3
"""
檢查 Notion 數據庫中的主題和內容
"""

import os
import sys
from notion_client import Client
import json
from datetime import datetime
from dotenv import load_dotenv

# 加載 .env 文件
load_dotenv()

def main():
    """檢查數據庫主題"""
    
    print("🔍 檢查 Notion 數據庫主題")
    print("="*50)
    
    # 檢查環境變數
    notion_token = os.getenv('NOTION_TOKEN')
    database_id = os.getenv('NOTION_DATABASE_ID')
    
    if not notion_token:
        print("❌ 請先設置 NOTION_TOKEN")
        print("\n💡 設置步驟:")
        print("1. 前往: https://www.notion.so/my-integrations")
        print("2. 創建新集成或使用現有集成")
        print("3. 複製 Integration Token")
        print("4. 運行: export NOTION_TOKEN='secret_your_token'")
        return
    
    if not database_id:
        print("❌ 請先設置 NOTION_DATABASE_ID")
        print("\n💡 獲取數據庫 ID 步驟:")
        print("1. 打開您的「財商成長思維」Notion 頁面")
        print("2. 點擊頁面右上角的 '...' 按鈕")
        print("3. 選擇 'Copy link'")
        print("4. 從 URL 中提取 32 位數據庫 ID")
        print("5. 運行: export NOTION_DATABASE_ID='your_database_id'")
        
        # 提供互動式輸入
        print("\n" + "="*50)
        user_token = input("您也可以現在輸入 Token (或按 Enter 跳過): ").strip()
        if user_token:
            user_db_id = input("請輸入數據庫 ID: ").strip()
            if user_db_id:
                notion_token = user_token
                database_id = user_db_id
            else:
                return
        else:
            return
    
    try:
        print(f"🔗 連接到數據庫: {database_id[:8]}...")
        
        # 初始化 Notion 客戶端
        client = Client(auth=notion_token)
        
        # 獲取數據庫信息
        database = client.databases.retrieve(database_id=database_id)
        
        # 提取數據庫標題
        title_list = database.get('title', [])
        db_title = title_list[0].get('plain_text', '未命名數據庫') if title_list else '未命名數據庫'
        
        print(f"✅ 數據庫: {db_title}")
        
        # 獲取數據庫內容
        print(f"\n📋 查詢數據庫內容...")
        
        pages_result = client.databases.query(
            database_id=database_id,
            page_size=100  # 獲取更多內容
        )
        
        pages = pages_result.get('results', [])
        print(f"📊 找到 {len(pages)} 個條目")
        
        if not pages:
            print("📭 數據庫目前是空的")
            return
        
        # 分析內容
        print(f"\n🎯 主題分析:")
        print("="*50)
        
        topics = []
        categories = {}
        keywords = {}
        statuses = {}
        
        for i, page in enumerate(pages):
            properties = page.get('properties', {})
            
            # 提取信息
            title = ""
            category = ""
            page_keywords = []
            status = ""
            
            for prop_name, prop_data in properties.items():
                prop_type = prop_data.get('type')
                
                # 標題
                if prop_type == 'title':
                    title_list = prop_data.get('title', [])
                    if title_list:
                        title = title_list[0].get('plain_text', '')
                
                # 分類/類別
                elif prop_type == 'select':
                    select_obj = prop_data.get('select')
                    if select_obj:
                        value = select_obj.get('name', '')
                        # 判斷是否為分類欄位
                        if any(keyword in prop_name for keyword in ['分類', '類別', 'category', 'Category']):
                            category = value
                        # 判斷是否為狀態欄位  
                        elif any(keyword in prop_name for keyword in ['狀態', '狀況', 'status', 'Status']):
                            status = value
                
                # 關鍵字/標籤
                elif prop_type == 'multi_select':
                    multi_list = prop_data.get('multi_select', [])
                    if any(keyword in prop_name for keyword in ['關鍵字', '標籤', 'keyword', 'tag', 'Tag']):
                        page_keywords = [item.get('name', '') for item in multi_list]
            
            # 統計
            if category:
                categories[category] = categories.get(category, 0) + 1
            if status:
                statuses[status] = statuses.get(status, 0) + 1
            for kw in page_keywords:
                if kw:
                    keywords[kw] = keywords.get(kw, 0) + 1
            
            # 收集主題
            topics.append({
                'title': title,
                'category': category,
                'status': status,
                'keywords': page_keywords
            })
        
        # 顯示統計結果
        if categories:
            print("\n📂 主題分類統計:")
            for category, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
                print(f"   • {category}: {count} 篇")
        
        if statuses:
            print("\n📊 狀態統計:")
            for status, count in sorted(statuses.items(), key=lambda x: x[1], reverse=True):
                print(f"   • {status}: {count} 篇")
        
        if keywords:
            print("\n🏷️ 熱門關鍵字 (前10個):")
            sorted_keywords = sorted(keywords.items(), key=lambda x: x[1], reverse=True)[:10]
            for keyword, count in sorted_keywords:
                print(f"   • {keyword}: {count} 次")
        
        # 顯示最近的文章
        print(f"\n📰 最近的文章 (前10篇):")
        print("="*50)
        
        for i, topic in enumerate(topics[:10], 1):
            print(f"{i:2d}. {topic['title'][:50]}...")
            if topic['category']:
                print(f"     分類: {topic['category']}")
            if topic['status']:
                print(f"     狀態: {topic['status']}")
            if topic['keywords']:
                print(f"     關鍵字: {', '.join(topic['keywords'][:3])}...")
            print()
        
        # 保存分析結果
        analysis_result = {
            'database_title': db_title,
            'total_entries': len(pages),
            'categories': categories,
            'statuses': statuses,
            'keywords': keywords,
            'recent_topics': topics[:20],
            'analysis_time': datetime.now().isoformat()
        }
        
        # 保存到文件
        with open('notion_topics_analysis.json', 'w', encoding='utf-8') as f:
            json.dump(analysis_result, f, ensure_ascii=False, indent=2)
        
        print(f"💾 分析結果已保存到: notion_topics_analysis.json")
        
    except Exception as e:
        print(f"❌ 錯誤: {e}")
        print("\n💡 可能的解決方案:")
        print("1. 檢查 Token 是否正確")
        print("2. 確認數據庫 ID 是否正確")
        print("3. 確保集成有訪問數據庫的權限")

if __name__ == "__main__":
    main()