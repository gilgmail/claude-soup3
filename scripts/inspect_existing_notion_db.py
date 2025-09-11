#!/usr/bin/env python3
"""
檢查現有的「財商成長思維」Notion 數據庫結構
分析屬性和內容以調整服務代碼
"""

import os
import sys
from notion_client import Client
import json

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def inspect_notion_database(client: Client, database_id: str):
    """檢查 Notion 數據庫結構"""
    
    try:
        print(f"🔍 正在檢查數據庫: {database_id}")
        
        # 獲取數據庫信息
        database = client.databases.retrieve(database_id=database_id)
        
        print(f"\n📊 數據庫名稱: {get_database_title(database)}")
        print(f"📅 創建時間: {database.get('created_time', 'N/A')}")
        print(f"🆔 數據庫 ID: {database_id}")
        
        # 分析屬性結構
        properties = database.get('properties', {})
        
        print(f"\n🏗️ 屬性結構 ({len(properties)} 個屬性):")
        print("="*60)
        
        for prop_name, prop_config in properties.items():
            prop_type = prop_config.get('type', 'unknown')
            print(f"• {prop_name} ({prop_type})")
            
            # 詳細顯示選項型屬性
            if prop_type == 'select' and 'select' in prop_config:
                options = prop_config['select'].get('options', [])
                if options:
                    print(f"  選項: {[opt['name'] for opt in options]}")
            elif prop_type == 'multi_select' and 'multi_select' in prop_config:
                options = prop_config['multi_select'].get('options', [])
                if options:
                    print(f"  選項: {[opt['name'] for opt in options]}")
        
        # 獲取數據庫內容樣本
        print(f"\n📋 內容樣本:")
        print("="*60)
        
        try:
            pages = client.databases.query(
                database_id=database_id,
                page_size=5  # 只獲取前5條記錄
            )
            
            if pages.get('results'):
                for i, page in enumerate(pages['results'][:3], 1):  # 顯示前3條
                    page_props = page.get('properties', {})
                    
                    # 提取標題
                    title = "未命名"
                    for prop_name, prop_data in page_props.items():
                        if prop_data.get('type') == 'title':
                            title_list = prop_data.get('title', [])
                            if title_list:
                                title = title_list[0].get('plain_text', '未命名')
                            break
                    
                    print(f"{i}. {title}")
                    
                    # 顯示其他重要屬性
                    for prop_name, prop_data in page_props.items():
                        if prop_data.get('type') in ['select', 'multi_select', 'number', 'date']:
                            value = extract_property_value(prop_data)
                            if value:
                                print(f"   {prop_name}: {value}")
                    print()
                
                print(f"總共有 {len(pages.get('results', []))} 條記錄 (僅顯示前3條)")
            else:
                print("數據庫為空")
        
        except Exception as e:
            print(f"⚠️  無法讀取內容: {e}")
        
        return database
        
    except Exception as e:
        print(f"❌ 檢查數據庫失敗: {e}")
        return None

def get_database_title(database):
    """提取數據庫標題"""
    title_list = database.get('title', [])
    if title_list:
        return title_list[0].get('plain_text', '未命名數據庫')
    return '未命名數據庫'

def extract_property_value(prop_data):
    """提取屬性值"""
    prop_type = prop_data.get('type')
    
    if prop_type == 'select':
        select_obj = prop_data.get('select')
        return select_obj.get('name') if select_obj else None
    
    elif prop_type == 'multi_select':
        multi_select_list = prop_data.get('multi_select', [])
        return [item.get('name') for item in multi_select_list]
    
    elif prop_type == 'number':
        return prop_data.get('number')
    
    elif prop_type == 'date':
        date_obj = prop_data.get('date')
        return date_obj.get('start') if date_obj else None
    
    elif prop_type == 'checkbox':
        return prop_data.get('checkbox')
    
    elif prop_type == 'rich_text':
        rich_text_list = prop_data.get('rich_text', [])
        if rich_text_list:
            return rich_text_list[0].get('plain_text')
        return None
    
    return None

def generate_config_suggestions(database):
    """根據數據庫結構生成配置建議"""
    if not database:
        return
        
    properties = database.get('properties', {})
    
    print(f"\n💡 配置建議:")
    print("="*60)
    
    print("建議的環境變數配置:")
    database_id = database.get('id')
    print(f"export NOTION_DATABASE_ID=\"{database_id}\"")
    
    # 分析可能的映射
    title_props = []
    status_props = []
    category_props = []
    
    for prop_name, prop_config in properties.items():
        prop_type = prop_config.get('type')
        
        if prop_type == 'title':
            title_props.append(prop_name)
        elif prop_type == 'select':
            options = prop_config.get('select', {}).get('options', [])
            option_names = [opt.get('name', '') for opt in options]
            
            # 檢查是否像狀態欄位
            status_keywords = ['草稿', '發布', '完成', 'draft', 'published', 'status']
            if any(keyword in ''.join(option_names).lower() for keyword in status_keywords):
                status_props.append((prop_name, option_names))
            else:
                category_props.append((prop_name, option_names))
    
    print(f"\n檢測到的欄位類型:")
    print(f"• 標題欄位: {title_props}")
    print(f"• 狀態類欄位: {status_props}")  
    print(f"• 分類類欄位: {category_props}")

def main():
    """主函數"""
    print("🔍 Notion 數據庫結構檢查工具")
    print("="*60)
    
    # 檢查環境變數
    notion_token = os.getenv('NOTION_TOKEN')
    if not notion_token:
        print("❌ 錯誤: NOTION_TOKEN 環境變數未設定")
        print("請設定: export NOTION_TOKEN=your_token")
        return
    
    # 獲取數據庫 ID
    database_id = os.getenv('NOTION_DATABASE_ID')
    if not database_id:
        print("⚠️  NOTION_DATABASE_ID 未設定")
        database_id = input("請輸入您的「財商成長思維」數據庫 ID: ").strip()
        
        if not database_id:
            print("❌ 必須提供數據庫 ID")
            return
    
    try:
        # 初始化 Notion 客戶端
        client = Client(auth=notion_token)
        print(f"✅ Notion 客戶端初始化成功")
        
        # 檢查數據庫
        database = inspect_notion_database(client, database_id)
        
        # 生成配置建議
        generate_config_suggestions(database)
        
    except Exception as e:
        print(f"❌ 初始化失敗: {e}")

if __name__ == "__main__":
    main()