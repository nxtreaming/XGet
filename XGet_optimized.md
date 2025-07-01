# XGet 优化实施方案 - 实用版

## 项目概述

基于技术验证结果，这是一个**实用优先、避免过度设计**的X(Twitter)数据采集系统方案。专注于核心功能的快速实现和稳定运行。

## 核心原则

1. **简单有效** - 优先选择最简单可行的解决方案
2. **快速迭代** - 先实现基础功能，后续按需优化
3. **实用导向** - 每个组件都有明确的业务价值
4. **易于维护** - 代码结构清晰，便于理解和修改

## 🎯 简化技术栈

### 核心组件（MVP版本）
```
📦 XGet项目结构
├── 🐍 Python 3.12 (已验证)
├── 🔧 twscrape (数据采集)
├── 🎭 Playwright (cookies管理)
├── 📁 SQLite (数据存储)
├── ⚡ FastAPI (API接口)
└── 📝 Python logging (日志)
```

### 避免的复杂组件
- ❌ Redis/MongoDB (初期不需要)
- ❌ Celery任务队列 (同步处理足够)
- ❌ 复杂监控系统 (基础日志即可)
- ❌ 微服务架构 (单体应用更简单)
- ❌ 容器化部署 (直接运行更快)

## 🏗️ 简化架构设计

```text
┌─────────────────────────────────────────────┐
│              XGet 简化架构                   │
├─────────────────┬─────────────────┬─────────┤
│   🌐 API层      │   🔧 业务层      │  💾 数据层│
│   FastAPI       │   采集管理       │  SQLite  │
└─────────────────┴─────────────────┴─────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
   🍪 Playwright    📊 twscrape    📝 Logging
   (获取cookies)    (数据采集)     (记录日志)
```

## 📁 项目结构

```
xget/
├── main.py              # 主程序入口
├── config.py            # 配置管理
├── models.py            # 数据模型
├── scraper.py           # 采集核心
├── auth_manager.py      # 认证管理
├── api.py               # API接口
├── database.py          # 数据库操作
├── utils.py             # 工具函数
├── requirements.txt     # 依赖包
├── config.yaml          # 配置文件
└── logs/                # 日志目录
```

## 🔧 核心模块设计

### 1. 配置管理 (config.py)
```python
from pydantic import BaseSettings
from typing import List

class Settings(BaseSettings):
    # 基础配置
    debug: bool = False
    log_level: str = "INFO"
    
    # 数据库配置
    database_url: str = "sqlite:///xget.db"
    
    # API配置
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    
    # Twitter账号配置
    twitter_accounts: List[dict] = []
    
    # 采集配置
    default_tweet_limit: int = 100
    request_delay: float = 1.0
    
    class Config:
        env_file = ".env"

settings = Settings()
```

### 2. 数据模型 (models.py)
```python
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class Tweet(BaseModel):
    id: str
    text: str
    user_id: str
    username: str
    created_at: datetime
    retweet_count: int = 0
    like_count: int = 0
    reply_count: int = 0
    collected_at: datetime

class User(BaseModel):
    user_id: str
    username: str
    display_name: str
    description: Optional[str] = None
    followers_count: int = 0
    following_count: int = 0
    tweet_count: int = 0
    collected_at: datetime

class SearchTask(BaseModel):
    id: Optional[int] = None
    keyword: str
    limit: int = 100
    status: str = "pending"  # pending, running, completed, failed
    created_at: datetime
    completed_at: Optional[datetime] = None
    result_count: int = 0
    error_message: Optional[str] = None
```

### 3. 简化采集器 (scraper.py)
```python
import asyncio
import logging
from twscrape import API
from typing import List, Optional
from datetime import datetime

class SimpleTwitterScraper:
    """简化版Twitter采集器"""
    
    def __init__(self):
        self.api = API()
        self.logger = logging.getLogger(__name__)
    
    async def search_tweets(self, keyword: str, limit: int = 100) -> List[dict]:
        """搜索推文"""
        tweets = []
        try:
            async for tweet in self.api.search(keyword, limit=limit):
                tweet_data = {
                    'id': tweet.id,
                    'text': tweet.rawContent,
                    'user_id': tweet.user.id,
                    'username': tweet.user.username,
                    'created_at': tweet.date,
                    'retweet_count': tweet.retweetCount,
                    'like_count': tweet.likeCount,
                    'reply_count': tweet.replyCount,
                    'collected_at': datetime.utcnow()
                }
                tweets.append(tweet_data)
                
                # 简单的延迟控制
                await asyncio.sleep(0.5)
                
        except Exception as e:
            self.logger.error(f"搜索失败: {e}")
            raise
            
        return tweets
    
    async def get_user_info(self, username: str) -> Optional[dict]:
        """获取用户信息"""
        try:
            user = await self.api.user_by_login(username)
            if not user:
                return None
                
            return {
                'user_id': user.id,
                'username': user.username,
                'display_name': user.displayname,
                'description': user.description,
                'followers_count': user.followersCount,
                'following_count': user.followingCount,
                'tweet_count': user.statusesCount,
                'collected_at': datetime.utcnow()
            }
        except Exception as e:
            self.logger.error(f"获取用户信息失败: {e}")
            return None
```

