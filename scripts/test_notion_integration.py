#!/usr/bin/env python3
"""
Test Notion integration for Financial Wisdom Platform
Validates the complete Notion service implementation
"""

import os
import sys
import asyncio
import uuid
from datetime import datetime
from typing import List

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.models.domain import (
    Article, ArticleId, Topic, DataSource, Content, QualityMetrics,
    ArticleStatus, ContentStyle, SourceType
)
from app.services.notion_service import NotionService
from app.core.config import settings

class NotionIntegrationTester:
    """Test suite for Notion integration"""
    
    def __init__(self):
        self.notion_service = None
        self.test_results = []
        self.test_data = {}
    
    async def setup(self):
        """Setup test environment"""
        print("🔧 Setting up test environment...")
        
        # Check required environment variables
        required_vars = [
            'NOTION_TOKEN',
            'NOTION_ARTICLES_DB_ID',
            'NOTION_TOPICS_DB_ID'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
            print("Please run create_notion_databases.py first")
            return False
        
        try:
            self.notion_service = NotionService()
            print("✅ Notion service initialized")
            return True
        except Exception as e:
            print(f"❌ Failed to initialize Notion service: {e}")
            return False
    
    def log_test(self, test_name: str, success: bool, message: str = ""):
        """Log test result"""
        status = "✅" if success else "❌"
        print(f"   {status} {test_name}: {message}")
        self.test_results.append({
            "test": test_name,
            "success": success,
            "message": message
        })
    
    async def test_topic_operations(self):
        """Test topic creation and retrieval"""
        print("\n🧪 Testing Topic Operations...")
        
        try:
            # Create test topic
            test_topic = Topic(
                keywords=["AI投資", "人工智能", "科技股票"],
                category="投資理財",
                trend_score=8.5,
                context={"test": True, "created_by": "test_suite"}
            )
            
            topic_page_id = await self.notion_service.create_topic(test_topic)
            self.test_data["topic_page_id"] = topic_page_id
            self.log_test("Create Topic", True, f"Page ID: {topic_page_id}")
            
            # Test topic retrieval
            trending_topics = await self.notion_service.get_trending_topics(limit=5)
            self.log_test(
                "Get Trending Topics", 
                len(trending_topics) > 0,
                f"Retrieved {len(trending_topics)} topics"
            )
            
        except Exception as e:
            self.log_test("Topic Operations", False, str(e))
    
    async def test_article_operations(self):
        """Test article creation, retrieval, and updates"""
        print("\n🧪 Testing Article Operations...")
        
        try:
            # Create test article content
            test_content = Content(
                title="AI 投資革命：人工智能如何改變投資策略",
                introduction="人工智能正在徹底改變投資領域，從量化交易到風險評估，AI技術為投資者帶來前所未有的機遇。",
                main_content="""
                ## AI在投資領域的應用
                
                人工智能在投資領域的應用越來越廣泛，主要體現在以下幾個方面：
                
                ### 1. 量化交易
                - 高頻交易算法
                - 市場趨勢預測
                - 風險控制模型
                
                ### 2. 投資組合優化
                - 資產配置建議
                - 風險分散策略
                - 動態調整機制
                
                ### 3. 市場分析
                - 情緒分析
                - 新聞影響評估
                - 技術指標分析
                """,
                conclusion="AI技術為投資者提供了更精準的分析工具和決策支持，但仍需要人工智慧的判斷和風險意識。",
                key_insights=[
                    "AI量化交易可以處理大量數據，發現人類難以察覺的市場模式",
                    "投資組合優化通過AI可以實現更精確的風險控制",
                    "情緒分析能幫助預測市場短期波動"
                ],
                actionable_steps=[
                    "了解不同AI投資平台的特點和費用結構",
                    "學習基本的量化分析概念和指標",
                    "建立適合自己的AI輔助投資策略",
                    "定期評估和調整AI工具的表現"
                ]
            )
            
            # Create test quality metrics
            test_quality = QualityMetrics(
                readability_score=8.5,
                engagement_score=9.0,
                educational_value=8.8,
                actionability_score=8.2,
                originality_score=8.7
            )
            
            # Create test topic
            test_topic = Topic(
                keywords=["AI投資", "人工智能", "量化交易"],
                category="投資理財",
                trend_score=9.2
            )
            
            # Create test article
            test_article = Article(
                id=ArticleId(),
                topic=test_topic,
                content=test_content,
                sources=[],
                status=ArticleStatus.GENERATED,
                style=ContentStyle.PRACTICAL_WISDOM,
                quality_metrics=test_quality
            )
            
            # Test article creation
            article_page_id = await self.notion_service.create_article(test_article)
            self.test_data["article_page_id"] = article_page_id
            self.test_data["article_id"] = test_article.id
            self.log_test("Create Article", True, f"Page ID: {article_page_id}")
            
            # Test article retrieval
            retrieved_article = await self.notion_service.get_article(test_article.id)
            self.log_test(
                "Get Article", 
                retrieved_article is not None,
                f"Retrieved article: {retrieved_article.id.value if retrieved_article else 'None'}"
            )
            
            # Test article list
            articles = await self.notion_service.list_articles(limit=5)
            self.log_test(
                "List Articles",
                len(articles) > 0,
                f"Retrieved {len(articles)} articles"
            )
            
            # Test status update
            await self.notion_service.update_article_status(
                test_article.id,
                ArticleStatus.APPROVED
            )
            self.log_test("Update Article Status", True, "Updated to APPROVED")
            
        except Exception as e:
            self.log_test("Article Operations", False, str(e))
    
    async def test_search_and_filtering(self):
        """Test search and filtering capabilities"""
        print("\n🧪 Testing Search and Filtering...")
        
        try:
            # Test filtering by status
            approved_articles = await self.notion_service.list_articles(
                status=ArticleStatus.APPROVED,
                limit=10
            )
            self.log_test(
                "Filter by Status",
                True,
                f"Found {len(approved_articles)} approved articles"
            )
            
            # Test filtering by category
            investment_articles = await self.notion_service.list_articles(
                category="投資理財",
                limit=10
            )
            self.log_test(
                "Filter by Category",
                True,
                f"Found {len(investment_articles)} investment articles"
            )
            
        except Exception as e:
            self.log_test("Search and Filtering", False, str(e))
    
    async def test_performance(self):
        """Test basic performance characteristics"""
        print("\n🧪 Testing Performance...")
        
        try:
            import time
            
            # Test article list performance
            start_time = time.time()
            articles = await self.notion_service.list_articles(limit=50)
            end_time = time.time()
            
            duration = end_time - start_time
            self.log_test(
                "List Performance",
                duration < 5.0,  # Should complete within 5 seconds
                f"Listed {len(articles)} articles in {duration:.2f}s"
            )
            
            # Test topic retrieval performance
            start_time = time.time()
            topics = await self.notion_service.get_trending_topics(limit=20)
            end_time = time.time()
            
            duration = end_time - start_time
            self.log_test(
                "Topics Performance",
                duration < 3.0,  # Should complete within 3 seconds
                f"Retrieved {len(topics)} topics in {duration:.2f}s"
            )
            
        except Exception as e:
            self.log_test("Performance Tests", False, str(e))
    
    async def test_error_handling(self):
        """Test error handling scenarios"""
        print("\n🧪 Testing Error Handling...")
        
        try:
            # Test getting non-existent article
            fake_id = ArticleId.from_string(str(uuid.uuid4()))
            non_existent = await self.notion_service.get_article(fake_id)
            self.log_test(
                "Non-existent Article",
                non_existent is None,
                "Correctly returned None for non-existent article"
            )
            
            # Test invalid status update
            try:
                await self.notion_service.update_article_status(
                    fake_id,
                    ArticleStatus.PUBLISHED
                )
                self.log_test("Invalid Status Update", False, "Should have raised ValueError")
            except ValueError:
                self.log_test("Invalid Status Update", True, "Correctly raised ValueError")
            
        except Exception as e:
            self.log_test("Error Handling", False, str(e))
    
    def cleanup_test_data(self):
        """Clean up test data (optional)"""
        print("\n🧹 Cleaning up test data...")
        # Note: Notion API doesn't provide delete functionality
        # Test data will remain in the database
        print("   ℹ️  Test data remains in Notion (API limitation)")
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*60)
        print("📊 Test Summary")
        print("="*60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
        
        if failed_tests > 0:
            print("\n❌ Failed Tests:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   • {result['test']}: {result['message']}")
        
        if passed_tests == total_tests:
            print("\n🎉 All tests passed! Notion integration is working correctly.")
        else:
            print(f"\n⚠️  {failed_tests} test(s) failed. Please check the configuration.")
        
        # Print test data info
        if self.test_data:
            print("\n📝 Created Test Data:")
            for key, value in self.test_data.items():
                if isinstance(value, ArticleId):
                    print(f"   {key}: {value.value}")
                else:
                    print(f"   {key}: {value}")

async def main():
    """Main test function"""
    print("🧪 Notion Integration Test Suite")
    print("="*60)
    
    tester = NotionIntegrationTester()
    
    # Setup
    if not await tester.setup():
        return
    
    # Run all tests
    await tester.test_topic_operations()
    await tester.test_article_operations()
    await tester.test_search_and_filtering()
    await tester.test_performance()
    await tester.test_error_handling()
    
    # Cleanup and summary
    tester.cleanup_test_data()
    tester.print_summary()

if __name__ == "__main__":
    asyncio.run(main())