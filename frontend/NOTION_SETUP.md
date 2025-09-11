# Notion 整合設定指南

將金融智慧平台的資料庫從 JSON 文件遷移到 Notion 的完整設定指南。

## 🚀 快速開始

### 步驟 1: 創建 Notion 集成

1. 前往 [Notion Integrations](https://www.notion.so/my-integrations)
2. 點擊 **"New integration"**
3. 填寫以下資訊：
   - **Name**: `金融智慧平台 API`
   - **Description**: `用於儲存和管理金融智慧文章的集成`
   - **Associated workspace**: 選擇您的工作區
4. 點擊 **"Submit"** 創建集成
5. 複製 **Internal Integration Token**（格式：`secret_...`）

### 步驟 2: 創建 Notion 頁面

1. 在您的 Notion 工作區創建一個新頁面
2. 頁面標題建議：`金融智慧平台資料庫`
3. 點擊頁面右上角的 **"Share"** 按鈕
4. 點擊 **"Copy link"** 獲取頁面連結
5. 從 URL 中提取頁面 ID（32 字符的字符串）
   - 例如：`https://www.notion.so/your-page-title-abc123def456...`
   - 頁面 ID 就是 `abc123def456...` 部分

### 步驟 3: 授予集成權限

1. 在剛創建的頁面中，點擊右上角的 **"Share"**
2. 點擊 **"Invite"**
3. 搜索並選擇您剛創建的集成（`金融智慧平台 API`）
4. 點擊 **"Invite"** 授予權限

### 步驟 4: 設定環境變數

在終端中設定以下環境變數：

```bash
# 設定 Notion API Token
export NOTION_TOKEN="secret_your_token_here"

# 設定父頁面 ID
export NOTION_PARENT_PAGE_ID="your_page_id_here"
```

### 步驟 5: 創建資料庫

運行以下命令創建 Notion 資料庫：

```bash
python3 create_notion_database.py
```

成功後會顯示：
```
✅ 資料庫創建成功!
   資料庫ID: abc123def456...
   資料庫URL: https://www.notion.so/...
```

### 步驟 6: 設定資料庫 ID

將創建的資料庫 ID 設定為環境變數：

```bash
export NOTION_DATABASE_ID="your_database_id_here"
```

### 步驟 7: 測試連接

測試 Notion 連接是否正常：

```bash
python3 notion_config.py
```

應該看到：
```
✅ 連接成功!
   資料庫: 金融智慧文章資料庫
   使用者數量: 1
   資料庫ID: your_database_id
```

## 🔧 啟動 Notion API 服務器

### 停止舊服務器

```bash
# 停止現有的 API 服務器
pkill -f "api_server.py"
```

### 啟動新的 Notion API 服務器

```bash
python3 notion_api_server.py
```

應該看到：
```
🚀 Notion API服務器已啟動
📡 監聽端口: 8001
🔗 API端點: http://localhost:8001/api/articles
🏥 健康檢查: http://localhost:8001/api/health
📊 資料庫: Notion Database
```

## 📊 資料庫結構

創建的 Notion 資料庫包含以下屬性：

| 屬性名稱 | 類型 | 說明 |
|---------|------|------|
| 標題 | Title | 文章標題 |
| 主題分類 | Select | 投資理財、數字貨幣投資等 |
| 內容風格 | Select | 實用智慧、哲學思考等 |
| 品質評分 | Number | 文章品質評分 (0-10) |
| 字數統計 | Number | 文章字數 |
| 可讀性評分 | Number | 可讀性評分 (0-10) |
| 參與度評分 | Number | 參與度評分 (0-10) |
| 創建時間 | Date | 文章創建時間 |
| 關鍵字 | Multi-select | 文章關鍵字標籤 |
| 狀態 | Select | 草稿、已發布、存檔 |

## 🔍 API 端點

### POST /api/articles
創建新文章到 Notion 資料庫

### GET /api/articles  
從 Notion 資料庫獲取文章列表

### GET /api/health
健康檢查，測試 Notion 連接狀態

## 🛠️ 故障排除

### 常見錯誤

#### 1. "NOTION_TOKEN環境變數未設定"
**解決方法**: 確保正確設定了 Notion API Token
```bash
export NOTION_TOKEN="secret_your_actual_token"
```

#### 2. "NOTION_DATABASE_ID環境變數未設定"
**解決方法**: 先運行 `create_notion_database.py` 創建資料庫

#### 3. "The integration doesn't have permission to read the page"
**解決方法**: 
1. 在 Notion 頁面中點擊 "Share"
2. 邀請您的集成並授予權限

#### 4. "Object not found"
**解決方法**: 檢查頁面 ID 或資料庫 ID 是否正確

### 檢查權限

確保您的集成有以下權限：
- ✅ Read content
- ✅ Update content  
- ✅ Insert content

## 📝 遷移現有資料

如果您有現有的 JSON 文章數據，可以創建遷移腳本：

```python
# migrate_to_notion.py
import json
from notion_config import NotionArticleDatabase

def migrate_articles():
    # 讀取現有 JSON 文件
    with open('static/data/articles.json', 'r', encoding='utf-8') as f:
        articles = json.load(f)
    
    # 連接 Notion 資料庫
    db = NotionArticleDatabase()
    
    # 遷移每篇文章
    for article in articles:
        result = db.create_article(article)
        if result['success']:
            print(f"✅ 遷移成功: {article['title']}")
        else:
            print(f"❌ 遷移失敗: {result['error']}")

if __name__ == "__main__":
    migrate_articles()
```

## 🔄 環境變數持久化

為了避免每次重啟終端都要重新設定環境變數，建議將它們添加到您的 shell 配置文件：

### Zsh (macOS 預設)
```bash
echo 'export NOTION_TOKEN="your_token"' >> ~/.zshrc
echo 'export NOTION_DATABASE_ID="your_db_id"' >> ~/.zshrc
source ~/.zshrc
```

### Bash
```bash
echo 'export NOTION_TOKEN="your_token"' >> ~/.bash_profile  
echo 'export NOTION_DATABASE_ID="your_db_id"' >> ~/.bash_profile
source ~/.bash_profile
```

## ✅ 驗證設定

完成所有步驟後，運行以下命令驗證：

```bash
# 1. 測試 Notion 連接
python3 notion_config.py

# 2. 啟動 Notion API 服務器
python3 notion_api_server.py

# 3. 在另一個終端測試健康檢查
curl http://localhost:8001/api/health
```

成功後，您的金融智慧平台將使用 Notion 作為資料庫！🎉

## 📞 支援

如果遇到問題：
1. 檢查 Notion 集成權限
2. 確認環境變數設定正確
3. 查看終端錯誤訊息
4. 參考故障排除部分