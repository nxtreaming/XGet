# XGet 社媒搜索采集系统 - 生产就绪版本

## 项目概述

基于甲方需求文档，这是一个专业的X(Twitter)数据采集系统，提供关键词搜索、数据解析、资源下载和API接口服务。系统支持定时搜索和按需搜索两种模式，完整实现甲乙双方的数据交互需求。

### 🎯 **核心业务需求**

1. **关键词搜索采集** - 支持多语言关键词的X平台搜索
2. **双模式任务** - 定时搜索 + 按需搜索
3. **完整数据解析** - 帖子、作者、媒体、互动数据
4. **资源下载管理** - 图片/视频下载到OSS
5. **标准API接口** - 任务下发、结果上报、数据统计
6. **数据去重统计** - 按关键词月度去重计量

### 📋 **甲方需求分析**

#### **搜索任务类型**
1. **定时搜索任务**
   - 参数：关键词、优先级、搜索频率
   - 按频率和优先级自动执行

2. **按需搜索任务**
   - 参数：关键词、优先级、需要条数、开始时间、结束时间
   - 条数=0时尽力采集，≠0时达到目标后结束

#### **数据字段要求**
- **基础帖子信息**：地址、ID、类型、内容、时间
- **作者信息**：头像、名字、handle
- **互动数据**：评论数、转发数、点赞数、曝光数、bookmark
- **媒体资源**：图片、视频封面（数组形式）
- **转发帖特殊字段**：原贴信息、关系标识
- **其他字段**：链接、OSS地址、原始数据

## 核心原则

1. **业务需求驱动** - 严格按照甲方需求文档实现
2. **API标准化** - 提供标准的任务下发和结果上报接口
3. **数据完整性** - 确保所有必需字段的准确采集
4. **资源管理** - 完整的图片/视频下载和OSS存储
5. **可扩展架构** - 支持后续Facebook、Instagram等平台

## 技术栈选择

### 🚀 **基于Apify架构优化的技术栈**

参考Apify Twitter Scraper的成功经验，我们采用以下优化的技术组合：

#### **核心采集技术**
- **编程语言**: Python 3.12.11 (已验证) / Python 3.9+ (最低要求)
- **主要爬取框架**: **集成式twscrape** (基于twscrape 0.17.0定制开发)
- **网络层**: httpx 0.28.1 (异步HTTP客户端)
- **备用采集方案**: Apify-style Actor模式 (基于Playwright + 高级反检测)
- **浏览器自动化**: Playwright 1.53.0 (已验证，cookies管理 + 特殊场景)
- **查询优化**: Twitter高级搜索语法支持 (参考Apify Query Wizard)

#### **🔧 twscrape集成策略**

```text
XGet项目结构
├── src/
│   ├── xget_core/              # 核心业务逻辑
│   ├── xget_scraper/           # 集成的twscrape (定制版)
│   │   ├── __init__.py
│   │   ├── api.py              # 基于twscrape.API的增强版
│   │   ├── models.py           # 扩展的数据模型
│   │   ├── accounts.py         # 账号管理增强
│   │   ├── utils.py            # 工具函数
│   │   └── exceptions.py       # 自定义异常
│   ├── xget_api/               # FastAPI接口
│   └── xget_web/               # Web管理界面
├── third_party/
│   └── twscrape/               # 原始twscrape源码 (作为参考)
└── requirements.txt
```

#### **系统架构组件**
- **任务队列**: Celery + Redis (支持事件驱动定价模式)
- **数据存储**: MongoDB (文档存储) + Redis (缓存/会话)
- **API框架**: FastAPI + Uvicorn (高性能异步API)
- **配置管理**: Pydantic Settings + 环境变量
- **日志系统**: Structured Logging (JSON格式)
- **监控**: Prometheus + Grafana (可选)
- **部署**: Docker Compose (开发) + Docker Swarm/K8s (生产)

### ✅ 技术验证状态
- **🎉 核心技术栈**: 100% 验证通过
- **🍪 Cookies方案**: 已解决登录难题
- **📊 数据采集**: 已验证可获取真实数据
- **🎭 浏览器自动化**: 全功能验证通过
- **🚀 开发就绪**: 可立即开始项目开发

### 🎯 **Apify-inspired 查询优化器**

基于Apify Twitter Scraper的成功经验，实现智能查询优化：

```python
# services/query_optimizer.py
class TwitterQueryOptimizer:
    """
    基于Apify经验的查询优化器
    支持Twitter高级搜索语法，提高采集效率和成本控制
    """

    def optimize_profile_scraping(self, username: str, date_ranges: List[Tuple]) -> List[str]:
        """
        优化用户资料采集 - 分时间段查询
        参考Apify建议：每月最多800条推文，需要分段查询
        """
        queries = []
        for start_date, end_date in date_ranges:
            query = f"from:{username} since:{start_date} until:{end_date}"
            queries.append(query)
        return queries

    def build_advanced_search(self, keyword: str, filters: Dict) -> str:
        """
        构建高级搜索查询 - 支持Apify-style的复杂过滤条件
        参考: https://github.com/igorbrigadir/twitter-advanced-search
        """
        query_parts = [keyword]

        # 媒体过滤 (Apify支持的过滤器)
        if filters.get('only_images'):
            query_parts.append('filter:images')
        elif filters.get('only_videos'):
            query_parts.append('filter:videos')
        elif filters.get('exclude_images'):
            query_parts.append('-filter:images')

        # 互动过滤
        if filters.get('min_likes'):
            query_parts.append(f"min_faves:{filters['min_likes']}")
        if filters.get('min_retweets'):
            query_parts.append(f"min_retweets:{filters['min_retweets']}")

        # 用户类型过滤
        if filters.get('only_verified'):
            query_parts.append('filter:verified')
        if filters.get('only_blue_verified'):
            query_parts.append('filter:blue_verified')
        if filters.get('exclude_retweets'):
            query_parts.append('-filter:nativeretweets')

        # 语言过滤
        if filters.get('language'):
            query_parts.append(f"lang:{filters['language']}")

        return ' '.join(query_parts)

    def generate_conversation_queries(self, tweet_id: str, hashtag: str = None) -> List[str]:
        """
        生成对话查询 - 获取推文回复
        """
        base_query = f"conversation_id:{tweet_id}"
        if hashtag:
            base_query += f" #{hashtag}"
        return [base_query]

    def optimize_batch_queries(self, queries: List[str]) -> Dict[str, List[str]]:
        """
        批量查询优化 - 根据Apify定价模型优化查询分组
        """
        # 按查询复杂度分组，优化成本
        simple_queries = []
        complex_queries = []

        for query in queries:
            if len(query.split()) <= 3:
                simple_queries.append(query)
            else:
                complex_queries.append(query)

        return {
            "simple_batch": simple_queries,
            "complex_batch": complex_queries
        }
```

### 💰 **事件驱动定价模型**

参考Apify的透明定价策略，为甲方提供灵活的成本控制：

```python
# services/pricing_calculator.py
class PricingCalculator:
    """
    基于Apify模式的事件驱动定价计算器
    """

    # 基础定价 (参考Apify模型)
    QUERY_COSTS = {
        "standard_query": 0.016,      # 标准查询 (包含前2页约40条推文)
        "single_tweet": 0.05,         # 单条推文查询
        "profile_query": 0.016,       # 用户资料查询
        "search_query": 0.016         # 搜索查询
    }

    # 分层定价 (按批次大小)
    TIER_PRICING = {
        1: {"max_queries": 5, "cost_per_item": 0.0004},      # ≤5查询
        2: {"max_queries": 10, "cost_per_item": 0.0008},     # 6-10查询
        3: {"max_queries": 30, "cost_per_item": 0.0012},     # 11-30查询
        4: {"max_queries": 100, "cost_per_item": 0.0016},    # 31-100查询
        5: {"max_queries": float('inf'), "cost_per_item": 0.002}  # >100查询
    }

    def calculate_task_cost(self, task_params: Dict) -> Dict[str, float]:
        """
        计算任务成本
        """
        task_type = task_params.get("type")
        query_count = task_params.get("query_count", 1)
        expected_items = task_params.get("expected_items", 0)

        # 基础查询成本
        if task_type == "single_tweet":
            base_cost = self.QUERY_COSTS["single_tweet"]
        else:
            base_cost = self.QUERY_COSTS["standard_query"] * query_count

        # 确定定价层级
        tier = self._get_pricing_tier(query_count)

        # 计算数据项成本 (超出免费额度的部分)
        free_items = min(query_count * 40, expected_items)  # 每查询40条免费
        paid_items = max(0, expected_items - free_items)

        item_cost = paid_items * self.TIER_PRICING[tier]["cost_per_item"]

        total_cost = base_cost + item_cost

        return {
            "base_cost": base_cost,
            "item_cost": item_cost,
            "total_cost": total_cost,
            "tier": tier,
            "free_items": free_items,
            "paid_items": paid_items
        }

    def _get_pricing_tier(self, query_count: int) -> int:
        """确定定价层级"""
        for tier, config in self.TIER_PRICING.items():
            if query_count <= config["max_queries"]:
                return tier
        return 5
```

### 🔧 **twscrape集成实施方案**

#### **1. 集成方式选择**

**推荐方案：Fork + 定制开发**

```bash
# 1. Fork twscrape到您的组织
git clone https://github.com/vladkens/twscrape.git third_party/twscrape

# 2. 创建定制版本
cp -r third_party/twscrape/twscrape src/xget_scraper/
```

#### **2. 定制开发重点**

```python
# src/xget_scraper/enhanced_api.py
from typing import Dict, List, Optional, AsyncGenerator
from .api import API as BaseAPI
from ..models import XGetTweet, XGetUser

class XGetAPI(BaseAPI):
    """
    基于twscrape的增强API
    针对甲方需求进行定制优化
    """

    def __init__(self, pool_file: str = "accounts.db"):
        super().__init__(pool_file)
        self.request_count = 0
        self.success_count = 0
        self.error_count = 0

    async def search_enhanced(
        self,
        query: str,
        limit: int = 20,
        task_id: str = None,
        **kwargs
    ) -> AsyncGenerator[XGetTweet, None]:
        """
        增强的搜索功能
        - 添加任务追踪
        - 增强错误处理
        - 数据格式标准化
        """
        try:
            self.request_count += 1

            async for tweet in self.search(query, limit, **kwargs):
                # 转换为甲方要求的数据格式
                xget_tweet = self._convert_to_xget_format(tweet, task_id)
                self.success_count += 1
                yield xget_tweet

        except Exception as e:
            self.error_count += 1
            self.logger.error(f"Search failed for query: {query}, error: {str(e)}")
            raise

    def _convert_to_xget_format(self, tweet: Tweet, task_id: str) -> XGetTweet:
        """
        转换为甲方要求的20个字段格式
        """
        return XGetTweet(
            # 甲方字段0: 基础信息
            post_url=f"https://x.com/{tweet.user.username}/status/{tweet.id}",
            post_id=str(tweet.id),
            post_type=self._determine_post_type(tweet),

            # 甲方字段1-3: 作者信息
            author_avatar=tweet.user.profileImageUrl,
            author_name=tweet.user.displayname,
            author_handle=f"@{tweet.user.username}",

            # 甲方字段4: 时间
            post_time=tweet.date,

            # 甲方字段5: 内容
            post_content=tweet.rawContent,

            # 甲方字段6: 媒体 (数组形式)
            post_images=self._process_media(tweet.media),

            # 甲方字段7-10, 17: 互动数据
            comment_count=tweet.replyCount or 0,
            retweet_count=tweet.retweetCount or 0,
            like_count=tweet.likeCount or 0,
            view_count=tweet.viewCount or 0,
            bookmark_count=tweet.bookmarkCount or 0,

            # 甲方字段18-19: 类型标识
            is_retweet=bool(tweet.retweetedTweet),
            is_quote=bool(tweet.quotedTweet),

            # 甲方字段11-16: 转发帖信息
            **self._process_retweet_info(tweet),

            # 甲方字段20: 链接信息
            post_links=self._extract_links(tweet),

            # 甲方要求的关系字段
            parent_post_id=tweet.inReplyToTweetId,
            parent_comment_id=tweet.inReplyToUserId,

            # 系统字段
            task_id=task_id,
            collected_at=datetime.utcnow(),

            # 甲方要求保留原始数据
            raw_data={
                "twscrape_tweet": tweet.dict(),
                "collection_method": "xget_enhanced_twscrape"
            }
        )

    async def get_account_health(self) -> Dict:
        """
        获取账号池健康状态
        """
        accounts = await self.pool.accounts()

        health_stats = {
            "total_accounts": len(accounts),
            "active_accounts": 0,
            "suspended_accounts": 0,
            "error_accounts": 0,
            "request_stats": {
                "total_requests": self.request_count,
                "successful_requests": self.success_count,
                "failed_requests": self.error_count,
                "success_rate": self.success_count / max(self.request_count, 1)
            }
        }

        for account in accounts:
            if account.active:
                health_stats["active_accounts"] += 1
            elif "suspended" in str(account.status).lower():
                health_stats["suspended_accounts"] += 1
            else:
                health_stats["error_accounts"] += 1

        return health_stats
```

#### **3. 版本管理策略**

```python
# src/xget_scraper/__init__.py
"""
XGet定制版twscrape
基于twscrape 0.17.0定制开发

版本管理：
- 上游版本: twscrape 0.17.0
- XGet版本: 1.0.0
- 最后同步: 2024-01-01
"""

__version__ = "1.0.0"
__upstream_version__ = "0.17.0"
__last_sync__ = "2024-01-01"

from .enhanced_api import XGetAPI
from .models import XGetTweet, XGetUser

__all__ = ["XGetAPI", "XGetTweet", "XGetUser"]
```

#### **4. 升级和维护策略**

```bash
# scripts/sync_upstream.sh
#!/bin/bash
# 同步上游twscrape更新的脚本

echo "开始同步上游twscrape..."

# 1. 获取最新的twscrape
cd third_party/twscrape
git pull origin main

# 2. 检查变更
git log --oneline --since="2024-01-01" > ../../docs/upstream_changes.log

# 3. 创建合并分支
cd ../../
git checkout -b sync-upstream-$(date +%Y%m%d)

# 4. 手动合并关键更新
echo "请手动检查 docs/upstream_changes.log 并合并必要的更新"
echo "重点关注："
echo "- API接口变更"
echo "- 数据模型变更"
echo "- 错误处理改进"
echo "- 性能优化"
```

### 必要的生产组件
- **代理IP管理** - 生产环境必需
- **账号池管理** - Cookie轮换和健康检查
- **错误处理和重试** - 提高系统稳定性
- **数据验证** - Pydantic模型验证
- **基础监控** - 系统健康状态监控
- **配置管理** - 环境隔离和配置热更新

## 系统架构

```text
┌─────────────────────────────────────────────────────────────────────┐
│                            XGet 架构                                │
├─────────────────┬─────────────────┬─────────────────┬───────────────┤
│   Web API       │   任务调度       │   数据存储       │   基础设施     │
│   (FastAPI)     │   (Celery)      │   (MongoDB)     │   (监控/日志)  │
└─────────────────┴─────────────────┴─────────────────┴───────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│  采集引擎      │    │  资源管理      │    │  数据处理      │
│  twscrape     │    │  账号/代理池    │    │  验证/存储     │
│  Playwright   │    │  健康检查      │    │  Redis缓存     │
└───────────────┘    └───────────────┘    └───────────────┘
```

### 核心模块说明

1. **采集引擎层** - 负责实际的数据抓取
2. **资源管理层** - 管理账号池、代理IP等资源
3. **数据处理层** - 数据验证、存储、缓存
4. **API服务层** - 对外提供接口服务
5. **任务调度层** - 分布式任务管理
6. **基础设施层** - 监控、日志、配置管理

## 🎯 技术分层架构详解

基于技术验证结果，XGet项目采用分层架构，每层负责特定功能，实现高效协作：

### 📋 **技术分层概览**

```text
┌─────────────────────────────────────────────────────────────────────┐
│                        XGet 技术分层架构                            │
├─────────────────┬─────────────────┬─────────────────┬───────────────┤
│  🍪 认证层      │  📊 数据采集层  │   🔧 管理层     │   🚀 应用层    │
│   (Playwright)  │   (twscrape)    │   (Python)      │   (FastAPI)   │
└─────────────────┴─────────────────┴─────────────────┴───────────────┘
```

### 🍪 **第一层：认证层（Playwright）**

**核心职责**：自动化cookies获取和登录管理

#### ✅ **主要功能**：
- **自动登录获取cookies** - 解放人工操作
- **批量账号管理** - 支持多账号自动化
- **cookies自动刷新** - 过期时自动更新
- **处理登录验证** - 验证码、邮箱验证等

#### 🔧 **技术实现**：
```python
# 自动化cookies获取
async def auto_extract_cookies(account_info):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        # 1. 自动登录
        await auto_login(page, account_info)

        # 2. 提取cookies
        cookies = await page.context.cookies()

        # 3. 导入到twscrape
        await import_to_twscrape(cookies)

        return cookies
```

#### 🎯 **应用场景**：
- **批量账号初始化** - 新项目启动时
- **定期维护** - cookies过期自动刷新
- **故障恢复** - 账号被限制时重新获取
- **扩容支持** - 新增账号时自动配置

### 📊 **第二层：数据采集层（twscrape）**

**核心职责**：高效的Twitter数据采集

#### ✅ **主要功能**：
- **推文搜索** - 关键词、话题、用户搜索
- **用户信息获取** - 完整的用户资料
- **速率限制管理** - 内置智能限制
- **多账号轮换** - 自动账号切换

#### 🔧 **技术优势**：
```python
# 高效数据采集
async def efficient_data_collection():
    api = API()  # 使用Playwright维护的cookies

    # 高性能搜索
    tweets = []
    async for tweet in api.search("python", limit=1000):
        tweets.append(process_tweet(tweet))

    return tweets
```

#### 📈 **性能特点**：
- **⚡ 高效率** - API调用比浏览器快10倍
- **🛡️ 稳定性** - 专门优化的反检测
- **🔄 智能轮换** - 自动管理账号和请求
- **📊 结构化数据** - 直接返回Python对象

### 🔧 **第三层：管理层（Python脚本）**

**核心职责**：协调两个工具，提供统一管理

#### ✅ **主要功能**：
- **工具协调** - Playwright + twscrape协作
- **错误处理** - 统一的异常处理和重试
- **数据处理** - 清洗、验证、存储
- **监控日志** - 系统状态监控

#### 🔧 **架构设计**：
```python
class XGetManager:
    """XGet统一管理器"""

    def __init__(self):
        self.playwright_manager = PlaywrightManager()
        self.twscrape_manager = TwscrapeManager()
        self.data_manager = DataManager()

    async def collect_data(self, keyword: str):
        # 1. 确保cookies有效
        await self.playwright_manager.ensure_cookies_valid()

        # 2. 执行数据采集
        tweets = await self.twscrape_manager.search(keyword)

        # 3. 数据处理和存储
        processed_data = await self.data_manager.process(tweets)

        return processed_data
```

#### 🎯 **核心价值**：
- **🔗 无缝集成** - 两个工具完美配合
- **🛡️ 容错能力** - 自动处理各种异常
- **📊 数据质量** - 统一的数据验证
- **🔍 可观测性** - 完整的监控和日志

### 🚀 **第四层：应用层（FastAPI）**

**核心职责**：对外提供服务接口

#### ✅ **主要功能**：
- **RESTful API** - 标准的HTTP接口
- **任务管理** - 异步任务调度
- **数据查询** - 灵活的数据检索
- **系统监控** - 健康状态检查

## 💡 **分层协作流程**

### 🔄 **典型工作流程**：

```text
1. 🍪 Playwright层：
   ├── 检查cookies有效性
   ├── 自动刷新过期cookies
   └── 维护账号登录状态

2. 📊 twscrape层：
   ├── 使用有效cookies
   ├── 执行高效数据采集
   └── 返回结构化数据

3. 🔧 管理层：
   ├── 协调上述两层
   ├── 处理错误和重试
   └── 数据清洗和存储

4. 🚀 应用层：
   ├── 接收用户请求
   ├── 调用管理层服务
   └── 返回处理结果
```

### 🎯 **分工优势**：

| 层级 | 专长 | 优势 |
|------|------|------|
| **Playwright** | 浏览器自动化 | 🍪 解决登录难题 |
| **twscrape** | API高效调用 | ⚡ 10倍性能提升 |
| **Python管理** | 系统协调 | 🔧 统一控制 |
| **FastAPI** | 服务接口 | 🚀 标准化服务 |

## 🎉 **架构优势总结**

### ✅ **技术优势**：
1. **🔑 解决核心难题** - Playwright解决登录问题
2. **⚡ 保持高性能** - twscrape提供高效采集
3. **🛡️ 提高稳定性** - 分层设计降低耦合
4. **🔧 便于维护** - 职责清晰，易于调试

