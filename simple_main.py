"""
簡化的主應用程序，只包含核心功能
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

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

@app.get("/health")
async def health_check():
    """健康檢查"""
    return {"status": "healthy", "service": "financial-wisdom-platform"}

# 導入 Notion API 路由
try:
    from app.api.notion_web_endpoints import router as web_router
    app.include_router(web_router)
except ImportError as e:
    print(f"無法導入 Notion 路由: {e}")
    print("將在沒有完整功能的情況下運行基本伺服器")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("simple_main:app", host="0.0.0.0", port=8000, reload=True)