### 4. 简化API (api.py)
```python
from fastapi import FastAPI, HTTPException
from typing import List
import asyncio

app = FastAPI(title="XGet API", version="1.0.0")

@app.get("/")
async def root():
    return {"message": "XGet API is running"}

@app.post("/search")
async def search_tweets(keyword: str, limit: int = 100):
    """搜索推文"""
    try:
        scraper = SimpleTwitterScraper()
        tweets = await scraper.search_tweets(keyword, limit)
        
        # 保存到数据库
        db = get_database()
        saved_count = db.save_tweets(tweets)
        
        return {
            "status": "success",
            "keyword": keyword,
            "found": len(tweets),
            "saved": saved_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tweets")
async def get_tweets(limit: int = 50):
    """获取已采集的推文"""
    db = get_database()
    tweets = db.get_tweets(limit)
    return {"tweets": tweets}

@app.get("/stats")
async def get_stats():
    """获取统计信息"""
    db = get_database()
    stats = db.get_stats()
    return stats
```

## 🚀 快速开始

### 1. 环境准备
```bash
# 创建虚拟环境
python -m venv venv_py312
source venv_py312/bin/activate  # Linux/Mac
# 或 venv_py312\Scripts\activate  # Windows

# 安装依赖
pip install twscrape playwright fastapi uvicorn pydantic sqlalchemy
playwright install chromium
```

### 2. 配置账号
```bash
# 添加Twitter账号
twscrape add_accounts accounts.txt
twscrape login_accounts
```

### 3. 运行程序
```bash
# 启动API服务
python main.py

# 或直接使用
uvicorn api:app --host 0.0.0.0 --port 8000
```

## 📈 后续优化路径

### 阶段1：基础功能 (当前)
- ✅ 基础数据采集
- ✅ 简单API接口
- ✅ SQLite存储

### 阶段2：功能增强
- 🔄 添加任务队列 (如需要)
- 🔄 改用PostgreSQL (数据量大时)
- 🔄 添加基础监控

### 阶段3：生产优化
- 🔄 容器化部署
- 🔄 负载均衡
- 🔄 高可用架构

## 💡 实施建议

1. **先跑起来** - 用最简单的方式实现核心功能
2. **逐步优化** - 根据实际使用情况决定优化方向
3. **监控关键指标** - 采集成功率、响应时间、错误率
4. **保持简单** - 不要为了技术而技术

这个方案的核心思想是：**先让系统工作，再让系统工作得更好**。

## 🔧 关键实现细节

### 5. 数据库操作 (database.py)
```python
import sqlite3
from typing import List, Dict, Optional
from datetime import datetime
import json

class SimpleDatabase:
    """简化数据库操作"""

    def __init__(self, db_path: str = "xget.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """初始化数据库表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 推文表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tweets (
                id TEXT PRIMARY KEY,
                text TEXT NOT NULL,
                user_id TEXT,
                username TEXT,
                created_at TEXT,
                retweet_count INTEGER DEFAULT 0,
                like_count INTEGER DEFAULT 0,
                reply_count INTEGER DEFAULT 0,
                collected_at TEXT,
                raw_data TEXT
            )
        ''')

        # 用户表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                username TEXT,
                display_name TEXT,
                description TEXT,
                followers_count INTEGER DEFAULT 0,
                following_count INTEGER DEFAULT 0,
                tweet_count INTEGER DEFAULT 0,
                collected_at TEXT
            )
        ''')

        # 搜索任务表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS search_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                keyword TEXT NOT NULL,
                limit_count INTEGER DEFAULT 100,
                status TEXT DEFAULT 'pending',
                created_at TEXT,
                completed_at TEXT,
                result_count INTEGER DEFAULT 0,
                error_message TEXT
            )
        ''')

        conn.commit()
        conn.close()

    def save_tweets(self, tweets: List[Dict]) -> int:
        """保存推文数据"""
        if not tweets:
            return 0

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        saved_count = 0
        for tweet in tweets:
            try:
                cursor.execute('''
                    INSERT OR REPLACE INTO tweets
                    (id, text, user_id, username, created_at, retweet_count,
                     like_count, reply_count, collected_at, raw_data)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    tweet['id'],
                    tweet['text'],
                    tweet['user_id'],
                    tweet['username'],
                    tweet['created_at'].isoformat() if isinstance(tweet['created_at'], datetime) else tweet['created_at'],
                    tweet.get('retweet_count', 0),
                    tweet.get('like_count', 0),
                    tweet.get('reply_count', 0),
                    tweet['collected_at'].isoformat() if isinstance(tweet['collected_at'], datetime) else tweet['collected_at'],
                    json.dumps(tweet)
                ))
                saved_count += 1
            except Exception as e:
                print(f"保存推文失败: {e}")
                continue

        conn.commit()
        conn.close()
        return saved_count

    def get_tweets(self, limit: int = 50) -> List[Dict]:
        """获取推文数据"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, text, username, created_at, retweet_count, like_count, reply_count
            FROM tweets
            ORDER BY collected_at DESC
            LIMIT ?
        ''', (limit,))

        tweets = []
        for row in cursor.fetchall():
            tweets.append({
                'id': row[0],
                'text': row[1],
                'username': row[2],
                'created_at': row[3],
                'retweet_count': row[4],
                'like_count': row[5],
                'reply_count': row[6]
            })

        conn.close()
        return tweets

    def get_stats(self) -> Dict:
        """获取统计信息"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 推文总数
        cursor.execute('SELECT COUNT(*) FROM tweets')
        tweet_count = cursor.fetchone()[0]

        # 用户总数
        cursor.execute('SELECT COUNT(*) FROM users')
        user_count = cursor.fetchone()[0]

        # 今日采集数
        cursor.execute('''
            SELECT COUNT(*) FROM tweets
            WHERE date(collected_at) = date('now')
        ''')
        today_count = cursor.fetchone()[0]

        conn.close()

        return {
            'total_tweets': tweet_count,
            'total_users': user_count,
            'today_tweets': today_count
        }

# 全局数据库实例
_db_instance = None

def get_database() -> SimpleDatabase:
    """获取数据库实例"""
    global _db_instance
    if _db_instance is None:
        _db_instance = SimpleDatabase()
    return _db_instance
```