### ✅ **业务优势**：
1. **📈 可扩展性** - 每层独立扩展
2. **🔄 可替换性** - 单层替换不影响整体
3. **🎯 专业化** - 每层专注核心能力
4. **💰 成本效益** - 最大化利用各工具优势

## 核心模块设计

### 🎯 **基于Apify最佳实践的模块架构**

参考Apify Twitter Scraper的成功架构，我们设计了以下优化模块：

### 1. 智能数据采集模块 (Smart Scraping Module)

**技术栈**: twscrape + httpx + Playwright + Apify-style优化
**核心职责**: 高效稳定的X平台数据采集，支持高级查询优化

#### 🚀 **Apify-inspired 查询优化**

```python
# core/smart_scraper.py
class SmartScrapingEngine:
    """
    基于Apify经验的智能采集引擎
    支持高级查询、成本优化和反检测
    """

    def __init__(self):
        self.query_optimizer = TwitterQueryOptimizer()
        self.pricing_calculator = PricingCalculator()
        self.rate_limiter = AdaptiveRateLimiter()

    async def execute_optimized_search(self, task_params: Dict) -> Dict:
        """
        执行优化的搜索任务 - 参考Apify的查询优化策略
        """
        # 1. 查询优化 (Apify-style)
        if task_params["type"] == "profile_scraping":
            queries = self._optimize_profile_queries(task_params)
        else:
            queries = self._build_advanced_search_queries(task_params)

        # 2. 成本预估 (透明定价)
        cost_estimate = self.pricing_calculator.calculate_task_cost({
            "type": task_params["type"],
            "query_count": len(queries),
            "expected_items": task_params.get("required_count", 1000)
        })

        # 3. 执行采集
        results = []
        for query in queries:
            batch_result = await self._execute_single_query(query, task_params)
            results.extend(batch_result)

            # 检查是否达到甲方要求的条数
            if (task_params.get("required_count", 0) > 0 and
                len(results) >= task_params["required_count"]):
                break

        return {
            "results": results,
            "cost_info": cost_estimate,
            "queries_executed": len(queries),
            "total_collected": len(results)
        }

    def _optimize_profile_queries(self, task_params: Dict) -> List[str]:
        """
        优化用户资料查询 - 参考Apify分时间段策略
        每月最多800条推文，需要分段查询
        """
        username = task_params["username"]

        # 生成月度时间范围
        date_ranges = self._generate_monthly_ranges(
            task_params.get("start_time"),
            task_params.get("end_time")
        )

        return [f"from:{username} since:{start} until:{end}"
                for start, end in date_ranges]

    def _build_advanced_search_queries(self, task_params: Dict) -> List[str]:
        """
        构建高级搜索查询 - 支持Apify-style复杂过滤
        参考: https://github.com/igorbrigadir/twitter-advanced-search
        """
        keyword = task_params["keyword"]
        filters = {
            "only_images": task_params.get("only_images", False),
            "only_videos": task_params.get("only_videos", False),
            "only_verified": task_params.get("only_verified", False),
            "min_likes": task_params.get("min_likes"),
            "language": task_params.get("language")
        }

        # 使用查询优化器构建复杂查询
        optimized_query = self.query_optimizer.build_advanced_search(keyword, filters)

        # 如果有时间范围，分段查询 (提高成功率)
        if task_params.get("start_time") and task_params.get("end_time"):
            date_ranges = self._generate_date_ranges(
                task_params["start_time"],
                task_params["end_time"]
            )
            return [f"{optimized_query} since:{start} until:{end}"
                   for start, end in date_ranges]

        return [optimized_query]
```

#### 📊 **Apify-style 数据处理器**

```python
# core/data_processor.py
class ApifyStyleDataProcessor:
    """
    基于Apify输出格式的数据处理器
    确保数据格式与甲方需求完全匹配
    """

    def process_tweet_data(self, raw_tweet: Dict, task_info: Dict) -> Dict:
        """
        处理推文数据 - 完全按照甲方20个字段要求
        参考Apify的详细输出格式
        """
        processed = {
            # 甲方字段0: 基础信息
            "post_url": f"https://x.com/{raw_tweet['user']['username']}/status/{raw_tweet['id']}",
            "post_id": raw_tweet["id"],
            "post_type": self._determine_post_type(raw_tweet),

            # 甲方字段1-3: 作者信息
            "author_avatar": raw_tweet["user"].get("profilePicture", ""),
            "author_name": raw_tweet["user"].get("name", ""),
            "author_handle": f"@{raw_tweet['user'].get('userName', '')}",

            # 甲方字段4: 时间
            "post_time": self._parse_twitter_date(raw_tweet.get("createdAt")),

            # 甲方字段5: 内容
            "post_content": raw_tweet.get("text", ""),

            # 甲方字段6: 媒体 (数组形式，如Apify)
            "post_images": self._process_media_array(raw_tweet.get("extendedEntities", {})),

            # 甲方字段7-10, 17: 互动数据
            "comment_count": raw_tweet.get("replyCount", 0),
            "retweet_count": raw_tweet.get("retweetCount", 0),
            "like_count": raw_tweet.get("likeCount", 0),
            "view_count": raw_tweet.get("viewCount", 0),
            "bookmark_count": raw_tweet.get("bookmarkCount", 0),

            # 甲方字段18-19: 类型标识
            "is_retweet": raw_tweet.get("isRetweet", False),
            "is_quote": raw_tweet.get("isQuote", False),

            # 甲方字段11-16: 转发帖信息
            **self._process_retweet_data(raw_tweet),

            # 甲方字段20: 链接信息
            "post_links": self._extract_links(raw_tweet),

            # 甲方要求的关系字段
            "parent_post_id": raw_tweet.get("inReplyToStatusId"),
            "parent_comment_id": raw_tweet.get("inReplyToUserId"),

            # 系统字段
            "oss_file_path": None,  # 后续OSS上传时填充
            "collected_at": datetime.utcnow().isoformat(),
            "keyword": task_info.get("keyword"),
            "task_id": task_info.get("task_id"),

            # 甲方要求保留原始数据
            "raw_data": {
                "twitter_api_response": raw_tweet,
                "collection_method": "twscrape_optimized",
                "apify_style_processing": True
            }
        }

        return processed

    def _process_media_array(self, extended_entities: Dict) -> List[Dict]:
        """
        处理媒体数组 - 参考Apify的详细媒体信息
        """
        media_list = []

        for media in extended_entities.get("media", []):
            media_item = {
                "original_url": media.get("media_url_https", ""),
                "oss_url": None,  # 后续OSS上传时填充
                "type": "video_cover" if media.get("type") == "video" else "image",
                "width": media.get("original_info", {}).get("width"),
                "height": media.get("original_info", {}).get("height")
            }

            # 视频特殊处理 (参考Apify视频信息)
            if media.get("video_info"):
                media_item.update({
                    "video_duration": media["video_info"].get("duration_millis"),
                    "video_variants": media["video_info"].get("variants", [])
                })

            media_list.append(media_item)

        return media_list

    def _determine_post_type(self, raw_tweet: Dict) -> str:
        """
        确定帖子类型 - 参考Apify的类型分类
        """
        if raw_tweet.get("isRetweet"):
            return "retweet"
        elif raw_tweet.get("isQuote"):
            return "quote"
        elif raw_tweet.get("extendedEntities", {}).get("media"):
            media_types = [m.get("type") for m in raw_tweet["extendedEntities"]["media"]]
            if "video" in media_types:
                return "video"
            elif "photo" in media_types:
                return "image"
        return "text"
```
import asyncio
import random
from twscrape import API
from typing import List, Dict, Optional
from datetime import datetime
import logging
from .proxy_manager import ProxyManager
from .account_manager import AccountManager

class ProductionTwitterScraper:
    """生产级Twitter采集器"""

    def __init__(self, account_manager: AccountManager, proxy_manager: ProxyManager):
        self.api = API()
        self.account_manager = account_manager
        self.proxy_manager = proxy_manager
        self.logger = logging.getLogger(__name__)

    async def search_tweets(self, keyword: str, count: int = 100) -> List[Dict]:
        """搜索推文 - 带错误处理和重试"""
        tweets = []
        retry_count = 0
        max_retries = 3

        while retry_count < max_retries:
            try:
                # 获取可用账号和代理
                account = await self.account_manager.get_available_account()
                proxy = await self.proxy_manager.get_proxy()

                # 配置API
                if proxy:
                    self.api.set_proxy(proxy['url'])

                async for tweet in self.api.search(keyword, limit=count):
                    tweet_data = {
                        'id': tweet.id,
                        'text': tweet.rawContent,
                        'user_id': tweet.user.id,
                        'username': tweet.user.username,
                        'created_at': tweet.date.isoformat(),
                        'retweet_count': tweet.retweetCount,
                        'like_count': tweet.likeCount,
                        'reply_count': tweet.replyCount,
                        'quote_count': tweet.quoteCount,
                        'view_count': getattr(tweet, 'viewCount', 0),
                        'media': [{'url': m.url, 'type': m.type} for m in tweet.media] if tweet.media else [],
                        'hashtags': [tag.text for tag in tweet.hashtags] if tweet.hashtags else [],
                        'urls': [url.expandedUrl for url in tweet.urls] if tweet.urls else [],
                        'collected_at': datetime.utcnow().isoformat(),
                        'source_account': account['id'],
                        'source_proxy': proxy['id'] if proxy else None
                    }
                    tweets.append(tweet_data)

                # 成功后更新账号状态
                await self.account_manager.update_account_success(account['id'])
                break

            except Exception as e:
                retry_count += 1
                self.logger.warning(f"Search failed (attempt {retry_count}): {str(e)}")

                if retry_count < max_retries:
                    # 标记账号可能有问题
                    if 'account' in locals():
                        await self.account_manager.mark_account_error(account['id'], str(e))

                    # 等待后重试
                    await asyncio.sleep(random.uniform(5, 15))
                else:
                    raise

        return tweets

    async def get_user_profile(self, username: str) -> Optional[Dict]:
        """获取用户资料 - 完整实现"""
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
                'verified': user.verified,
                'created_at': user.created.isoformat() if user.created else None,
                'location': user.location,
                'profile_image_url': user.profileImageUrl,
                'profile_banner_url': user.profileBannerUrl,
                'collected_at': datetime.utcnow().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Failed to get user profile for {username}: {str(e)}")
            raise
```

### 2. 账号管理模块

```python
# core/account_manager.py
import asyncio
import json
import logging
import hashlib
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, asdict
import redis.asyncio as redis
from twscrape import API, Account

class AccountStatus(Enum):
    """账号状态枚举"""
    ACTIVE = "active"           # 活跃可用
    SUSPENDED = "suspended"     # 暂停使用
    ERROR = "error"            # 错误状态
    MAINTENANCE = "maintenance" # 维护中
    COOLDOWN = "cooldown"      # 冷却期
    EXPIRED = "expired"        # 已过期

class AccountPriority(Enum):
    """账号优先级"""
    HIGH = "high"      # 高优先级（稳定账号）
    NORMAL = "normal"  # 普通优先级
    LOW = "low"        # 低优先级（测试账号）
    BACKUP = "backup"  # 备用账号

