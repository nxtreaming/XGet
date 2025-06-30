#!/usr/bin/env python3
"""
账号管理模块实现示例
基于完善的设计方案的简化实现版本
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, asdict

# 模拟Redis（实际使用时替换为真实的Redis客户端）
class MockRedis:
    def __init__(self):
        self.data = {}
        self.sets = {}
    
    async def hset(self, key: str, field: str = None, value: str = None, mapping: Dict = None, **kwargs):
        if key not in self.data:
            self.data[key] = {}
        if mapping:
            self.data[key].update(mapping)
        if field and value:
            self.data[key][field] = value
        self.data[key].update(kwargs)
    
    async def hget(self, key: str, field: str):
        return self.data.get(key, {}).get(field)
    
    async def hgetall(self, key: str):
        return self.data.get(key, {})
    
    async def hincrby(self, key: str, field: str, amount: int = 1):
        if key not in self.data:
            self.data[key] = {}
        current = int(self.data[key].get(field, 0))
        self.data[key][field] = str(current + amount)
    
    async def sadd(self, key: str, *values):
        if key not in self.sets:
            self.sets[key] = set()
        for value in values:
            self.sets[key].add(value)
    
    async def smembers(self, key: str):
        return [v.encode() if isinstance(v, str) else v for v in self.sets.get(key, set())]
    
    async def srem(self, key: str, *values):
        if key in self.sets:
            for value in values:
                self.sets[key].discard(value)

class AccountStatus(Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    ERROR = "error"
    MAINTENANCE = "maintenance"

class AccountPriority(Enum):
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"

@dataclass
class AccountMetrics:
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    consecutive_errors: int = 0
    daily_usage: int = 0
    last_used: Optional[datetime] = None
    last_success: Optional[datetime] = None
    
    @property
    def success_rate(self) -> float:
        if self.total_requests == 0:
            return 1.0
        return self.successful_requests / self.total_requests
    
    @property
    def health_score(self) -> float:
        base_score = self.success_rate
        error_penalty = min(self.consecutive_errors * 0.1, 0.5)
        usage_factor = 1.0 if self.daily_usage < 800 else 0.8
        return max(0.0, (base_score - error_penalty) * usage_factor)

@dataclass
class AccountConfig:
    account_id: str
    username: str
    email: str
    status: AccountStatus
    priority: AccountPriority
    daily_limit: int = 1000
    max_consecutive_errors: int = 5

class SimpleAccountManager:
    """简化版账号管理器 - 用于演示核心功能"""
    
    def __init__(self, redis_client=None):
        self.redis = redis_client or MockRedis()
        self.logger = logging.getLogger(__name__)
        self.health_threshold = 0.7
        
    async def add_account(self, username: str, email: str, 
                         priority: AccountPriority = AccountPriority.NORMAL) -> str:
        """添加账号"""
        account_id = f"acc_{username}"
        
        config = AccountConfig(
            account_id=account_id,
            username=username,
            email=email,
            status=AccountStatus.ACTIVE,
            priority=priority
        )
        
        await self._save_account_config(config)
        await self._initialize_account_metrics(account_id)
        
        self.logger.info(f"Account {username} added with ID {account_id}")
        return account_id
    
    async def get_available_account(self, priority: Optional[AccountPriority] = None) -> Optional[Dict]:
        """获取可用账号"""
        try:
            # 获取活跃账号
            active_accounts = await self.redis.smembers('accounts:active')
            
            candidates = []
            for account_id in active_accounts:
                account_id = account_id.decode() if isinstance(account_id, bytes) else account_id
                
                config = await self._get_account_config(account_id)
                metrics = await self._get_account_metrics(account_id)
                
                if not config or not metrics:
                    continue
                
                # 优先级过滤
                if priority and config.priority != priority:
                    continue
                
                # 检查使用限制
                if metrics.daily_usage >= config.daily_limit:
                    continue
                
                candidates.append({
                    'account_id': account_id,
                    'config': config,
                    'metrics': metrics,
                    'score': self._calculate_score(config, metrics)
                })
            
            if not candidates:
                return None
            
            # 选择最佳账号
            best = max(candidates, key=lambda x: x['score'])
            
            # 记录使用
            await self._record_usage(best['account_id'])
            
            return {
                'account_id': best['account_id'],
                'username': best['config'].username,
                'health_score': best['metrics'].health_score,
                'daily_usage': best['metrics'].daily_usage
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get available account: {e}")
            return None
    
    async def update_account_success(self, account_id: str):
        """更新账号成功记录"""
        await self.redis.hincrby(f'account:{account_id}:metrics', 'total_requests', 1)
        await self.redis.hincrby(f'account:{account_id}:metrics', 'successful_requests', 1)
        await self.redis.hset(f'account:{account_id}:metrics', field='consecutive_errors', value='0')
        await self.redis.hset(f'account:{account_id}:metrics', field='last_success', value=datetime.utcnow().isoformat())
        
        self.logger.debug(f"Account {account_id} success recorded")
    
    async def mark_account_error(self, account_id: str, error: str):
        """标记账号错误"""
        await self.redis.hincrby(f'account:{account_id}:metrics', 'total_requests', 1)
        await self.redis.hincrby(f'account:{account_id}:metrics', 'failed_requests', 1)
        await self.redis.hincrby(f'account:{account_id}:metrics', 'consecutive_errors', 1)
        
        # 检查是否需要暂停
        consecutive_errors = await self.redis.hget(f'account:{account_id}:metrics', 'consecutive_errors')
        if consecutive_errors and int(consecutive_errors) >= 5:
            await self._suspend_account(account_id, f"Too many errors: {error}")
        
        self.logger.warning(f"Account {account_id} error: {error}")
    
    async def get_statistics(self) -> Dict:
        """获取统计信息"""
        active_accounts = await self.redis.smembers('accounts:active')
        suspended_accounts = await self.redis.smembers('accounts:suspended')
        
        total_health = 0.0
        total_usage = 0
        
        for account_id in active_accounts:
            account_id = account_id.decode() if isinstance(account_id, bytes) else account_id
            metrics = await self._get_account_metrics(account_id)
            total_health += metrics.health_score
            total_usage += metrics.daily_usage
        
        active_count = len(active_accounts)
        
        return {
            'total_accounts': active_count + len(suspended_accounts),
            'active_accounts': active_count,
            'suspended_accounts': len(suspended_accounts),
            'average_health_score': total_health / active_count if active_count > 0 else 0.0,
            'total_daily_usage': total_usage
        }
    
    # 辅助方法
    async def _save_account_config(self, config: AccountConfig):
        config_dict = asdict(config)
        config_dict['status'] = config.status.value
        config_dict['priority'] = config.priority.value
        
        await self.redis.hset(f'account:{config.account_id}:config', mapping=config_dict)
        await self.redis.sadd('accounts:active', config.account_id)
    
    async def _get_account_config(self, account_id: str) -> Optional[AccountConfig]:
        config_data = await self.redis.hgetall(f'account:{account_id}:config')
        if not config_data:
            return None
        
        # 处理枚举类型
        config_data['status'] = AccountStatus(config_data['status'])
        config_data['priority'] = AccountPriority(config_data['priority'])
        
        # 处理数值类型
        for field in ['daily_limit', 'max_consecutive_errors']:
            if field in config_data:
                config_data[field] = int(config_data[field])
        
        return AccountConfig(**config_data)
    
    async def _initialize_account_metrics(self, account_id: str):
        metrics = AccountMetrics()
        metrics_dict = asdict(metrics)
        
        # 处理datetime字段
        for key, value in metrics_dict.items():
            if isinstance(value, datetime):
                metrics_dict[key] = value.isoformat()
            elif value is None:
                metrics_dict[key] = ''
        
        await self.redis.hset(f'account:{account_id}:metrics', mapping=metrics_dict)
    
    async def _get_account_metrics(self, account_id: str) -> AccountMetrics:
        metrics_data = await self.redis.hgetall(f'account:{account_id}:metrics')
        if not metrics_data:
            return AccountMetrics()
        
        # 转换数据类型
        for key in ['total_requests', 'successful_requests', 'failed_requests', 'consecutive_errors', 'daily_usage']:
            if key in metrics_data:
                metrics_data[key] = int(metrics_data[key] or 0)
        
        for key in ['last_used', 'last_success']:
            if key in metrics_data and metrics_data[key]:
                metrics_data[key] = datetime.fromisoformat(metrics_data[key])
        
        return AccountMetrics(**{k: v for k, v in metrics_data.items() if k in AccountMetrics.__annotations__})
    
    def _calculate_score(self, config: AccountConfig, metrics: AccountMetrics) -> float:
        """计算账号评分"""
        health_score = metrics.health_score * 0.5
        usage_score = (1 - metrics.daily_usage / config.daily_limit) * 0.3
        priority_score = {'high': 1.0, 'normal': 0.8, 'low': 0.6}[config.priority.value] * 0.2
        
        return health_score + usage_score + priority_score
    
    async def _record_usage(self, account_id: str):
        await self.redis.hincrby(f'account:{account_id}:metrics', 'daily_usage', 1)
        await self.redis.hset(f'account:{account_id}:metrics', field='last_used', value=datetime.utcnow().isoformat())
    
    async def _suspend_account(self, account_id: str, reason: str):
        # 更新状态
        await self.redis.hset(f'account:{account_id}:config', field='status', value=AccountStatus.SUSPENDED.value)
        
        # 更新索引
        await self.redis.srem('accounts:active', account_id)
        await self.redis.sadd('accounts:suspended', account_id)
        
        self.logger.warning(f"Account {account_id} suspended: {reason}")

# 使用示例
async def example_usage():
    """使用示例"""
    logging.basicConfig(level=logging.INFO)
    
    # 创建账号管理器
    manager = SimpleAccountManager()
    
    # 添加测试账号
    await manager.add_account("test_user1", "test1@example.com", AccountPriority.HIGH)
    await manager.add_account("test_user2", "test2@example.com", AccountPriority.NORMAL)
    await manager.add_account("test_user3", "test3@example.com", AccountPriority.LOW)
    
    print("=== 账号管理器演示 ===")
    
    # 获取统计信息
    stats = await manager.get_statistics()
    print(f"总账号数: {stats['total_accounts']}")
    print(f"活跃账号: {stats['active_accounts']}")
    print(f"平均健康分数: {stats['average_health_score']:.2f}")
    
    # 获取可用账号
    account = await manager.get_available_account()
    if account:
        print(f"\n选中账号: {account['username']}")
        print(f"健康分数: {account['health_score']:.2f}")
        print(f"今日使用: {account['daily_usage']}")
        
        # 模拟成功操作
        await manager.update_account_success(account['account_id'])
        print("✅ 成功操作已记录")
        
        # 模拟错误操作
        await manager.mark_account_error(account['account_id'], "Rate limit exceeded")
        print("❌ 错误已记录")
    
    # 再次获取统计
    stats = await manager.get_statistics()
    print(f"\n更新后平均健康分数: {stats['average_health_score']:.2f}")

if __name__ == "__main__":
    asyncio.run(example_usage())
