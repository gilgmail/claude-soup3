#!/usr/bin/env python3
"""
Notion API服務器 - 使用Notion資料庫儲存文章
提供REST API將生成的文章保存到Notion資料庫
"""

import os
import json
import uuid
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import socket
import sys

# 添加當前目錄到Python路徑以導入notion_config
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from notion_config import NotionArticleDatabase

class NotionArticleAPIHandler(BaseHTTPRequestHandler):
    """處理文章API請求 - 使用Notion儲存"""
    
    def __init__(self, *args, **kwargs):
        # 初始化Notion資料庫連接
        try:
            self.notion_db = NotionArticleDatabase()
            print("✅ Notion資料庫連接已建立")
        except Exception as e:
            print(f"❌ Notion初始化失敗: {e}")
            self.notion_db = None
        super().__init__(*args, **kwargs)
    
    def do_OPTIONS(self):
        """處理CORS預檢請求"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
    
    def do_GET(self):
        """處理GET請求 - 獲取文章列表"""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/api/articles':
            self.get_articles()
        elif parsed_path.path == '/api/health':
            self.health_check()
        else:
            self.send_error(404, '路徑未找到')
    
    def do_POST(self):
        """處理POST請求 - 保存新文章"""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/api/articles':
            try:
                # 讀取請求數據
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                article_data = json.loads(post_data.decode('utf-8'))
                
                # 檢查Notion連接
                if not self.notion_db:
                    self.send_error(500, 'Notion資料庫未初始化')
                    return
                
                # 保存文章到Notion
                result = self.save_article_to_notion(article_data)
                
                if result['success']:
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    
                    response = {
                        'success': True,
                        'message': '文章已保存到Notion',
                        'notion_page_id': result.get('notion_page_id'),
                        'title': result.get('title'),
                        'url': result.get('url')
                    }
                    self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
                else:
                    self.send_error(500, f"保存失敗: {result.get('error')}")
                    
            except Exception as e:
                print(f"處理POST請求失敗: {e}")
                self.send_error(500, f'服務器錯誤: {str(e)}')
        else:
            self.send_error(404, '路徑未找到')
    
    def save_article_to_notion(self, article_data):
        """保存文章到Notion資料庫"""
        try:
            # 格式化文章數據以符合Notion結構
            formatted_article = {
                "title": article_data.get('title', '未命名文章'),
                "topic_category": article_data.get('topic_category', '投資理財'),
                "content_style": self._map_content_style(article_data.get('content_style', 'practical_wisdom')),
                "quality_score": round(article_data.get('quality_score', 9.0), 2),
                "word_count": self.calculate_word_count(article_data.get('content_json', {}).get('content', '')),
                "readability_score": round(article_data.get('readability_score', 8.0), 1),
                "engagement_score": round(article_data.get('engagement_score', 8.5), 1),
                "content_json": article_data.get('content_json', {}),
                "topic_keywords": self.extract_keywords(article_data.get('title', ''))
            }
            
            print(f"🔄 正在保存文章到Notion: {formatted_article['title']}")
            
            # 使用NotionArticleDatabase保存
            result = self.notion_db.create_article(formatted_article)
            
            if result['success']:
                print(f"✅ 文章已保存到Notion: {formatted_article['title']}")
                # 同時保存一份到JSON文件作為備份
                self.save_backup_to_json(formatted_article)
            
            return result
            
        except Exception as e:
            print(f"❌ 保存到Notion失敗: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def save_backup_to_json(self, article_data):
        """備份文章到JSON文件"""
        try:
            backup_dir = os.path.join(os.path.dirname(__file__), 'backup')
            os.makedirs(backup_dir, exist_ok=True)
            
            backup_file = os.path.join(backup_dir, 'articles_backup.json')
            
            # 讀取現有備份
            existing_articles = []
            if os.path.exists(backup_file):
                with open(backup_file, 'r', encoding='utf-8') as f:
                    existing_articles = json.load(f)
            
            # 添加新文章
            article_with_id = {
                **article_data,
                "id": str(uuid.uuid4()),
                "backup_time": datetime.now().isoformat()
            }
            existing_articles.insert(0, article_with_id)
            
            # 保存備份（保留最近100篇）
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(existing_articles[:100], f, ensure_ascii=False, indent=2)
            
            print(f"💾 文章備份已保存")
            
        except Exception as e:
            print(f"⚠️ 備份保存失敗: {e}")
    
    def get_articles(self):
        """從Notion獲取文章列表"""
        try:
            if not self.notion_db:
                self.send_error(500, 'Notion資料庫未初始化')
                return
            
            # 從Notion查詢文章
            result = self.notion_db.query_articles(page_size=20)
            
            if 'error' in result:
                self.send_error(500, f"查詢失敗: {result['error']}")
                return
            
            # 轉換Notion頁面為前端需要的格式
            articles = []
            for page in result.get('results', []):
                article = self._convert_notion_page_to_article(page)
                if article:
                    articles.append(article)
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response = {
                'success': True,
                'articles': articles,
                'total': len(articles)
            }
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
            
        except Exception as e:
            print(f"❌ 獲取文章失敗: {e}")
            self.send_error(500, f'服務器錯誤: {str(e)}')
    
    def health_check(self):
        """健康檢查端點"""
        try:
            if self.notion_db:
                test_result = self.notion_db.test_connection()
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                
                response = {
                    'status': 'healthy' if test_result['success'] else 'unhealthy',
                    'notion_connected': test_result['success'],
                    'database_title': test_result.get('database_title', 'N/A'),
                    'timestamp': datetime.now().isoformat()
                }
                
                self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
            else:
                self.send_error(503, 'Notion未初始化')
                
        except Exception as e:
            print(f"❌ 健康檢查失敗: {e}")
            self.send_error(500, f'健康檢查錯誤: {str(e)}')
    
    def _convert_notion_page_to_article(self, page):
        """將Notion頁面轉換為文章格式"""
        try:
            properties = page.get('properties', {})
            
            # 提取屬性值
            title = self._extract_title(properties.get('標題', {}))
            topic_category = self._extract_select(properties.get('主題分類', {}))
            content_style = self._extract_select(properties.get('內容風格', {}))
            quality_score = self._extract_number(properties.get('品質評分', {}))
            word_count = self._extract_number(properties.get('字數統計', {}))
            readability_score = self._extract_number(properties.get('可讀性評分', {}))
            engagement_score = self._extract_number(properties.get('參與度評分', {}))
            created_time = self._extract_date(properties.get('創建時間', {}))
            keywords = self._extract_multi_select(properties.get('關鍵字', {}))
            
            return {
                'id': page['id'],
                'title': title,
                'topic_category': topic_category,
                'content_style': content_style,
                'quality_score': quality_score,
                'word_count': word_count,
                'readability_score': readability_score,
                'engagement_score': engagement_score,
                'created_at': created_time,
                'topic_keywords': keywords,
                'notion_url': page.get('url'),
                'content_json': {
                    'content': f'{title} 的詳細內容...',  # 簡化內容預覽
                    'summary': f'這是關於 {topic_category} 的 {content_style} 文章'
                }
            }
            
        except Exception as e:
            print(f"❌ 轉換頁面失敗: {e}")
            return None
    
    def _extract_title(self, title_prop):
        """提取標題"""
        title_list = title_prop.get('title', [])
        if title_list:
            return title_list[0].get('plain_text', '未命名文章')
        return '未命名文章'
    
    def _extract_select(self, select_prop):
        """提取選擇屬性"""
        select_obj = select_prop.get('select')
        if select_obj:
            return select_obj.get('name', '')
        return ''
    
    def _extract_number(self, number_prop):
        """提取數字屬性"""
        return number_prop.get('number', 0)
    
    def _extract_date(self, date_prop):
        """提取日期屬性"""
        date_obj = date_prop.get('date')
        if date_obj:
            return date_obj.get('start', '')
        return ''
    
    def _extract_multi_select(self, multi_select_prop):
        """提取多選屬性"""
        multi_select_list = multi_select_prop.get('multi_select', [])
        return [item.get('name', '') for item in multi_select_list]
    
    def _map_content_style(self, style):
        """映射內容風格"""
        style_map = {
            'practical_wisdom': '實用智慧',
            'philosophical_money': '哲學思考',
            'motivational_finance': '勵志財經',
            'historical_insights': '歷史洞察'
        }
        return style_map.get(style, '實用智慧')
    
    def calculate_word_count(self, content):
        """計算字數"""
        if not content:
            return 0
        # 去除HTML標籤和多餘空白
        import re
        clean_text = re.sub(r'<[^>]*>', '', content)
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        return len(clean_text)
    
    def extract_keywords(self, title):
        """從標題提取關鍵詞"""
        keywords = []
        
        keyword_map = {
            '投資': '投資',
            '理財': '理財',
            '基金': '基金', 
            '股票': '股票',
            '風險': '風險管理',
            'ESG': 'ESG',
            '比特': '數字貨幣',
            'AI': '人工智能',
            '房地產': '房地產'
        }
        
        for key, value in keyword_map.items():
            if key in title:
                keywords.append(value)
        
        # 如果沒有找到特定關鍵詞，添加通用關鍵詞
        if not keywords:
            keywords = ['投資', '理財']
        
        return keywords[:3]  # 最多3個關鍵詞

def find_free_port(start_port=8001):
    """找到可用端口"""
    for port in range(start_port, start_port + 100):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', port))
                return port
        except OSError:
            continue
    return start_port

def run_notion_api_server(port=8001):
    """運行Notion API服務器"""
    try:
        # 檢查環境變數
        if not os.getenv('NOTION_TOKEN'):
            print("❌ 錯誤: NOTION_TOKEN環境變數未設定")
            print("請設定: export NOTION_TOKEN=your_token")
            return
        
        if not os.getenv('NOTION_DATABASE_ID'):
            print("❌ 錯誤: NOTION_DATABASE_ID環境變數未設定")
            print("請先運行 create_notion_database.py 創建資料庫")
            return
        
        port = find_free_port(port)
        server = HTTPServer(('', port), NotionArticleAPIHandler)
        
        print(f"🚀 Notion API服務器已啟動")
        print(f"📡 監聽端口: {port}")
        print(f"🔗 API端點: http://localhost:{port}/api/articles")
        print(f"🏥 健康檢查: http://localhost:{port}/api/health")
        print(f"📊 資料庫: Notion Database")
        print("=" * 50)
        print("✅ 服務器運行中...")
        print("按 Ctrl+C 停止服務器")
        
        server.serve_forever()
        
    except KeyboardInterrupt:
        print("\n🛑 Notion API服務器已停止")
    except Exception as e:
        print(f"❌ 服務器啟動失敗: {e}")

if __name__ == '__main__':
    run_notion_api_server()