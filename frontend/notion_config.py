#!/usr/bin/env python3
"""
Notion API配置和資料庫連接器
管理文章資料的Notion儲存
"""

import os
from notion_client import Client
from datetime import datetime
import uuid
import logging

# 配置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NotionArticleDatabase:
    def __init__(self, notion_token=None, database_id=None):
        """
        初始化Notion文章資料庫連接器
        
        Args:
            notion_token: Notion API token
            database_id: Notion資料庫ID
        """
        self.notion_token = notion_token or os.getenv('NOTION_TOKEN')
        self.database_id = database_id or os.getenv('NOTION_DATABASE_ID')
        
        if not self.notion_token:
            raise ValueError("NOTION_TOKEN環境變數必須設定")
        if not self.database_id:
            raise ValueError("NOTION_DATABASE_ID環境變數必須設定")
            
        self.notion = Client(auth=self.notion_token)
        logger.info(f"✅ Notion客戶端初始化成功")
    
    def create_article(self, article_data):
        """
        在Notion資料庫中創建新文章
        
        Args:
            article_data: 文章資料字典
            
        Returns:
            dict: 創建的頁面資訊
        """
        try:
            # 準備頁面屬性
            properties = {
                "標題": {
                    "title": [
                        {
                            "text": {
                                "content": article_data.get('title', '未命名文章')
                            }
                        }
                    ]
                },
                "主題分類": {
                    "select": {
                        "name": article_data.get('topic_category', '投資理財')
                    }
                },
                "內容風格": {
                    "select": {
                        "name": article_data.get('content_style', '實用智慧')
                    }
                },
                "品質評分": {
                    "number": article_data.get('quality_score', 9.0)
                },
                "字數統計": {
                    "number": article_data.get('word_count', 0)
                },
                "創建時間": {
                    "date": {
                        "start": datetime.now().isoformat()
                    }
                },
                "關鍵字": {
                    "multi_select": [
                        {"name": keyword} 
                        for keyword in article_data.get('topic_keywords', [])
                    ]
                }
            }
            
            # 創建頁面
            page = self.notion.pages.create(
                parent={"database_id": self.database_id},
                properties=properties
            )
            
            # 如果有內容，添加到頁面中
            content_json = article_data.get('content_json', {})
            if content_json and content_json.get('content'):
                self._add_content_to_page(page['id'], content_json)
            
            logger.info(f"✅ 文章已創建到Notion: {article_data.get('title')}")
            return {
                'success': True,
                'notion_page_id': page['id'],
                'title': article_data.get('title'),
                'url': page.get('url')
            }
            
        except Exception as e:
            logger.error(f"❌ 創建Notion文章失敗: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _add_content_to_page(self, page_id, content_json):
        """
        添加內容到Notion頁面
        
        Args:
            page_id: 頁面ID
            content_json: 內容JSON
        """
        try:
            content = content_json.get('content', '')
            
            # 將內容轉換為Notion blocks
            blocks = self._convert_content_to_blocks(content)
            
            if blocks:
                self.notion.blocks.children.append(
                    block_id=page_id,
                    children=blocks
                )
                logger.info("✅ 內容已添加到Notion頁面")
                
        except Exception as e:
            logger.error(f"❌ 添加內容到頁面失敗: {e}")
    
    def _convert_content_to_blocks(self, content):
        """
        將文字內容轉換為Notion blocks格式
        
        Args:
            content: 文字內容
            
        Returns:
            list: Notion blocks列表
        """
        blocks = []
        
        # 簡單的段落處理
        paragraphs = content.split('\n\n')
        
        for paragraph in paragraphs:
            if paragraph.strip():
                # 檢查是否是標題
                if paragraph.startswith('#'):
                    # 標題處理
                    heading_level = min(len(paragraph) - len(paragraph.lstrip('#')), 3)
                    heading_text = paragraph.lstrip('# ').strip()
                    
                    heading_type = f"heading_{heading_level}"
                    blocks.append({
                        "object": "block",
                        "type": heading_type,
                        heading_type: {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {"content": heading_text}
                                }
                            ]
                        }
                    })
                else:
                    # 普通段落
                    blocks.append({
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {"content": paragraph.strip()}
                                }
                            ]
                        }
                    })
        
        return blocks
    
    def query_articles(self, filters=None, sorts=None, page_size=50):
        """
        查詢Notion資料庫中的文章
        
        Args:
            filters: 查詢過濾條件
            sorts: 排序條件
            page_size: 頁面大小
            
        Returns:
            dict: 查詢結果
        """
        try:
            query_params = {
                "database_id": self.database_id,
                "page_size": page_size
            }
            
            if filters:
                query_params["filter"] = filters
            
            if sorts:
                query_params["sorts"] = sorts
            else:
                # 預設按創建時間降序排列
                query_params["sorts"] = [
                    {
                        "property": "創建時間",
                        "direction": "descending"
                    }
                ]
            
            result = self.notion.databases.query(**query_params)
            
            logger.info(f"✅ 查詢到 {len(result['results'])} 篇文章")
            return result
            
        except Exception as e:
            logger.error(f"❌ 查詢Notion文章失敗: {e}")
            return {"results": [], "error": str(e)}
    
    def test_connection(self):
        """
        測試Notion連接
        
        Returns:
            dict: 測試結果
        """
        try:
            # 測試用戶權限
            users = self.notion.users.list()
            
            # 測試資料庫訪問
            database = self.notion.databases.retrieve(database_id=self.database_id)
            
            return {
                'success': True,
                'database_title': database.get('title', [{}])[0].get('plain_text', '未知'),
                'user_count': len(users.get('results', [])),
                'database_id': self.database_id
            }
            
        except Exception as e:
            logger.error(f"❌ Notion連接測試失敗: {e}")
            return {
                'success': False,
                'error': str(e)
            }

def get_notion_database():
    """
    獲取Notion資料庫實例（單例模式）
    
    Returns:
        NotionArticleDatabase: 資料庫實例
    """
    if not hasattr(get_notion_database, '_instance'):
        get_notion_database._instance = NotionArticleDatabase()
    
    return get_notion_database._instance

if __name__ == "__main__":
    # 測試腳本
    print("🧪 測試Notion連接...")
    
    try:
        db = NotionArticleDatabase()
        result = db.test_connection()
        
        if result['success']:
            print(f"✅ 連接成功!")
            print(f"   資料庫: {result['database_title']}")
            print(f"   使用者數量: {result['user_count']}")
            print(f"   資料庫ID: {result['database_id']}")
        else:
            print(f"❌ 連接失敗: {result['error']}")
            
    except Exception as e:
        print(f"❌ 初始化失敗: {e}")
        print("\n請確保設定以下環境變數:")
        print("export NOTION_TOKEN=your_notion_api_token")
        print("export NOTION_DATABASE_ID=your_database_id")