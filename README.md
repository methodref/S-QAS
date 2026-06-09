# S-QAS - 智能问答系统

一个基于 Flask 的轻量级智能问答系统，支持问题管理和智能匹配功能。

## 功能特性

- 智能问答匹配
- 问题管理后台
- 分类管理
- 示例数据导入

## 快速开始

### 使用 Docker（推荐）

#### 方式一：使用 Docker Compose（最简单）

```bash
# 构建并启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

服务启动后访问：
- 主页: http://localhost:8080
- 管理后台: http://localhost:8080/admin

#### 方式二：手动构建 Docker 镜像

```bash
# 1. 构建镜像
docker build -t simple-sqa:latest .

# 2. 运行容器
docker run -d \
  --name simple-sqa \
  -p 8080:8080 \
  -v $(pwd)/qa_system.db:/app/qa_system.db \
  simple-sqa:latest

# 查看容器状态
docker ps

# 查看日志
docker logs -f simple-sqa

# 停止容器
docker stop simple-sqa
docker rm simple-sqa
```

### 本地运行

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 运行应用
python app.py
# 或使用 start.sh
chmod +x start.sh && ./start.sh
```

## 项目结构

```
s-qas/
├── app.py                 # 主应用文件
├── models.py              # 数据模型
├── similarity.py          # 相似度匹配算法
├── requirements.txt       # 依赖包列表
├── Dockerfile             # Docker 构建文件
├── docker-compose.yml     # Docker Compose 配置
├── start.sh               # 启动脚本
├── templates/             # 模板文件
│   ├── index.html
│   └── admin.html
└── instance/              # 数据库文件目录
    └── qa_system.db
```

## API 文档

### 获取问题列表

```
GET /api/questions?page=1&page_size=10&search=关键词
```

### 添加问题

```
POST /api/questions
Content-Type: application/json

{
  "question": "问题内容",
  "answer": "答案内容",
  "category": "分类"
}
```

### 提问

```
POST /api/ask
Content-Type: application/json

{
  "query": "你的问题"
}
```

### 导入示例数据

```
POST /api/seed
```

## 技术栈

- Flask 3.0.0
- Flask-SQLAlchemy 3.1.1
- scikit-learn
- jieba 中文分词
- SQLite 数据库
- Gunicorn WSGI 服务器
- Docker 容器化
