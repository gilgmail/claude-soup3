"""
Simplified FastAPI endpoints for single Notion database operations
Works with your existing "財商成長思維" database
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.services.simple_notion_service import SimpleNotionService, get_simple_notion_service

router = APIRouter(prefix="/api/v1/articles", tags=["財商成長思維"])

# Request/Response models
class ArticleCreateRequest(BaseModel):
    """創建文章請求"""
    title: str
    content: Optional[str] = None
    summary: Optional[str] = None
    category: Optional[str] = None
    keywords: Optional[List[str]] = None
    quality_score: Optional[float] = None
    word_count: Optional[int] = None
    status: Optional[str] = "草稿"
    style: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "AI 投資策略分析",
                "content": "詳細的文章內容...",
                "summary": "本文分析了AI在投資領域的應用...", 
                "category": "投資理財",
                "keywords": ["AI投資", "量化交易", "風險管理"],
                "quality_score": 8.5,
                "word_count": 1500,
                "status": "草稿",
                "style": "實用智慧"
            }
        }

class ArticleResponse(BaseModel):
    """文章操作響應"""
    success: bool
    message: str
    notion_id: Optional[str] = None
    notion_url: Optional[str] = None

class DatabaseStructureResponse(BaseModel):
    """數據庫結構響應"""
    title: str
    properties: Dict[str, Any]
    database_id: str
    created_time: Optional[str]

@router.get("/health")
async def health_check(
    notion_service: SimpleNotionService = Depends(get_simple_notion_service)
):
    """健康檢查 - 測試與 Notion 數據庫的連接"""
    try:
        result = await notion_service.test_connection()
        
        if result['success']:
            return {
                "status": "healthy",
                "database_title": result['database_title'],
                "database_id": result['database_id'],
                "properties_count": result['properties_count'],
                "created_time": result['created_time']
            }
        else:
            raise HTTPException(
                status_code=503,
                detail=f"Notion connection failed: {result['error']}"
            )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Health check failed: {str(e)}"
        )

@router.get("/database/structure", response_model=DatabaseStructureResponse)
async def get_database_structure(
    notion_service: SimpleNotionService = Depends(get_simple_notion_service)
):
    """獲取數據庫結構信息"""
    try:
        structure = await notion_service.inspect_database_structure()
        
        return DatabaseStructureResponse(
            title=structure['title'],
            properties=structure['properties'],
            database_id=structure['id'],
            created_time=structure.get('created_time')
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get database structure: {str(e)}"
        )

@router.post("/", response_model=ArticleResponse)
async def create_article(
    article: ArticleCreateRequest,
    notion_service: SimpleNotionService = Depends(get_simple_notion_service)
):
    """創建新文章到 Notion 數據庫"""
    try:
        # 轉換為字典格式
        article_data = article.model_dump()
        
        # 創建文章條目
        notion_id = await notion_service.create_article_entry(article_data)
        
        return ArticleResponse(
            success=True,
            message=f"文章「{article.title}」已成功創建到 Notion 數據庫",
            notion_id=notion_id,
            notion_url=f"https://notion.so/{notion_id.replace('-', '')}"
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"創建文章失敗: {str(e)}"
        )

@router.get("/")
async def list_articles(
    limit: int = Query(20, ge=1, le=100, description="返回條目數量"),
    category: Optional[str] = Query(None, description="按分類篩選"),
    status: Optional[str] = Query(None, description="按狀態篩選"),
    notion_service: SimpleNotionService = Depends(get_simple_notion_service)
):
    """獲取文章列表"""
    try:
        # 構建過濾條件
        filters = []
        
        if category:
            # 需要根據實際數據庫欄位調整
            filters.append({
                "property": "分類",  # 假設有這個欄位
                "select": {"equals": category}
            })
        
        if status:
            filters.append({
                "property": "狀態",  # 假設有這個欄位
                "select": {"equals": status}
            })
        
        # 構建最終過濾器
        final_filter = None
        if len(filters) == 1:
            final_filter = filters[0]
        elif len(filters) > 1:
            final_filter = {"and": filters}
        
        # 查詢條目
        entries = await notion_service.query_entries(
            filters=final_filter,
            limit=limit
        )
        
        return {
            "success": True,
            "articles": entries,
            "total": len(entries),
            "limit": limit
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"獲取文章列表失敗: {str(e)}"
        )

@router.get("/sample")
async def create_sample_article(
    notion_service: SimpleNotionService = Depends(get_simple_notion_service)
):
    """創建範例文章 - 用於測試"""
    
    sample_data = {
        "title": "AI 驅動的投資策略：財商成長新思維",
        "content": """
        在這個快速變化的金融世界中，人工智能正在重塑投資領域的格局。本文將探討如何運用AI技術提升個人投資決策能力。

        ## 主要內容

        ### 1. AI投資工具的現狀
        - 量化分析平台
        - 風險評估模型
        - 市場預測算法

        ### 2. 實用策略
        - 數據驅動決策
        - 風險控制機制
        - 投資組合優化

        ## 結論
        
        結合傳統投資智慧與現代AI技術，能夠幫助投資者在複雜的市場環境中做出更明智的決策。
        """,
        "summary": "探討AI技術在投資領域的應用，提供實用的投資策略建議",
        "category": "投資理財",
        "keywords": ["AI投資", "量化交易", "風險管理", "投資策略"],
        "quality_score": 9.2,
        "word_count": 800,
        "status": "草稿",
        "style": "實用智慧",
        "featured": True,
        "completed": False
    }
    
    try:
        notion_id = await notion_service.create_article_entry(sample_data)
        
        return {
            "success": True,
            "message": "範例文章創建成功",
            "notion_id": notion_id,
            "sample_data": sample_data,
            "notion_url": f"https://notion.so/{notion_id.replace('-', '')}"
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"創建範例文章失敗: {str(e)}"
        )

@router.get("/inspect")
async def inspect_existing_data(
    limit: int = Query(5, ge=1, le=20, description="檢查條目數量"),
    notion_service: SimpleNotionService = Depends(get_simple_notion_service)
):
    """檢查現有數據庫內容"""
    try:
        # 獲取數據庫結構
        structure = await notion_service.inspect_database_structure()
        
        # 獲取現有條目
        entries = await notion_service.query_entries(limit=limit)
        
        return {
            "database_info": {
                "title": structure['title'],
                "database_id": structure['id'],
                "properties_count": len(structure['properties']),
                "created_time": structure.get('created_time')
            },
            "properties": structure['properties'],
            "sample_entries": entries,
            "total_sampled": len(entries)
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"檢查數據庫失敗: {str(e)}"
        )

# 兼容性端點 - 與現有前端保持兼容
@router.post("/legacy")
async def create_article_legacy_format(
    article_data: Dict[str, Any],
    notion_service: SimpleNotionService = Depends(get_simple_notion_service)
):
    """兼容現有格式的文章創建端點"""
    try:
        notion_id = await notion_service.create_article_entry(article_data)
        
        return {
            "success": True,
            "message": "文章已保存到 Notion 數據庫",
            "notion_page_id": notion_id,
            "title": article_data.get("title", "Untitled"),
            "url": f"https://notion.so/{notion_id.replace('-', '')}"
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"保存文章失敗: {str(e)}"
        )