### 6. 认证管理 (auth_manager.py)
```python
import asyncio
import logging
from playwright.async_api import async_playwright
from typing import Dict, List, Optional
import json
import os

class SimpleAuthManager:
    """简化认证管理"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.cookies_dir = "cookies"
        os.makedirs(self.cookies_dir, exist_ok=True)

    async def login_and_save_cookies(self, username: str, password: str, email: str) -> bool:
        """登录并保存cookies"""
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=False)
                page = await browser.new_page()

                # 访问Twitter登录页
                await page.goto("https://twitter.com/login")
                await page.wait_for_timeout(3000)

                # 输入用户名/邮箱
                await page.fill('input[name="text"]', username)
                await page.click('div[role="button"]:has-text("Next")')
                await page.wait_for_timeout(2000)

                # 如果需要输入邮箱验证
                try:
                    email_input = page.locator('input[name="text"]')
                    if await email_input.is_visible():
                        await email_input.fill(email)
                        await page.click('div[role="button"]:has-text("Next")')
                        await page.wait_for_timeout(2000)
                except:
                    pass

                # 输入密码
                await page.fill('input[name="password"]', password)
                await page.click('div[data-testid="LoginForm_Login_Button"]')

                # 等待登录完成
                await page.wait_for_url("https://twitter.com/home", timeout=30000)

                # 保存cookies
                cookies = await page.context.cookies()
                cookies_file = os.path.join(self.cookies_dir, f"{username}.json")
                with open(cookies_file, 'w') as f:
                    json.dump(cookies, f, indent=2)

                await browser.close()

                self.logger.info(f"账号 {username} 登录成功，cookies已保存")
                return True

        except Exception as e:
            self.logger.error(f"账号 {username} 登录失败: {e}")
            return False

    def load_cookies(self, username: str) -> Optional[List[Dict]]:
        """加载cookies"""
        cookies_file = os.path.join(self.cookies_dir, f"{username}.json")
        if os.path.exists(cookies_file):
            with open(cookies_file, 'r') as f:
                return json.load(f)
        return None

    def list_available_accounts(self) -> List[str]:
        """列出可用账号"""
        accounts = []
        for file in os.listdir(self.cookies_dir):
            if file.endswith('.json'):
                accounts.append(file[:-5])  # 移除.json后缀
        return accounts
```

### 7. 主程序 (main.py)
```python
import asyncio
import logging
import uvicorn
from config import settings
from api import app
from database import get_database

# 配置日志
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/xget.log'),
        logging.StreamHandler()
    ]
)

def main():
    """主程序入口"""
    # 初始化数据库
    db = get_database()
    logging.info("数据库初始化完成")

    # 启动API服务
    logging.info(f"启动API服务: http://{settings.api_host}:{settings.api_port}")
    uvicorn.run(
        app,
        host=settings.api_host,
        port=settings.api_port,
        log_level=settings.log_level.lower()
    )

if __name__ == "__main__":
    main()
```

## 🎯 使用示例

### 命令行使用
```bash
# 1. 启动服务
python main.py

# 2. 搜索推文
curl -X POST "http://localhost:8000/search?keyword=python&limit=50"

# 3. 查看结果
curl "http://localhost:8000/tweets?limit=10"

# 4. 查看统计
curl "http://localhost:8000/stats"
```

### Python脚本使用
```python
import asyncio
from scraper import SimpleTwitterScraper
from database import get_database

async def example_usage():
    # 初始化
    scraper = SimpleTwitterScraper()
    db = get_database()

    # 搜索推文
    tweets = await scraper.search_tweets("python", limit=20)
    print(f"找到 {len(tweets)} 条推文")

    # 保存到数据库
    saved = db.save_tweets(tweets)
    print(f"保存了 {saved} 条推文")

    # 查看统计
    stats = db.get_stats()
    print(f"数据库统计: {stats}")

if __name__ == "__main__":
    asyncio.run(example_usage())
```

## 📦 依赖文件

### requirements.txt
```
twscrape==0.17.0
playwright==1.53.0
fastapi==0.104.1
uvicorn==0.24.0
pydantic==2.5.0
pydantic-settings==2.1.0
httpx==0.28.1
aiofiles==23.2.1
python-multipart==0.0.6
```

### config.yaml (可选配置文件)
```yaml
# XGet 配置文件
app:
  name: "XGet"
  version: "1.0.0"
  debug: false

api:
  host: "127.0.0.1"
  port: 8000

database:
  path: "data/xget.db"

logging:
  level: "INFO"
  file: "logs/xget.log"

scraper:
  default_limit: 100
  request_delay: 1.0
  max_retries: 3

accounts:
  # 在这里配置Twitter账号信息
  # - username: "your_username"
  #   password: "your_password"
  #   email: "your_email@gmail.com"
```

