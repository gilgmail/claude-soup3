"""
財商成長思維 Web API 端點
提供 Notion 資料庫讀取和 AI 文章生成功能
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import json
from datetime import datetime

from notion_client import Client
from app.core.config import get_settings
from app.services.financial_wisdom_service import AIContentGenerationService

router = APIRouter(prefix="/api/v1/financial-wisdom", tags=["財商成長思維"])

# Pydantic 模型
class ArticleResponse(BaseModel):
    id: str
    title: str
    category: str
    status: str
    tags: List[str]
    word_count: Optional[int]
    reading_time: Optional[int]
    publish_date: Optional[str]
    summary: Optional[str]

class ArticleListResponse(BaseModel):
    articles: List[ArticleResponse]
    total: int
    categories: Dict[str, int]

class ArticleGenerationRequest(BaseModel):
    title: str
    topic: str
    target_audience: str = "一般投資者"
    writing_style: str = "實用智慧"
    word_count_target: int = 1500
    include_case_study: bool = True
    focus_areas: List[str] = []
    
class GeneratedArticleResponse(BaseModel):
    title: str
    content: str
    category: str
    tags: List[str]
    word_count: int
    reading_time: int
    quality_score: float

# Notion 客戶端初始化
def get_notion_client():
    settings = get_settings()
    if not settings.notion_token:
        raise HTTPException(status_code=500, detail="Notion API Token 未設置")
    return Client(auth=settings.notion_token)

# AI 內容生成服務
def get_ai_service():
    return AIContentGenerationService()

@router.get("/articles", response_model=ArticleListResponse)
async def get_articles(
    limit: int = 20,
    category: Optional[str] = None,
    search: Optional[str] = None
):
    """獲取文章列表"""
    try:
        client = get_notion_client()
        settings = get_settings()
        
        # 構建查詢條件
        filter_conditions = []
        if category:
            filter_conditions.append({
                "property": "主題類別",
                "select": {"equals": category}
            })
        
        if search:
            filter_conditions.append({
                "property": "文章標題",
                "title": {"contains": search}
            })
        
        query_params = {
            "database_id": settings.notion_database_id,
            "page_size": limit,
            "sorts": [
                {"property": "發布日期", "direction": "descending"}
            ]
        }
        
        if filter_conditions:
            if len(filter_conditions) == 1:
                query_params["filter"] = filter_conditions[0]
            else:
                query_params["filter"] = {
                    "and": filter_conditions
                }
        
        # 查詢 Notion 資料庫
        response = client.databases.query(**query_params)
        
        articles = []
        categories = {}
        
        for page in response.get('results', []):
            properties = page.get('properties', {})
            
            # 提取文章信息
            title = ""
            if 'title' in properties.get('文章標題', {}):
                title_list = properties['文章標題']['title']
                title = title_list[0]['plain_text'] if title_list else ""
            
            category_obj = properties.get('主題類別', {}).get('select')
            category = category_obj['name'] if category_obj else ""
            
            status_obj = properties.get('發布狀態', {}).get('select')
            status = status_obj['name'] if status_obj else ""
            
            tags_list = properties.get('標籤', {}).get('multi_select', [])
            tags = [tag['name'] for tag in tags_list]
            
            word_count = properties.get('字數', {}).get('number')
            reading_time = properties.get('閱讀時間', {}).get('number')
            
            publish_date = properties.get('發布日期', {}).get('date')
            publish_date_str = publish_date['start'] if publish_date else None
            
            summary_rich_text = properties.get('核心要點', {}).get('rich_text', [])
            summary = summary_rich_text[0]['plain_text'] if summary_rich_text else ""
            
            article = ArticleResponse(
                id=page['id'],
                title=title,
                category=category,
                status=status,
                tags=tags,
                word_count=word_count,
                reading_time=reading_time,
                publish_date=publish_date_str,
                summary=summary
            )
            
            articles.append(article)
            
            # 統計分類
            if category:
                categories[category] = categories.get(category, 0) + 1
        
        return ArticleListResponse(
            articles=articles,
            total=len(articles),
            categories=categories
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"獲取文章列表失敗: {str(e)}")

@router.get("/articles/{article_id}")
async def get_article_content(article_id: str):
    """獲取特定文章的完整內容"""
    try:
        client = get_notion_client()
        
        # 獲取頁面內容
        page = client.pages.retrieve(page_id=article_id)
        blocks = client.blocks.children.list(block_id=article_id)
        
        # 提取頁面屬性
        properties = page.get('properties', {})
        
        title = ""
        if 'title' in properties.get('文章標題', {}):
            title_list = properties['文章標題']['title']
            title = title_list[0]['plain_text'] if title_list else ""
        
        # 提取文章內容
        content_blocks = []
        for block in blocks.get('results', []):
            block_type = block.get('type')
            if block_type == 'paragraph':
                text_content = ""
                for rich_text in block.get('paragraph', {}).get('rich_text', []):
                    text_content += rich_text.get('plain_text', '')
                if text_content.strip():
                    content_blocks.append(text_content)
            elif block_type == 'heading_1':
                text_content = ""
                for rich_text in block.get('heading_1', {}).get('rich_text', []):
                    text_content += rich_text.get('plain_text', '')
                if text_content.strip():
                    content_blocks.append(f"# {text_content}")
            elif block_type == 'heading_2':
                text_content = ""
                for rich_text in block.get('heading_2', {}).get('rich_text', []):
                    text_content += rich_text.get('plain_text', '')
                if text_content.strip():
                    content_blocks.append(f"## {text_content}")
        
        content = "\n\n".join(content_blocks)
        
        return {
            "id": article_id,
            "title": title,
            "content": content,
            "properties": properties
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"獲取文章內容失敗: {str(e)}")

@router.get("/categories")
async def get_categories():
    """獲取所有文章分類"""
    try:
        client = get_notion_client()
        settings = get_settings()
        
        # 獲取資料庫結構
        database = client.databases.retrieve(database_id=settings.notion_database_id)
        
        # 提取分類選項
        properties = database.get('properties', {})
        category_property = properties.get('主題類別', {})
        
        categories = []
        if category_property.get('type') == 'select':
            options = category_property.get('select', {}).get('options', [])
            categories = [option['name'] for option in options]
        
        return {"categories": categories}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"獲取分類失敗: {str(e)}")

@router.post("/generate", response_model=GeneratedArticleResponse)
async def generate_article(request: ArticleGenerationRequest):
    """基於主題和要求生成新的財商文章"""
    try:
        ai_service = get_ai_service()
        
        # 構建生成請求
        generation_request = {
            "title": request.title,
            "topic": request.topic,
            "target_audience": request.target_audience,
            "writing_style": request.writing_style,
            "word_count_target": request.word_count_target,
            "include_case_study": request.include_case_study,
            "focus_areas": request.focus_areas,
            "template": "financial_wisdom"
        }
        
        # 調用 AI 生成服務
        result = await ai_service.generate_financial_article(generation_request)
        
        if not result.get('success'):
            raise HTTPException(status_code=500, detail=result.get('error', '生成失敗'))
        
        article_data = result['data']
        
        # 計算閱讀時間
        reading_time = max(1, round(article_data['word_count'] / 250))
        
        return GeneratedArticleResponse(
            title=article_data['title'],
            content=article_data['content'],
            category=article_data.get('category', '財富建構'),
            tags=article_data.get('keywords', ['財富思維', '個人成長']),
            word_count=article_data['word_count'],
            reading_time=reading_time,
            quality_score=article_data.get('quality_score', 8.0)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文章生成失敗: {str(e)}")

@router.post("/save-generated")
async def save_generated_article(article: GeneratedArticleResponse):
    """將生成的文章保存到 Notion 資料庫"""
    try:
        client = get_notion_client()
        settings = get_settings()
        
        # 準備屬性數據
        properties = {
            '文章標題': {
                "title": [{"text": {"content": article.title}}]
            },
            '主題類別': {
                "select": {"name": article.category}
            },
            '發布狀態': {
                "select": {"name": "草稿"}
            },
            '標籤': {
                "multi_select": [{"name": tag} for tag in article.tags[:3]]
            },
            '字數': {
                "number": article.word_count
            },
            '閱讀時間': {
                "number": article.reading_time
            },
            '發布日期': {
                "date": {"start": datetime.now().strftime("%Y-%m-%d")}
            }
        }
        
        # 創建頁面內容
        content_blocks = []
        
        # 將內容分段並創建區塊
        paragraphs = article.content.split('\n\n')
        for paragraph in paragraphs[:20]:  # 限制區塊數量
            if paragraph.strip():
                if paragraph.startswith('#'):
                    # 標題區塊
                    level = paragraph.count('#')
                    text = paragraph.lstrip('#').strip()
                    if level == 1:
                        content_blocks.append({
                            "object": "block",
                            "type": "heading_1",
                            "heading_1": {
                                "rich_text": [{"type": "text", "text": {"content": text}}]
                            }
                        })
                    else:
                        content_blocks.append({
                            "object": "block",
                            "type": "heading_2", 
                            "heading_2": {
                                "rich_text": [{"type": "text", "text": {"content": text}}]
                            }
                        })
                else:
                    # 段落區塊
                    content_blocks.append({
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{"type": "text", "text": {"content": paragraph[:2000]}}]
                        }
                    })
        
        # 創建 Notion 頁面
        response = client.pages.create(
            parent={"database_id": settings.notion_database_id},
            properties=properties,
            children=content_blocks
        )
        
        return {
            "success": True,
            "page_id": response['id'],
            "message": "文章已成功保存到 Notion 資料庫"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存文章失敗: {str(e)}")

@router.get("/stats")
async def get_database_stats():
    """獲取資料庫統計信息"""
    try:
        client = get_notion_client()
        settings = get_settings()
        
        # 獲取所有文章
        response = client.databases.query(
            database_id=settings.notion_database_id,
            page_size=100
        )
        
        total_articles = len(response.get('results', []))
        categories = {}
        tags_count = {}
        total_words = 0
        
        for page in response.get('results', []):
            properties = page.get('properties', {})
            
            # 統計分類
            category_obj = properties.get('主題類別', {}).get('select')
            if category_obj:
                category = category_obj['name']
                categories[category] = categories.get(category, 0) + 1
            
            # 統計標籤
            tags_list = properties.get('標籤', {}).get('multi_select', [])
            for tag_obj in tags_list:
                tag = tag_obj['name']
                tags_count[tag] = tags_count.get(tag, 0) + 1
            
            # 統計字數
            word_count = properties.get('字數', {}).get('number', 0)
            if word_count:
                total_words += word_count
        
        # 排序統計數據
        top_categories = sorted(categories.items(), key=lambda x: x[1], reverse=True)
        top_tags = sorted(tags_count.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            "total_articles": total_articles,
            "total_words": total_words,
            "average_words": round(total_words / total_articles) if total_articles > 0 else 0,
            "categories": dict(top_categories),
            "top_tags": dict(top_tags),
            "last_updated": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"獲取統計信息失敗: {str(e)}")