@dataclass
class AccountMetrics:
    """账号指标数据"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    rate_limit_hits: int = 0
    last_used: Optional[datetime] = None
    last_success: Optional[datetime] = None
    last_error: Optional[datetime] = None
    consecutive_errors: int = 0
    daily_usage: int = 0
    weekly_usage: int = 0

    @property
    def success_rate(self) -> float:
        """成功率计算"""
        if self.total_requests == 0:
            return 1.0
        return self.successful_requests / self.total_requests

    @property
    def health_score(self) -> float:
        """健康分数计算 (0-1)"""
        base_score = self.success_rate

        # 连续错误惩罚
        error_penalty = min(self.consecutive_errors * 0.1, 0.5)

        # 使用频率调整
        usage_factor = 1.0
        if self.daily_usage > 800:  # 接近限制时降低分数
            usage_factor = 0.8
        elif self.daily_usage > 600:
            usage_factor = 0.9

        return max(0.0, (base_score - error_penalty) * usage_factor)

@dataclass
class AccountConfig:
    """账号配置"""
    account_id: str
    username: str
    email: str
    status: AccountStatus
    priority: AccountPriority
    daily_limit: int = 1000
    hourly_limit: int = 100
    cooldown_minutes: int = 30
    max_consecutive_errors: int = 5
    auto_recovery: bool = True
    tags: List[str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []

class ProductionAccountManager:
    """生产级账号池管理器"""

    def __init__(self, redis_client: redis.Redis, twscrape_api: API = None):
        self.redis = redis_client
        self.api = twscrape_api or API()
        self.logger = logging.getLogger(__name__)

        # 配置参数
        self.health_threshold = 0.7
        self.max_daily_usage = 1000
        self.cooldown_duration = 1800  # 30分钟
        self.error_threshold = 5

    async def initialize(self):
        """初始化账号管理器"""
        await self._sync_twscrape_accounts()
        await self._setup_redis_structures()

    async def _sync_twscrape_accounts(self):
        """同步twscrape账号到Redis"""
        try:
            accounts = await self.api.pool.get_all()
            self.logger.info(f"Found {len(accounts)} accounts in twscrape")

            for account in accounts:
                await self._import_account_from_twscrape(account)

        except Exception as e:
            self.logger.error(f"Failed to sync twscrape accounts: {e}")

    async def _import_account_from_twscrape(self, account: Account):
        """从twscrape导入账号"""
        account_config = AccountConfig(
            account_id=f"tw_{account.username}",
            username=account.username,
            email=account.email or f"{account.username}@unknown.com",
            status=AccountStatus.ACTIVE if account.active else AccountStatus.SUSPENDED,
            priority=AccountPriority.NORMAL
        )

        # 保存账号配置
        await self._save_account_config(account_config)

        # 保存cookies
        if hasattr(account, 'cookies') and account.cookies:
            await self._save_account_cookies(account_config.account_id, account.cookies)

    async def _setup_redis_structures(self):
        """设置Redis数据结构"""
        # 创建索引集合
        await self.redis.sadd('account_manager:initialized', '1')

    async def get_available_account(self,
                                  priority: Optional[AccountPriority] = None,
                                  tags: Optional[List[str]] = None,
                                  exclude_accounts: Optional[List[str]] = None) -> Optional[Dict]:
        """获取可用账号 - 智能选择算法"""
        try:
            # 获取候选账号
            candidates = await self._get_candidate_accounts(priority, tags, exclude_accounts)

            if not candidates:
                self.logger.warning("No candidate accounts available")
                return None

            # 智能选择最佳账号
            best_account = await self._select_best_account(candidates)

            if best_account:
                # 更新使用记录
                await self._record_account_usage(best_account['account_id'])

                # 获取完整账号信息
                return await self._get_full_account_info(best_account['account_id'])

            return None

        except Exception as e:
            self.logger.error(f"Failed to get available account: {e}")
            return None

    async def _get_candidate_accounts(self,
                                    priority: Optional[AccountPriority],
                                    tags: Optional[List[str]],
                                    exclude_accounts: Optional[List[str]]) -> List[Dict]:
        """获取候选账号列表"""
        candidates = []

        # 获取所有活跃账号
        active_accounts = await self.redis.smembers('accounts:active')

        for account_id in active_accounts:
            account_id = account_id.decode()

            # 排除指定账号
            if exclude_accounts and account_id in exclude_accounts:
                continue

            # 检查账号配置
            config = await self._get_account_config(account_id)
            if not config:
                continue

            # 优先级过滤
            if priority and config.priority != priority:
                continue

            # 标签过滤
            if tags and not any(tag in config.tags for tag in tags):
                continue

            # 检查是否在冷却期
            if await self._is_account_in_cooldown(account_id):
                continue

            # 检查使用限制
            if await self._is_account_over_limit(account_id):
                continue

            # 获取账号指标
            metrics = await self._get_account_metrics(account_id)

            candidates.append({
                'account_id': account_id,
                'config': config,
                'metrics': metrics,
                'health_score': metrics.health_score
            })

        return candidates

    async def _select_best_account(self, candidates: List[Dict]) -> Optional[Dict]:
        """选择最佳账号 - 综合评分算法"""
        if not candidates:
            return None

        # 计算综合评分
        for candidate in candidates:
            score = await self._calculate_account_score(candidate)
            candidate['final_score'] = score

        # 按评分排序，选择最高分
        candidates.sort(key=lambda x: x['final_score'], reverse=True)

        return candidates[0]

    async def _calculate_account_score(self, candidate: Dict) -> float:
        """计算账号综合评分"""
        config = candidate['config']
        metrics = candidate['metrics']

        # 基础健康分数 (40%)
        health_score = metrics.health_score * 0.4

        # 使用频率分数 (30%) - 使用越少分数越高
        usage_ratio = metrics.daily_usage / config.daily_limit
        usage_score = (1 - usage_ratio) * 0.3

        # 优先级分数 (20%)
        priority_scores = {
            AccountPriority.HIGH: 1.0,
            AccountPriority.NORMAL: 0.8,
            AccountPriority.LOW: 0.6,
            AccountPriority.BACKUP: 0.4
        }
        priority_score = priority_scores.get(config.priority, 0.8) * 0.2

        # 最近成功时间分数 (10%)
        time_score = 0.1
        if metrics.last_success:
            hours_since_success = (datetime.utcnow() - metrics.last_success).total_seconds() / 3600
            time_score = max(0, (24 - hours_since_success) / 24) * 0.1

        return health_score + usage_score + priority_score + time_score

    async def update_account_success(self, account_id: str, operation_type: str = "general"):
        """更新账号成功记录"""
        try:
            current_time = datetime.utcnow()

            # 更新基础指标
            await self.redis.hincrby(f'account:{account_id}:metrics', 'total_requests', 1)
            await self.redis.hincrby(f'account:{account_id}:metrics', 'successful_requests', 1)
            await self.redis.hset(f'account:{account_id}:metrics', 'last_success', current_time.isoformat())
            await self.redis.hset(f'account:{account_id}:metrics', 'consecutive_errors', 0)

            # 更新使用计数
            await self._update_usage_counters(account_id)

            # 记录操作历史
            await self._record_operation_history(account_id, 'success', operation_type)

            # 如果账号之前有问题，尝试恢复
            await self._try_account_recovery(account_id)

            self.logger.debug(f"Account {account_id} success updated for {operation_type}")

        except Exception as e:
            self.logger.error(f"Failed to update account success: {e}")

    async def mark_account_error(self, account_id: str, error: str, error_type: str = "general"):
        """标记账号错误 - 增强错误处理"""
        try:
            current_time = datetime.utcnow()

            # 更新错误指标
            await self.redis.hincrby(f'account:{account_id}:metrics', 'total_requests', 1)
            await self.redis.hincrby(f'account:{account_id}:metrics', 'failed_requests', 1)
            await self.redis.hincrby(f'account:{account_id}:metrics', 'consecutive_errors', 1)
            await self.redis.hset(f'account:{account_id}:metrics', 'last_error', current_time.isoformat())

            # 记录错误详情
            await self._record_error_details(account_id, error, error_type)

            # 检查是否需要特殊处理
            await self._handle_specific_errors(account_id, error, error_type)

            # 检查是否需要暂停账号
            consecutive_errors = await self.redis.hget(f'account:{account_id}:metrics', 'consecutive_errors')
            if consecutive_errors and int(consecutive_errors) >= self.error_threshold:
                await self._suspend_account(account_id, f"Too many consecutive errors: {consecutive_errors}")

            self.logger.warning(f"Account {account_id} error marked: {error_type} - {error}")

        except Exception as e:
            self.logger.error(f"Failed to mark account error: {e}")

    async def _handle_specific_errors(self, account_id: str, error: str, error_type: str):
        """处理特定类型的错误"""
        error_lower = error.lower()

        if 'rate limit' in error_lower or 'too many requests' in error_lower:
            # 速率限制错误 - 设置冷却期
            await self._set_account_cooldown(account_id, self.cooldown_duration)
            await self.redis.hincrby(f'account:{account_id}:metrics', 'rate_limit_hits', 1)

        elif 'unauthorized' in error_lower or 'forbidden' in error_lower:
            # 认证错误 - 可能需要重新登录
            await self._mark_account_needs_reauth(account_id)

        elif 'suspended' in error_lower or 'locked' in error_lower:
            # 账号被封 - 立即暂停
            await self._suspend_account(account_id, f"Account suspended by platform: {error}")

        elif 'not found' in error_lower:
            # 资源不存在 - 不算严重错误
            pass  # 不增加连续错误计数

    async def get_account_statistics(self) -> Dict:
        """获取账号池统计信息"""
        try:
            stats = {
                'total_accounts': 0,
                'active_accounts': 0,
                'suspended_accounts': 0,
                'error_accounts': 0,
                'maintenance_accounts': 0,
                'cooldown_accounts': 0,
                'health_distribution': {'high': 0, 'medium': 0, 'low': 0},
                'priority_distribution': {},
                'daily_usage_total': 0,
                'average_health_score': 0.0
            }

            # 获取所有账号
            all_accounts = await self.redis.smembers('accounts:all')
            stats['total_accounts'] = len(all_accounts)

            total_health = 0.0

            for account_id in all_accounts:
                account_id = account_id.decode()

                # 获取账号配置和指标
                config = await self._get_account_config(account_id)
                metrics = await self._get_account_metrics(account_id)

                if not config or not metrics:
                    continue

                # 状态统计
                status_key = f"{config.status.value}_accounts"
                if status_key in stats:
                    stats[status_key] += 1

                # 优先级统计
                priority = config.priority.value
                stats['priority_distribution'][priority] = stats['priority_distribution'].get(priority, 0) + 1

                # 健康分数统计
                health_score = metrics.health_score
                total_health += health_score

                if health_score >= 0.8:
                    stats['health_distribution']['high'] += 1
                elif health_score >= 0.6:
                    stats['health_distribution']['medium'] += 1
                else:
                    stats['health_distribution']['low'] += 1

                # 使用量统计
                stats['daily_usage_total'] += metrics.daily_usage

            # 计算平均健康分数
            if stats['total_accounts'] > 0:
                stats['average_health_score'] = total_health / stats['total_accounts']

            return stats

        except Exception as e:
            self.logger.error(f"Failed to get account statistics: {e}")
            return {}

    async def batch_health_check(self) -> Dict:
        """批量健康检查"""
        try:
            results = {
                'checked': 0,
                'healthy': 0,
                'unhealthy': 0,
                'recovered': 0,
                'suspended': 0,
                'details': []
            }

            all_accounts = await self.redis.smembers('accounts:all')

            for account_id in all_accounts:
                account_id = account_id.decode()

                try:
                    # 执行单个账号健康检查
                    health_result = await self._check_single_account_health(account_id)
                    results['details'].append(health_result)
                    results['checked'] += 1

                    if health_result['healthy']:
                        results['healthy'] += 1

                        # 尝试恢复之前有问题的账号
                        if health_result.get('recovered'):
                            results['recovered'] += 1
                    else:
                        results['unhealthy'] += 1

                        # 检查是否需要暂停
                        if health_result.get('should_suspend'):
                            await self._suspend_account(account_id, health_result.get('reason', 'Health check failed'))
                            results['suspended'] += 1

                except Exception as e:
                    self.logger.error(f"Health check failed for account {account_id}: {e}")
                    results['details'].append({
                        'account_id': account_id,
                        'healthy': False,
                        'error': str(e)
                    })

            self.logger.info(f"Batch health check completed: {results['checked']} accounts checked")
            return results

        except Exception as e:
            self.logger.error(f"Batch health check failed: {e}")
            return {'error': str(e)}

    async def _check_single_account_health(self, account_id: str) -> Dict:
        """单个账号健康检查"""
        try:
            config = await self._get_account_config(account_id)
            metrics = await self._get_account_metrics(account_id)

            if not config or not metrics:
                return {
                    'account_id': account_id,
                    'healthy': False,
                    'reason': 'Missing config or metrics'
                }

            health_score = metrics.health_score
            is_healthy = health_score >= self.health_threshold

            result = {
                'account_id': account_id,
                'healthy': is_healthy,
                'health_score': health_score,
                'status': config.status.value,
                'daily_usage': metrics.daily_usage,
                'success_rate': metrics.success_rate,
                'consecutive_errors': metrics.consecutive_errors
            }

            # 检查是否需要特殊处理
            if not is_healthy:
                if metrics.consecutive_errors >= config.max_consecutive_errors:
                    result['should_suspend'] = True
                    result['reason'] = f"Too many consecutive errors: {metrics.consecutive_errors}"
                elif metrics.success_rate < 0.5:
                    result['should_suspend'] = True
                    result['reason'] = f"Low success rate: {metrics.success_rate:.2%}"

            # 检查是否可以恢复
            elif config.status in [AccountStatus.SUSPENDED, AccountStatus.ERROR]:
                if health_score >= 0.8 and metrics.consecutive_errors == 0:
                    result['recovered'] = True
                    await self._recover_account(account_id)

            return result

        except Exception as e:
            return {
                'account_id': account_id,
                'healthy': False,
                'error': str(e)
            }

    async def add_account(self, username: str, password: str, email: str,
                         priority: AccountPriority = AccountPriority.NORMAL,
                         tags: List[str] = None) -> bool:
        """添加新账号"""
        try:
            # 添加到twscrape
            await self.api.pool.add_account(username, password, email, password)

            # 创建账号配置
            account_config = AccountConfig(
                account_id=f"tw_{username}",
                username=username,
                email=email,
                status=AccountStatus.MAINTENANCE,  # 新账号先设为维护状态
                priority=priority,
                tags=tags or []
            )

            # 保存配置
            await self._save_account_config(account_config)

            # 初始化指标
            await self._initialize_account_metrics(account_config.account_id)

            self.logger.info(f"Account {username} added successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to add account {username}: {e}")
            return False

    async def remove_account(self, account_id: str) -> bool:
        """移除账号"""
        try:
            config = await self._get_account_config(account_id)
            if not config:
                return False

            # 从twscrape移除
            await self.api.pool.delete(config.username)

            # 从Redis清理数据
            await self._cleanup_account_data(account_id)

            self.logger.info(f"Account {account_id} removed successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to remove account {account_id}: {e}")
            return False

    # ========== 辅助方法 ==========

    async def _get_account_config(self, account_id: str) -> Optional[AccountConfig]:
        """获取账号配置"""
        try:
            config_data = await self.redis.hgetall(f'account:{account_id}:config')
            if not config_data:
                return None

            # 转换字节数据
            config_dict = {k.decode(): v.decode() for k, v in config_data.items()}

            # 处理枚举类型
            config_dict['status'] = AccountStatus(config_dict['status'])
            config_dict['priority'] = AccountPriority(config_dict['priority'])
            config_dict['tags'] = json.loads(config_dict.get('tags', '[]'))

            # 处理数值类型
            for field in ['daily_limit', 'hourly_limit', 'cooldown_minutes', 'max_consecutive_errors']:
                if field in config_dict:
                    config_dict[field] = int(config_dict[field])

            config_dict['auto_recovery'] = config_dict.get('auto_recovery', 'true').lower() == 'true'

            return AccountConfig(**config_dict)

        except Exception as e:
            self.logger.error(f"Failed to get account config for {account_id}: {e}")
            return None

    async def _save_account_config(self, config: AccountConfig):
        """保存账号配置"""
        try:
            config_dict = asdict(config)
            config_dict['status'] = config.status.value
            config_dict['priority'] = config.priority.value
            config_dict['tags'] = json.dumps(config.tags)

            await self.redis.hset(f'account:{config.account_id}:config', mapping=config_dict)
            await self.redis.sadd('accounts:all', config.account_id)

            # 更新状态索引
            await self._update_status_index(config.account_id, config.status)

        except Exception as e:
            self.logger.error(f"Failed to save account config: {e}")

    async def _get_account_metrics(self, account_id: str) -> AccountMetrics:
        """获取账号指标"""
        try:
            metrics_data = await self.redis.hgetall(f'account:{account_id}:metrics')

            if not metrics_data:
                return AccountMetrics()

            # 转换数据类型
            metrics_dict = {}
            for k, v in metrics_data.items():
                key = k.decode()
                value = v.decode()

                if key in ['total_requests', 'successful_requests', 'failed_requests',
                          'rate_limit_hits', 'consecutive_errors', 'daily_usage', 'weekly_usage']:
                    metrics_dict[key] = int(value)
                elif key in ['last_used', 'last_success', 'last_error']:
                    if value:
                        metrics_dict[key] = datetime.fromisoformat(value)

            return AccountMetrics(**metrics_dict)

        except Exception as e:
            self.logger.error(f"Failed to get account metrics for {account_id}: {e}")
            return AccountMetrics()

    async def _save_account_metrics(self, account_id: str, metrics: AccountMetrics):
        """保存账号指标"""
        try:
            metrics_dict = asdict(metrics)

            # 转换datetime为字符串
            for key, value in metrics_dict.items():
                if isinstance(value, datetime):
                    metrics_dict[key] = value.isoformat()
                elif value is None:
                    metrics_dict[key] = ''

            await self.redis.hset(f'account:{account_id}:metrics', mapping=metrics_dict)

        except Exception as e:
            self.logger.error(f"Failed to save account metrics: {e}")

    async def _initialize_account_metrics(self, account_id: str):
        """初始化账号指标"""
        metrics = AccountMetrics()
        await self._save_account_metrics(account_id, metrics)

    async def _update_status_index(self, account_id: str, status: AccountStatus):
        """更新状态索引"""
        # 从所有状态集合中移除
        for s in AccountStatus:
            await self.redis.srem(f'accounts:{s.value}', account_id)

        # 添加到新状态集合
        await self.redis.sadd(f'accounts:{status.value}', account_id)

    async def _is_account_in_cooldown(self, account_id: str) -> bool:
        """检查账号是否在冷却期"""
        cooldown_until = await self.redis.get(f'account:{account_id}:cooldown')
        if not cooldown_until:
            return False

        cooldown_time = datetime.fromisoformat(cooldown_until.decode())
        return datetime.utcnow() < cooldown_time

    async def _is_account_over_limit(self, account_id: str) -> bool:
        """检查账号是否超过使用限制"""
        config = await self._get_account_config(account_id)
        metrics = await self._get_account_metrics(account_id)

        if not config or not metrics:
            return True

        return metrics.daily_usage >= config.daily_limit

    async def _set_account_cooldown(self, account_id: str, duration_seconds: int):
        """设置账号冷却期"""
        cooldown_until = datetime.utcnow() + timedelta(seconds=duration_seconds)
        await self.redis.set(f'account:{account_id}:cooldown',
                           cooldown_until.isoformat(),
                           ex=duration_seconds)

    async def _suspend_account(self, account_id: str, reason: str):
        """暂停账号"""
        config = await self._get_account_config(account_id)
        if config:
            config.status = AccountStatus.SUSPENDED
            await self._save_account_config(config)

        # 记录暂停原因
        await self.redis.hset(f'account:{account_id}:suspension',
                            'reason', reason,
                            'suspended_at', datetime.utcnow().isoformat())

        self.logger.warning(f"Account {account_id} suspended: {reason}")

    async def _recover_account(self, account_id: str):
        """恢复账号"""
        config = await self._get_account_config(account_id)
        if config:
            config.status = AccountStatus.ACTIVE
            await self._save_account_config(config)

        # 清理暂停记录
        await self.redis.delete(f'account:{account_id}:suspension')
        await self.redis.delete(f'account:{account_id}:cooldown')

        self.logger.info(f"Account {account_id} recovered")

    async def _record_account_usage(self, account_id: str):
        """记录账号使用"""
        await self.redis.hincrby(f'account:{account_id}:metrics', 'daily_usage', 1)
        await self.redis.hset(f'account:{account_id}:metrics', 'last_used', datetime.utcnow().isoformat())

    async def _get_full_account_info(self, account_id: str) -> Dict:
        """获取完整账号信息"""
        config = await self._get_account_config(account_id)
        metrics = await self._get_account_metrics(account_id)

        # 获取cookies
        cookies_data = await self.redis.hget(f'account:{account_id}', 'cookies')
        cookies = json.loads(cookies_data.decode()) if cookies_data else {}

        return {
            'account_id': account_id,
            'username': config.username,
            'email': config.email,
            'status': config.status.value,
            'priority': config.priority.value,
            'health_score': metrics.health_score,
            'daily_usage': metrics.daily_usage,
            'success_rate': metrics.success_rate,
            'cookies': cookies,
            'last_used': metrics.last_used.isoformat() if metrics.last_used else None
        }

    async def _cleanup_account_data(self, account_id: str):
        """清理账号数据"""
        # 删除所有相关的Redis键
        keys_to_delete = [
            f'account:{account_id}:config',
            f'account:{account_id}:metrics',
            f'account:{account_id}:cookies',
            f'account:{account_id}:suspension',
            f'account:{account_id}:cooldown',
            f'account:{account_id}:history'
        ]

        for key in keys_to_delete:
            await self.redis.delete(key)

        # 从所有集合中移除
        await self.redis.srem('accounts:all', account_id)
        for status in AccountStatus:
            await self.redis.srem(f'accounts:{status.value}', account_id)

# ========== 账号管理使用示例 ==========

class AccountManagerExample:
    """账号管理器使用示例"""

    async def example_usage(self):
        """完整使用示例"""
        import redis.asyncio as redis
        from twscrape import API

        # 初始化
        redis_client = redis.Redis(host='localhost', port=6379, db=0)
        api = API()
        account_manager = ProductionAccountManager(redis_client, api)

        # 初始化账号管理器
        await account_manager.initialize()

        # 1. 添加新账号
        success = await account_manager.add_account(
            username="test_account",
            password="password123",
            email="test@example.com",
            priority=AccountPriority.NORMAL,
            tags=["test", "development"]
        )

        # 2. 获取可用账号
        account = await account_manager.get_available_account(
            priority=AccountPriority.HIGH,
            tags=["production"],
            exclude_accounts=["problematic_account_id"]
        )

        if account:
            print(f"Selected account: {account['username']}")
            print(f"Health score: {account['health_score']}")

            # 3. 使用账号执行操作
            try:
                # 模拟成功操作
                await account_manager.update_account_success(
                    account['account_id'],
                    operation_type="tweet_search"
                )
            except Exception as e:
                # 记录错误
                await account_manager.mark_account_error(
                    account['account_id'],
                    str(e),
                    error_type="api_error"
                )

        # 4. 获取统计信息
        stats = await account_manager.get_account_statistics()
        print(f"Total accounts: {stats['total_accounts']}")
        print(f"Active accounts: {stats['active_accounts']}")
        print(f"Average health: {stats['average_health_score']:.2f}")

        # 5. 执行健康检查
        health_results = await account_manager.batch_health_check()
        print(f"Health check: {health_results['healthy']}/{health_results['checked']} healthy")

# ========== 配置管理 ==========

class AccountManagerConfig:
    """账号管理器配置类"""

    def __init__(self):
        # 基础配置
        self.HEALTH_THRESHOLD = 0.7
        self.MAX_DAILY_USAGE = 1000
        self.COOLDOWN_DURATION = 1800  # 30分钟
        self.ERROR_THRESHOLD = 5

        # 限制配置
        self.DEFAULT_DAILY_LIMIT = 1000
        self.DEFAULT_HOURLY_LIMIT = 100
        self.HIGH_PRIORITY_DAILY_LIMIT = 1500
        self.LOW_PRIORITY_DAILY_LIMIT = 500

        # 恢复配置
        self.AUTO_RECOVERY_ENABLED = True
        self.RECOVERY_HEALTH_THRESHOLD = 0.8
        self.RECOVERY_CHECK_INTERVAL = 3600  # 1小时

        # 监控配置
        self.HEALTH_CHECK_INTERVAL = 300  # 5分钟
        self.METRICS_RETENTION_DAYS = 30
        self.ALERT_THRESHOLDS = {
            'low_health_accounts': 0.3,  # 30%以下健康账号时告警
            'high_error_rate': 0.2,      # 20%以上错误率时告警
            'account_shortage': 5         # 可用账号少于5个时告警
        }

# ========== Redis数据结构设计 ==========

class RedisDataStructure:
    """Redis数据结构说明"""

    def __init__(self):
        self.structures = {
            # 账号配置
            "account:{account_id}:config": {
                "type": "hash",
                "fields": [
                    "account_id", "username", "email", "status", "priority",
                    "daily_limit", "hourly_limit", "cooldown_minutes",
                    "max_consecutive_errors", "auto_recovery", "tags"
                ],
                "example": {
                    "account_id": "tw_testuser",
                    "username": "testuser",
                    "email": "test@example.com",
                    "status": "active",
                    "priority": "normal",
                    "daily_limit": "1000",
                    "hourly_limit": "100",
                    "cooldown_minutes": "30",
                    "max_consecutive_errors": "5",
                    "auto_recovery": "true",
                    "tags": '["test", "development"]'
                }
            },

            # 账号指标
            "account:{account_id}:metrics": {
                "type": "hash",
                "fields": [
                    "total_requests", "successful_requests", "failed_requests",
                    "rate_limit_hits", "last_used", "last_success", "last_error",
                    "consecutive_errors", "daily_usage", "weekly_usage"
                ],
                "example": {
                    "total_requests": "150",
                    "successful_requests": "142",
                    "failed_requests": "8",
                    "rate_limit_hits": "2",
                    "last_used": "2024-01-01T12:00:00",
                    "last_success": "2024-01-01T11:58:00",
                    "last_error": "2024-01-01T10:30:00",
                    "consecutive_errors": "0",
                    "daily_usage": "45",
                    "weekly_usage": "320"
                }
            },

            # 账号Cookies
            "account:{account_id}:cookies": {
                "type": "hash",
                "fields": ["cookies_data", "updated_at", "expires_at"],
                "example": {
                    "cookies_data": '{"auth_token": "...", "ct0": "..."}',
                    "updated_at": "2024-01-01T08:00:00",
                    "expires_at": "2024-01-08T08:00:00"
                }
            },

            # 状态索引集合
            "accounts:all": {
                "type": "set",
                "description": "所有账号ID集合"
            },
            "accounts:active": {
                "type": "set",
                "description": "活跃账号ID集合"
            },
            "accounts:suspended": {
                "type": "set",
                "description": "暂停账号ID集合"
            },

            # 冷却期管理
            "account:{account_id}:cooldown": {
                "type": "string",
                "description": "冷却期结束时间",
                "ttl": "自动过期"
            },

            # 暂停信息
            "account:{account_id}:suspension": {
                "type": "hash",
                "fields": ["reason", "suspended_at", "suspended_by"],
                "example": {
                    "reason": "Too many consecutive errors: 5",
                    "suspended_at": "2024-01-01T12:00:00",
                    "suspended_by": "auto_system"
                }
            }
        }

# ========== 监控和告警系统 ==========

class AccountMonitoringSystem:
    """账号监控和告警系统"""

    def __init__(self, account_manager: ProductionAccountManager):
        self.account_manager = account_manager
        self.logger = logging.getLogger(__name__)

    async def start_monitoring(self):
        """启动监控系统"""
        # 启动定时任务
        asyncio.create_task(self._health_check_loop())
        asyncio.create_task(self._metrics_collection_loop())
        asyncio.create_task(self._alert_check_loop())

    async def _health_check_loop(self):
        """健康检查循环"""
        while True:
            try:
                await self.account_manager.batch_health_check()
                await asyncio.sleep(300)  # 5分钟检查一次
            except Exception as e:
                self.logger.error(f"Health check loop error: {e}")
                await asyncio.sleep(60)

    async def _metrics_collection_loop(self):
        """指标收集循环"""
        while True:
            try:
                await self._collect_system_metrics()
                await asyncio.sleep(60)  # 1分钟收集一次
            except Exception as e:
                self.logger.error(f"Metrics collection error: {e}")
                await asyncio.sleep(30)

    async def _alert_check_loop(self):
        """告警检查循环"""
        while True:
            try:
                await self._check_alerts()
                await asyncio.sleep(120)  # 2分钟检查一次
            except Exception as e:
                self.logger.error(f"Alert check error: {e}")
                await asyncio.sleep(60)

    async def _collect_system_metrics(self):
        """收集系统指标"""
        stats = await self.account_manager.get_account_statistics()
        timestamp = datetime.utcnow().isoformat()

        # 保存到时序数据
        metrics_key = f"metrics:system:{datetime.utcnow().strftime('%Y%m%d%H%M')}"
        await self.account_manager.redis.hset(metrics_key, mapping={
            'timestamp': timestamp,
            'total_accounts': stats['total_accounts'],
            'active_accounts': stats['active_accounts'],
            'suspended_accounts': stats['suspended_accounts'],
            'average_health_score': stats['average_health_score'],
            'daily_usage_total': stats['daily_usage_total']
        })

        # 设置过期时间（保留30天）
        await self.account_manager.redis.expire(metrics_key, 86400 * 30)

    async def _check_alerts(self):
        """检查告警条件"""
        stats = await self.account_manager.get_account_statistics()

        alerts = []

        # 检查健康账号比例
        if stats['total_accounts'] > 0:
            healthy_ratio = stats['active_accounts'] / stats['total_accounts']
            if healthy_ratio < 0.3:
                alerts.append({
                    'type': 'low_healthy_accounts',
                    'severity': 'critical',
                    'message': f"Only {healthy_ratio:.1%} accounts are healthy",
                    'value': healthy_ratio,
                    'threshold': 0.3
                })

        # 检查可用账号数量
        if stats['active_accounts'] < 5:
            alerts.append({
                'type': 'account_shortage',
                'severity': 'warning',
                'message': f"Only {stats['active_accounts']} active accounts available",
                'value': stats['active_accounts'],
                'threshold': 5
            })

        # 检查平均健康分数
        if stats['average_health_score'] < 0.6:
            alerts.append({
                'type': 'low_health_score',
                'severity': 'warning',
                'message': f"Average health score is {stats['average_health_score']:.2f}",
                'value': stats['average_health_score'],
                'threshold': 0.6
            })

        # 发送告警
        for alert in alerts:
            await self._send_alert(alert)

    async def _send_alert(self, alert: Dict):
        """发送告警"""
        # 检查是否已经发送过相同告警（避免重复）
        alert_key = f"alert:{alert['type']}:{datetime.utcnow().strftime('%Y%m%d%H')}"
        if await self.account_manager.redis.exists(alert_key):
            return

        # 记录告警
        await self.account_manager.redis.setex(alert_key, 3600, "sent")

        # 记录到日志
        self.logger.warning(f"ALERT [{alert['severity'].upper()}] {alert['message']}")

        # 这里可以集成其他告警渠道（邮件、Slack、钉钉等）
        await self._send_to_external_channels(alert)

    async def _send_to_external_channels(self, alert: Dict):
        """发送到外部告警渠道"""
        # 示例：发送到Webhook
        # webhook_url = "https://hooks.slack.com/services/..."
        # payload = {
        #     "text": f"XGet Alert: {alert['message']}",
        #     "severity": alert['severity']
        # }
        # async with aiohttp.ClientSession() as session:
        #     await session.post(webhook_url, json=payload)
        pass

# ========== 性能优化建议 ==========

class PerformanceOptimizations:
    """性能优化建议和最佳实践"""

    def __init__(self):
        self.optimizations = {
            "redis_connection_pool": {
                "description": "使用Redis连接池",
                "implementation": """
                # 使用连接池
                redis_pool = redis.ConnectionPool(
                    host='localhost',
                    port=6379,
                    db=0,
                    max_connections=20,
                    retry_on_timeout=True
                )
                redis_client = redis.Redis(connection_pool=redis_pool)
                """
            },

            "batch_operations": {
                "description": "批量操作减少Redis调用",
                "implementation": """
                # 批量更新指标
                async def batch_update_metrics(self, updates: List[Dict]):
                    pipe = self.redis.pipeline()
                    for update in updates:
                        pipe.hincrby(f"account:{update['id']}:metrics",
                                   update['field'], update['value'])
                    await pipe.execute()
                """
            },

            "caching_strategy": {
                "description": "缓存频繁访问的数据",
                "implementation": """
                # 内存缓存账号配置
                from functools import lru_cache

                @lru_cache(maxsize=1000)
                async def get_cached_account_config(self, account_id: str):
                    # 实现缓存逻辑
                    pass
                """
            },

            "async_optimization": {
                "description": "异步操作优化",
                "implementation": """
                # 并发处理多个账号
                async def parallel_health_check(self, account_ids: List[str]):
                    tasks = [self._check_single_account_health(aid)
                            for aid in account_ids]
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    return results
                """
            }
        }

# ========== 部署和运维指南 ==========

class DeploymentGuide:
    """部署和运维指南"""

    def __init__(self):
        self.deployment_steps = [
            {
                "step": 1,
                "title": "环境准备",
                "tasks": [
                    "安装Redis服务器",
                    "配置Redis持久化",
                    "设置Redis内存限制",
                    "配置Redis安全认证"
                ]
            },
            {
                "step": 2,
                "title": "账号管理器部署",
                "tasks": [
                    "创建core目录结构",
                    "部署account_manager.py",
                    "配置环境变量",
                    "初始化Redis数据结构"
                ]
            },
            {
                "step": 3,
                "title": "监控系统配置",
                "tasks": [
                    "配置Prometheus指标收集",
                    "设置Grafana仪表板",
                    "配置告警规则",
                    "测试告警通道"
                ]
            },
            {
                "step": 4,
                "title": "生产环境优化",
                "tasks": [
                    "调整Redis配置参数",
                    "设置日志轮转",
                    "配置健康检查",
                    "制定备份策略"
                ]
            }
        ]

        self.redis_config = """
        # Redis生产配置建议
        maxmemory 2gb
        maxmemory-policy allkeys-lru
        save 900 1
        save 300 10
        save 60 10000
        appendonly yes
        appendfsync everysec
        """

        self.monitoring_config = """
        # Prometheus配置
        global:
          scrape_interval: 15s

        scrape_configs:
          - job_name: 'xget-accounts'
            static_configs:
              - targets: ['localhost:8000']
            metrics_path: '/metrics'
            scrape_interval: 30s
        """

# ========== 总结和下一步 ==========

class AccountManagerSummary:
    """账号管理模块总结"""

    def __init__(self):
        self.features = {
            "✅ 已完善的功能": [
                "智能账号选择算法",
                "健康分数计算",
                "错误处理和恢复",
                "使用限制和冷却",
                "批量健康检查",
                "统计分析功能",
                "监控和告警系统",
                "Redis数据结构设计"
            ],

            "🚀 核心优势": [
                "生产级稳定性",
                "智能轮换策略",
                "自动故障恢复",
                "全面监控体系",
                "灵活配置管理",
                "高性能设计"
            ],

            "📋 实施建议": [
                "先实现核心AccountManager类",
                "逐步添加监控功能",
                "测试各种错误场景",
                "优化性能参数",
                "完善告警机制"
            ]
        }

        self.next_steps = [
            "创建core/account_manager.py文件",
            "实现基础的AccountManager类",
            "集成到现有的twscrape测试中",
            "添加Redis支持和配置",
            "实现监控和统计功能",
            "编写单元测试",
            "性能测试和优化",
            "文档完善和部署指南"
        ]
```

### 3. 代理管理模块 - SOCKS5专用版

```python
# core/proxy_manager.py
import asyncio
import aiohttp
import aiosocks
import random
import json
import logging
import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, asdict
import redis.asyncio as redis

class ProxyProtocol(Enum):
    """代理协议类型"""
    SOCKS5 = "socks5"
    SOCKS4 = "socks4"
    HTTP = "http"
    HTTPS = "https"

class ProxyStatus(Enum):
    """代理状态"""
    ACTIVE = "active"           # 活跃可用
    INACTIVE = "inactive"       # 不活跃
    ERROR = "error"            # 错误状态
    TESTING = "testing"        # 测试中
    BANNED = "banned"          # 被封禁
    MAINTENANCE = "maintenance" # 维护中

class ProxyRegion(Enum):
    """代理地区"""
    US = "us"          # 美国
    EU = "eu"          # 欧洲
    ASIA = "asia"      # 亚洲
    GLOBAL = "global"  # 全球

@dataclass
class ProxyMetrics:
    """代理指标数据"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    timeout_requests: int = 0
    banned_requests: int = 0
    last_used: Optional[datetime] = None
    last_success: Optional[datetime] = None
    last_error: Optional[datetime] = None
    consecutive_errors: int = 0
    average_response_time: float = 0.0
    daily_usage: int = 0
    weekly_usage: int = 0

    @property
    def success_rate(self) -> float:
        """成功率计算"""
        if self.total_requests == 0:
            return 1.0
        return self.successful_requests / self.total_requests

    @property
    def health_score(self) -> float:
        """健康分数计算 (0-1)"""
        base_score = self.success_rate

        # 连续错误惩罚
        error_penalty = min(self.consecutive_errors * 0.15, 0.6)

        # 响应时间因子
        time_factor = 1.0
        if self.average_response_time > 5.0:  # 超过5秒响应时间
            time_factor = 0.7
        elif self.average_response_time > 3.0:  # 超过3秒
            time_factor = 0.85

        # 使用频率调整
        usage_factor = 1.0
        if self.daily_usage > 800:  # 接近限制时降低分数
            usage_factor = 0.8
        elif self.daily_usage > 600:
            usage_factor = 0.9

        return max(0.0, (base_score - error_penalty) * time_factor * usage_factor)

