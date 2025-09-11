#!/usr/bin/env python3
"""
系統功能測試腳本
"""

import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "http://localhost:8000"

def test_health():
    """測試健康檢查"""
    print("🔍 測試健康檢查...")
    response = requests.get(f"{BASE_URL}/health")
    
    if response.status_code == 200:
        print("✅ 健康檢查通過")
        print(f"   回應: {response.json()}")
    else:
        print(f"❌ 健康檢查失敗: {response.status_code}")
    
    return response.status_code == 200

def test_static_files():
    """測試靜態文件服務"""
    print("\n🔍 測試靜態文件服務...")
    response = requests.get(f"{BASE_URL}/")
    
    if response.status_code == 200 and "財商成長思維" in response.text:
        print("✅ 靜態文件服務正常")
        print("   主頁面加載成功")
    else:
        print(f"❌ 靜態文件服務失敗: {response.status_code}")
    
    return response.status_code == 200

def test_notion_connection():
    """測試 Notion 連接"""
    print("\n🔍 測試 Notion 連接...")
    
    # 檢查環境變數
    notion_token = os.getenv('NOTION_TOKEN')
    database_id = os.getenv('NOTION_DATABASE_ID')
    
    if not notion_token or not database_id:
        print("⚠️  Notion 環境變數未設置，跳過 Notion 測試")
        return True
    
    try:
        # 測試統計端點
        response = requests.get(f"{BASE_URL}/api/v1/financial-wisdom/stats")
        
        if response.status_code == 200:
            stats = response.json()
            print("✅ Notion 連接成功")
            print(f"   總文章數: {stats.get('total_articles', 0)}")
            print(f"   總字數: {stats.get('total_words', 0)}")
            return True
        else:
            print(f"❌ Notion 連接失敗: {response.status_code}")
            if response.text:
                print(f"   錯誤詳情: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Notion 連接異常: {e}")
        return False

def test_article_listing():
    """測試文章列表"""
    print("\n🔍 測試文章列表...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/v1/financial-wisdom/articles")
        
        if response.status_code == 200:
            data = response.json()
            articles = data.get('articles', [])
            print(f"✅ 文章列表獲取成功")
            print(f"   找到 {len(articles)} 篇文章")
            
            if articles:
                first_article = articles[0]
                print(f"   第一篇文章: {first_article.get('title', 'N/A')}")
            
            return True
        else:
            print(f"❌ 文章列表獲取失敗: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 文章列表獲取異常: {e}")
        return False

def test_categories():
    """測試分類獲取"""
    print("\n🔍 測試分類獲取...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/v1/financial-wisdom/categories")
        
        if response.status_code == 200:
            data = response.json()
            categories = data.get('categories', [])
            print(f"✅ 分類獲取成功")
            print(f"   找到 {len(categories)} 個分類: {', '.join(categories)}")
            return True
        else:
            print(f"❌ 分類獲取失敗: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 分類獲取異常: {e}")
        return False

def test_article_generation():
    """測試文章生成"""
    print("\n🔍 測試文章生成...")
    
    # 檢查是否有 AI API 密鑰
    anthropic_key = os.getenv('ANTHROPIC_API_KEY')
    
    if not anthropic_key:
        print("⚠️  ANTHROPIC_API_KEY 未設置，跳過文章生成測試")
        return True
    
    try:
        payload = {
            "title": "測試：複利思維的實戰應用",
            "topic": "探討複利思維在日常生活和投資中的具體應用方法",
            "target_audience": "一般投資者",
            "writing_style": "實用智慧",
            "word_count_target": 800,
            "include_case_study": True,
            "focus_areas": ["複利效應", "長期思維"]
        }
        
        print("   發送文章生成請求...")
        response = requests.post(
            f"{BASE_URL}/api/v1/financial-wisdom/generate",
            json=payload,
            timeout=60  # 60秒超時
        )
        
        if response.status_code == 200:
            article = response.json()
            print("✅ 文章生成成功")
            print(f"   標題: {article.get('title', 'N/A')}")
            print(f"   字數: {article.get('word_count', 0)}")
            print(f"   品質分數: {article.get('quality_score', 0)}")
            return True
        else:
            print(f"❌ 文章生成失敗: {response.status_code}")
            if response.text:
                print(f"   錯誤詳情: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 文章生成異常: {e}")
        return False

def main():
    """主測試函數"""
    print("🚀 財商成長思維平台系統測試")
    print("=" * 50)
    
    tests = [
        test_health,
        test_static_files,
        test_notion_connection,
        test_article_listing,
        test_categories,
        test_article_generation
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        if test_func():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 測試結果: {passed}/{total} 通過")
    
    if passed == total:
        print("🎉 所有測試通過！系統運行正常")
    else:
        print(f"⚠️  {total - passed} 個測試失敗，請檢查相關配置")
    
    # 提供使用指南
    print("\n💡 使用指南:")
    print(f"1. 訪問網站: {BASE_URL}")
    print("2. 在瀏覽器中打開上述網址即可使用完整功能")
    print("3. 確保 .env 文件中設置了正確的 API 密鑰")

if __name__ == "__main__":
    main()