### .env (环境变量文件)
```bash
# 开发环境配置
DEBUG=true
LOG_LEVEL=DEBUG
API_HOST=127.0.0.1
API_PORT=8000

# 数据库配置
DATABASE_URL=sqlite:///data/xget.db

# Twitter配置 (可选，也可以通过twscrape命令行添加)
# TWITTER_USERNAME=your_username
# TWITTER_PASSWORD=your_password
# TWITTER_EMAIL=your_email@gmail.com
```

## 🚀 快速部署指南

### 1. 本地开发部署
```bash
# 克隆或创建项目目录
mkdir xget && cd xget

# 创建虚拟环境
python -m venv venv_py312
source venv_py312/bin/activate

# 安装依赖
pip install -r requirements.txt
playwright install chromium

# 创建必要目录
mkdir -p logs data cookies

# 配置账号 (手动方式)
twscrape add_accounts accounts.txt
twscrape login_accounts

# 启动服务
python main.py
```

### 2. 生产环境部署 (简化版)
```bash
# 使用systemd服务 (Linux)
sudo tee /etc/systemd/system/xget.service > /dev/null <<EOF
[Unit]
Description=XGet Twitter Scraper
After=network.target

[Service]
Type=simple
User=xget
WorkingDirectory=/opt/xget
Environment=PATH=/opt/xget/venv_py312/bin
ExecStart=/opt/xget/venv_py312/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 启动服务
sudo systemctl enable xget
sudo systemctl start xget
sudo systemctl status xget
```

### 3. Docker部署 (可选)
```dockerfile
# Dockerfile
FROM python:3.12-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 安装Playwright
RUN playwright install chromium
RUN playwright install-deps chromium

# 复制应用代码
COPY . .

# 创建必要目录
RUN mkdir -p logs data cookies

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["python", "main.py"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  xget:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
      - ./cookies:/app/cookies
    environment:
      - DEBUG=false
      - LOG_LEVEL=INFO
    restart: unless-stopped
```

## 🔧 实用工具脚本

### 账号管理脚本 (tools/account_manager.py)
```python
#!/usr/bin/env python3
"""账号管理工具"""

import asyncio
import sys
from auth_manager import SimpleAuthManager

async def add_account():
    """添加新账号"""
    username = input("请输入用户名: ")
    password = input("请输入密码: ")
    email = input("请输入邮箱: ")

    auth_manager = SimpleAuthManager()
    success = await auth_manager.login_and_save_cookies(username, password, email)

    if success:
        print(f"✅ 账号 {username} 添加成功")

        # 同时添加到twscrape
        import subprocess
        result = subprocess.run([
            'twscrape', 'add_account', username, password, email, password
        ], capture_output=True, text=True)

        if result.returncode == 0:
            print("✅ 已同步到twscrape")
        else:
            print(f"⚠️ twscrape同步失败: {result.stderr}")
    else:
        print(f"❌ 账号 {username} 添加失败")

def list_accounts():
    """列出所有账号"""
    auth_manager = SimpleAuthManager()
    accounts = auth_manager.list_available_accounts()

    if accounts:
        print("📋 可用账号列表:")
        for i, account in enumerate(accounts, 1):
            print(f"  {i}. {account}")
    else:
        print("❌ 没有找到可用账号")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使用方法:")
        print("  python account_manager.py add    # 添加账号")
        print("  python account_manager.py list   # 列出账号")
        sys.exit(1)

    command = sys.argv[1]
    if command == "add":
        asyncio.run(add_account())
    elif command == "list":
        list_accounts()
    else:
        print(f"未知命令: {command}")
```

### 数据导出脚本 (tools/export_data.py)
```python
#!/usr/bin/env python3
"""数据导出工具"""

import csv
import json
import sys
from database import get_database

def export_to_csv(filename: str, limit: int = None):
    """导出到CSV文件"""
    db = get_database()
    tweets = db.get_tweets(limit or 10000)

    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['id', 'text', 'username', 'created_at', 'retweet_count', 'like_count', 'reply_count']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for tweet in tweets:
            writer.writerow(tweet)

    print(f"✅ 已导出 {len(tweets)} 条推文到 {filename}")

def export_to_json(filename: str, limit: int = None):
    """导出到JSON文件"""
    db = get_database()
    tweets = db.get_tweets(limit or 10000)

    with open(filename, 'w', encoding='utf-8') as jsonfile:
        json.dump(tweets, jsonfile, ensure_ascii=False, indent=2)

    print(f"✅ 已导出 {len(tweets)} 条推文到 {filename}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("使用方法:")
        print("  python export_data.py csv output.csv [limit]")
        print("  python export_data.py json output.json [limit]")
        sys.exit(1)

    format_type = sys.argv[1]
    filename = sys.argv[2]
    limit = int(sys.argv[3]) if len(sys.argv) > 3 else None

    if format_type == "csv":
        export_to_csv(filename, limit)
    elif format_type == "json":
        export_to_json(filename, limit)
    else:
        print(f"不支持的格式: {format_type}")
```

## 📊 监控和维护

