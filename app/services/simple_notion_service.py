"""
Simplified Notion Database Service
Works with your existing "財商成長思維" database
"""

import os
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from notion_client import Client
import asyncio
from concurrent.futures import ThreadPoolExecutor
import logging

from app.models.domain import (
    Article, ArticleId, Topic, Content, QualityMetrics,
    ArticleStatus, ContentStyle
)
from app.core.config import settings

logger = logging.getLogger(__name__)

class SimpleNotionService:
    """Simplified Notion service for single database operations"""
    
    def __init__(self, notion_token: Optional[str] = None, database_id: Optional[str] = None):
        self.notion_token = notion_token or settings.notion_token
        self.database_id = database_id or settings.notion_database_id
        
        if not self.notion_token:
            raise ValueError("NOTION_TOKEN is required")
        if not self.database_id:
            raise ValueError("NOTION_DATABASE_ID is required")
        
        self.client = Client(auth=self.notion_token)
        self.executor = ThreadPoolExecutor(max_workers=4)
    
    async def inspect_database_structure(self) -> Dict:
        """檢查數據庫結構"""
        loop = asyncio.get_event_loop()
        
        def get_database():
            return self.client.databases.retrieve(database_id=self.database_id)
        
        database = await loop.run_in_executor(self.executor, get_database)
        
        return {
            'title': self._extract_database_title(database),
            'properties': database.get('properties', {}),
            'id': database.get('id'),
            'created_time': database.get('created_time'),
            'last_edited_time': database.get('last_edited_time')
        }
    
    async def create_article_entry(self, article_data: Dict[str, Any]) -> str:
        """在 Notion 數據庫中創建文章條目"""
        loop = asyncio.get_event_loop()
        
        # 根據實際數據庫結構構建屬性
        # 這個函數會適應您現有的數據庫欄位
        properties = await self._build_properties(article_data)
        
        def create_page():
            return self.client.pages.create(
                parent={"database_id": self.database_id},
                properties=properties
            )
        
        page = await loop.run_in_executor(self.executor, create_page)
        page_id = page["id"]
        
        # 如果有內容，添加到頁面中
        if article_data.get('content'):
            await self._add_content_blocks(page_id, article_data['content'])
        
        logger.info(f"Created article entry in Notion: {article_data.get('title', 'Untitled')}")
        return page_id
    
    async def _build_properties(self, article_data: Dict[str, Any]) -> Dict:
        """根據數據庫結構構建屬性字典"""
        
        # 先檢查數據庫結構
        db_structure = await self.inspect_database_structure()
        properties = {}
        property_configs = db_structure['properties']
        
        # 動態構建屬性
        for prop_name, prop_config in property_configs.items():
            prop_type = prop_config.get('type')
            
            # 根據屬性名稱和類型進行智能映射
            if prop_type == 'title':
                # 標題欄位
                title_value = article_data.get('title', article_data.get('標題', 'Untitled Article'))
                properties[prop_name] = {
                    "title": [{"text": {"content": str(title_value)}}]
                }
            
            elif prop_type == 'rich_text':
                # 富文本欄位 - 可能是內容摘要、描述等
                if '內容' in prop_name or 'content' in prop_name.lower():
                    content_text = article_data.get('summary', article_data.get('摘要', ''))
                elif '描述' in prop_name or 'description' in prop_name.lower():
                    content_text = article_data.get('description', article_data.get('描述', ''))
                else:
                    content_text = article_data.get(prop_name.lower(), '')
                
                if content_text:
                    properties[prop_name] = {
                        "rich_text": [{"text": {"content": str(content_text)[:2000]}}]  # Notion 限制
                    }
            
            elif prop_type == 'select':
                # 選擇欄位 - 狀態、分類等
                select_value = self._map_select_value(prop_name, article_data, prop_config)
                if select_value:
                    properties[prop_name] = {"select": {"name": select_value}}
            
            elif prop_type == 'multi_select':
                # 多選欄位 - 標籤、關鍵字等
                multi_values = self._map_multi_select_values(prop_name, article_data, prop_config)
                if multi_values:
                    properties[prop_name] = {
                        "multi_select": [{"name": val} for val in multi_values]
                    }
            
            elif prop_type == 'number':
                # 數字欄位 - 評分、字數等
                number_value = self._map_number_value(prop_name, article_data)
                if number_value is not None:
                    properties[prop_name] = {"number": number_value}
            
            elif prop_type == 'date':
                # 日期欄位
                date_value = self._map_date_value(prop_name, article_data)
                if date_value:
                    properties[prop_name] = {"date": {"start": date_value}}
            
            elif prop_type == 'checkbox':
                # 複選框欄位
                checkbox_value = self._map_checkbox_value(prop_name, article_data)
                if checkbox_value is not None:
                    properties[prop_name] = {"checkbox": checkbox_value}
        
        return properties
    
    def _map_select_value(self, prop_name: str, article_data: Dict, prop_config: Dict) -> Optional[str]:
        """映射選擇欄位的值"""
        options = [opt['name'] for opt in prop_config.get('select', {}).get('options', [])]
        
        # 根據欄位名稱進行智能映射
        prop_lower = prop_name.lower()
        
        if '狀態' in prop_name or 'status' in prop_lower:
            status = article_data.get('status', article_data.get('狀態', ''))
            # 映射狀態值
            status_mapping = {
                'draft': '草稿',
                'generated': '已生成', 
                'published': '已發布',
                'completed': '完成',
                'pending': '待處理'
            }
            mapped_status = status_mapping.get(str(status).lower(), str(status))
            return mapped_status if mapped_status in options else (options[0] if options else None)
        
        elif '分類' in prop_name or 'category' in prop_lower:
            category = article_data.get('category', article_data.get('topic_category', article_data.get('分類', '')))
            return str(category) if str(category) in options else (options[0] if options else None)
        
        elif '風格' in prop_name or 'style' in prop_lower:
            style = article_data.get('style', article_data.get('content_style', article_data.get('風格', '')))
            style_mapping = {
                'practical_wisdom': '實用智慧',
                'motivational_finance': '勵志財經',
                'philosophical_money': '哲學思考'
            }
            mapped_style = style_mapping.get(str(style).lower(), str(style))
            return mapped_style if mapped_style in options else (options[0] if options else None)
        
        # 通用映射
        value = article_data.get(prop_name, article_data.get(prop_name.lower(), ''))
        return str(value) if str(value) in options else None
    
    def _map_multi_select_values(self, prop_name: str, article_data: Dict, prop_config: Dict) -> List[str]:
        """映射多選欄位的值"""
        options = [opt['name'] for opt in prop_config.get('multi_select', {}).get('options', [])]
        
        # 根據欄位名稱進行智能映射
        prop_lower = prop_name.lower()
        
        if '關鍵字' in prop_name or 'keywords' in prop_lower or '標籤' in prop_name or 'tags' in prop_lower:
            keywords = article_data.get('keywords', article_data.get('topic_keywords', article_data.get('關鍵字', [])))
            if isinstance(keywords, str):
                keywords = [kw.strip() for kw in keywords.split(',')]
            elif not isinstance(keywords, list):
                keywords = []
            
            # 過濾出存在於選項中的關鍵字，或取前幾個
            valid_keywords = [kw for kw in keywords if kw in options]
            if not valid_keywords and keywords:
                # 如果沒有完全匹配的，創建新的（Notion 會自動創建）
                valid_keywords = keywords[:5]  # 限制數量
            
            return valid_keywords
        
        return []
    
    def _map_number_value(self, prop_name: str, article_data: Dict) -> Optional[float]:
        """映射數字欄位的值"""
        prop_lower = prop_name.lower()
        
        if '評分' in prop_name or 'score' in prop_lower or '分數' in prop_lower:
            score = article_data.get('quality_score', article_data.get('score', article_data.get('評分', None)))
            if score is not None:
                return float(score)
        
        elif '字數' in prop_name or 'word' in prop_lower:
            word_count = article_data.get('word_count', article_data.get('字數', None))
            if word_count is not None:
                return float(word_count)
        
        elif '趨勢' in prop_name or 'trend' in prop_lower:
            trend_score = article_data.get('trend_score', article_data.get('趨勢分數', None))
            if trend_score is not None:
                return float(trend_score)
        
        # 通用數字映射
        value = article_data.get(prop_name, article_data.get(prop_name.lower()))
        if value is not None:
            try:
                return float(value)
            except (ValueError, TypeError):
                pass
        
        return None
    
    def _map_date_value(self, prop_name: str, article_data: Dict) -> Optional[str]:
        """映射日期欄位的值"""
        prop_lower = prop_name.lower()
        
        if '創建' in prop_name or 'created' in prop_lower:
            date_val = article_data.get('created_at', article_data.get('創建時間'))
        elif '發布' in prop_name or 'published' in prop_lower:
            date_val = article_data.get('published_at', article_data.get('發布時間'))
        else:
            date_val = article_data.get(prop_name, article_data.get(prop_name.lower()))
        
        if date_val:
            if isinstance(date_val, datetime):
                return date_val.isoformat()
            elif isinstance(date_val, str):
                return date_val
        
        # 默認使用當前時間
        if '創建' in prop_name or 'created' in prop_lower:
            return datetime.now(timezone.utc).isoformat()
        
        return None
    
    def _map_checkbox_value(self, prop_name: str, article_data: Dict) -> Optional[bool]:
        """映射複選框欄位的值"""
        prop_lower = prop_name.lower()
        
        if '完成' in prop_name or 'completed' in prop_lower:
            return article_data.get('completed', False)
        elif '發布' in prop_name or 'published' in prop_lower:
            return article_data.get('published', False)
        elif '推薦' in prop_name or 'featured' in prop_lower:
            return article_data.get('featured', False)
        
        # 通用布爾值映射
        value = article_data.get(prop_name, article_data.get(prop_name.lower()))
        if value is not None:
            return bool(value)
        
        return None
    
    async def _add_content_blocks(self, page_id: str, content: str):
        """添加內容塊到 Notion 頁面"""
        loop = asyncio.get_event_loop()
        
        # 將內容轉換為段落
        blocks = []
        paragraphs = content.split('\n\n')
        
        for paragraph in paragraphs[:10]:  # 限制段落數量
            if paragraph.strip():
                blocks.append({
                    "object": "block",
                    "type": "paragraph", 
                    "paragraph": {
                        "rich_text": [{"text": {"content": paragraph.strip()[:2000]}}]
                    }
                })
        
        if blocks:
            def append_blocks():
                return self.client.blocks.children.append(
                    block_id=page_id,
                    children=blocks
                )
            
            await loop.run_in_executor(self.executor, append_blocks)
    
    async def query_entries(self, filters: Optional[Dict] = None, limit: int = 50) -> List[Dict]:
        """查詢數據庫條目"""
        loop = asyncio.get_event_loop()
        
        def query_database():
            params = {
                "database_id": self.database_id,
                "page_size": limit
            }
            if filters:
                params["filter"] = filters
            
            return self.client.databases.query(**params)
        
        result = await loop.run_in_executor(self.executor, query_database)
        
        entries = []
        for page in result.get("results", []):
            entry = self._convert_page_to_dict(page)
            entries.append(entry)
        
        return entries
    
    def _convert_page_to_dict(self, page: Dict) -> Dict:
        """將 Notion 頁面轉換為字典"""
        properties = page.get("properties", {})
        entry = {
            "notion_id": page.get("id"),
            "url": page.get("url"),
            "created_time": page.get("created_time"),
            "last_edited_time": page.get("last_edited_time")
        }
        
        # 提取所有屬性
        for prop_name, prop_data in properties.items():
            prop_type = prop_data.get("type")
            
            if prop_type == "title":
                title_list = prop_data.get("title", [])
                entry[prop_name] = title_list[0].get("plain_text", "") if title_list else ""
            
            elif prop_type == "rich_text":
                rich_text_list = prop_data.get("rich_text", [])
                entry[prop_name] = rich_text_list[0].get("plain_text", "") if rich_text_list else ""
            
            elif prop_type == "select":
                select_obj = prop_data.get("select")
                entry[prop_name] = select_obj.get("name", "") if select_obj else ""
            
            elif prop_type == "multi_select":
                multi_select_list = prop_data.get("multi_select", [])
                entry[prop_name] = [item.get("name", "") for item in multi_select_list]
            
            elif prop_type == "number":
                entry[prop_name] = prop_data.get("number")
            
            elif prop_type == "date":
                date_obj = prop_data.get("date")
                entry[prop_name] = date_obj.get("start") if date_obj else None
            
            elif prop_type == "checkbox":
                entry[prop_name] = prop_data.get("checkbox", False)
        
        return entry
    
    def _extract_database_title(self, database: Dict) -> str:
        """提取數據庫標題"""
        title_list = database.get('title', [])
        if title_list:
            return title_list[0].get('plain_text', '未命名數據庫')
        return '未命名數據庫'
    
    async def test_connection(self) -> Dict:
        """測試連接"""
        try:
            structure = await self.inspect_database_structure()
            
            return {
                'success': True,
                'database_title': structure['title'],
                'database_id': self.database_id,
                'properties_count': len(structure['properties']),
                'created_time': structure['created_time']
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

# Singleton pattern for service instance
_simple_notion_service_instance = None

def get_simple_notion_service() -> SimpleNotionService:
    """Get Simple Notion service instance (singleton)"""
    global _simple_notion_service_instance
    if _simple_notion_service_instance is None:
        _simple_notion_service_instance = SimpleNotionService()
    return _simple_notion_service_instance