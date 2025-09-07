#!/usr/bin/env python3
"""
金融智慧平台前端服务器
简单的HTTP服务器，用于提供前端网页服务
"""

import os
import sys
import http.server
import socketserver
from urllib.parse import urlparse
import mimetypes

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class FinancialWisdomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """自定义HTTP请求处理器"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=os.path.dirname(__file__), **kwargs)
    
    def end_headers(self):
        # 添加CORS头，允许前端调用API
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        super().end_headers()
    
    def do_GET(self):
        """处理GET请求"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        # 根路径重定向到index.html
        if path == '/' or path == '':
            path = '/templates/index.html'
            self.path = path
        elif path.startswith('/static/') or path.startswith('/templates/'):
            # 保持静态文件和模板文件的原始路径
            pass  
        else:
            # 对于其他路径，重定向到主页
            path = '/templates/index.html'
            self.path = path
        
        return super().do_GET()
    
    def do_OPTIONS(self):
        """处理OPTIONS请求（CORS预检）"""
        self.send_response(200)
        self.end_headers()

def run_server(port=3000):
    """启动前端服务器"""
    print(f"🌐 金融智慧平台前端服务器")
    print(f"📁 服务目录: {os.path.dirname(__file__)}")
    print(f"🚀 启动地址: http://localhost:{port}")
    print(f"📋 主页面: http://localhost:{port}/templates/index.html")
    print(f"🔧 API文档: http://localhost:8000/docs")
    print("=" * 50)
    
    # 创建服务器
    with socketserver.TCPServer(("", port), FinancialWisdomHTTPRequestHandler) as httpd:
        print(f"✅ 前端服务器已启动在端口 {port}")
        print("按 Ctrl+C 停止服务器")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 服务器已停止")

if __name__ == '__main__':
    # 默认端口3000，可以通过命令行参数指定
    port = 3000
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print("无效端口号，使用默认端口3000")
    
    run_server(port)