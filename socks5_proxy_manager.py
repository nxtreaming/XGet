#!/usr/bin/env python3
"""
SOCKS5代理管理器实现示例
专门针对大量SOCKS5代理IP的管理和使用
"""

import asyncio
import aiohttp
import json
import logging
import time
import random
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
    
    async def incr(self, key: str):
        current = int(self.data.get(key, 0))
        self.data[key] = str(current + 1)
        return current + 1
    
    async def expire(self, key: str, seconds: int):
        pass  # 简化实现，实际Redis会自动过期
    
    async def delete(self, key: str):
        self.data.pop(key, None)
        self.sets.pop(key, None)

class ProxyStatus(Enum):
    ACTIVE = "active"
    ERROR = "error"
    BANNED = "banned"
    TESTING = "testing"

class ProxyRegion(Enum):
    US = "us"
    EU = "eu"
    ASIA = "asia"
    GLOBAL = "global"

@dataclass
class ProxyMetrics:
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    consecutive_errors: int = 0
    daily_usage: int = 0
    average_response_time: float = 0.0
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
        error_penalty = min(self.consecutive_errors * 0.15, 0.6)
        time_factor = 1.0 if self.average_response_time < 3.0 else 0.8
        usage_factor = 1.0 if self.daily_usage < 800 else 0.8
        return max(0.0, (base_score - error_penalty) * time_factor * usage_factor)

@dataclass
class ProxyConfig:
    proxy_id: str
    host: str
    port: int
    username: str
    password: str
    region: ProxyRegion = ProxyRegion.GLOBAL
    status: ProxyStatus = ProxyStatus.ACTIVE
    max_concurrent: int = 10
    daily_limit: int = 1000
    provider: str = "unknown"
    
    @property
    def proxy_url(self) -> str:
        return f"socks5://{self.username}:{self.password}@{self.host}:{self.port}"
    
    @property
    def connection_info(self) -> Dict:
        return {
            'host': self.host,
            'port': self.port,
            'username': self.username,
            'password': self.password,
            'proxy_url': self.proxy_url
        }