@dataclass
class ProxyConfig:
    """SOCKS5代理配置"""
    proxy_id: str
    host: str
    port: int
    username: str
    password: str
    protocol: ProxyProtocol = ProxyProtocol.SOCKS5
    region: ProxyRegion = ProxyRegion.GLOBAL
    status: ProxyStatus = ProxyStatus.ACTIVE
    max_concurrent: int = 10
    daily_limit: int = 1000
    max_consecutive_errors: int = 5
    timeout_seconds: int = 10
    provider: str = "unknown"
    cost_per_gb: float = 0.0
    expires_at: Optional[datetime] = None
    tags: List[str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []

    @property
    def proxy_url(self) -> str:
        """生成代理URL"""
        if self.protocol == ProxyProtocol.SOCKS5:
            return f"socks5://{self.username}:{self.password}@{self.host}:{self.port}"
        elif self.protocol == ProxyProtocol.HTTP:
            return f"http://{self.username}:{self.password}@{self.host}:{self.port}"
        else:
            return f"{self.protocol.value}://{self.username}:{self.password}@{self.host}:{self.port}"

    @property
    def connection_info(self) -> Dict:
        """获取连接信息"""
        return {
            'proxy_type': aiosocks.SOCKS5 if self.protocol == ProxyProtocol.SOCKS5 else aiosocks.SOCKS4,
            'addr': self.host,
            'port': self.port,
            'username': self.username,
            'password': self.password
        }

class ProductionProxyManager:
    """生产级SOCKS5代理管理器"""

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.logger = logging.getLogger(__name__)

        # 配置参数
        self.health_threshold = 0.7
        self.max_concurrent_per_proxy = 10
        self.health_check_interval = 300  # 5分钟
        self.test_urls = [
            'https://httpbin.org/ip',
            'https://api.ipify.org?format=json',
            'https://ifconfig.me/ip'
        ]

        # 性能统计
        self.response_times = {}

    async def initialize(self):
        """初始化代理管理器"""
        await self._setup_redis_structures()
        self.logger.info("Proxy manager initialized")

    async def _setup_redis_structures(self):
        """设置Redis数据结构"""
        await self.redis.sadd('proxy_manager:initialized', '1')

    async def add_proxy_batch(self, proxy_list: List[Dict]) -> Dict[str, bool]:
        """批量添加SOCKS5代理"""
        results = {}

        for proxy_data in proxy_list:
            try:
                proxy_config = ProxyConfig(
                    proxy_id=f"socks5_{proxy_data['host']}_{proxy_data['port']}",
                    host=proxy_data['host'],
                    port=int(proxy_data['port']),
                    username=proxy_data['username'],
                    password=proxy_data['password'],
                    protocol=ProxyProtocol.SOCKS5,
                    region=ProxyRegion(proxy_data.get('region', 'global')),
                    provider=proxy_data.get('provider', 'unknown'),
                    cost_per_gb=float(proxy_data.get('cost_per_gb', 0.0)),
                    tags=proxy_data.get('tags', [])
                )

                success = await self._add_single_proxy(proxy_config)
                results[proxy_config.proxy_id] = success

            except Exception as e:
                self.logger.error(f"Failed to add proxy {proxy_data}: {e}")
                results[f"error_{proxy_data.get('host', 'unknown')}"] = False

        self.logger.info(f"Batch add completed: {sum(results.values())}/{len(proxy_list)} successful")
        return results

    async def _add_single_proxy(self, config: ProxyConfig) -> bool:
        """添加单个代理"""
        try:
            # 保存代理配置
            await self._save_proxy_config(config)

            # 初始化指标
            await self._initialize_proxy_metrics(config.proxy_id)

            # 执行初始健康检查
            is_healthy = await self._test_proxy_connection(config)

            if is_healthy:
                await self._update_proxy_status(config.proxy_id, ProxyStatus.ACTIVE)
                self.logger.info(f"Proxy {config.proxy_id} added and verified")
            else:
                await self._update_proxy_status(config.proxy_id, ProxyStatus.ERROR)
                self.logger.warning(f"Proxy {config.proxy_id} added but failed initial test")

            return True

        except Exception as e:
            self.logger.error(f"Failed to add proxy {config.proxy_id}: {e}")
            return False

    async def get_available_proxy(self,
                                region: Optional[ProxyRegion] = None,
                                tags: Optional[List[str]] = None,
                                exclude_proxies: Optional[List[str]] = None,
                                min_health_score: float = 0.7) -> Optional[Dict]:
        """获取可用代理 - 智能选择算法"""
        try:
            # 获取候选代理
            candidates = await self._get_candidate_proxies(region, tags, exclude_proxies, min_health_score)

            if not candidates:
                self.logger.warning("No candidate proxies available")
                return None

            # 智能选择最佳代理
            best_proxy = await self._select_best_proxy(candidates)

            if best_proxy:
                # 更新使用记录
                await self._record_proxy_usage(best_proxy['proxy_id'])

                # 返回连接信息
                return {
                    'proxy_id': best_proxy['proxy_id'],
                    'proxy_url': best_proxy['config'].proxy_url,
                    'connection_info': best_proxy['config'].connection_info,
                    'health_score': best_proxy['metrics'].health_score,
                    'region': best_proxy['config'].region.value,
                    'response_time': best_proxy['metrics'].average_response_time
                }

            return None

        except Exception as e:
            self.logger.error(f"Failed to get available proxy: {e}")
            return None

    async def _get_candidate_proxies(self,
                                   region: Optional[ProxyRegion],
                                   tags: Optional[List[str]],
                                   exclude_proxies: Optional[List[str]],
                                   min_health_score: float) -> List[Dict]:
        """获取候选代理列表"""
        candidates = []

        # 获取所有活跃代理
        active_proxies = await self.redis.smembers('proxies:active')

        for proxy_id in active_proxies:
            proxy_id = proxy_id.decode()

            # 排除指定代理
            if exclude_proxies and proxy_id in exclude_proxies:
                continue

            # 检查代理配置
            config = await self._get_proxy_config(proxy_id)
            if not config:
                continue

            # 地区过滤
            if region and config.region != region:
                continue

            # 标签过滤
            if tags and not any(tag in config.tags for tag in tags):
                continue

            # 检查并发限制
            current_usage = await self._get_current_concurrent_usage(proxy_id)
            if current_usage >= config.max_concurrent:
                continue

            # 检查使用限制
            if await self._is_proxy_over_limit(proxy_id):
                continue

            # 获取代理指标
            metrics = await self._get_proxy_metrics(proxy_id)

            # 健康分数过滤
            if metrics.health_score < min_health_score:
                continue

            candidates.append({
                'proxy_id': proxy_id,
                'config': config,
                'metrics': metrics,
                'current_usage': current_usage
            })

        return candidates

    async def _select_best_proxy(self, candidates: List[Dict]) -> Optional[Dict]:
        """选择最佳代理 - 综合评分算法"""
        if not candidates:
            return None

        # 计算综合评分
        for candidate in candidates:
            score = await self._calculate_proxy_score(candidate)
            candidate['final_score'] = score

        # 按评分排序，选择最高分
        candidates.sort(key=lambda x: x['final_score'], reverse=True)

        return candidates[0]

    async def _calculate_proxy_score(self, candidate: Dict) -> float:
        """计算代理综合评分"""
        config = candidate['config']
        metrics = candidate['metrics']
        current_usage = candidate['current_usage']

        # 基础健康分数 (40%)
        health_score = metrics.health_score * 0.4

        # 响应时间分数 (25%) - 响应时间越短分数越高
        max_acceptable_time = 5.0  # 5秒
        time_score = max(0, (max_acceptable_time - metrics.average_response_time) / max_acceptable_time) * 0.25

        # 使用频率分数 (20%) - 使用越少分数越高
        usage_ratio = metrics.daily_usage / config.daily_limit
        usage_score = (1 - usage_ratio) * 0.2

        # 并发使用分数 (15%) - 并发越少分数越高
        concurrent_ratio = current_usage / config.max_concurrent
        concurrent_score = (1 - concurrent_ratio) * 0.15

        return health_score + time_score + usage_score + concurrent_score

    async def _test_proxy_connection(self, config: ProxyConfig) -> bool:
        """测试SOCKS5代理连接"""
        try:
            start_time = time.time()

            # 使用aiosocks进行SOCKS5连接测试
            conn_info = config.connection_info

            # 测试连接到目标URL
            test_url = random.choice(self.test_urls)

            async with aiosocks.Socks5Connector(
                proxy_host=conn_info['addr'],
                proxy_port=conn_info['port'],
                username=conn_info['username'],
                password=conn_info['password']
            ) as connector:

                timeout = aiohttp.ClientTimeout(total=config.timeout_seconds)
                async with aiohttp.ClientSession(
                    connector=connector,
                    timeout=timeout
                ) as session:

                    async with session.get(test_url) as response:
                        if response.status == 200:
                            response_time = time.time() - start_time
                            await self._update_response_time(config.proxy_id, response_time)
                            return True
                        else:
                            return False

        except asyncio.TimeoutError:
            self.logger.warning(f"Proxy {config.proxy_id} timeout during test")
            return False
        except Exception as e:
            self.logger.warning(f"Proxy {config.proxy_id} test failed: {e}")
            return False

    async def update_proxy_success(self, proxy_id: str, response_time: float = 0.0):
        """更新代理成功记录"""
        try:
            current_time = datetime.utcnow()

            # 更新基础指标
            await self.redis.hincrby(f'proxy:{proxy_id}:metrics', 'total_requests', 1)
            await self.redis.hincrby(f'proxy:{proxy_id}:metrics', 'successful_requests', 1)
            await self.redis.hset(f'proxy:{proxy_id}:metrics', 'last_success', current_time.isoformat())
            await self.redis.hset(f'proxy:{proxy_id}:metrics', 'consecutive_errors', 0)

            # 更新响应时间
            if response_time > 0:
                await self._update_response_time(proxy_id, response_time)

            # 更新使用计数
            await self._update_usage_counters(proxy_id)

            # 尝试恢复代理状态
            await self._try_proxy_recovery(proxy_id)

            self.logger.debug(f"Proxy {proxy_id} success updated")

        except Exception as e:
            self.logger.error(f"Failed to update proxy success: {e}")

    async def mark_proxy_error(self, proxy_id: str, error: str, error_type: str = "general"):
        """标记代理错误"""
        try:
            current_time = datetime.utcnow()

            # 更新错误指标
            await self.redis.hincrby(f'proxy:{proxy_id}:metrics', 'total_requests', 1)
            await self.redis.hincrby(f'proxy:{proxy_id}:metrics', 'failed_requests', 1)
            await self.redis.hincrby(f'proxy:{proxy_id}:metrics', 'consecutive_errors', 1)
            await self.redis.hset(f'proxy:{proxy_id}:metrics', 'last_error', current_time.isoformat())

            # 处理特定错误类型
            await self._handle_specific_proxy_errors(proxy_id, error, error_type)

            # 检查是否需要暂停代理
            consecutive_errors = await self.redis.hget(f'proxy:{proxy_id}:metrics', 'consecutive_errors')
            if consecutive_errors and int(consecutive_errors) >= 5:
                await self._suspend_proxy(proxy_id, f"Too many consecutive errors: {consecutive_errors}")

            self.logger.warning(f"Proxy {proxy_id} error marked: {error_type} - {error}")

        except Exception as e:
            self.logger.error(f"Failed to mark proxy error: {e}")

    async def _handle_specific_proxy_errors(self, proxy_id: str, error: str, error_type: str):
        """处理特定类型的代理错误"""
        error_lower = error.lower()

        if 'timeout' in error_lower or 'connection timeout' in error_lower:
            # 超时错误
            await self.redis.hincrby(f'proxy:{proxy_id}:metrics', 'timeout_requests', 1)

        elif 'banned' in error_lower or 'blocked' in error_lower or '403' in error:
            # 被封禁错误
            await self.redis.hincrby(f'proxy:{proxy_id}:metrics', 'banned_requests', 1)
            await self._suspend_proxy(proxy_id, f"Proxy appears to be banned: {error}")

        elif 'authentication' in error_lower or 'auth' in error_lower:
            # 认证错误 - 可能用户名密码有问题
            await self._mark_proxy_auth_error(proxy_id, error)

        elif 'connection refused' in error_lower or 'unreachable' in error_lower:
            # 连接被拒绝 - 代理服务器可能下线
            await self._suspend_proxy(proxy_id, f"Proxy server unreachable: {error}")

    async def batch_health_check(self) -> Dict:
        """批量健康检查"""
        try:
            results = {
                'checked': 0,
                'healthy': 0,
                'unhealthy': 0,
                'recovered': 0,
                'suspended': 0,
                'details': []
            }

            all_proxies = await self.redis.smembers('proxies:all')

            # 并发检查代理健康状态
            tasks = []
            for proxy_id in all_proxies:
                proxy_id = proxy_id.decode()
                tasks.append(self._check_single_proxy_health(proxy_id))

            # 执行并发检查
            health_results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in health_results:
                if isinstance(result, Exception):
                    self.logger.error(f"Health check error: {result}")
                    continue

                results['details'].append(result)
                results['checked'] += 1

                if result['healthy']:
                    results['healthy'] += 1
                    if result.get('recovered'):
                        results['recovered'] += 1
                else:
                    results['unhealthy'] += 1
                    if result.get('suspended'):
                        results['suspended'] += 1

            self.logger.info(f"Batch health check completed: {results['healthy']}/{results['checked']} healthy")
            return results

        except Exception as e:
            self.logger.error(f"Batch health check failed: {e}")
            return {'error': str(e)}

    async def _check_single_proxy_health(self, proxy_id: str) -> Dict:
        """单个代理健康检查"""
        try:
            config = await self._get_proxy_config(proxy_id)
            metrics = await self._get_proxy_metrics(proxy_id)

            if not config or not metrics:
                return {
                    'proxy_id': proxy_id,
                    'healthy': False,
                    'reason': 'Missing config or metrics'
                }

            # 执行连接测试
            is_connected = await self._test_proxy_connection(config)
            health_score = metrics.health_score

            result = {
                'proxy_id': proxy_id,
                'healthy': is_connected and health_score >= self.health_threshold,
                'connected': is_connected,
                'health_score': health_score,
                'status': config.status.value,
                'response_time': metrics.average_response_time,
                'success_rate': metrics.success_rate,
                'consecutive_errors': metrics.consecutive_errors
            }

            # 检查是否需要暂停
            if not result['healthy']:
                if metrics.consecutive_errors >= config.max_consecutive_errors:
                    result['should_suspend'] = True
                    result['reason'] = f"Too many consecutive errors: {metrics.consecutive_errors}"
                elif not is_connected:
                    result['should_suspend'] = True
                    result['reason'] = "Connection test failed"
                elif metrics.success_rate < 0.3:
                    result['should_suspend'] = True
                    result['reason'] = f"Low success rate: {metrics.success_rate:.2%}"

            # 检查是否可以恢复
            elif config.status in [ProxyStatus.ERROR, ProxyStatus.INACTIVE]:
                if is_connected and health_score >= 0.8:
                    result['recovered'] = True
                    await self._recover_proxy(proxy_id)

            return result

        except Exception as e:
            return {
                'proxy_id': proxy_id,
                'healthy': False,
                'error': str(e)
            }

    async def get_proxy_statistics(self) -> Dict:
        """获取代理池统计信息"""
        try:
            stats = {
                'total_proxies': 0,
                'active_proxies': 0,
                'inactive_proxies': 0,
                'error_proxies': 0,
                'banned_proxies': 0,
                'region_distribution': {},
                'provider_distribution': {},
                'health_distribution': {'high': 0, 'medium': 0, 'low': 0},
                'average_health_score': 0.0,
                'average_response_time': 0.0,
                'total_daily_usage': 0,
                'total_concurrent_usage': 0
            }

            # 获取所有代理
            all_proxies = await self.redis.smembers('proxies:all')
            stats['total_proxies'] = len(all_proxies)

            total_health = 0.0
            total_response_time = 0.0
            active_count = 0

            for proxy_id in all_proxies:
                proxy_id = proxy_id.decode()

                config = await self._get_proxy_config(proxy_id)
                metrics = await self._get_proxy_metrics(proxy_id)

                if not config or not metrics:
                    continue

                # 状态统计
                status_key = f"{config.status.value}_proxies"
                if status_key in stats:
                    stats[status_key] += 1

                # 地区统计
                region = config.region.value
                stats['region_distribution'][region] = stats['region_distribution'].get(region, 0) + 1

                # 提供商统计
                provider = config.provider
                stats['provider_distribution'][provider] = stats['provider_distribution'].get(provider, 0) + 1

                # 健康分数统计
                health_score = metrics.health_score
                total_health += health_score

                if health_score >= 0.8:
                    stats['health_distribution']['high'] += 1
                elif health_score >= 0.6:
                    stats['health_distribution']['medium'] += 1
                else:
                    stats['health_distribution']['low'] += 1

                # 响应时间统计
                if metrics.average_response_time > 0:
                    total_response_time += metrics.average_response_time
                    active_count += 1

                # 使用量统计
                stats['total_daily_usage'] += metrics.daily_usage

                # 并发使用统计
                current_usage = await self._get_current_concurrent_usage(proxy_id)
                stats['total_concurrent_usage'] += current_usage

            # 计算平均值
            if stats['total_proxies'] > 0:
                stats['average_health_score'] = total_health / stats['total_proxies']

            if active_count > 0:
                stats['average_response_time'] = total_response_time / active_count

            return stats

        except Exception as e:
            self.logger.error(f"Failed to get proxy statistics: {e}")
            return {}

    async def remove_proxy(self, proxy_id: str) -> bool:
        """移除代理"""
        try:
            # 清理代理数据
            await self._cleanup_proxy_data(proxy_id)

            self.logger.info(f"Proxy {proxy_id} removed successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to remove proxy {proxy_id}: {e}")
            return False

    # ========== 辅助方法 ==========

    async def _save_proxy_config(self, config: ProxyConfig):
        """保存代理配置"""
        try:
            config_dict = asdict(config)
            config_dict['protocol'] = config.protocol.value
            config_dict['region'] = config.region.value
            config_dict['status'] = config.status.value
            config_dict['tags'] = json.dumps(config.tags)

            if config.expires_at:
                config_dict['expires_at'] = config.expires_at.isoformat()

            await self.redis.hset(f'proxy:{config.proxy_id}:config', mapping=config_dict)
            await self.redis.sadd('proxies:all', config.proxy_id)

            # 更新状态索引
            await self._update_proxy_status_index(config.proxy_id, config.status)

        except Exception as e:
            self.logger.error(f"Failed to save proxy config: {e}")

    async def _get_proxy_config(self, proxy_id: str) -> Optional[ProxyConfig]:
        """获取代理配置"""
        try:
            config_data = await self.redis.hgetall(f'proxy:{proxy_id}:config')
            if not config_data:
                return None

            # 转换字节数据
            config_dict = {k.decode(): v.decode() for k, v in config_data.items()}

            # 处理枚举类型
            config_dict['protocol'] = ProxyProtocol(config_dict['protocol'])
            config_dict['region'] = ProxyRegion(config_dict['region'])
            config_dict['status'] = ProxyStatus(config_dict['status'])
            config_dict['tags'] = json.loads(config_dict.get('tags', '[]'))

            # 处理数值类型
            for field in ['port', 'max_concurrent', 'daily_limit', 'max_consecutive_errors', 'timeout_seconds']:
                if field in config_dict:
                    config_dict[field] = int(config_dict[field])

            config_dict['cost_per_gb'] = float(config_dict.get('cost_per_gb', 0.0))

            # 处理日期时间
            if 'expires_at' in config_dict and config_dict['expires_at']:
                config_dict['expires_at'] = datetime.fromisoformat(config_dict['expires_at'])

            return ProxyConfig(**config_dict)

        except Exception as e:
            self.logger.error(f"Failed to get proxy config for {proxy_id}: {e}")
            return None

    async def _initialize_proxy_metrics(self, proxy_id: str):
        """初始化代理指标"""
        metrics = ProxyMetrics()
        await self._save_proxy_metrics(proxy_id, metrics)

    async def _get_proxy_metrics(self, proxy_id: str) -> ProxyMetrics:
        """获取代理指标"""
        try:
            metrics_data = await self.redis.hgetall(f'proxy:{proxy_id}:metrics')

            if not metrics_data:
                return ProxyMetrics()

            # 转换数据类型
            metrics_dict = {}
            for k, v in metrics_data.items():
                key = k.decode()
                value = v.decode()

                if key in ['total_requests', 'successful_requests', 'failed_requests',
                          'timeout_requests', 'banned_requests', 'consecutive_errors',
                          'daily_usage', 'weekly_usage']:
                    metrics_dict[key] = int(value) if value else 0
                elif key == 'average_response_time':
                    metrics_dict[key] = float(value) if value else 0.0
                elif key in ['last_used', 'last_success', 'last_error']:
                    if value:
                        metrics_dict[key] = datetime.fromisoformat(value)

            return ProxyMetrics(**metrics_dict)

        except Exception as e:
            self.logger.error(f"Failed to get proxy metrics for {proxy_id}: {e}")
            return ProxyMetrics()

    async def _save_proxy_metrics(self, proxy_id: str, metrics: ProxyMetrics):
        """保存代理指标"""
        try:
            metrics_dict = asdict(metrics)

            # 转换datetime为字符串
            for key, value in metrics_dict.items():
                if isinstance(value, datetime):
                    metrics_dict[key] = value.isoformat()
                elif value is None:
                    metrics_dict[key] = ''

            await self.redis.hset(f'proxy:{proxy_id}:metrics', mapping=metrics_dict)

        except Exception as e:
            self.logger.error(f"Failed to save proxy metrics: {e}")

    async def _update_proxy_status_index(self, proxy_id: str, status: ProxyStatus):
        """更新代理状态索引"""
        # 从所有状态集合中移除
        for s in ProxyStatus:
            await self.redis.srem(f'proxies:{s.value}', proxy_id)

        # 添加到新状态集合
        await self.redis.sadd(f'proxies:{status.value}', proxy_id)

    async def _update_proxy_status(self, proxy_id: str, status: ProxyStatus):
        """更新代理状态"""
        await self.redis.hset(f'proxy:{proxy_id}:config', 'status', status.value)
        await self._update_proxy_status_index(proxy_id, status)

    async def _get_current_concurrent_usage(self, proxy_id: str) -> int:
        """获取当前并发使用数"""
        usage = await self.redis.get(f'proxy:{proxy_id}:concurrent')
        return int(usage) if usage else 0

    async def _is_proxy_over_limit(self, proxy_id: str) -> bool:
        """检查代理是否超过使用限制"""
        config = await self._get_proxy_config(proxy_id)
        metrics = await self._get_proxy_metrics(proxy_id)

        if not config or not metrics:
            return True

        return metrics.daily_usage >= config.daily_limit

    async def _record_proxy_usage(self, proxy_id: str):
        """记录代理使用"""
        await self.redis.hincrby(f'proxy:{proxy_id}:metrics', 'daily_usage', 1)
        await self.redis.hset(f'proxy:{proxy_id}:metrics', 'last_used', datetime.utcnow().isoformat())

        # 增加并发计数
        await self.redis.incr(f'proxy:{proxy_id}:concurrent')
        await self.redis.expire(f'proxy:{proxy_id}:concurrent', 300)  # 5分钟过期

    async def _update_response_time(self, proxy_id: str, response_time: float):
        """更新响应时间"""
        # 获取当前平均响应时间
        current_avg = await self.redis.hget(f'proxy:{proxy_id}:metrics', 'average_response_time')
        current_avg = float(current_avg) if current_avg else 0.0

        # 计算新的平均响应时间（简单移动平均）
        new_avg = (current_avg * 0.8) + (response_time * 0.2)

        await self.redis.hset(f'proxy:{proxy_id}:metrics', 'average_response_time', str(new_avg))

    async def _suspend_proxy(self, proxy_id: str, reason: str):
        """暂停代理"""
        await self._update_proxy_status(proxy_id, ProxyStatus.ERROR)

        # 记录暂停原因
        await self.redis.hset(f'proxy:{proxy_id}:suspension',
                            'reason', reason,
                            'suspended_at', datetime.utcnow().isoformat())

        self.logger.warning(f"Proxy {proxy_id} suspended: {reason}")

    async def _recover_proxy(self, proxy_id: str):
        """恢复代理"""
        await self._update_proxy_status(proxy_id, ProxyStatus.ACTIVE)

        # 清理暂停记录
        await self.redis.delete(f'proxy:{proxy_id}:suspension')

        self.logger.info(f"Proxy {proxy_id} recovered")

    async def _cleanup_proxy_data(self, proxy_id: str):
        """清理代理数据"""
        # 删除所有相关的Redis键
        keys_to_delete = [
            f'proxy:{proxy_id}:config',
            f'proxy:{proxy_id}:metrics',
            f'proxy:{proxy_id}:suspension',
            f'proxy:{proxy_id}:concurrent'
        ]

        for key in keys_to_delete:
            await self.redis.delete(key)

        # 从所有集合中移除
        await self.redis.srem('proxies:all', proxy_id)
        for status in ProxyStatus:
            await self.redis.srem(f'proxies:{status.value}', proxy_id)

### 4. 数据存储模块

```python
# core/storage.py
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, ValidationError
from typing import Dict, List, Optional
import logging
from datetime import datetime

class TweetModel(BaseModel):
    """推文数据模型"""
    id: str
    text: str
    user_id: str
    username: str
    created_at: str
    retweet_count: int = 0
    like_count: int = 0
    reply_count: int = 0
    quote_count: int = 0
    view_count: int = 0
    media: List[Dict] = []
    hashtags: List[str] = []
    urls: List[str] = []
    collected_at: str
    source_account: Optional[str] = None
    source_proxy: Optional[str] = None

class ProductionDataManager:
    """生产级数据管理器"""

    def __init__(self, mongodb_uri: str, redis_client):
        self.client = AsyncIOMotorClient(mongodb_uri)
        self.db = self.client.xget
        self.redis = redis_client
        self.logger = logging.getLogger(__name__)

    async def save_tweets(self, tweets: List[Dict]) -> Dict[str, int]:
        """批量保存推文 - 带验证和统计"""
        stats = {'saved': 0, 'failed': 0, 'duplicates': 0}

        for tweet_data in tweets:
            try:
                # 数据验证
                tweet = TweetModel(**tweet_data)

                # 检查是否已存在
                existing = await self.db.tweets.find_one({'id': tweet.id})
                if existing:
                    # 更新互动数据
                    await self.db.tweets.update_one(
                        {'id': tweet.id},
                        {'$set': {
                            'retweet_count': tweet.retweet_count,
                            'like_count': tweet.like_count,
                            'reply_count': tweet.reply_count,
                            'quote_count': tweet.quote_count,
                            'view_count': tweet.view_count,
                            'updated_at': datetime.utcnow()
                        }}
                    )
                    stats['duplicates'] += 1
                else:
                    # 插入新推文
                    await self.db.tweets.insert_one(tweet.dict())
                    stats['saved'] += 1

            except ValidationError as e:
                self.logger.error(f"Tweet validation failed: {e}")
                stats['failed'] += 1
            except Exception as e:
                self.logger.error(f"Failed to save tweet: {e}")
                stats['failed'] += 1

        # 更新统计信息
        await self._update_collection_stats('tweets', stats)
        return stats

    async def _update_collection_stats(self, collection: str, stats: Dict):
        """更新集合统计信息"""
        date_key = datetime.utcnow().strftime('%Y-%m-%d')
        for key, value in stats.items():
            await self.redis.hincrby(f'stats:{collection}:{date_key}', key, value)
        await self.redis.expire(f'stats:{collection}:{date_key}', 86400 * 30)
```

### 5. 任务调度模块

```python
# core/tasks.py
from celery import Celery
from celery.exceptions import Retry
import asyncio
import logging
from datetime import datetime
from .scraper import ProductionTwitterScraper
from .storage import ProductionDataManager
from .account_manager import AccountManager
from .proxy_manager import ProxyManager

app = Celery('xget')
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_routes={
        'core.tasks.search_task': {'queue': 'search'},
        'core.tasks.user_profile_task': {'queue': 'profile'},
        'core.tasks.health_check_task': {'queue': 'maintenance'},
    }
)

@app.task(bind=True, max_retries=3, default_retry_delay=60)
def search_task(self, keyword: str, count: int = 100, priority: str = 'normal'):
    """搜索任务 - 带重试和错误处理"""
    try:
        # 初始化组件
        account_manager = AccountManager(redis_client)
        proxy_manager = ProxyManager(redis_client)
        scraper = ProductionTwitterScraper(account_manager, proxy_manager)
        data_manager = ProductionDataManager(MONGODB_URI, redis_client)

        # 执行搜索
        tweets = asyncio.run(scraper.search_tweets(keyword, count))

        # 保存数据
        stats = asyncio.run(data_manager.save_tweets(tweets))

        # 记录任务完成
        task_result = {
            "status": "success",
            "keyword": keyword,
            "requested_count": count,
            "collected_count": len(tweets),
            "save_stats": stats,
            "completed_at": datetime.utcnow().isoformat()
        }

        logging.info(f"Search task completed: {keyword}, collected {len(tweets)} tweets")
        return task_result

    except Exception as e:
        logging.error(f"Search task failed: {keyword}, error: {str(e)}")

        # 重试逻辑
        if self.request.retries < self.max_retries:
            logging.info(f"Retrying search task for {keyword} (attempt {self.request.retries + 1})")
            raise self.retry(countdown=60 * (2 ** self.request.retries))

        return {
            "status": "failed",
            "keyword": keyword,
            "error": str(e),
            "retries": self.request.retries,
            "failed_at": datetime.utcnow().isoformat()
        }

@app.task(bind=True, max_retries=2)
def user_profile_task(self, username: str):
    """用户资料采集任务"""
    try:
        account_manager = AccountManager(redis_client)
        proxy_manager = ProxyManager(redis_client)
        scraper = ProductionTwitterScraper(account_manager, proxy_manager)
        data_manager = ProductionDataManager(MONGODB_URI, redis_client)

        # 获取用户资料
        user_data = asyncio.run(scraper.get_user_profile(username))
        if not user_data:
            return {"status": "not_found", "username": username}

        # 保存用户数据
        await data_manager.save_user(user_data)

        return {
            "status": "success",
            "username": username,
            "user_id": user_data['user_id'],
            "completed_at": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logging.error(f"User profile task failed: {username}, error: {str(e)}")

        if self.request.retries < self.max_retries:
            raise self.retry(countdown=30)

        return {
            "status": "failed",
            "username": username,
            "error": str(e),
            "failed_at": datetime.utcnow().isoformat()
        }

@app.task
def health_check_task():
    """系统健康检查任务"""
    try:
        account_manager = AccountManager(redis_client)
        proxy_manager = ProxyManager(redis_client)

        # 检查账号健康状态
        asyncio.run(account_manager.check_all_accounts_health())

        # 检查代理健康状态
        asyncio.run(proxy_manager.batch_health_check())

        return {
            "status": "completed",
            "checked_at": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logging.error(f"Health check failed: {str(e)}")
        return {"status": "failed", "error": str(e)}

# 定时任务配置
app.conf.beat_schedule = {
    'health-check': {
        'task': 'core.tasks.health_check_task',
        'schedule': 300.0,  # 每5分钟执行一次
    },
}
```

## 部署配置

### 生产级 Docker Compose 配置

```yaml
# docker-compose.yml
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes --maxmemory 2gb --maxmemory-policy allkeys-lru
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3

  mongodb:
    image: mongo:6
    ports:
      - "27017:27017"
    environment:
      - MONGO_INITDB_ROOT_USERNAME=${MONGO_USER}
      - MONGO_INITDB_ROOT_PASSWORD=${MONGO_PASSWORD}
      - MONGO_INITDB_DATABASE=xget
    volumes:
      - mongodb_data:/data/db
      - ./mongo-init.js:/docker-entrypoint-initdb.d/mongo-init.js:ro
    restart: unless-stopped
    healthcheck:
      test: echo 'db.runCommand("ping").ok' | mongosh localhost:27017/test --quiet
      interval: 30s
      timeout: 10s
      retries: 3

  xget-api:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - REDIS_URL=redis://redis:6379
      - MONGODB_URI=mongodb://${MONGO_USER}:${MONGO_PASSWORD}@mongodb:27017/xget
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
      - ENVIRONMENT=${ENVIRONMENT:-production}
    depends_on:
      redis:
        condition: service_healthy
      mongodb:
        condition: service_healthy
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  celery-worker-search:
    build: .
    command: celery -A core.tasks worker --loglevel=info --queues=search --concurrency=4
    environment:
      - REDIS_URL=redis://redis:6379
      - MONGODB_URI=mongodb://${MONGO_USER}:${MONGO_PASSWORD}@mongodb:27017/xget
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
    depends_on:
      redis:
        condition: service_healthy
      mongodb:
        condition: service_healthy
    restart: unless-stopped
    deploy:
      replicas: 2

  celery-worker-profile:
    build: .
    command: celery -A core.tasks worker --loglevel=info --queues=profile --concurrency=2
    environment:
      - REDIS_URL=redis://redis:6379
      - MONGODB_URI=mongodb://${MONGO_USER}:${MONGO_PASSWORD}@mongodb:27017/xget
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
    depends_on:
      redis:
        condition: service_healthy
      mongodb:
        condition: service_healthy
    restart: unless-stopped

  celery-beat:
    build: .
    command: celery -A core.tasks beat --loglevel=info
    environment:
      - REDIS_URL=redis://redis:6379
      - MONGODB_URI=mongodb://${MONGO_USER}:${MONGO_PASSWORD}@mongodb:27017/xget
    depends_on:
      redis:
        condition: service_healthy
      mongodb:
        condition: service_healthy
    restart: unless-stopped

  # 可选：监控组件
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD:-admin}
    volumes:
      - grafana_data:/var/lib/grafana
    restart: unless-stopped

volumes:
  redis_data:
  mongodb_data:
  prometheus_data:
  grafana_data:

networks:
  default:
    driver: bridge
```

### 环境配置文件

```bash
# .env.production
MONGO_USER=xget_user
MONGO_PASSWORD=your_secure_password
LOG_LEVEL=INFO
ENVIRONMENT=production
GRAFANA_PASSWORD=your_grafana_password

# 代理配置
PROXY_API_KEY=your_proxy_api_key
PROXY_ENDPOINT=https://your-proxy-provider.com/api

# Twitter账号加密密钥
ACCOUNT_ENCRYPTION_KEY=your_32_char_encryption_key

# 监控配置
PROMETHEUS_ENABLED=true
GRAFANA_ENABLED=true
```

### Dockerfile

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 安装Python依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 安装Playwright浏览器
RUN playwright install chromium

# 复制应用代码
COPY . .

# 创建非root用户
RUN useradd --create-home --shell /bin/bash xget
RUN chown -R xget:xget /app
USER xget

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 实施计划

### 🎉 技术验证阶段 (已完成)

- [x] **Python 3.12 环境搭建** - 完成
- [x] **twscrape 功能验证** - 100% 通过
- [x] **Playwright 功能验证** - 100% 通过
- [x] **Cookies 自动化方案** - 核心突破完成
- [x] **Twitter 数据采集测试** - 获取真实数据成功
- [x] **技术分层架构设计** - 完成
- [x] **开发环境配置** - 完成
- [x] **项目文档和工具** - 完成

### 第一阶段 (2-3周): 核心功能开发

- [x] 项目结构搭建和技术验证
- [ ] 账号管理模块开发 (基于Playwright自动化)
- [ ] 代理管理模块开发
- [ ] 基础爬取模块开发 (twscrape集成，已验证可行)
- [ ] 数据存储模块开发 (MongoDB + 数据验证)
- [ ] 任务调度系统 (Celery + 队列分离)
- [ ] Docker环境配置

### 第二阶段 (1-2周): API和监控

- [ ] FastAPI接口开发
- [ ] 任务管理API (提交、查询、取消)
- [ ] 数据查询API (支持复杂查询)
- [ ] 系统监控API (健康状态、统计信息)
- [ ] 基础Web管理界面
- [ ] Prometheus + Grafana集成

### 第三阶段 (1-2周): 生产优化

- [ ] 错误处理和重试机制完善
- [ ] 性能优化 (批量处理、连接池)
- [ ] 安全加固 (输入验证、访问控制)
- [ ] 日志系统完善 (结构化日志)
- [ ] 压力测试和性能调优
- [ ] 部署文档和运维手册

### 第四阶段 (1周): 测试和发布

- [ ] 集成测试
- [ ] 生产环境部署
- [ ] 监控告警配置
- [ ] 用户培训和文档

## 技术债务管理

### 必须实现的核心功能

1. **账号池管理** - 不可省略，直接影响系统稳定性
2. **代理IP轮换** - 生产环境必需
3. **数据验证** - 确保数据质量
4. **错误处理** - 提高系统鲁棒性
5. **基础监控** - 生产运维必需

### 可以后期添加的功能

1. **复杂的ML预测** - 非核心功能
2. **企业级权限系统** - 可用简单认证替代
3. **数据关系图谱** - 可在MongoDB中简单存储
4. **高级分析功能** - 业务价值验证后添加

## 风险评估与应对

### 技术风险 ⚠️

**风险**: Twitter反爬虫机制升级
**应对**:
- 多样化的爬取策略 (twscrape + Playwright)
- 灵活的账号和代理轮换
- 快速适应机制

**风险**: 账号封禁率过高
**应对**:
- 账号健康监控
- 使用频率控制
- 多账号池备份

### 业务风险 ⚠️

**风险**: 数据量超出预期
**应对**:
- 水平扩展设计
- 数据分片策略
- 性能监控和预警

### 运维风险 ✅

**风险**: 系统维护复杂
**应对**:
- 完善的监控体系
- 自动化部署
- 详细的运维文档

## 成本估算

### 开发成本

- **人力**: 2-3名开发人员，6-8周
- **技术栈**: 全部使用开源技术，无授权费用
- **总体**: 相比原方案减少60%的开发时间

### 运维成本

- **服务器**: 中等配置即可满足初期需求
- **代理IP**: 根据采集量按需购买
- **监控**: 使用开源方案，成本可控

## Web展示页面设计

### 管理后台界面

基于FastAPI + Vue.js构建的现代化Web管理界面，提供完整的系统管理功能。

#### 🎯 **核心页面模块**

```text
┌─────────────────────────────────────────────────────────────────────┐
│                        XGet Web管理界面                            │
├─────────────────┬─────────────────┬─────────────────┬───────────────┤
│   📊 数据查询    │   🔧 系统管理    │   📈 统计分析    │   ⚙️ 系统设置   │
│   推文搜索      │   账号管理      │   采集统计      │   配置管理     │
│   用户查询      │   代理管理      │   性能监控      │   权限管理     │
│   数据导出      │   任务管理      │   错误分析      │   系统日志     │
└─────────────────┴─────────────────┴─────────────────┴───────────────┘
```

#### 📊 **数据查询页面**

**推文搜索界面**
```html
<!-- 推文搜索页面 -->
<template>
  <div class="tweet-search-page">
    <!-- 搜索表单 -->
    <el-card class="search-form">
      <el-form :model="searchForm" label-width="120px">
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="关键词">
              <el-input v-model="searchForm.keyword" placeholder="输入搜索关键词" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="时间范围">
              <el-date-picker
                v-model="searchForm.dateRange"
                type="datetimerange"
                range-separator="至"
                start-placeholder="开始时间"
                end-placeholder="结束时间"
              />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="用户名">
              <el-input v-model="searchForm.username" placeholder="指定用户名" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row>
          <el-col :span="24">
            <el-button type="primary" @click="searchTweets">搜索</el-button>
            <el-button @click="resetForm">重置</el-button>
            <el-button type="success" @click="exportData">导出数据</el-button>
          </el-col>
        </el-row>
      </el-form>
    </el-card>

    <!-- 搜索结果 -->
    <el-card class="search-results">
      <el-table :data="tweets" v-loading="loading">
        <el-table-column prop="text" label="推文内容" width="400" show-overflow-tooltip />
        <el-table-column prop="username" label="用户" width="120" />
        <el-table-column prop="created_at" label="发布时间" width="180" />
        <el-table-column prop="like_count" label="点赞" width="80" />
        <el-table-column prop="retweet_count" label="转发" width="80" />
        <el-table-column label="操作" width="120">
          <template #default="scope">
            <el-button size="small" @click="viewDetail(scope.row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.size"
        :total="pagination.total"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </el-card>
  </div>
</template>
```

#### 🔧 **系统管理页面**

**账号管理界面**
```html
<!-- 账号管理页面 -->
<template>
  <div class="account-management">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>X.com账号管理</span>
          <el-button type="primary" @click="addAccount">添加账号</el-button>
        </div>
      </template>

      <!-- 账号状态统计 -->
      <el-row :gutter="20" class="stats-row">
        <el-col :span="6">
          <el-statistic title="总账号数" :value="accountStats.total" />
        </el-col>
        <el-col :span="6">
          <el-statistic title="健康账号" :value="accountStats.healthy" />
        </el-col>
        <el-col :span="6">
          <el-statistic title="暂停账号" :value="accountStats.suspended" />
        </el-col>
        <el-col :span="6">
          <el-statistic title="错误账号" :value="accountStats.error" />
        </el-col>
      </el-row>

      <!-- 账号列表 -->
      <el-table :data="accounts" v-loading="loading">
        <el-table-column prop="username" label="用户名" width="150" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="scope">
            <el-tag :type="getStatusType(scope.row.status)">
              {{ getStatusText(scope.row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="last_used" label="最后使用" width="180" />
        <el-table-column prop="success_count" label="成功次数" width="100" />
        <el-table-column prop="error_count" label="错误次数" width="100" />
        <el-table-column prop="health_score" label="健康分数" width="100">
          <template #default="scope">
            <el-progress :percentage="scope.row.health_score" :color="getHealthColor(scope.row.health_score)" />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200">
          <template #default="scope">
            <el-button size="small" @click="testAccount(scope.row)">测试</el-button>
            <el-button size="small" @click="refreshCookies(scope.row)">刷新</el-button>
            <el-button size="small" type="danger" @click="deleteAccount(scope.row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>
```

**代理IP管理界面**
```html
<!-- 代理管理页面 -->
<template>
  <div class="proxy-management">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>代理IP池管理</span>
          <el-button type="primary" @click="addProxy">添加代理</el-button>
        </div>
      </template>

      <!-- 代理状态统计 -->
      <el-row :gutter="20" class="stats-row">
        <el-col :span="6">
          <el-statistic title="总代理数" :value="proxyStats.total" />
        </el-col>
        <el-col :span="6">
          <el-statistic title="可用代理" :value="proxyStats.available" />
        </el-col>
        <el-col :span="6">
          <el-statistic title="平均延迟" :value="proxyStats.avgLatency" suffix="ms" />
        </el-col>
        <el-col :span="6">
          <el-statistic title="成功率" :value="proxyStats.successRate" suffix="%" />
        </el-col>
      </el-row>

      <!-- 代理列表 -->
      <el-table :data="proxies" v-loading="loading">
        <el-table-column prop="host" label="主机" width="150" />
        <el-table-column prop="port" label="端口" width="80" />
        <el-table-column prop="type" label="类型" width="100" />
        <el-table-column prop="location" label="位置" width="120" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="scope">
            <el-tag :type="getProxyStatusType(scope.row.status)">
              {{ scope.row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="latency" label="延迟" width="80" />
        <el-table-column prop="success_rate" label="成功率" width="100" />
        <el-table-column label="操作" width="200">
          <template #default="scope">
            <el-button size="small" @click="testProxy(scope.row)">测试</el-button>
            <el-button size="small" type="warning" @click="toggleProxy(scope.row)">
              {{ scope.row.status === 'active' ? '禁用' : '启用' }}
            </el-button>
            <el-button size="small" type="danger" @click="deleteProxy(scope.row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>
```

#### 📈 **统计分析页面**

**数据采集统计**
```html
<!-- 统计分析页面 -->
<template>
  <div class="analytics-dashboard">
    <!-- 关键指标卡片 -->
    <el-row :gutter="20" class="metrics-row">
      <el-col :span="6">
        <el-card class="metric-card">
          <el-statistic title="今日采集" :value="todayStats.collected" />
          <div class="metric-trend">
            <span :class="todayStats.trend > 0 ? 'trend-up' : 'trend-down'">
              {{ todayStats.trend > 0 ? '↗' : '↘' }} {{ Math.abs(todayStats.trend) }}%
            </span>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="metric-card">
          <el-statistic title="成功率" :value="todayStats.successRate" suffix="%" />
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="metric-card">
          <el-statistic title="活跃任务" :value="todayStats.activeTasks" />
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="metric-card">
          <el-statistic title="数据总量" :value="todayStats.totalData" />
        </el-card>
      </el-col>
    </el-row>

    <!-- 图表区域 -->
    <el-row :gutter="20">
      <el-col :span="12">
        <el-card title="采集趋势">
          <div ref="collectionChart" style="height: 300px;"></div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card title="账号使用分布">
          <div ref="accountChart" style="height: 300px;"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20">
      <el-col :span="24">
        <el-card title="实时任务监控">
          <el-table :data="realtimeTasks" v-loading="loading">
            <el-table-column prop="task_id" label="任务ID" width="200" />
            <el-table-column prop="type" label="类型" width="100" />
            <el-table-column prop="keyword" label="关键词" width="150" />
            <el-table-column prop="status" label="状态" width="100">
              <template #default="scope">
                <el-tag :type="getTaskStatusType(scope.row.status)">
                  {{ scope.row.status }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="progress" label="进度" width="150">
              <template #default="scope">
                <el-progress :percentage="scope.row.progress" />
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="创建时间" width="180" />
            <el-table-column label="操作" width="120">
              <template #default="scope">
                <el-button size="small" @click="viewTaskDetail(scope.row)">详情</el-button>
                <el-button size="small" type="danger" @click="cancelTask(scope.row)">取消</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>
```

## 数据库结构设计

### MongoDB集合设计

基于文档型数据库的特点，设计灵活且高效的数据结构。

#### 📊 **核心数据集合**

```javascript
// 推文集合 (tweets) - 完全按照甲方需求字段设计
{
  "_id": ObjectId("..."),

  // 基础信息 (甲方字段0)
  "post_url": "https://x.com/0xairdropfarmer/status/1940603123074228282",
  "post_id": "1940603123074228282",  // 从URL中提取的ID
  "post_type": "text",  // text/image/video/retweet/quote

  // 作者信息 (甲方字段1-3)
  "author_avatar": "https://pbs.twimg.com/profile_images/...",
  "author_name": "示例用户",
  "author_handle": "@example_user",

  // 时间信息 (甲方字段4)
  "post_time": ISODate("2024-01-01T12:00:00Z"),

  // 内容信息 (甲方字段5)
  "post_content": "推文内容...",

  // 媒体资源 (甲方字段6) - 数组形式
  "post_images": [
    {
      "original_url": "https://pbs.twimg.com/media/...",
      "oss_url": "https://oss.example.com/images/2024/01/01/img_001.jpg",
      "type": "image",  // image/video_cover
      "width": 1200,
      "height": 800
    }
  ],

  // 互动数据 (甲方字段7-10, 17)
  "comment_count": 25,
  "retweet_count": 50,
  "like_count": 100,
  "view_count": 5000,
  "bookmark_count": 15,

  // 转发帖特殊字段 (甲方字段11-16, 18-19)
  "is_retweet": false,
  "is_quote": false,
  "original_post_id": null,
  "original_author_avatar": null,
  "original_author_name": null,
  "original_author_handle": null,
  "original_post_time": null,
  "original_post_content": null,
  "original_post_images": [],

  // 链接信息 (甲方字段20)
  "post_links": [
    {
      "url": "https://t.co/abc123",
      "expanded_url": "https://example.com/article",
      "display_url": "example.com/article"
    }
  ],

  // OSS文件地址 (甲方要求)
  "oss_file_path": "data/2024/01/01/task_20240101_001_batch_001.json",

  // 甲方要求的Post关系
  "parent_post_id": null,
  "parent_comment_id": null,

  // 原始数据 (甲方要求保留Twitter原始数据)
  "raw_data": {
    "twitter_api_response": "原始API响应数据...",
    "collection_method": "twscrape",
    "raw_json": "完整的原始JSON数据"
  },

  // 系统元数据
  "metadata": {
    "collected_at": ISODate("2024-01-01T12:05:00Z"),
    "search_keyword": "人工智能",  // 采集关键词
    "task_id": "task_20240101_001",
    "source_account": "account_001",
    "source_proxy": "proxy_001",
    "batch_id": "batch_001",
    "collection_method": "search"  // search/timeline/profile
  }
}

// 用户集合 (users)
{
  "_id": ObjectId("..."),
  "user_id": "987654321",
  "username": "example_user",
  "display_name": "示例用户",
  "description": "用户简介...",
  "profile": {
    "verified": false,
    "protected": false,
    "location": "北京",
    "website": "https://example.com",
    "profile_image_url": "https://pbs.twimg.com/profile_images/...",
    "profile_banner_url": "https://pbs.twimg.com/profile_banners/..."
  },
  "metrics": {
    "followers_count": 1000,
    "following_count": 500,
    "tweet_count": 2000,
    "listed_count": 10
  },
  "metadata": {
    "created_at": ISODate("2020-01-01T00:00:00Z"),
    "collected_at": ISODate("2024-01-01T12:00:00Z"),
    "last_updated": ISODate("2024-01-01T12:00:00Z")
  },
  "analysis": {
    "activity_score": 0.7,
    "influence_score": 0.5,
    "topics": ["technology", "ai"],
    "sentiment_trend": "positive"
  }
}

// 采集任务集合 (collection_tasks) - 按甲方需求设计
{
  "_id": ObjectId("..."),
  "task_id": "task_20240101_001",  // 甲方要求的任务ID

  // 任务类型 (甲方两种搜索模式)
  "task_type": "scheduled",  // scheduled(定时搜索) / ondemand(按需搜索)

  // 甲方主要参数
  "parameters": {
    "keyword": "人工智能",  // 关键词 (支持中文、英文、小语种)
    "priority": 1,         // 优先级 (1-10, 1最高)

    // 定时搜索参数
    "frequency": "daily",      // 搜索频率 (仅定时任务)
    "frequency_count": 3,      // 每日搜索次数 (仅定时任务)

    // 按需搜索参数
    "required_count": 1000,    // 需要的条数 (0=尽力采集, 仅按需任务)
    "start_time": ISODate("2024-01-01T00:00:00Z"),  // 开始时间 (仅按需任务)
    "end_time": ISODate("2024-01-01T23:59:59Z"),    // 结束时间 (仅按需任务)
  },

  // 任务状态
  "status": "completed",  // pending, running, completed, failed, cancelled

  // 执行进度
  "progress": {
    "target_count": 1000,      // 目标数量
    "collected_count": 856,    // 已采集数量
    "failed_count": 12,        // 失败数量
    "percentage": 85.6,        // 完成百分比
    "current_batch": 9,        // 当前批次
    "total_batches": 10        // 总批次数
  },

  // 资源分配
  "resources": {
    "assigned_accounts": ["account_001", "account_002"],
    "used_proxies": ["proxy_001", "proxy_002"],
    "worker_id": "worker_001"
  },

  // 时间信息
  "timing": {
    "created_at": ISODate("2024-01-01T10:00:00Z"),
    "started_at": ISODate("2024-01-01T10:01:00Z"),
    "completed_at": ISODate("2024-01-01T12:00:00Z"),
    "duration_seconds": 7140,
    "next_execution": ISODate("2024-01-02T10:00:00Z")  // 仅定时任务
  },

  // 执行结果
  "results": {
    "posts_collected": 856,
    "unique_posts": 834,       // 去重后数量
    "duplicate_posts": 22,     // 重复数量
    "images_downloaded": 245,  // 下载的图片数
    "oss_files_created": 9,    // 创建的OSS文件数
    "data_reported": true,     // 是否已上报给甲方
    "errors": [
      {
        "type": "rate_limit",
        "count": 5,
        "last_occurrence": ISODate("2024-01-01T11:30:00Z")
      }
    ]
  },

  // 甲方上报信息
  "reporting": {
    "batches_reported": [
      {
        "batch_id": "batch_001",
        "oss_file_path": "data/2024/01/01/task_20240101_001_batch_001.json",
        "post_count": 100,
        "reported_at": ISODate("2024-01-01T11:00:00Z"),
        "report_status": "success"
      }
    ],
    "total_reported": 856,
    "last_report_at": ISODate("2024-01-01T12:00:00Z")
  }
}

// 账号管理集合 (accounts)
{
  "_id": ObjectId("..."),
  "account_id": "account_001",
  "username": "scraper_account_1",
  "email": "account1@example.com",
  "status": "active",  // active, suspended, error, maintenance
  "health": {
    "score": 0.85,
    "last_check": ISODate("2024-01-01T12:00:00Z"),
    "consecutive_errors": 0,
    "total_requests": 10000,
    "successful_requests": 9500,
    "success_rate": 0.95
  },
  "usage": {
    "daily_limit": 1000,
    "daily_used": 234,
    "last_used": ISODate("2024-01-01T11:45:00Z"),
    "cooldown_until": null
  },
  "authentication": {
    "cookies_updated": ISODate("2024-01-01T08:00:00Z"),
    "cookies_expires": ISODate("2024-01-08T08:00:00Z"),
    "login_method": "playwright_auto"
  },
  "metadata": {
    "created_at": ISODate("2024-01-01T00:00:00Z"),
    "last_maintenance": ISODate("2024-01-01T08:00:00Z"),
    "notes": "主要用于技术类推文采集"
  }
}

// 代理管理集合 (proxies)
{
  "_id": ObjectId("..."),
  "proxy_id": "proxy_001",
  "config": {
    "host": "proxy.example.com",
    "port": 8080,
    "protocol": "http",  // http, https, socks5
    "username": "proxy_user",
    "password": "proxy_pass",
    "location": "US-East"
  },
  "status": "active",  // active, inactive, error
  "performance": {
    "latency_ms": 150,
    "success_rate": 0.92,
    "total_requests": 5000,
    "failed_requests": 400,
    "last_test": ISODate("2024-01-01T12:00:00Z")
  },
  "usage": {
    "concurrent_limit": 10,
    "current_usage": 3,
    "daily_limit": 10000,
    "daily_used": 2340
  },
  "metadata": {
    "provider": "ProxyProvider Inc",
    "cost_per_gb": 0.1,
    "created_at": ISODate("2024-01-01T00:00:00Z"),
    "expires_at": ISODate("2024-02-01T00:00:00Z")
  }
}
```

#### 🔍 **索引设计**

```javascript
// 推文集合索引
db.tweets.createIndex({ "tweet_id": 1 }, { unique: true })
db.tweets.createIndex({ "metadata.created_at": -1 })
db.tweets.createIndex({ "metadata.search_keyword": 1 })
db.tweets.createIndex({ "user.username": 1 })
db.tweets.createIndex({ "content.hashtags": 1 })
db.tweets.createIndex({ "metadata.collected_at": -1 })

// 复合索引用于复杂查询
db.tweets.createIndex({
  "metadata.search_keyword": 1,
  "metadata.created_at": -1
})
db.tweets.createIndex({
  "user.username": 1,
  "metadata.created_at": -1
})

// 用户集合索引
db.users.createIndex({ "user_id": 1 }, { unique: true })
db.users.createIndex({ "username": 1 }, { unique: true })
db.users.createIndex({ "metrics.followers_count": -1 })
db.users.createIndex({ "metadata.collected_at": -1 })

// 任务集合索引
db.collection_tasks.createIndex({ "task_id": 1 }, { unique: true })
db.collection_tasks.createIndex({ "status": 1 })
db.collection_tasks.createIndex({ "timing.created_at": -1 })
db.collection_tasks.createIndex({ "type": 1, "status": 1 })

// 账号集合索引
db.accounts.createIndex({ "account_id": 1 }, { unique: true })
db.accounts.createIndex({ "username": 1 }, { unique: true })
db.accounts.createIndex({ "status": 1 })
db.accounts.createIndex({ "health.score": -1 })

// 代理集合索引
db.proxies.createIndex({ "proxy_id": 1 }, { unique: true })
db.proxies.createIndex({ "status": 1 })
db.proxies.createIndex({ "performance.success_rate": -1 })
```

## 业务API接口设计

### 甲乙双方接口规范

基于甲方需求文档，设计标准化的API接口体系，实现任务下发、数据上报和统计查询。

#### 🔄 **接口交互流程**

```text
甲方 ──────────────────────────────────────────────────── 乙方(XGet系统)
  │                                                      │
  ├─ 1. 搜索任务下发接口1 (定时搜索) ──────────────────────→ │
  ├─ 2. 搜索任务下发接口2 (按需搜索) ──────────────────────→ │
  │                                                      │
  │                                                      ├─ 3. 执行搜索采集
  │                                                      ├─ 4. 数据解析处理
  │                                                      ├─ 5. 资源下载到OSS
  │                                                      │
  ├─ 6. 搜索结果上报接口 ←──────────────────────────────── │
  ├─ 7. 数据统计查询接口 ←──────────────────────────────── │
```

#### 📤 **乙方提供的接口 (甲方调用)**

##### **1. 定时搜索任务下发接口**
```python
# POST /api/v1/tasks/scheduled
{
    "keyword": "人工智能",           # 关键词 (支持中文、英文、小语种)
    "priority": 1,                  # 优先级 (1-10, 1最高)
    "frequency": "daily",           # 搜索频率 (daily/hourly/weekly)
    "frequency_count": 3,           # 每日搜索次数
    "task_id": "task_20240101_001"  # 任务ID
}

# 响应
{
    "status": "success",
    "task_id": "task_20240101_001",
    "message": "定时搜索任务创建成功",
    "next_execution": "2024-01-01T08:00:00Z"
}
```

##### **2. 按需搜索任务下发接口**
```python
# POST /api/v1/tasks/ondemand
{
    "keyword": "ChatGPT",           # 关键词
    "priority": 2,                  # 优先级
    "required_count": 1000,         # 需要的条数 (0=尽力采集)
    "start_time": "2024-01-01T00:00:00Z",  # 开始时间
    "end_time": "2024-01-01T23:59:59Z",    # 结束时间
    "task_id": "task_20240101_002"  # 任务ID
}

# 响应
{
    "status": "success",
    "task_id": "task_20240101_002",
    "message": "按需搜索任务创建成功",
    "estimated_completion": "2024-01-01T12:00:00Z"
}
```

##### **3. 任务状态查询接口**
```python
# GET /api/v1/tasks/{task_id}/status
{
    "task_id": "task_20240101_001",
    "status": "running",            # pending/running/completed/failed
    "progress": {
        "collected": 856,           # 已采集数量
        "target": 1000,            # 目标数量
        "percentage": 85.6         # 完成百分比
    },
    "created_at": "2024-01-01T08:00:00Z",
    "updated_at": "2024-01-01T10:30:00Z"
}
```

#### 📥 **甲方提供的接口 (乙方调用)**

##### **4. 搜索结果上报接口**
```python
# POST {甲方提供的上报URL}
{
    "post_id": "1940603123074228282",    # 帖子ID
    "keyword": "人工智能",                # 关键词
    "task_id": "task_20240101_001",      # 任务ID
    "oss_file_path": "data/2024/01/01/task_20240101_001_batch_001.json",
    "batch_size": 100,                   # 本批次数据量
    "total_collected": 856,              # 累计采集量
    "completion_status": "partial"       # partial/completed
}

# 甲方响应
{
    "status": "received",
    "message": "数据接收成功",
    "next_batch_allowed": true
}
```

### 数据格式规范

#### 📊 **标准数据字段定义**

根据甲方需求，定义完整的数据字段结构：

```python
# 标准帖子数据结构
{
    # 基础信息 (字段0)
    "post_url": "https://x.com/0xairdropfarmer/status/1940603123074228282",
    "post_id": "1940603123074228282",
    "post_type": "text",  # text/image/video/retweet/quote

    # 作者信息 (字段1-3)
    "author_avatar": "https://pbs.twimg.com/profile_images/...",
    "author_name": "示例用户",
    "author_handle": "@example_user",

    # 时间信息 (字段4)
    "post_time": "2024-01-01T12:00:00Z",

    # 内容信息 (字段5)
    "post_content": "这是一条示例推文内容...",

    # 媒体资源 (字段6)
    "post_images": [
        {
            "original_url": "https://pbs.twimg.com/media/...",
            "oss_url": "https://oss.example.com/images/2024/01/01/img_001.jpg",
            "type": "image",
            "width": 1200,
            "height": 800
        }
    ],

    # 互动数据 (字段7-10)
    "comment_count": 25,
    "retweet_count": 50,
    "like_count": 100,
    "view_count": 5000,
    "bookmark_count": 15,  # 字段17

    # 转发帖特殊字段 (字段11-16)
    "is_retweet": false,        # 字段18
    "is_quote": false,          # 字段19
    "original_post_id": null,
    "original_author_avatar": null,
    "original_author_name": null,
    "original_author_handle": null,
    "original_post_time": null,
    "original_post_content": null,
    "original_post_images": [],

    # 链接信息 (字段20)
    "post_links": [
        {
            "url": "https://t.co/abc123",
            "expanded_url": "https://example.com/article",
            "display_url": "example.com/article"
        }
    ],

    # 系统字段
    "oss_file_path": "data/2024/01/01/post_1940603123074228282.json",
    "collected_at": "2024-01-01T12:05:00Z",
    "keyword": "人工智能",
    "task_id": "task_20240101_001",

    # 原始数据 (甲方要求)
    "raw_data": {
        "twitter_api_response": "原始API响应数据..."
    },

    # 关系字段 (甲方要求的Post关系)
    "parent_post_id": null,
    "parent_comment_id": null
}
```

### OSS资源管理

#### 📁 **文件存储规范**

根据甲方要求，实现图片和数据文件的OSS存储管理：

```python
# OSS存储结构
oss_bucket/
├── images/                    # 图片资源
│   ├── 2024/01/01/           # 按日期分目录
│   │   ├── img_001.jpg
│   │   ├── img_002.png
│   │   └── video_001_cover.jpg
│   └── ...
├── videos/                    # 视频封面
│   ├── 2024/01/01/
│   └── ...
├── data/                      # JSON数据文件
│   ├── 2024/01/01/
│   │   ├── task_20240101_001_batch_001.json
│   │   ├── task_20240101_001_batch_002.json
│   │   └── ...
│   └── ...
└── raw_data/                  # 原始数据备份
    ├── 2024/01/01/
    └── ...
```

#### 🔧 **OSS上传服务**

```python
# services/oss_service.py
import asyncio
import aiofiles
from datetime import datetime
from typing import List, Dict, Optional
import hashlib
import os

class OSSService:
    """OSS资源管理服务"""

    def __init__(self, oss_config: Dict):
        self.bucket_name = oss_config["bucket_name"]
        self.endpoint = oss_config["endpoint"]
        self.access_key = oss_config["access_key"]
        self.secret_key = oss_config["secret_key"]
        self.base_url = f"https://{self.bucket_name}.{self.endpoint}"

    async def upload_image(self, image_url: str, task_id: str) -> Dict[str, str]:
        """上传图片到OSS"""
        try:
            # 下载图片
            image_data = await self._download_media(image_url)

            # 生成OSS路径
            date_path = datetime.now().strftime("%Y/%m/%d")
            file_hash = hashlib.md5(image_data).hexdigest()[:8]
            file_ext = self._get_file_extension(image_url)
            oss_path = f"images/{date_path}/{task_id}_{file_hash}{file_ext}"

            # 上传到OSS
            oss_url = await self._upload_to_oss(oss_path, image_data, "image")

            return {
                "original_url": image_url,
                "oss_url": oss_url,
                "oss_path": oss_path,
                "file_size": len(image_data)
            }

        except Exception as e:
            self.logger.error(f"图片上传失败: {image_url}, 错误: {str(e)}")
            return {
                "original_url": image_url,
                "oss_url": None,
                "error": str(e)
            }

    async def upload_data_file(self, data: Dict, task_id: str, batch_id: str) -> str:
        """上传JSON数据文件到OSS"""
        try:
            # 生成文件路径
            date_path = datetime.now().strftime("%Y/%m/%d")
            filename = f"{task_id}_batch_{batch_id}.json"
            oss_path = f"data/{date_path}/{filename}"

            # 转换为JSON字符串
            import json
            json_data = json.dumps(data, ensure_ascii=False, indent=2).encode('utf-8')

            # 上传到OSS
            oss_url = await self._upload_to_oss(oss_path, json_data, "application/json")

            return oss_url

        except Exception as e:
            self.logger.error(f"数据文件上传失败: {task_id}, 错误: {str(e)}")
            raise

    async def batch_upload_images(self, image_urls: List[str], task_id: str) -> List[Dict]:
        """批量上传图片"""
        tasks = [self.upload_image(url, task_id) for url in image_urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        return [
            result if not isinstance(result, Exception) else {"error": str(result)}
            for result in results
        ]
```

### 数据统计服务

#### 📊 **月度去重统计**

根据甲方要求，实现按关键词的月度去重数据统计：

```python
# services/statistics_service.py
from datetime import datetime, timedelta
from typing import Dict, List
import calendar

class StatisticsService:
    """数据统计服务"""

    def __init__(self, db_client):
        self.db = db_client.xget
        self.logger = logging.getLogger(__name__)

    async def get_monthly_stats_by_keyword(
        self,
        keyword: str,
        year: int,
        month: int
    ) -> Dict[str, int]:
        """按关键词获取月度去重统计"""
        try:
            # 计算月份时间范围
            start_date = datetime(year, month, 1)
            if month == 12:
                end_date = datetime(year + 1, 1, 1)
            else:
                end_date = datetime(year, month + 1, 1)

            # 聚合查询 - 按帖子ID去重
            pipeline = [
                {
                    "$match": {
                        "metadata.search_keyword": keyword,
                        "metadata.collected_at": {
                            "$gte": start_date,
                            "$lt": end_date
                        }
                    }
                },
                {
                    "$group": {
                        "_id": "$tweet_id",  # 按帖子ID去重
                        "first_collected": {"$min": "$metadata.collected_at"},
                        "keyword": {"$first": "$metadata.search_keyword"}
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "unique_posts": {"$sum": 1},
                        "keywords": {"$addToSet": "$keyword"}
                    }
                }
            ]

            result = await self.db.tweets.aggregate(pipeline).to_list(length=1)

            if result:
                return {
                    "keyword": keyword,
                    "year": year,
                    "month": month,
                    "unique_posts_count": result[0]["unique_posts"],
                    "period": f"{year}-{month:02d}",
                    "calculated_at": datetime.utcnow().isoformat()
                }
            else:
                return {
                    "keyword": keyword,
                    "year": year,
                    "month": month,
                    "unique_posts_count": 0,
                    "period": f"{year}-{month:02d}",
                    "calculated_at": datetime.utcnow().isoformat()
                }

        except Exception as e:
            self.logger.error(f"月度统计计算失败: {keyword}, {year}-{month}, 错误: {str(e)}")
            raise

    async def get_all_keywords_monthly_stats(
        self,
        year: int,
        month: int
    ) -> List[Dict]:
        """获取所有关键词的月度统计"""
        try:
            # 获取该月份所有关键词
            start_date = datetime(year, month, 1)
            if month == 12:
                end_date = datetime(year + 1, 1, 1)
            else:
                end_date = datetime(year, month + 1, 1)

            keywords = await self.db.tweets.distinct(
                "metadata.search_keyword",
                {
                    "metadata.collected_at": {
                        "$gte": start_date,
                        "$lt": end_date
                    }
                }
            )

            # 为每个关键词计算统计
            stats = []
            for keyword in keywords:
                keyword_stats = await self.get_monthly_stats_by_keyword(keyword, year, month)
                stats.append(keyword_stats)

            return stats

        except Exception as e:
            self.logger.error(f"全量月度统计失败: {year}-{month}, 错误: {str(e)}")
            raise

    async def get_task_completion_stats(self, task_id: str) -> Dict:
        """获取任务完成统计"""
        try:
            task = await self.db.collection_tasks.find_one({"task_id": task_id})
            if not task:
                return {"error": "任务不存在"}

            # 统计该任务采集的数据
            collected_count = await self.db.tweets.count_documents({
                "metadata.task_id": task_id
            })

            # 去重统计
            unique_posts = await self.db.tweets.distinct(
                "tweet_id",
                {"metadata.task_id": task_id}
            )

            return {
                "task_id": task_id,
                "total_collected": collected_count,
                "unique_posts": len(unique_posts),
                "duplicate_rate": (collected_count - len(unique_posts)) / collected_count if collected_count > 0 else 0,
                "task_status": task["status"],
                "keyword": task["parameters"].get("keyword"),
                "created_at": task["timing"]["created_at"].isoformat(),
                "completed_at": task["timing"].get("completed_at", {}).isoformat() if task["timing"].get("completed_at") else None
            }

        except Exception as e:
            self.logger.error(f"任务统计失败: {task_id}, 错误: {str(e)}")
            raise
```

#### 📈 **统计API接口**

```python
# api/routes/statistics.py
from fastapi import APIRouter, Query, Depends
from typing import List, Optional
from datetime import datetime
from ..services import StatisticsService

router = APIRouter(prefix="/api/v1/statistics", tags=["数据统计"])

@router.get("/monthly/{keyword}")
async def get_keyword_monthly_stats(
    keyword: str,
    year: int = Query(..., description="年份"),
    month: int = Query(..., ge=1, le=12, description="月份"),
    token: str = Depends(verify_token)
):
    """获取关键词月度去重统计"""
    try:
        stats_service = StatisticsService(db_client)
        stats = await stats_service.get_monthly_stats_by_keyword(keyword, year, month)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"统计查询失败: {str(e)}")

@router.get("/monthly/all")
async def get_all_monthly_stats(
    year: int = Query(..., description="年份"),
    month: int = Query(..., ge=1, le=12, description="月份"),
    token: str = Depends(verify_token)
):
    """获取所有关键词月度统计"""
    try:
        stats_service = StatisticsService(db_client)
        stats = await stats_service.get_all_keywords_monthly_stats(year, month)
        return {
            "period": f"{year}-{month:02d}",
            "total_keywords": len(stats),
            "statistics": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"统计查询失败: {str(e)}")

@router.get("/tasks/{task_id}")
async def get_task_stats(
    task_id: str,
    token: str = Depends(verify_token)
):
    """获取任务完成统计"""
    try:
        stats_service = StatisticsService(db_client)
        stats = await stats_service.get_task_completion_stats(task_id)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"任务统计失败: {str(e)}")
```

## API服务设计

### RESTful API接口

基于FastAPI构建的高性能API服务，提供完整的数据访问和管理功能。

#### 🚀 **API架构设计**

```python
# api/main.py - FastAPI主应用
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import asyncio
from datetime import datetime, timedelta

app = FastAPI(
    title="XGet API",
    description="X(Twitter)数据采集系统API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 安全认证
security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """验证API访问令牌"""
    # 这里实现具体的token验证逻辑
    if not credentials.token or credentials.token != "your-api-token":
        raise HTTPException(status_code=401, detail="Invalid authentication token")
    return credentials.token
```

#### 📊 **数据查询API**

```python
# api/routes/data.py - 数据查询接口
from fastapi import APIRouter, Query, Depends
from typing import List, Optional
from datetime import datetime
from ..models import TweetResponse, UserResponse, SearchRequest
from ..services import DataService

router = APIRouter(prefix="/api/v1/data", tags=["数据查询"])

@router.get("/tweets/search", response_model=List[TweetResponse])
async def search_tweets(
    keyword: str = Query(..., description="搜索关键词"),
    limit: int = Query(100, ge=1, le=1000, description="返回数量限制"),
    start_date: Optional[datetime] = Query(None, description="开始时间"),
    end_date: Optional[datetime] = Query(None, description="结束时间"),
    username: Optional[str] = Query(None, description="指定用户名"),
    min_likes: Optional[int] = Query(None, description="最小点赞数"),
    has_media: Optional[bool] = Query(None, description="是否包含媒体"),
    token: str = Depends(verify_token)
):
    """
    搜索推文数据

    支持多种过滤条件：
    - 关键词搜索
    - 时间范围过滤
    - 用户过滤
    - 互动数过滤
    - 媒体类型过滤
    """
    try:
        data_service = DataService()
        tweets = await data_service.search_tweets(
            keyword=keyword,
            limit=limit,
            start_date=start_date,
            end_date=end_date,
            username=username,
            min_likes=min_likes,
            has_media=has_media
        )
        return tweets
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")

@router.get("/tweets/{tweet_id}", response_model=TweetResponse)
async def get_tweet_by_id(
    tweet_id: str,
    token: str = Depends(verify_token)
):
    """根据推文ID获取详细信息"""
    try:
        data_service = DataService()
        tweet = await data_service.get_tweet_by_id(tweet_id)
        if not tweet:
            raise HTTPException(status_code=404, detail="推文不存在")
        return tweet
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取推文失败: {str(e)}")

@router.get("/users/{username}", response_model=UserResponse)
async def get_user_profile(
    username: str,
    token: str = Depends(verify_token)
):
    """获取用户资料"""
    try:
        data_service = DataService()
        user = await data_service.get_user_by_username(username)
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        return user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取用户失败: {str(e)}")

@router.get("/users/{username}/tweets", response_model=List[TweetResponse])
async def get_user_tweets(
    username: str,
    limit: int = Query(100, ge=1, le=1000),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    token: str = Depends(verify_token)
):
    """获取用户的推文列表"""
    try:
        data_service = DataService()
        tweets = await data_service.get_user_tweets(
            username=username,
            limit=limit,
            start_date=start_date,
            end_date=end_date
        )
        return tweets
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取用户推文失败: {str(e)}")

@router.get("/analytics/trending", response_model=Dict[str, Any])
async def get_trending_topics(
    hours: int = Query(24, ge=1, le=168, description="时间范围(小时)"),
    limit: int = Query(20, ge=1, le=100, description="返回数量"),
    token: str = Depends(verify_token)
):
    """获取热门话题和趋势"""
    try:
        data_service = DataService()
        trending = await data_service.get_trending_topics(hours=hours, limit=limit)
        return trending
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取趋势失败: {str(e)}")
```

#### 🔧 **任务管理API**

```python
# api/routes/tasks.py - 任务管理接口
from fastapi import APIRouter, BackgroundTasks, Depends
from typing import List, Optional
from ..models import TaskRequest, TaskResponse, TaskStatus
from ..services import TaskService

router = APIRouter(prefix="/api/v1/tasks", tags=["任务管理"])

@router.post("/search", response_model=TaskResponse)
async def create_search_task(
    request: TaskRequest,
    background_tasks: BackgroundTasks,
    token: str = Depends(verify_token)
):
    """
    创建搜索任务

    支持的任务类型：
    - keyword_search: 关键词搜索
    - user_timeline: 用户时间线
    - user_profile: 用户资料采集
    """
    try:
        task_service = TaskService()
        task = await task_service.create_search_task(request)

        # 异步执行任务
        background_tasks.add_task(task_service.execute_task, task.task_id)

        return task
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建任务失败: {str(e)}")

@router.get("/", response_model=List[TaskResponse])
async def list_tasks(
    status: Optional[TaskStatus] = Query(None, description="任务状态过滤"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    token: str = Depends(verify_token)
):
    """获取任务列表"""
    try:
        task_service = TaskService()
        tasks = await task_service.list_tasks(
            status=status,
            limit=limit,
            offset=offset
        )
        return tasks
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取任务列表失败: {str(e)}")

@router.get("/{task_id}", response_model=TaskResponse)
async def get_task_detail(
    task_id: str,
    token: str = Depends(verify_token)
):
    """获取任务详情"""
    try:
        task_service = TaskService()
        task = await task_service.get_task_by_id(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        return task
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取任务详情失败: {str(e)}")

@router.post("/{task_id}/cancel")
async def cancel_task(
    task_id: str,
    token: str = Depends(verify_token)
):
    """取消任务"""
    try:
        task_service = TaskService()
        result = await task_service.cancel_task(task_id)
        if not result:
            raise HTTPException(status_code=404, detail="任务不存在或无法取消")
        return {"message": "任务已取消", "task_id": task_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"取消任务失败: {str(e)}")

@router.get("/{task_id}/progress")
async def get_task_progress(
    task_id: str,
    token: str = Depends(verify_token)
):
    """获取任务进度"""
    try:
        task_service = TaskService()
        progress = await task_service.get_task_progress(task_id)
        if not progress:
            raise HTTPException(status_code=404, detail="任务不存在")
        return progress
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取任务进度失败: {str(e)}")
```

#### ⚙️ **系统管理API**

```python
# api/routes/admin.py - 系统管理接口
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from ..models import AccountResponse, ProxyResponse, SystemStats
from ..services import AdminService

router = APIRouter(prefix="/api/v1/admin", tags=["系统管理"])

@router.get("/accounts", response_model=List[AccountResponse])
async def list_accounts(
    status: Optional[str] = Query(None, description="账号状态过滤"),
    token: str = Depends(verify_token)
):
    """获取账号列表"""
    try:
        admin_service = AdminService()
        accounts = await admin_service.list_accounts(status=status)
        return accounts
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取账号列表失败: {str(e)}")

@router.post("/accounts/{account_id}/test")
async def test_account(
    account_id: str,
    token: str = Depends(verify_token)
):
    """测试账号可用性"""
    try:
        admin_service = AdminService()
        result = await admin_service.test_account(account_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"测试账号失败: {str(e)}")

@router.post("/accounts/{account_id}/refresh")
async def refresh_account_cookies(
    account_id: str,
    token: str = Depends(verify_token)
):
    """刷新账号cookies"""
    try:
        admin_service = AdminService()
        result = await admin_service.refresh_account_cookies(account_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"刷新cookies失败: {str(e)}")

@router.get("/proxies", response_model=List[ProxyResponse])
async def list_proxies(
    status: Optional[str] = Query(None, description="代理状态过滤"),
    token: str = Depends(verify_token)
):
    """获取代理列表"""
    try:
        admin_service = AdminService()
        proxies = await admin_service.list_proxies(status=status)
        return proxies
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取代理列表失败: {str(e)}")

@router.post("/proxies/{proxy_id}/test")
async def test_proxy(
    proxy_id: str,
    token: str = Depends(verify_token)
):
    """测试代理可用性"""
    try:
        admin_service = AdminService()
        result = await admin_service.test_proxy(proxy_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"测试代理失败: {str(e)}")

@router.get("/stats", response_model=SystemStats)
async def get_system_stats(
    token: str = Depends(verify_token)
):
    """获取系统统计信息"""
    try:
        admin_service = AdminService()
        stats = await admin_service.get_system_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取系统统计失败: {str(e)}")

@router.get("/health")
async def health_check():
    """系统健康检查（无需认证）"""
    try:
        admin_service = AdminService()
        health = await admin_service.health_check()
        return health
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"系统不健康: {str(e)}")
```

#### 📋 **数据模型定义**

```python
# api/models.py - API数据模型
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TaskType(str, Enum):
    KEYWORD_SEARCH = "keyword_search"
    USER_TIMELINE = "user_timeline"
    USER_PROFILE = "user_profile"

class MediaItem(BaseModel):
    type: str = Field(..., description="媒体类型")
    url: str = Field(..., description="媒体URL")
    width: Optional[int] = Field(None, description="宽度")
    height: Optional[int] = Field(None, description="高度")

class UserInfo(BaseModel):
    user_id: str = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    display_name: str = Field(..., description="显示名称")
    verified: bool = Field(False, description="是否认证")
    followers_count: int = Field(0, description="粉丝数")

class TweetResponse(BaseModel):
    tweet_id: str = Field(..., description="推文ID")
    text: str = Field(..., description="推文内容")
    user: UserInfo = Field(..., description="用户信息")
    like_count: int = Field(0, description="点赞数")
    retweet_count: int = Field(0, description="转发数")
    reply_count: int = Field(0, description="回复数")
    quote_count: int = Field(0, description="引用数")
    view_count: int = Field(0, description="查看数")
    hashtags: List[str] = Field(default_factory=list, description="话题标签")
    mentions: List[str] = Field(default_factory=list, description="提及用户")
    urls: List[str] = Field(default_factory=list, description="链接")
    media: List[MediaItem] = Field(default_factory=list, description="媒体内容")
    created_at: datetime = Field(..., description="创建时间")
    collected_at: datetime = Field(..., description="采集时间")

class UserResponse(BaseModel):
    user_id: str = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    display_name: str = Field(..., description="显示名称")
    description: Optional[str] = Field(None, description="用户简介")
    verified: bool = Field(False, description="是否认证")
    protected: bool = Field(False, description="是否受保护")
    followers_count: int = Field(0, description="粉丝数")
    following_count: int = Field(0, description="关注数")
    tweet_count: int = Field(0, description="推文数")
    location: Optional[str] = Field(None, description="位置")
    website: Optional[str] = Field(None, description="网站")
    profile_image_url: Optional[str] = Field(None, description="头像URL")
    created_at: Optional[datetime] = Field(None, description="账号创建时间")
    collected_at: datetime = Field(..., description="采集时间")

class TaskRequest(BaseModel):
    type: TaskType = Field(..., description="任务类型")
    keyword: Optional[str] = Field(None, description="搜索关键词")
    username: Optional[str] = Field(None, description="用户名")
    count: int = Field(100, ge=1, le=10000, description="采集数量")
    priority: str = Field("normal", description="任务优先级")
    start_date: Optional[datetime] = Field(None, description="开始时间")
    end_date: Optional[datetime] = Field(None, description="结束时间")

class TaskProgress(BaseModel):
    total: int = Field(..., description="总数")
    collected: int = Field(..., description="已采集")
    failed: int = Field(..., description="失败数")
    percentage: float = Field(..., description="完成百分比")

class TaskResponse(BaseModel):
    task_id: str = Field(..., description="任务ID")
    type: TaskType = Field(..., description="任务类型")
    status: TaskStatus = Field(..., description="任务状态")
    parameters: Dict[str, Any] = Field(..., description="任务参数")
    progress: Optional[TaskProgress] = Field(None, description="任务进度")
    created_at: datetime = Field(..., description="创建时间")
    started_at: Optional[datetime] = Field(None, description="开始时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")
    error_message: Optional[str] = Field(None, description="错误信息")

class AccountResponse(BaseModel):
    account_id: str = Field(..., description="账号ID")
    username: str = Field(..., description="用户名")
    status: str = Field(..., description="账号状态")
    health_score: float = Field(..., description="健康分数")
    success_rate: float = Field(..., description="成功率")
    daily_used: int = Field(..., description="今日使用次数")
    daily_limit: int = Field(..., description="每日限制")
    last_used: Optional[datetime] = Field(None, description="最后使用时间")

class ProxyResponse(BaseModel):
    proxy_id: str = Field(..., description="代理ID")
    host: str = Field(..., description="主机地址")
    port: int = Field(..., description="端口")
    type: str = Field(..., description="代理类型")
    location: str = Field(..., description="位置")
    status: str = Field(..., description="状态")
    latency_ms: int = Field(..., description="延迟(毫秒)")
    success_rate: float = Field(..., description="成功率")

class SystemStats(BaseModel):
    total_tweets: int = Field(..., description="总推文数")
    total_users: int = Field(..., description="总用户数")
    active_tasks: int = Field(..., description="活跃任务数")
    healthy_accounts: int = Field(..., description="健康账号数")
    available_proxies: int = Field(..., description="可用代理数")
    today_collected: int = Field(..., description="今日采集数")
    system_uptime: str = Field(..., description="系统运行时间")
    last_updated: datetime = Field(..., description="最后更新时间")
```

#### 🔧 **服务层实现**

```python
# api/services/data_service.py - 数据服务
from motor.motor_asyncio import AsyncIOMotorClient
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging
from ..models import TweetResponse, UserResponse

class DataService:
    """数据查询服务"""

    def __init__(self):
        self.client = AsyncIOMotorClient(MONGODB_URI)
        self.db = self.client.xget
        self.logger = logging.getLogger(__name__)

    async def search_tweets(
        self,
        keyword: str,
        limit: int = 100,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        username: Optional[str] = None,
        min_likes: Optional[int] = None,
        has_media: Optional[bool] = None
    ) -> List[TweetResponse]:
        """搜索推文"""
        try:
            # 构建查询条件
            query = {}

            # 关键词搜索
            if keyword:
                query["$or"] = [
                    {"text": {"$regex": keyword, "$options": "i"}},
                    {"content.hashtags": {"$regex": keyword, "$options": "i"}}
                ]

            # 时间范围
            if start_date or end_date:
                date_query = {}
                if start_date:
                    date_query["$gte"] = start_date
                if end_date:
                    date_query["$lte"] = end_date
                query["metadata.created_at"] = date_query

            # 用户过滤
            if username:
                query["user.username"] = username

            # 互动数过滤
            if min_likes:
                query["metrics.like_count"] = {"$gte": min_likes}

            # 媒体过滤
            if has_media is not None:
                if has_media:
                    query["content.media"] = {"$exists": True, "$ne": []}
                else:
                    query["$or"] = [
                        {"content.media": {"$exists": False}},
                        {"content.media": []}
                    ]

            # 执行查询
            cursor = self.db.tweets.find(query).sort("metadata.created_at", -1).limit(limit)
            tweets = await cursor.to_list(length=limit)

            # 转换为响应模型
            return [self._tweet_to_response(tweet) for tweet in tweets]

        except Exception as e:
            self.logger.error(f"搜索推文失败: {str(e)}")
            raise

    async def get_tweet_by_id(self, tweet_id: str) -> Optional[TweetResponse]:
        """根据ID获取推文"""
        try:
            tweet = await self.db.tweets.find_one({"tweet_id": tweet_id})
            return self._tweet_to_response(tweet) if tweet else None
        except Exception as e:
            self.logger.error(f"获取推文失败: {str(e)}")
            raise

    async def get_user_by_username(self, username: str) -> Optional[UserResponse]:
        """根据用户名获取用户信息"""
        try:
            user = await self.db.users.find_one({"username": username})
            return self._user_to_response(user) if user else None
        except Exception as e:
            self.logger.error(f"获取用户失败: {str(e)}")
            raise

    async def get_trending_topics(self, hours: int = 24, limit: int = 20) -> Dict[str, Any]:
        """获取热门话题"""
        try:
            start_time = datetime.utcnow() - timedelta(hours=hours)

            # 聚合查询热门话题
            pipeline = [
                {"$match": {"metadata.created_at": {"$gte": start_time}}},
                {"$unwind": "$content.hashtags"},
                {"$group": {
                    "_id": "$content.hashtags",
                    "count": {"$sum": 1},
                    "total_likes": {"$sum": "$metrics.like_count"},
                    "total_retweets": {"$sum": "$metrics.retweet_count"}
                }},
                {"$sort": {"count": -1}},
                {"$limit": limit}
            ]

            trending = await self.db.tweets.aggregate(pipeline).to_list(length=limit)

            return {
                "time_range_hours": hours,
                "trending_topics": [
                    {
                        "hashtag": item["_id"],
                        "tweet_count": item["count"],
                        "total_likes": item["total_likes"],
                        "total_retweets": item["total_retweets"]
                    }
                    for item in trending
                ]
            }

        except Exception as e:
            self.logger.error(f"获取热门话题失败: {str(e)}")
            raise

    def _tweet_to_response(self, tweet: Dict) -> TweetResponse:
        """转换推文数据为响应模型"""
        return TweetResponse(
            tweet_id=tweet["tweet_id"],
            text=tweet["text"],
            user=UserInfo(
                user_id=tweet["user"]["user_id"],
                username=tweet["user"]["username"],
                display_name=tweet["user"]["display_name"],
                verified=tweet["user"].get("verified", False),
                followers_count=tweet["user"].get("followers_count", 0)
            ),
            like_count=tweet["metrics"].get("like_count", 0),
            retweet_count=tweet["metrics"].get("retweet_count", 0),
            reply_count=tweet["metrics"].get("reply_count", 0),
            quote_count=tweet["metrics"].get("quote_count", 0),
            view_count=tweet["metrics"].get("view_count", 0),
            hashtags=tweet["content"].get("hashtags", []),
            mentions=tweet["content"].get("mentions", []),
            urls=[url["expanded_url"] for url in tweet["content"].get("urls", [])],
            media=[
                MediaItem(
                    type=media["type"],
                    url=media["url"],
                    width=media.get("width"),
                    height=media.get("height")
                )
                for media in tweet["content"].get("media", [])
            ],
            created_at=tweet["metadata"]["created_at"],
            collected_at=tweet["metadata"]["collected_at"]
        )

    def _user_to_response(self, user: Dict) -> UserResponse:
        """转换用户数据为响应模型"""
        return UserResponse(
            user_id=user["user_id"],
            username=user["username"],
            display_name=user["display_name"],
            description=user.get("description"),
            verified=user["profile"].get("verified", False),
            protected=user["profile"].get("protected", False),
            followers_count=user["metrics"].get("followers_count", 0),
            following_count=user["metrics"].get("following_count", 0),
            tweet_count=user["metrics"].get("tweet_count", 0),
            location=user["profile"].get("location"),
            website=user["profile"].get("website"),
            profile_image_url=user["profile"].get("profile_image_url"),
            created_at=user["metadata"].get("created_at"),
            collected_at=user["metadata"]["collected_at"]
        )
```

#### 🎯 **API使用示例**

```bash
# 1. 搜索推文
curl -X GET "http://localhost:8000/api/v1/data/tweets/search?keyword=python&limit=50" \
  -H "Authorization: Bearer your-api-token"

# 2. 获取用户资料
curl -X GET "http://localhost:8000/api/v1/data/users/elonmusk" \
  -H "Authorization: Bearer your-api-token"

# 3. 创建搜索任务
curl -X POST "http://localhost:8000/api/v1/tasks/search" \
  -H "Authorization: Bearer your-api-token" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "keyword_search",
    "keyword": "artificial intelligence",
    "count": 1000,
    "priority": "high"
  }'

# 4. 获取系统统计
curl -X GET "http://localhost:8000/api/v1/admin/stats" \
  -H "Authorization: Bearer your-api-token"

# 5. 健康检查
curl -X GET "http://localhost:8000/api/v1/admin/health"
```

#### 📊 **API响应示例**

```json
{
  "tweet_id": "1234567890123456789",
  "text": "Python is amazing for data science! #python #datascience",
  "user": {
    "user_id": "987654321",
    "username": "data_scientist",
    "display_name": "Data Scientist",
    "verified": false,
    "followers_count": 5000
  },
  "like_count": 150,
  "retweet_count": 45,
  "reply_count": 12,
  "quote_count": 8,
  "view_count": 2500,
  "hashtags": ["python", "datascience"],
  "mentions": [],
  "urls": ["https://example.com/article"],
  "media": [],
  "created_at": "2024-01-01T12:00:00Z",
  "collected_at": "2024-01-01T12:05:00Z"
}
```

## 后续扩展需求

### 🚀 **甲方后续需求规划**

根据甲方需求文档，系统需要支持多平台扩展：

#### 📘 **Facebook 扩展需求**

```python
# Facebook用户数据结构
{
  "platform": "facebook",
  "user_id": "facebook_user_123",
  "user_details": {
    "name": "用户名称",
    "avatar": "头像URL",
    "description": "用户简介",
    "gender": "性别",
    "friends_count": 1500,  # 好友数
    "location": {
      "country": "中国",
      "city": "北京"
    }
  },
  "posts": {
    "post_id": "facebook_post_456",
    "content": "帖文内容",
    "like_list": [  # 点赞列表
      {"user_id": "user1", "name": "用户1"},
      {"user_id": "user2", "name": "用户2"}
    ],
    "share_list": [  # 转发列表
      {"user_id": "user3", "name": "用户3"},
      {"user_id": "user4", "name": "用户4"}
    ]
  }
}
```

#### 🐦 **Twitter 扩展需求**

```python
# Twitter扩展数据结构
{
  "platform": "twitter",
  "extended_features": {
    "search_terms": ["搜索词1", "搜索词2"],  # 搜索词功能
    "retweet_lists": {
      "direct_retweets": [  # 直接转推列表
        {"user_id": "user1", "retweet_time": "2024-01-01T12:00:00Z"}
      ],
      "quote_retweets": [   # 引用转推列表
        {
          "user_id": "user2",
          "quote_content": "引用内容",
          "quote_time": "2024-01-01T12:30:00Z"
        }
      ]
    }
  }
}
```

#### 📸 **Instagram 扩展需求**

```python
# Instagram数据结构
{
  "platform": "instagram",
  "user_id": "instagram_user_789",
  "user_details": {
    "username": "用户名",
    "display_name": "显示名称",
    "avatar": "头像URL",
    "bio": "个人简介",
    "location": {
      "country": "美国",
      "city": "纽约"
    }
  },
  "posts": {
    "post_id": "instagram_post_101",
    "content": "帖文内容",
    "media_type": "image",  # image/video/carousel
    "like_list": [  # 点赞列表
      {"user_id": "user5", "username": "user5_name"}
    ]
  },
  "search_terms": ["搜索词A", "搜索词B"]  # 搜索词功能
}
```

### 📊 **实施优先级**

#### **第一阶段 (当前)：Twitter核心功能**
- ✅ 关键词搜索采集
- ✅ 双模式任务系统
- ✅ 完整数据解析
- ✅ OSS资源管理
- ✅ API接口体系

#### **第二阶段：Twitter扩展功能**
- 🔄 搜索词管理
- 🔄 转推列表采集
- 🔄 引用转推分析
- 🔄 高级数据分析

#### **第三阶段：Facebook集成**
- 📋 用户详情采集
- 📋 好友关系分析
- 📋 帖文互动列表
- 📋 地理位置数据

#### **第四阶段：Instagram集成**
- 📋 视觉内容采集
- 📋 用户地理数据
- 📋 互动列表分析
- 📋 搜索词功能

## 总结

### ✅ **完全符合甲方需求**

1. **业务需求100%覆盖** - 所有甲方要求的功能都已设计
2. **数据字段完整对应** - 严格按照甲方20个字段要求
3. **API接口标准化** - 提供甲乙双方完整的接口规范
4. **OSS资源管理** - 完整的图片下载和存储方案
5. **数据统计去重** - 按关键词月度去重统计

### 🎯 **技术实现优势**

1. **生产就绪** - 包含生产环境必需组件
2. **可扩展性** - 支持多平台后续扩展
3. **稳定性** - 完善的错误处理和监控
4. **标准化** - 统一的数据格式和API规范

### 💡 **Apify经验集成优势**

基于Apify Twitter Scraper的成功经验，我们的方案具有以下优势：

#### **🎯 查询优化**
- **高级搜索语法** - 支持复杂的Twitter查询语法
- **智能分段查询** - 自动优化大量数据采集
- **成本控制** - 透明的事件驱动定价模型

#### **📊 数据质量**
- **完整字段映射** - 严格按照甲方20个字段要求
- **媒体处理** - 支持图片、视频的完整信息
- **原始数据保留** - 满足甲方原始数据要求

#### **⚡ 性能优化**
- **批量处理** - 支持大规模数据采集
- **智能重试** - 自动处理失败和限流
- **资源管理** - 高效的账号和代理轮换

#### **💰 成本效益**
- **透明定价** - 参考Apify的事件驱动模型
- **查询优化** - 减少不必要的API调用
- **批量折扣** - 大量采集时的成本优势

### 🚀 **实施建议**

1. **立即开始Twitter核心功能** - 技术风险可控，可以立即实施
2. **分阶段交付** - 每个阶段都有可用的功能
3. **严格按需求实施** - 确保每个功能都符合甲方要求
4. **预留扩展接口** - 为后续多平台扩展做好准备
5. **借鉴Apify最佳实践** - 采用经过验证的架构和优化策略

### 📈 **预期效果**

基于Apify Twitter Scraper的成功案例，我们的XGet系统预期能够实现：

- **采集效率**: 每秒处理49-64条推文 (参考Apify性能)
- **成本控制**: 透明的$0.0004/条推文定价模型
- **稳定性**: >99%的运行成功率
- **可扩展性**: 支持无限量数据采集
- **合规性**: 完全符合甲方业务需求

这个方案完全基于甲方需求文档设计，并融合了Apify Twitter Scraper的成功经验，确保了业务需求的100%覆盖和技术实现的可行性。
