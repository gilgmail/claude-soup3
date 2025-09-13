"""
簡化的主應用程序，只包含核心功能
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

# 創建基本的 FastAPI 應用
app = FastAPI(
    title="財商成長思維平台",
    description="智能文章生成和管理平台",
    version="1.0.0"
)

# CORS 中介軟體
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 靜態文件
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def serve_index():
    """提供主頁面"""
    return FileResponse("static/index.html")

@app.get("/analytics")
async def serve_analytics():
    """提供分析頁面"""
    return FileResponse("static/analytics.html")

@app.get("/dashboard")
async def serve_dashboard():
    """提供資料統計儀表板"""
    return FileResponse("static/dashboard.html")

@app.get("/health")
async def health_check():
    """健康檢查"""
    return {"status": "healthy", "service": "financial-wisdom-platform"}

@app.get("/robots.txt")
async def robots_txt():
    """提供 robots.txt 文件"""
    return FileResponse("static/robots.txt", media_type="text/plain")

@app.get("/sitemap.xml")
async def sitemap_xml():
    """重定向到動態生成的 sitemap"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/api/v1/financial-wisdom/sitemap.xml")

# 導入 Notion API 路由
try:
    from app.api.notion_web_endpoints import router as web_router, limiter
    app.include_router(web_router)
    
    # 註冊速率限制錯誤處理器
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    
except ImportError as e:
    print(f"無法導入 Notion 路由: {e}")
    print("將在沒有完整功能的情況下運行基本伺服器")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("simple_main:app", host="0.0.0.0", port=8000, reload=True)