### 简单的健康检查脚本 (tools/health_check.py)
```python
#!/usr/bin/env python3
"""健康检查工具"""

import requests
import sys
from datetime import datetime

def check_api_health(base_url: str = "http://localhost:8000"):
    """检查API健康状态"""
    try:
        # 检查根路径
        response = requests.get(f"{base_url}/", timeout=5)
        if response.status_code == 200:
            print("✅ API服务正常")
        else:
            print(f"❌ API服务异常: {response.status_code}")
            return False

        # 检查统计信息
        response = requests.get(f"{base_url}/stats", timeout=5)
        if response.status_code == 200:
            stats = response.json()
            print(f"📊 数据统计: {stats}")
        else:
            print("⚠️ 无法获取统计信息")

        return True

    except requests.exceptions.RequestException as e:
        print(f"❌ API连接失败: {e}")
        return False

def check_database_health():
    """检查数据库健康状态"""
    try:
        from database import get_database
        db = get_database()
        stats = db.get_stats()
        print(f"✅ 数据库正常: {stats}")
        return True
    except Exception as e:
        print(f"❌ 数据库异常: {e}")
        return False

if __name__ == "__main__":
    print(f"🔍 XGet健康检查 - {datetime.now()}")
    print("-" * 40)

    api_ok = check_api_health()
    db_ok = check_database_health()

    if api_ok and db_ok:
        print("\n✅ 系统运行正常")
        sys.exit(0)
    else:
        print("\n❌ 系统存在问题")
        sys.exit(1)
```

## 🎯 最佳实践和常见问题

### 账号管理最佳实践
```python
# 简单的账号轮换策略
class SimpleAccountRotator:
    def __init__(self):
        self.accounts = []
        self.current_index = 0
        self.load_accounts()

    def load_accounts(self):
        """加载可用账号"""
        auth_manager = SimpleAuthManager()
        self.accounts = auth_manager.list_available_accounts()

    def get_next_account(self):
        """获取下一个账号"""
        if not self.accounts:
            return None

        account = self.accounts[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.accounts)
        return account
```

### 错误处理和重试机制
```python
import time
import random
from functools import wraps

def retry_on_error(max_retries=3, delay_range=(1, 5)):
    """重试装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise e

                    delay = random.uniform(*delay_range)
                    print(f"重试 {attempt + 1}/{max_retries}，等待 {delay:.1f}s: {e}")
                    await asyncio.sleep(delay)

        return wrapper
    return decorator

# 使用示例
class RobustScraper(SimpleTwitterScraper):
    @retry_on_error(max_retries=3)
    async def search_tweets_robust(self, keyword: str, limit: int = 100):
        """带重试的搜索"""
        return await self.search_tweets(keyword, limit)
```

### 数据验证和清洗
```python
from pydantic import BaseModel, validator
import re

class CleanTweet(BaseModel):
    id: str
    text: str
    username: str
    created_at: str

    @validator('text')
    def clean_text(cls, v):
        """清理推文文本"""
        # 移除多余空白
        v = re.sub(r'\s+', ' ', v).strip()
        # 移除特殊字符（可选）
        # v = re.sub(r'[^\w\s#@]', '', v)
        return v

    @validator('username')
    def validate_username(cls, v):
        """验证用户名格式"""
        if not v or not v.replace('_', '').isalnum():
            raise ValueError('Invalid username format')
        return v.lower()

def clean_tweet_data(raw_tweets):
    """清洗推文数据"""
    cleaned_tweets = []
    for tweet in raw_tweets:
        try:
            clean_tweet = CleanTweet(**tweet)
            cleaned_tweets.append(clean_tweet.dict())
        except Exception as e:
            print(f"数据清洗失败: {e}, 原始数据: {tweet}")
            continue
    return cleaned_tweets
```

## 🔧 实用工具和脚本

### 批量搜索脚本
```python
# tools/batch_search.py
import asyncio
import csv
from scraper import SimpleTwitterScraper
from database import get_database

async def batch_search_from_file(keywords_file: str):
    """从文件批量搜索关键词"""
    scraper = SimpleTwitterScraper()
    db = get_database()

    # 读取关键词
    with open(keywords_file, 'r', encoding='utf-8') as f:
        keywords = [line.strip() for line in f if line.strip()]

    print(f"开始批量搜索 {len(keywords)} 个关键词...")

    for i, keyword in enumerate(keywords, 1):
        try:
            print(f"[{i}/{len(keywords)}] 搜索: {keyword}")
            tweets = await scraper.search_tweets(keyword, limit=50)
            saved = db.save_tweets(tweets)
            print(f"  ✅ 找到 {len(tweets)} 条，保存 {saved} 条")

            # 避免请求过快
            await asyncio.sleep(2)

        except Exception as e:
            print(f"  ❌ 搜索失败: {e}")
            continue

    print("批量搜索完成！")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("使用方法: python batch_search.py keywords.txt")
        sys.exit(1)

    asyncio.run(batch_search_from_file(sys.argv[1]))
```

