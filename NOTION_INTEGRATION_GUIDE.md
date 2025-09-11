# 使用現有 Notion 數據庫集成指南

簡化版本 - 直接使用您現有的「財商成長思維」Notion 數據庫

## 🎯 概述

已重新設計系統以使用您現有的單一 Notion 數據庫，移除了之前複雜的多數據庫架構。

### 主要特性
- ✅ **智能屬性映射** - 自動適配您現有的數據庫結構
- ✅ **靈活的數據類型支持** - 支持標題、選擇、多選、數字、日期等
- ✅ **中英文欄位兼容** - 同時支持中文和英文欄位名稱
- ✅ **保留現有數據** - 不影響您現有的數據和結構

## 🚀 快速開始

### 1. 環境設置

```bash
# 設置 Notion API Token
export NOTION_TOKEN="secret_your_notion_api_token"

# 設置數據庫 ID（從您的 Notion 頁面 URL 中獲取）
export NOTION_DATABASE_ID="your_database_id_here"
```

### 2. 運行設置腳本

```bash
python3 scripts/setup_existing_notion.py
```

這個腳本將：
- ✅ 驗證您的 Notion Token
- ✅ 檢查數據庫連接
- ✅ 分析數據庫結構
- ✅ 生成配置建議
- ✅ 可選創建測試條目

### 3. 測試集成

```bash
python3 scripts/test_existing_notion.py
```

這將運行完整的測試套件來驗證所有功能。

## 📊 API 使用

### 啟動服務器

```bash
uvicorn app.api.main:app --reload --host 0.0.0.0 --port 8000
```

### 主要端點

| 端點 | 方法 | 功能 |
|------|------|------|
| `/api/v1/articles/health` | GET | 健康檢查 |
| `/api/v1/articles/database/structure` | GET | 查看數據庫結構 |
| `/api/v1/articles/` | POST | 創建新文章 |
| `/api/v1/articles/` | GET | 獲取文章列表 |
| `/api/v1/articles/sample` | GET | 創建範例文章 |
| `/api/v1/articles/inspect` | GET | 檢查現有數據 |

### 創建文章範例

```bash
curl -X POST "http://localhost:8000/api/v1/articles/" \
     -H "Content-Type: application/json" \
     -d '{
       "title": "AI 投資策略分析",
       "content": "詳細的文章內容...",
       "summary": "本文分析了AI在投資領域的應用",
       "category": "投資理財",
       "keywords": ["AI投資", "量化交易", "風險管理"],
       "quality_score": 8.5,
       "word_count": 1500,
       "status": "草稿"
     }'
```

## 🔧 智能映射系統

### 自動屬性映射

系統會自動識別並映射您的數據庫欄位：

#### 標題類欄位
- 任何 `title` 類型的欄位
- 自動映射文章標題

#### 狀態類欄位
- 包含「狀態」或 "status" 的 `select` 欄位
- 自動映射狀態值（草稿、已發布、完成等）

#### 分類類欄位
- 包含「分類」或 "category" 的 `select` 欄位
- 映射文章分類（投資理財、數字貨幣投資等）

#### 關鍵字欄位
- 包含「關鍵字」、"keywords"、「標籤」或 "tags" 的 `multi_select` 欄位
- 自動處理關鍵字數組

#### 數字欄位
- **評分相關**: 「評分」、"score"、「分數」→ quality_score
- **字數相關**: 「字數」、"word" → word_count  
- **趨勢相關**: 「趨勢」、"trend" → trend_score

#### 日期欄位
- **創建相關**: 「創建」、"created" → 創建時間
- **發布相關**: 「發布」、"published" → 發布時間

## 🎨 支持的數據格式

### 輸入數據範例

```python
article_data = {
    # 基本信息
    "title": "文章標題",
    "content": "文章內容...",
    "summary": "文章摘要",
    
    # 分類和標籤
    "category": "投資理財",
    "keywords": ["投資", "理財", "AI"],
    
    # 數值信息
    "quality_score": 8.5,
    "word_count": 1500,
    "trend_score": 9.2,
    
    # 狀態信息
    "status": "草稿",
    "style": "實用智慧",
    
    # 布爾值
    "featured": True,
    "completed": False
}
```

### 中文欄位支持

系統也支持中文欄位名稱：

```python
article_data = {
    "標題": "中文標題",
    "內容": "中文內容...",
    "分類": "投資理財",
    "關鍵字": ["投資", "理財"],
    "評分": 8.5,
    "狀態": "草稿"
}
```

