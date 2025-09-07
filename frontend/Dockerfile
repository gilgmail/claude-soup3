# 金融智慧平台前端Dockerfile
FROM nginx:alpine

# 设置工作目录
WORKDIR /usr/share/nginx/html

# 复制前端文件
COPY templates/ ./
COPY static/ ./static/

# 复制nginx配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 暴露端口
EXPOSE 80

# 启动nginx
CMD ["nginx", "-g", "daemon off;"]