### 数据统计脚本
```python
# tools/data_stats.py
import sqlite3
from collections import Counter
import matplotlib.pyplot as plt
import pandas as pd

def analyze_tweet_data(db_path="xget.db"):
    """分析推文数据"""
    conn = sqlite3.connect(db_path)

    # 基础统计
    df = pd.read_sql_query("""
        SELECT username, created_at, retweet_count, like_count,
               length(text) as text_length
        FROM tweets
    """, conn)

    print("📊 数据统计报告")
    print("=" * 40)
    print(f"总推文数: {len(df)}")
    print(f"用户数: {df['username'].nunique()}")
    print(f"平均文本长度: {df['text_length'].mean():.1f}")
    print(f"平均转发数: {df['retweet_count'].mean():.1f}")
    print(f"平均点赞数: {df['like_count'].mean():.1f}")

    # 热门用户
    print("\n🔥 最活跃用户 (Top 10):")
    top_users = df['username'].value_counts().head(10)
    for user, count in top_users.items():
        print(f"  {user}: {count} 条推文")

    # 时间分布
    df['hour'] = pd.to_datetime(df['created_at']).dt.hour
    print("\n⏰ 发推时间分布:")
    hour_dist = df['hour'].value_counts().sort_index()
    for hour, count in hour_dist.items():
        print(f"  {hour:02d}:00 - {count} 条")

    conn.close()

if __name__ == "__main__":
    analyze_tweet_data()
```

## 🚀 部署和运维

### 简单的进程管理脚本
```bash
#!/bin/bash
# scripts/xget_service.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
PID_FILE="$PROJECT_DIR/xget.pid"
LOG_FILE="$PROJECT_DIR/logs/xget.log"

start() {
    if [ -f "$PID_FILE" ]; then
        echo "XGet 已在运行 (PID: $(cat $PID_FILE))"
        return 1
    fi

    echo "启动 XGet 服务..."
    cd "$PROJECT_DIR"
    source venv_py312/bin/activate
    nohup python main.py > "$LOG_FILE" 2>&1 &
    echo $! > "$PID_FILE"
    echo "XGet 服务已启动 (PID: $!)"
}

stop() {
    if [ ! -f "$PID_FILE" ]; then
        echo "XGet 服务未运行"
        return 1
    fi

    PID=$(cat "$PID_FILE")
    echo "停止 XGet 服务 (PID: $PID)..."
    kill "$PID"
    rm -f "$PID_FILE"
    echo "XGet 服务已停止"
}

status() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null; then
            echo "XGet 服务运行中 (PID: $PID)"
        else
            echo "XGet 服务异常 (PID文件存在但进程不存在)"
            rm -f "$PID_FILE"
        fi
    else
        echo "XGet 服务未运行"
    fi
}

case "$1" in
    start)   start ;;
    stop)    stop ;;
    restart) stop; sleep 2; start ;;
    status)  status ;;
    *)       echo "使用方法: $0 {start|stop|restart|status}" ;;
esac
```

### 日志轮转配置
```bash
# /etc/logrotate.d/xget
/opt/xget/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 xget xget
    postrotate
        # 重启服务以重新打开日志文件
        /opt/xget/scripts/xget_service.sh restart > /dev/null 2>&1 || true
    endscript
}
```

## 📈 监控和告警

### 简单的监控脚本
```python
# tools/monitor.py
import time
import requests
import smtplib
from email.mime.text import MIMEText
from datetime import datetime

class SimpleMonitor:
    def __init__(self, api_url="http://localhost:8000", check_interval=300):
        self.api_url = api_url
        self.check_interval = check_interval
        self.last_alert_time = 0
        self.alert_cooldown = 3600  # 1小时内不重复告警

    def check_health(self):
        """健康检查"""
        try:
            response = requests.get(f"{self.api_url}/stats", timeout=10)
            if response.status_code == 200:
                stats = response.json()
                return True, stats
            else:
                return False, f"HTTP {response.status_code}"
        except Exception as e:
            return False, str(e)

    def send_alert(self, message):
        """发送告警（可以扩展为邮件、微信等）"""
        current_time = time.time()
        if current_time - self.last_alert_time < self.alert_cooldown:
            return  # 冷却期内不发送

        print(f"🚨 ALERT: {message}")
        # 这里可以添加邮件发送逻辑
        self.last_alert_time = current_time

    def run(self):
        """运行监控"""
        print(f"开始监控 XGet 服务 ({self.api_url})")

        while True:
            try:
                is_healthy, result = self.check_health()

                if is_healthy:
                    print(f"✅ {datetime.now()}: 服务正常 - {result}")
                else:
                    error_msg = f"服务异常: {result}"
                    print(f"❌ {datetime.now()}: {error_msg}")
                    self.send_alert(error_msg)

                time.sleep(self.check_interval)

            except KeyboardInterrupt:
                print("\n监控已停止")
                break
            except Exception as e:
                print(f"监控异常: {e}")
                time.sleep(60)

if __name__ == "__main__":
    monitor = SimpleMonitor()
    monitor.run()
```

## 🎯 常见问题和解决方案

### Q1: 账号登录失败
**问题**: twscrape 或 Playwright 登录 Twitter 失败

**解决方案**:
```bash
# 方案1: 重新配置账号
twscrape delete_accounts
twscrape add_accounts accounts.txt
twscrape login_accounts

# 方案2: 手动获取 cookies
python tools/account_manager.py add

# 方案3: 检查账号状态
twscrape accounts
```

### Q2: 数据采集速度慢或失败
**问题**: 搜索推文时速度很慢或经常失败

