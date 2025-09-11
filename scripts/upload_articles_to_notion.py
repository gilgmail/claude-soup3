#!/usr/bin/env python3
"""
批量上傳文章到 Notion 數據庫
"""

import os
import sys
import re
from pathlib import Path
from notion_client import Client
from dotenv import load_dotenv

# 加載 .env 文件
load_dotenv()

def extract_article_info(file_path):
    """從 Markdown 文件中提取文章信息"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 提取標題（第一行的 # 後面的內容）
    title_match = re.match(r'^# (.+)', content)
    title = title_match.group(1) if title_match else "未命名文章"
    
    # 移除標題行，剩下的作為內容
    content_lines = content.split('\n')[1:]
    article_content = '\n'.join(content_lines).strip()
    
    # 提取引言部分（## 引言 後面到下一個 ## 之間的內容）
    intro_match = re.search(r'## 引言\n\n(.*?)\n\n## ', content, re.DOTALL)
    summary = intro_match.group(1).strip() if intro_match else ""
    
    # 提取標籤（文章末尾的 #標籤，排除標題符號）
    tags_line = content.split('\n')[-1] if content.split('\n')[-1].startswith('#') else ""
    if tags_line:
        # 提取不包含空格的標籤
        tags_match = re.findall(r'#([^\s#]+)', tags_line)
        keywords = [tag for tag in tags_match if len(tag) > 1 and not tag.isdigit()][:5]
    else:
        keywords = []
    
    # 如果沒有找到標籤，使用默認標籤
    if not keywords:
        keywords = ["財富思維", "個人成長", "投資理財"]
    
    # 計算字數（去除標記符號）
    text_content = re.sub(r'[#*`\-\n\r]', '', content)
    word_count = len(text_content)
    
    # 根據內容判斷分類
    if any(keyword in content for keyword in ['複利', '規劃', '思維']):
        category = '思維轉換'
    elif any(keyword in content for keyword in ['風險', '管理', '波動', '情緒']):
        category = '風險管理' 
    elif any(keyword in content for keyword in ['收入', '變現', '創業', '品牌']):
        category = '實戰技巧'
    elif any(keyword in content for keyword in ['失敗', '心理', '習慣', '教育']):
        category = '心理素質'
    elif any(keyword in content for keyword in ['財富', '周期', '經濟']):
        category = '財富建構'
    else:
        category = '財富建構'
    
    return {
        'title': title,
        'content': article_content,
        'summary': summary,
        'category': category,
        'keywords': keywords,
        'quality_score': 9.0,  # 設定高品質分數
        'word_count': word_count,
        'status': '已發布'
    }

def create_notion_entry(client, database_id, article_data):
    """在 Notion 中創建文章條目"""
    try:
        # 準備屬性數據
        properties = {}
        
        # 標題（使用正確的屬性名稱）
        properties['文章標題'] = {
            "title": [{"text": {"content": article_data['title']}}]
        }
        
        # 分類
        properties['主題類別'] = {
            "select": {"name": article_data['category']}
        }
        
        # 狀態
        properties['發布狀態'] = {
            "select": {"name": article_data['status']}
        }
        
        # 標籤
        properties['標籤'] = {
            "multi_select": [{"name": keyword} for keyword in article_data['keywords'][:3]]
        }
        
        # 字數
        properties['字數'] = {
            "number": article_data['word_count']
        }
        
        # 閱讀時間（估算：250字/分鐘）
        properties['閱讀時間'] = {
            "number": max(1, round(article_data['word_count'] / 250))
        }
        
        # 核心要點
        properties['核心要點'] = {
            "rich_text": [{"text": {"content": article_data['summary'][:500]}}]
        }
        
        # 發布日期
        from datetime import datetime
        properties['發布日期'] = {
            "date": {"start": datetime.now().strftime("%Y-%m-%d")}
        }
        
        # 創建頁面
        response = client.pages.create(
            parent={"database_id": database_id},
            properties=properties,
            children=[
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": article_data['summary']}}]
                    }
                },
                {
                    "object": "block", 
                    "type": "divider",
                    "divider": {}
                },
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": article_data['content'][:2000]}}]
                    }
                }
            ]
        )
        
        return response
        
    except Exception as e:
        print(f"創建條目時出錯: {e}")
        return None

def main():
    """主函數"""
    print("🚀 開始批量上傳文章到 Notion 數據庫")
    print("=" * 50)
    
    # 檢查環境變數
    notion_token = os.getenv('NOTION_TOKEN')
    database_id = os.getenv('NOTION_DATABASE_ID')
    
    if not notion_token or not database_id:
        print("❌ 請先設置 NOTION_TOKEN 和 NOTION_DATABASE_ID 環境變數")
        return
    
    try:
        # 初始化 Notion 客戶端
        client = Client(auth=notion_token)
        print(f"✅ 連接到 Notion API 成功")
        
        # 找到文章目錄
        articles_dir = Path(__file__).parent.parent / 'articles'
        if not articles_dir.exists():
            print(f"❌ 文章目錄不存在: {articles_dir}")
            return
        
        # 獲取所有文章文件
        article_files = sorted(articles_dir.glob('*.md'))
        print(f"📚 發現 {len(article_files)} 篇文章")
        
        success_count = 0
        error_count = 0
        
        for i, file_path in enumerate(article_files, 1):
            print(f"\n📝 處理文章 {i}/{len(article_files)}: {file_path.name}")
            
            try:
                # 提取文章信息
                article_data = extract_article_info(file_path)
                print(f"   標題: {article_data['title'][:50]}...")
                print(f"   分類: {article_data['category']}")
                print(f"   關鍵字: {', '.join(article_data['keywords'][:3])}")
                print(f"   字數: {article_data['word_count']}")
                
                # 創建 Notion 條目
                response = create_notion_entry(client, database_id, article_data)
                
                if response:
                    print(f"   ✅ 成功創建條目")
                    success_count += 1
                else:
                    print(f"   ❌ 創建條目失敗")
                    error_count += 1
                    
            except Exception as e:
                print(f"   ❌ 處理文章時出錯: {e}")
                error_count += 1
        
        print(f"\n🎉 上傳完成!")
        print(f"✅ 成功: {success_count} 篇")
        print(f"❌ 失敗: {error_count} 篇")
        
        if success_count > 0:
            print(f"\n🔗 請檢查您的 Notion 數據庫以確認文章已成功添加")
        
    except Exception as e:
        print(f"❌ 執行過程中出錯: {e}")

if __name__ == "__main__":
    main()