class SOCKS5ProxyManager:
    """SOCKS5代理管理器"""
    
    def __init__(self, redis_client=None):
        self.redis = redis_client or MockRedis()
        self.logger = logging.getLogger(__name__)
        self.health_threshold = 0.7
        
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
                    region=ProxyRegion(proxy_data.get('region', 'global')),
                    provider=proxy_data.get('provider', 'unknown')
                )
                
                success = await self._add_single_proxy(proxy_config)
                results[proxy_config.proxy_id] = success
                
            except Exception as e:
                self.logger.error(f"Failed to add proxy {proxy_data}: {e}")
                results[f"error_{proxy_data.get('host', 'unknown')}"] = False
        
        successful = sum(results.values())
        self.logger.info(f"Batch add completed: {successful}/{len(proxy_list)} successful")
        return results
    
    async def _add_single_proxy(self, config: ProxyConfig) -> bool:
        """添加单个代理"""
        try:
            await self._save_proxy_config(config)
            await self._initialize_proxy_metrics(config.proxy_id)
            
            # 执行初始测试
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
    
    async def get_available_proxy(self, region: Optional[ProxyRegion] = None) -> Optional[Dict]:
        """获取可用代理"""
        try:
            # 获取活跃代理
            active_proxies = await self.redis.smembers('proxies:active')
            
            candidates = []
            for proxy_id in active_proxies:
                proxy_id = proxy_id.decode() if isinstance(proxy_id, bytes) else proxy_id
                
                config = await self._get_proxy_config(proxy_id)
                metrics = await self._get_proxy_metrics(proxy_id)
                
                if not config or not metrics:
                    continue
                
                # 地区过滤
                if region and config.region != region:
                    continue
                
                # 检查使用限制
                if metrics.daily_usage >= config.daily_limit:
                    continue
                
                # 健康分数过滤
                if metrics.health_score < self.health_threshold:
                    continue
                
                candidates.append({
                    'proxy_id': proxy_id,
                    'config': config,
                    'metrics': metrics,
                    'score': self._calculate_score(config, metrics)
                })
            
            if not candidates:
                return None
            
            # 选择最佳代理
            best = max(candidates, key=lambda x: x['score'])
            
            # 记录使用
            await self._record_usage(best['proxy_id'])
            
            return {
                'proxy_id': best['proxy_id'],
                'proxy_url': best['config'].proxy_url,
                'connection_info': best['config'].connection_info,
                'health_score': best['metrics'].health_score,
                'region': best['config'].region.value,
                'response_time': best['metrics'].average_response_time
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get available proxy: {e}")
            return None
    
    async def _test_proxy_connection(self, config: ProxyConfig) -> bool:
        """测试SOCKS5代理连接"""
        try:
            start_time = time.time()
            
            # 使用aiohttp测试代理连接
            proxy_url = config.proxy_url
            timeout = aiohttp.ClientTimeout(total=10)
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(
                    'https://httpbin.org/ip',
                    proxy=proxy_url
                ) as response:
                    if response.status == 200:
                        response_time = time.time() - start_time
                        await self._update_response_time(config.proxy_id, response_time)
                        return True
                    else:
                        return False
                        
        except Exception as e:
            self.logger.warning(f"Proxy {config.proxy_id} test failed: {e}")
            return False
    
    async def update_proxy_success(self, proxy_id: str, response_time: float = 0.0):
        """更新代理成功记录"""
        await self.redis.hincrby(f'proxy:{proxy_id}:metrics', 'total_requests', 1)
        await self.redis.hincrby(f'proxy:{proxy_id}:metrics', 'successful_requests', 1)
        await self.redis.hset(f'proxy:{proxy_id}:metrics', 'consecutive_errors', '0')
        await self.redis.hset(f'proxy:{proxy_id}:metrics', 'last_success', datetime.utcnow().isoformat())
        
        if response_time > 0:
            await self._update_response_time(proxy_id, response_time)
        
        self.logger.debug(f"Proxy {proxy_id} success recorded")
    
    async def mark_proxy_error(self, proxy_id: str, error: str):
        """标记代理错误"""
        await self.redis.hincrby(f'proxy:{proxy_id}:metrics', 'total_requests', 1)
        await self.redis.hincrby(f'proxy:{proxy_id}:metrics', 'failed_requests', 1)
        await self.redis.hincrby(f'proxy:{proxy_id}:metrics', 'consecutive_errors', 1)
        
        # 检查是否需要暂停
        consecutive_errors = await self.redis.hget(f'proxy:{proxy_id}:metrics', 'consecutive_errors')
        if consecutive_errors and int(consecutive_errors) >= 5:
            await self._suspend_proxy(proxy_id, f"Too many errors: {error}")
        
        self.logger.warning(f"Proxy {proxy_id} error: {error}")
    
    async def get_statistics(self) -> Dict:
        """获取代理池统计信息"""
        try:
            active_proxies = await self.redis.smembers('proxies:active')
            error_proxies = await self.redis.smembers('proxies:error')
            
            total_health = 0.0
            total_usage = 0
            total_response_time = 0.0
            region_stats = {}
            
            for proxy_id in active_proxies:
                proxy_id = proxy_id.decode() if isinstance(proxy_id, bytes) else proxy_id
                
                config = await self._get_proxy_config(proxy_id)
                metrics = await self._get_proxy_metrics(proxy_id)
                
                if config and metrics:
                    total_health += metrics.health_score
                    total_usage += metrics.daily_usage
                    total_response_time += metrics.average_response_time
                    
                    region = config.region.value
                    region_stats[region] = region_stats.get(region, 0) + 1
            
            active_count = len(active_proxies)
            
            return {
                'total_proxies': active_count + len(error_proxies),
                'active_proxies': active_count,
                'error_proxies': len(error_proxies),
                'average_health_score': total_health / active_count if active_count > 0 else 0.0,
                'average_response_time': total_response_time / active_count if active_count > 0 else 0.0,
                'total_daily_usage': total_usage,
                'region_distribution': region_stats
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get proxy statistics: {e}")
            return {}
    
    # 辅助方法
    async def _save_proxy_config(self, config: ProxyConfig):
        config_dict = asdict(config)
        config_dict['region'] = config.region.value
        config_dict['status'] = config.status.value
        
        await self.redis.hset(f'proxy:{config.proxy_id}:config', mapping=config_dict)
        await self.redis.sadd('proxies:all', config.proxy_id)
        await self.redis.sadd('proxies:active', config.proxy_id)
    
    async def _get_proxy_config(self, proxy_id: str) -> Optional[ProxyConfig]:
        config_data = await self.redis.hgetall(f'proxy:{proxy_id}:config')
        if not config_data:
            return None
        
        config_data['region'] = ProxyRegion(config_data['region'])
        config_data['status'] = ProxyStatus(config_data['status'])
        
        for field in ['port', 'max_concurrent', 'daily_limit']:
            if field in config_data:
                config_data[field] = int(config_data[field])
        
        return ProxyConfig(**config_data)
    
    async def _initialize_proxy_metrics(self, proxy_id: str):
        metrics = ProxyMetrics()
        metrics_dict = asdict(metrics)
        
        for key, value in metrics_dict.items():
            if isinstance(value, datetime):
                metrics_dict[key] = value.isoformat()
            elif value is None:
                metrics_dict[key] = ''
        
        await self.redis.hset(f'proxy:{proxy_id}:metrics', mapping=metrics_dict)
    
    async def _get_proxy_metrics(self, proxy_id: str) -> ProxyMetrics:
        metrics_data = await self.redis.hgetall(f'proxy:{proxy_id}:metrics')
        if not metrics_data:
            return ProxyMetrics()
        
        for key in ['total_requests', 'successful_requests', 'failed_requests', 'consecutive_errors', 'daily_usage']:
            if key in metrics_data:
                metrics_data[key] = int(metrics_data[key] or 0)
        
        if 'average_response_time' in metrics_data:
            metrics_data['average_response_time'] = float(metrics_data['average_response_time'] or 0.0)
        
        for key in ['last_used', 'last_success']:
            if key in metrics_data and metrics_data[key]:
                metrics_data[key] = datetime.fromisoformat(metrics_data[key])
        
        return ProxyMetrics(**{k: v for k, v in metrics_data.items() if k in ProxyMetrics.__annotations__})
    
    def _calculate_score(self, config: ProxyConfig, metrics: ProxyMetrics) -> float:
        health_score = metrics.health_score * 0.5
        usage_score = (1 - metrics.daily_usage / config.daily_limit) * 0.3
        response_score = max(0, (5.0 - metrics.average_response_time) / 5.0) * 0.2
        return health_score + usage_score + response_score
    
    async def _record_usage(self, proxy_id: str):
        await self.redis.hincrby(f'proxy:{proxy_id}:metrics', 'daily_usage', 1)
        await self.redis.hset(f'proxy:{proxy_id}:metrics', 'last_used', datetime.utcnow().isoformat())
    
    async def _update_response_time(self, proxy_id: str, response_time: float):
        current_avg = await self.redis.hget(f'proxy:{proxy_id}:metrics', 'average_response_time')
        current_avg = float(current_avg) if current_avg else 0.0
        new_avg = (current_avg * 0.8) + (response_time * 0.2)
        await self.redis.hset(f'proxy:{proxy_id}:metrics', 'average_response_time', str(new_avg))
    
    async def _update_proxy_status(self, proxy_id: str, status: ProxyStatus):
        await self.redis.hset(f'proxy:{proxy_id}:config', 'status', status.value)
        
        # 更新状态索引
        for s in ProxyStatus:
            await self.redis.srem(f'proxies:{s.value}', proxy_id)
        await self.redis.sadd(f'proxies:{status.value}', proxy_id)
    
    async def _suspend_proxy(self, proxy_id: str, reason: str):
        await self._update_proxy_status(proxy_id, ProxyStatus.ERROR)
        self.logger.warning(f"Proxy {proxy_id} suspended: {reason}")

# 使用示例
async def example_usage():
    """SOCKS5代理管理器使用示例"""
    logging.basicConfig(level=logging.INFO)
    
    # 创建代理管理器
    proxy_manager = SOCKS5ProxyManager()
    
    # 模拟大量SOCKS5代理数据
    proxy_list = [
        {
            'host': '192.168.1.100',
            'port': 1080,
            'username': 'user1',
            'password': 'pass1',
            'region': 'us',
            'provider': 'ProxyProvider1'
        },
        {
            'host': '192.168.1.101',
            'port': 1080,
            'username': 'user2',
            'password': 'pass2',
            'region': 'eu',
            'provider': 'ProxyProvider1'
        },
        {
            'host': '192.168.1.102',
            'port': 1080,
            'username': 'user3',
            'password': 'pass3',
            'region': 'asia',
            'provider': 'ProxyProvider2'
        }
    ]
    
    print("=== SOCKS5代理管理器演示 ===")
    
    # 批量添加代理
    results = await proxy_manager.add_proxy_batch(proxy_list)
    print(f"添加结果: {sum(results.values())}/{len(proxy_list)} 成功")
    
    # 获取统计信息
    stats = await proxy_manager.get_statistics()
    print(f"\n代理池统计:")
    print(f"总代理数: {stats['total_proxies']}")
    print(f"活跃代理: {stats['active_proxies']}")
    print(f"平均健康分数: {stats['average_health_score']:.2f}")
    print(f"地区分布: {stats['region_distribution']}")
    
    # 获取可用代理
    proxy = await proxy_manager.get_available_proxy(region=ProxyRegion.US)
    if proxy:
        print(f"\n选中代理:")
        print(f"代理URL: {proxy['proxy_url']}")
        print(f"健康分数: {proxy['health_score']:.2f}")
        print(f"地区: {proxy['region']}")
        
        # 模拟成功使用
        await proxy_manager.update_proxy_success(proxy['proxy_id'], response_time=1.5)
        print("✅ 代理使用成功")
        
        # 模拟错误
        await proxy_manager.mark_proxy_error(proxy['proxy_id'], "Connection timeout")
        print("❌ 代理错误已记录")
    
    # 再次获取统计
    stats = await proxy_manager.get_statistics()
    print(f"\n更新后平均健康分数: {stats['average_health_score']:.2f}")

if __name__ == "__main__":
    asyncio.run(example_usage())