**解决方案**:
```python
# 调整采集参数
class OptimizedScraper(SimpleTwitterScraper):
    async def search_tweets_optimized(self, keyword: str, limit: int = 100):
        tweets = []
        batch_size = 20

        try:
            async for tweet in self.api.search(keyword, limit=limit):
                tweets.append(self.process_tweet(tweet))

                # 每批次后短暂休息
                if len(tweets) % batch_size == 0:
                    await asyncio.sleep(1)

        except Exception as e:
            self.logger.warning(f"搜索中断: {e}, 已获取 {len(tweets)} 条")

        return tweets
```

### Q3: 数据库文件过大
**问题**: SQLite 文件越来越大，影响性能

**解决方案**:
```python
# 数据清理和压缩
def maintain_database():
    """数据库维护"""
    conn = sqlite3.connect("xget.db")
    cursor = conn.cursor()

    # 1. 删除30天前的数据
    cursor.execute('''
        DELETE FROM tweets
        WHERE date(collected_at) < date('now', '-30 days')
    ''')

    # 2. 压缩数据库
    cursor.execute('VACUUM')

    # 3. 重建索引
    cursor.execute('REINDEX')

    conn.commit()
    conn.close()
    print("数据库维护完成")

# 定期执行（可以用 cron 定时任务）
# 0 2 * * 0 cd /opt/xget && python -c "from tools.maintenance import maintain_database; maintain_database()"
```

### Q4: API 服务无响应
**问题**: FastAPI 服务启动后无法访问

**解决方案**:
```bash
# 检查端口占用
netstat -tlnp | grep :8000

# 检查防火墙
sudo ufw status
sudo ufw allow 8000

# 检查服务日志
tail -f logs/xget.log

# 重启服务
./scripts/xget_service.sh restart
```

## 🚀 5分钟快速开始

### 步骤1: 环境准备
```bash
# 创建项目目录
mkdir xget && cd xget

# 创建虚拟环境
python3 -m venv venv_py312
source venv_py312/bin/activate

# 安装依赖
pip install twscrape playwright fastapi uvicorn pydantic
playwright install chromium
```

### 步骤2: 创建核心文件
```bash
# 创建必要目录
mkdir -p logs data cookies tools scripts

# 复制上面的代码到对应文件
# main.py, config.py, models.py, scraper.py,
# auth_manager.py, api.py, database.py
```

### 步骤3: 配置账号
```bash
# 方法1: 使用 twscrape (推荐)
echo "username:password:email:email" > accounts.txt
twscrape add_accounts accounts.txt
twscrape login_accounts

# 方法2: 手动获取 cookies
python tools/account_manager.py add
```

### 步骤4: 启动服务
```bash
# 启动 API 服务
python main.py

# 或者后台运行
nohup python main.py > logs/xget.log 2>&1 &
```

### 步骤5: 测试功能
```bash
# 测试 API
curl "http://localhost:8000/"

# 搜索推文
curl -X POST "http://localhost:8000/search?keyword=python&limit=10"

# 查看结果
curl "http://localhost:8000/tweets?limit=5"

# 查看统计
curl "http://localhost:8000/stats"
```

## 📋 项目检查清单

### 部署前检查
- [ ] Python 3.12+ 环境已安装
- [ ] 所有依赖包已安装
- [ ] Twitter 账号已配置并测试
- [ ] 数据库文件可正常创建
- [ ] API 服务可正常启动
- [ ] 日志目录有写入权限

### 运行中监控
- [ ] API 服务响应正常
- [ ] 数据采集功能正常
- [ ] 数据库正常写入
- [ ] 日志文件正常记录
- [ ] 磁盘空间充足
- [ ] 账号状态正常

### 定期维护
- [ ] 每周检查账号状态
- [ ] 每月清理旧数据
- [ ] 每月备份数据库
- [ ] 每季度更新依赖包
- [ ] 定期查看错误日志

## 🎉 总结

这个 **XGet 优化实施方案** 的核心特点：

### ✅ 优势
1. **简单实用** - 避免过度设计，专注核心功能
2. **快速上手** - 最少依赖，最简配置，5分钟可运行
3. **易于维护** - 清晰的代码结构，完善的工具脚本
4. **渐进升级** - 支持从简单到复杂的平滑演进
5. **生产可用** - 包含必要的错误处理、日志、监控

### 🎯 适用场景
- **个人项目** - 快速搭建 Twitter 数据采集系统
- **小团队** - 简单的社交媒体数据分析
- **原型验证** - 快速验证数据采集可行性
- **学习研究** - 了解社交媒体数据采集技术

### 🔄 升级路径
1. **第一阶段**: 使用当前方案，验证核心功能
2. **第二阶段**: 根据数据量和并发需求，升级数据库和缓存
3. **第三阶段**: 根据业务需求，添加更多高级功能

### 💡 核心理念
**先让系统工作，再让系统工作得更好！**

不要一开始就追求完美的架构，而是：
1. 快速实现核心功能
2. 在使用中发现问题
3. 针对性地优化改进
4. 逐步演进到理想状态

这样既能快速看到效果，又能避免过度设计的陷阱。🚀

## 🎯 最佳实践

### 1. 账号管理建议
- **多账号轮换**: 准备3-5个测试账号，避免单账号过度使用
- **定期检查**: 每周检查账号状态，及时处理异常
- **备份cookies**: 定期备份cookies文件，避免重复登录

