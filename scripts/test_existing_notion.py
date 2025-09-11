#!/usr/bin/env python3
"""
測試與現有「財商成長思維」Notion 數據庫的集成
"""

import os
import sys
import asyncio
from datetime import datetime

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.simple_notion_service import SimpleNotionService

class ExistingNotionTester:
    """測試現有 Notion 數據庫集成"""
    
    def __init__(self):
        self.service = None
        self.test_results = []
    
    async def setup(self):
        """設置測試環境"""
        print("🔧 設置測試環境...")
        
        # 檢查環境變數
        notion_token = os.getenv('NOTION_TOKEN')
        database_id = os.getenv('NOTION_DATABASE_ID')
        
        if not notion_token:
            print("❌ NOTION_TOKEN 環境變數未設定")
            return False
            
        if not database_id:
            print("❌ NOTION_DATABASE_ID 環境變數未設定") 
            return False
        
        try:
            self.service = SimpleNotionService(notion_token, database_id)
            print("✅ Notion 服務初始化成功")
            return True
        except Exception as e:
            print(f"❌ 初始化失敗: {e}")
            return False
    
    def log_test(self, test_name: str, success: bool, message: str = ""):
        """記錄測試結果"""
        status = "✅" if success else "❌"
        print(f"   {status} {test_name}: {message}")
        self.test_results.append({
            "test": test_name, 
            "success": success,
            "message": message
        })
    
    async def test_connection(self):
        """測試連接"""
        print("\n🧪 測試 Notion 連接...")
        
        try:
            result = await self.service.test_connection()
            
            if result['success']:
                self.log_test(
                    "Connection Test",
                    True,
                    f"數據庫: {result['database_title']}"
                )
                print(f"     • 數據庫 ID: {result['database_id']}")
                print(f"     • 屬性數量: {result['properties_count']}")
                print(f"     • 創建時間: {result['created_time']}")
            else:
                self.log_test("Connection Test", False, result['error'])
                
        except Exception as e:
            self.log_test("Connection Test", False, str(e))
    
    async def test_database_structure(self):
        """測試數據庫結構檢查"""
        print("\n🧪 檢查數據庫結構...")
        
        try:
            structure = await self.service.inspect_database_structure()
            
            self.log_test(
                "Database Structure",
                True,
                f"發現 {len(structure['properties'])} 個屬性"
            )
            
            print("     📊 數據庫屬性:")
            for prop_name, prop_config in structure['properties'].items():
                prop_type = prop_config.get('type', 'unknown')
                print(f"        • {prop_name} ({prop_type})")
                
                # 顯示選項
                if prop_type == 'select':
                    options = prop_config.get('select', {}).get('options', [])
                    if options:
                        option_names = [opt['name'] for opt in options[:3]]
                        print(f"          選項: {option_names}...")
                elif prop_type == 'multi_select':
                    options = prop_config.get('multi_select', {}).get('options', [])
                    if options:
                        option_names = [opt['name'] for opt in options[:3]] 
                        print(f"          選項: {option_names}...")
        
        except Exception as e:
            self.log_test("Database Structure", False, str(e))
    
    async def test_create_sample_entry(self):
        """測試創建範例條目"""
        print("\n🧪 創建範例文章...")
        
        sample_data = {
            "title": f"測試文章 - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "content": """
            這是一篇測試文章，用於驗證 Notion 數據庫集成功能。
            
            ## 測試內容
            
            - 標題映射測試
            - 內容添加測試
            - 屬性映射測試
            
            這篇文章將幫助驗證系統是否能正確地與現有的「財商成長思維」數據庫集成。
            """,
            "summary": "這是用於測試 Notion 集成功能的範例文章",
            "category": "測試分類",
            "keywords": ["測試", "集成", "Notion"],
            "quality_score": 8.0,
            "word_count": 150,
            "status": "測試",
            "style": "測試風格",
            "featured": False,
            "completed": False
        }
        
        try:
            notion_id = await self.service.create_article_entry(sample_data)
            
            self.log_test(
                "Create Sample Entry",
                True,
                f"頁面 ID: {notion_id[:8]}..."
            )
            
            print(f"     🔗 Notion URL: https://notion.so/{notion_id.replace('-', '')}")
            return notion_id
            
        except Exception as e:
            self.log_test("Create Sample Entry", False, str(e))
            return None
    
    async def test_query_entries(self):
        """測試查詢條目"""
        print("\n🧪 查詢現有條目...")
        
        try:
            entries = await self.service.query_entries(limit=5)
            
            self.log_test(
                "Query Entries",
                True,
                f"查詢到 {len(entries)} 個條目"
            )
            
            if entries:
                print("     📋 條目樣本:")
                for i, entry in enumerate(entries[:3], 1):
                    # 尋找標題欄位
                    title = "未知標題"
                    for key, value in entry.items():
                        if key != 'notion_id' and key != 'url' and isinstance(value, str) and value:
                            title = value[:50]
                            break
                    
                    print(f"        {i}. {title}")
                    print(f"           ID: {entry.get('notion_id', 'N/A')[:8]}...")
            
        except Exception as e:
            self.log_test("Query Entries", False, str(e))
    
    async def test_property_mapping(self):
        """測試屬性映射"""
        print("\n🧪 測試屬性映射...")
        
        test_cases = [
            {
                "title": "屬性映射測試 - 基本類型",
                "category": "投資理財", 
                "keywords": ["投資", "理財", "測試"],
                "quality_score": 9.5,
                "status": "已完成"
            },
            {
                "title": "屬性映射測試 - 中文欄位",
                "分類": "數字貨幣",
                "關鍵字": ["比特幣", "區塊鏈"],
                "評分": 8.8,
                "狀態": "草稿"
            }
        ]
        
        success_count = 0
        for i, test_data in enumerate(test_cases, 1):
            try:
                notion_id = await self.service.create_article_entry(test_data)
                print(f"     ✅ 測試案例 {i}: 成功創建 ({notion_id[:8]}...)")
                success_count += 1
            except Exception as e:
                print(f"     ❌ 測試案例 {i}: {e}")
        
        self.log_test(
            "Property Mapping",
            success_count == len(test_cases),
            f"{success_count}/{len(test_cases)} 測試案例成功"
        )
    
    def print_summary(self):
        """打印測試摘要"""
        print("\n" + "="*60)
        print("📊 測試摘要")
        print("="*60)
        
        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r["success"])
        failed = total - passed
        
        print(f"總測試數: {total}")
        print(f"✅ 通過: {passed}")
        print(f"❌ 失敗: {failed}")
        print(f"成功率: {(passed/total*100):.1f}%")
        
        if failed > 0:
            print("\n❌ 失敗的測試:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   • {result['test']}: {result['message']}")
        
        if passed == total:
            print("\n🎉 所有測試通過！您的 Notion 數據庫集成正常工作。")
        else:
            print(f"\n⚠️  {failed} 個測試失敗，請檢查配置或數據庫權限。")

async def main():
    """主測試函數"""
    print("🧪 現有 Notion 數據庫集成測試")
    print("="*60)
    
    tester = ExistingNotionTester()
    
    # 設置
    if not await tester.setup():
        print("\n❌ 測試設置失敗")
        print("\n設置說明:")
        print("1. export NOTION_TOKEN='your_notion_token'")
        print("2. export NOTION_DATABASE_ID='your_database_id'")
        return
    
    # 運行測試
    await tester.test_connection()
    await tester.test_database_structure()
    await tester.test_create_sample_entry()
    await tester.test_query_entries()
    await tester.test_property_mapping()
    
    # 總結
    tester.print_summary()

if __name__ == "__main__":
    asyncio.run(main())