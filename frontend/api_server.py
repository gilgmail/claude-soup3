#!/usr/bin/env python3
"""
API服務器 - 處理文章保存請求
提供簡單的REST API來保存生成的文章到JSON文件
"""

import os
import json
import uuid
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import socket

class ArticleAPIHandler(BaseHTTPRequestHandler):
    """處理文章API請求"""
    
    def do_OPTIONS(self):
        """處理CORS預檢請求"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
    
    def do_POST(self):
        """處理POST請求 - 保存新文章"""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/api/articles':
            try:
                # 讀取請求數據
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                article_data = json.loads(post_data.decode('utf-8'))
                
                # 保存文章到JSON文件
                success = self.save_article(article_data)
                
                if success:
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    
                    response = {
                        'success': True,
                        'message': '文章保存成功',
                        'article_id': article_data.get('id')
                    }
                    self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
                else:
                    self.send_error(500, '保存文章失敗')
                    
            except Exception as e:
                print(f"處理POST請求失敗: {e}")
                self.send_error(500, f'服務器錯誤: {str(e)}')
        else:
            self.send_error(404, '路徑未找到')
    
    def save_article(self, article_data):
        """保存文章到JSON文件"""
        try:
            articles_file = os.path.join(os.path.dirname(__file__), 'static', 'data', 'articles.json')
            
            # 讀取現有文章
            existing_articles = []
            if os.path.exists(articles_file):
                with open(articles_file, 'r', encoding='utf-8') as f:
                    existing_articles = json.load(f)
            
            # 格式化新文章數據
            formatted_article = {
                "id": str(uuid.uuid4()),
                "title": article_data.get('title', ''),
                "topic_category": article_data.get('topic_category', ''),
                "content_style": article_data.get('content_style', ''),
                "quality_score": round(article_data.get('quality_score', 9.0), 2),
                "created_at": datetime.now().isoformat(),
                "word_count": self.calculate_word_count(article_data.get('content_json', {}).get('content', '')),
                "readability_score": round(8.0 + (2.0 * (hash(article_data.get('title', '')) % 100) / 100), 1),
                "engagement_score": round(8.5 + (1.5 * (hash(article_data.get('title', '')) % 100) / 100), 1),
                "content_json": article_data.get('content_json', {}),
                "topic_keywords": self.extract_keywords(article_data.get('title', ''))
            }
            
            # 將新文章添加到開頭
            existing_articles.insert(0, formatted_article)
            
            # 保存回文件
            with open(articles_file, 'w', encoding='utf-8') as f:
                json.dump(existing_articles, f, ensure_ascii=False, indent=2)
            
            print(f"✅ 文章已保存: {formatted_article['title']}")
            return True
            
        except Exception as e:
            print(f"❌ 保存文章失敗: {e}")
            return False
    
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
            keywords = ['投資理財', '財富管理']
        
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

def run_api_server(port=8001):
    """運行API服務器"""
    try:
        port = find_free_port(port)
        server = HTTPServer(('', port), ArticleAPIHandler)
        print(f"🚀 API服務器已啟動")
        print(f"📡 監聽端口: {port}")
        print(f"🔗 API端點: http://localhost:{port}/api/articles")
        print(f"📁 數據文件: ./static/data/articles.json")
        print("=" * 50)
        print("✅ 服務器運行中...")
        print("按 Ctrl+C 停止服務器")
        
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 API服務器已停止")

if __name__ == '__main__':
    run_api_server()