### 2. 数据采集建议
- **合理限速**: 每次请求间隔1-2秒，避免触发限制
- **小批量采集**: 每次采集100-500条数据，避免一次性大量请求
- **错误重试**: 设置合理的重试机制，但不要无限重试

### 3. 数据存储建议
- **定期备份**: 每天备份SQLite数据库文件
- **数据清理**: 定期清理过期或无用数据
- **索引优化**: 为常用查询字段添加索引

### 4. 监控和维护
- **日志监控**: 定期查看日志文件，关注错误信息
- **性能监控**: 监控API响应时间和数据库查询性能
- **资源监控**: 监控磁盘空间和内存使用情况

## ❓ 常见问题解决

### Q1: twscrape登录失败
```bash
# 解决方案1: 重新添加账号
twscrape delete_accounts
twscrape add_accounts accounts.txt
twscrape login_accounts

# 解决方案2: 使用Playwright手动获取cookies
python tools/account_manager.py add
```

### Q2: 数据采集速度慢
```python
# 优化建议: 调整并发和延迟
class OptimizedScraper(SimpleTwitterScraper):
    async def search_tweets_fast(self, keyword: str, limit: int = 100):
        """优化版搜索"""
        tweets = []
        batch_size = 20  # 批量处理

        async for tweet in self.api.search(keyword, limit=limit):
            tweets.append(self.process_tweet(tweet))

            # 每20条处理一次
            if len(tweets) % batch_size == 0:
                await asyncio.sleep(0.1)  # 短暂延迟

        return tweets
```

### Q3: 数据库文件过大
```python
# 数据清理脚本
def cleanup_old_data(days: int = 30):
    """清理N天前的数据"""
    conn = sqlite3.connect("xget.db")
    cursor = conn.cursor()

    cursor.execute('''
        DELETE FROM tweets
        WHERE date(collected_at) < date('now', '-{} days')
    '''.format(days))

    deleted = cursor.rowcount
    conn.commit()
    conn.close()

    print(f"清理了 {deleted} 条旧数据")
```

### Q4: API服务无响应
```bash
# 检查服务状态
python tools/health_check.py

# 重启服务
pkill -f "python main.py"
python main.py &

# 查看日志
tail -f logs/xget.log
```

## 📈 性能优化建议

### 1. 数据库优化
```sql
-- 添加索引提高查询性能
CREATE INDEX idx_tweets_username ON tweets(username);
CREATE INDEX idx_tweets_created_at ON tweets(created_at);
CREATE INDEX idx_tweets_collected_at ON tweets(collected_at);
```

### 2. 内存优化
```python
# 使用生成器减少内存占用
async def search_tweets_generator(self, keyword: str, limit: int = 100):
    """生成器版本，节省内存"""
    async for tweet in self.api.search(keyword, limit=limit):
        yield self.process_tweet(tweet)
        await asyncio.sleep(0.5)
```

### 3. 并发优化
```python
# 适度并发处理
import asyncio
from asyncio import Semaphore

class ConcurrentScraper:
    def __init__(self, max_concurrent: int = 3):
        self.semaphore = Semaphore(max_concurrent)

    async def search_multiple_keywords(self, keywords: List[str]):
        """并发搜索多个关键词"""
        tasks = []
        for keyword in keywords:
            task = self.search_with_semaphore(keyword)
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results

    async def search_with_semaphore(self, keyword: str):
        async with self.semaphore:
            return await self.search_tweets(keyword)
```

## 🔄 升级路径

### 从SQLite到PostgreSQL
```python
# 数据迁移脚本
def migrate_to_postgresql():
    """迁移数据到PostgreSQL"""
    # 1. 导出SQLite数据
    sqlite_db = SimpleDatabase("xget.db")
    tweets = sqlite_db.get_tweets(limit=None)

    # 2. 导入到PostgreSQL
    # (需要先安装 psycopg2-binary)
    import psycopg2
    conn = psycopg2.connect(
        host="localhost",
        database="xget",
        user="xget_user",
        password="password"
    )

    # 3. 批量插入数据
    # ... 实现数据迁移逻辑
```

### 添加Redis缓存
```python
# 缓存层
import redis

class CachedScraper(SimpleTwitterScraper):
    def __init__(self):
        super().__init__()
        self.redis_client = redis.Redis(host='localhost', port=6379, db=0)

    async def search_tweets_cached(self, keyword: str, limit: int = 100):
        """带缓存的搜索"""
        cache_key = f"search:{keyword}:{limit}"

        # 检查缓存
        cached = self.redis_client.get(cache_key)
        if cached:
            return json.loads(cached)

        # 执行搜索
        tweets = await self.search_tweets(keyword, limit)

        # 缓存结果（1小时过期）
        self.redis_client.setex(
            cache_key,
            3600,
            json.dumps(tweets, default=str)
        )

        return tweets
```

## 🎉 总结

这个优化方案的核心特点：

1. **简单实用** - 避免过度设计，专注核心功能
2. **快速上手** - 最少的依赖，最简的配置
3. **易于维护** - 清晰的代码结构，完善的工具脚本
4. **渐进升级** - 支持从简单到复杂的平滑演进

**立即开始的步骤**：
1. 复制代码文件
2. 安装依赖包
3. 配置Twitter账号
4. 启动服务测试
5. 根据需要逐步优化

记住：**先让它工作，再让它工作得更好！** 🚀