## 📱 前端集成

### JavaScript 範例

```javascript
// 創建文章
async function createArticle(articleData) {
    const response = await fetch('/api/v1/articles/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(articleData)
    });
    
    const result = await response.json();
    
    if (result.success) {
        console.log('文章創建成功:', result.notion_url);
    }
}

// 獲取文章列表
async function getArticles(limit = 20) {
    const response = await fetch(`/api/v1/articles/?limit=${limit}`);
    const result = await response.json();
    
    if (result.success) {
        return result.articles;
    }
}

// 健康檢查
async function checkHealth() {
    const response = await fetch('/api/v1/articles/health');
    const result = await response.json();
    
    console.log('數據庫狀態:', result.database_title);
    return result.status === 'healthy';
}
```

## 🔍 故障排除

### 常見問題

#### 1. Token 相關錯誤
```
❌ NOTION_TOKEN 環境變數未設定
```
**解決方案**:
1. 前往 https://www.notion.so/my-integrations
2. 創建或選擇現有集成
3. 複製 Integration Token
4. 設置環境變數: `export NOTION_TOKEN="secret_..."`

#### 2. 數據庫 ID 錯誤
```
❌ NOTION_DATABASE_ID 環境變數未設定
```
**解決方案**:
1. 打開您的 Notion 數據庫頁面
2. 點擊「分享」→「複製連結」
3. 從 URL 提取 32 位數據庫 ID
4. 設置環境變數: `export NOTION_DATABASE_ID="your_db_id"`

#### 3. 權限錯誤
```
❌ The integration doesn't have permission
```
**解決方案**:
1. 在 Notion 頁面點擊「分享」
2. 邀請您的集成
3. 給予讀寫權限

#### 4. 屬性映射失敗
```
⚠️ 某些欄位未正確映射
```
**解決方案**:
1. 檢查數據庫結構: `GET /api/v1/articles/database/structure`
2. 確認欄位名稱和類型
3. 調整輸入數據格式

### 調試工具

```bash
# 檢查數據庫結構
curl http://localhost:8000/api/v1/articles/database/structure

# 健康檢查
curl http://localhost:8000/api/v1/articles/health

# 檢查現有數據
curl http://localhost:8000/api/v1/articles/inspect

# 創建測試條目
curl http://localhost:8000/api/v1/articles/sample
```

## 📚 檔案結構

```
app/
├── services/
│   └── simple_notion_service.py     # 簡化的 Notion 服務
├── api/
│   └── simple_notion_endpoints.py   # API 端點
└── core/
    └── config.py                    # 配置（已更新）

scripts/
├── setup_existing_notion.py         # 設置腳本
├── test_existing_notion.py         # 測試腳本
└── inspect_existing_notion_db.py   # 數據庫檢查腳本
```

## 🎉 特色功能

### 1. 動態結構適配
- 自動分析您的數據庫結構
- 無需手動配置欄位映射
- 支援任何 Notion 數據庫布局

### 2. 中英文混合支持
- 智能識別中英文欄位名稱
- 自動處理不同語言的數據類型
- 靈活的數據格式轉換

### 3. 錯誤恢復機制
- 優雅處理屬性映射失敗
- 提供詳細的錯誤信息
- 自動跳過無效的欄位

### 4. 性能優化
- 異步操作提升響應速度
- 智能批量處理
- 最小化 API 調用次數

## 💡 使用建議

1. **初次使用**：先運行 `setup_existing_notion.py` 確保連接正常
2. **結構變更**：如果修改了數據庫結構，重新運行設置腳本
3. **測試環境**：使用 `sample` 端點創建測試數據
4. **生產部署**：確保正確設置環境變數
5. **監控健康**：定期調用健康檢查端點

## 🔧 高級配置

### 環境變數

```bash
# 必需
export NOTION_TOKEN="secret_your_token"
export NOTION_DATABASE_ID="your_database_id"

# 可選
export LOG_LEVEL="INFO"
export API_HOST="0.0.0.0"
export API_PORT="8000"
```

### .env 文件配置

```env
NOTION_TOKEN=secret_your_notion_token
NOTION_DATABASE_ID=your_database_id

# API 配置
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=true

# 其他配置
LOG_LEVEL=INFO
MAX_CONCURRENT_REQUESTS=10
```

---

🎊 **您的金融智慧平台現在已成功整合 Notion 數據庫！** 🎊

立即開始使用您現有的「財商成長思維」數據庫，享受更直觀的數據管理體驗！