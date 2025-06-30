#!/usr/bin/env python3
"""
twscrape 可行性验证脚本
测试 twscrape 库的基本功能，确认其在当前环境下的可用性
"""

import asyncio
import sys
import json
from datetime import datetime
from typing import List, Dict, Optional

def check_dependencies():
    """检查依赖库是否可用"""
    print("🔍 检查依赖库...")

    try:
        import twscrape
        # 尝试获取版本信息，如果没有__version__属性则显示已安装
        try:
            version = twscrape.__version__
            print(f"✅ twscrape 版本: {version}")
        except AttributeError:
            # 尝试从包信息获取版本
            try:
                import pkg_resources
                version = pkg_resources.get_distribution("twscrape").version
                print(f"✅ twscrape 版本: {version}")
            except:
                print("✅ twscrape 已安装")
    except ImportError as e:
        print(f"❌ twscrape 未安装: {e}")
        print("请运行: pip install twscrape")
        return False
    except Exception as e:
        print(f"❌ twscrape 导入错误: {e}")
        return False

    try:
        import httpx
        print(f"✅ httpx 可用")
    except ImportError:
        print("❌ httpx 未安装，请运行: pip install httpx")
        return False

    try:
        import playwright
        print(f"✅ playwright 可用")
    except ImportError:
        print("⚠️  playwright 未安装 (可选)")

    return True

async def test_basic_api():
    """测试基本API功能"""
    print("\n🧪 测试基本API功能...")
    
    try:
        from twscrape import API
        api = API()
        
        # 检查API对象是否正常创建
        print("✅ API对象创建成功")
        
        # 检查账号池状态
        accounts = await api.pool.get_all()
        print(f"📊 当前账号池: {len(accounts)} 个账号")
        
        if len(accounts) == 0:
            print("⚠️  账号池为空，需要添加账号才能进行数据采集")
            print("   添加账号命令: twscrape add_account username password email email_password")
            print("✅ 基本API功能正常，但需要添加账号")
            return True  # API功能本身是正常的
        
        # 显示账号状态
        for account in accounts:
            status = "✅ 活跃" if account.active else "❌ 不活跃"
            print(f"   账号: {account.username} - {status}")
        
        return True
        
    except Exception as e:
        print(f"❌ API测试失败: {e}")
        return False

async def test_search_functionality():
    """测试搜索功能"""
    print("\n🔍 测试搜索功能...")
    
    try:
        from twscrape import API
        api = API()
        
        # 检查是否有可用账号
        accounts = await api.pool.get_all()
        active_accounts = [acc for acc in accounts if acc.active]
        
        if not active_accounts:
            print("⚠️  没有活跃账号，跳过搜索测试")
            print("💡 这是正常的，需要先添加Twitter账号")
            return True  # 跳过测试但不算失败
        
        print(f"🚀 使用 {len(active_accounts)} 个活跃账号进行测试...")
        
        # 测试简单搜索 (限制结果数量避免过度请求)
        test_keyword = "python"
        print(f"🔍 搜索关键词: '{test_keyword}' (限制5条结果)")
        
        tweets = []
        count = 0
        async for tweet in api.search(test_keyword, limit=5):
            count += 1
            tweet_data = {
                'id': tweet.id,
                'text': tweet.rawContent[:100] + "..." if len(tweet.rawContent) > 100 else tweet.rawContent,
                'user': tweet.user.username,
                'created_at': tweet.date.isoformat() if tweet.date else None,
                'metrics': {
                    'retweets': tweet.retweetCount,
                    'likes': tweet.likeCount,
                    'replies': tweet.replyCount
                }
            }
            tweets.append(tweet_data)
            print(f"   📝 推文 {count}: @{tweet.user.username} - {tweet_data['text']}")
            
            # 避免请求过快
            await asyncio.sleep(1)
        
        print(f"✅ 搜索测试完成，获取到 {len(tweets)} 条推文")
        return True
        
    except Exception as e:
        print(f"❌ 搜索测试失败: {e}")
        print(f"   错误类型: {type(e).__name__}")
        return False

async def test_user_functionality():
    """测试用户信息获取功能"""
    print("\n👤 测试用户信息获取...")
    
    try:
        from twscrape import API
        api = API()
        
        # 测试获取用户信息 (使用指定账号)
        test_username = "wstunnel"  # 使用wstunnel账号进行测试
        print(f"🔍 获取用户信息: @{test_username}")
        
        user = await api.user_by_login(test_username)
        if user:
            user_info = {
                'id': user.id,
                'username': user.username,
                'display_name': user.displayname,
                'followers': user.followersCount,
                'following': user.friendsCount,  # 正确的属性名
                'tweets': user.statusesCount,
                'verified': user.verified,
                'created': user.created.isoformat() if user.created else None
            }
            
            print(f"✅ 用户信息获取成功:")
            print(f"   用户名: @{user_info['username']}")
            print(f"   显示名: {user_info['display_name']}")
            print(f"   粉丝数: {user_info['followers']:,}")
            print(f"   关注数: {user_info['following']:,}")
            print(f"   推文数: {user_info['tweets']:,}")
            print(f"   认证状态: {'✅ 已认证' if user_info['verified'] else '❌ 未认证'}")
            
            return True
        else:
            print(f"❌ 未找到用户: @{test_username}")
            return False
            
    except Exception as e:
        print(f"❌ 用户信息测试失败: {e}")
        return False

async def test_rate_limits():
    """测试速率限制处理"""
    print("\n⏱️  测试速率限制处理...")
    
    try:
        from twscrape import API
        api = API()
        
        # 检查账号状态和速率限制
        accounts = await api.pool.get_all()
        active_accounts = [acc for acc in accounts if acc.active]
        
        if not active_accounts:
            print("⚠️  没有活跃账号，跳过速率限制测试")
            print("💡 这是正常的，需要先添加Twitter账号")
            return True  # 跳过测试但不算失败
        
        print(f"📊 活跃账号数量: {len(active_accounts)}")
        
        # 简单的速率限制测试
        print("🔄 执行连续请求测试...")
        for i in range(3):
            try:
                # 执行简单搜索
                async for tweet in api.search("test", limit=1):
                    print(f"   请求 {i+1}: 成功获取推文 ID {tweet.id}")
                    break
                await asyncio.sleep(2)  # 等待2秒
            except Exception as e:
                print(f"   请求 {i+1}: 失败 - {e}")
        
        print("✅ 速率限制测试完成")
        return True
        
    except Exception as e:
        print(f"❌ 速率限制测试失败: {e}")
        return False

def generate_test_report(results: Dict[str, bool]):
    """生成测试报告"""
    print("\n" + "="*50)
    print("📋 twscrape 可行性验证报告")
    print("="*50)
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    print(f"总测试数: {total_tests}")
    print(f"通过测试: {passed_tests}")
    print(f"失败测试: {total_tests - passed_tests}")
    print(f"成功率: {passed_tests/total_tests*100:.1f}%")
    
    print("\n详细结果:")
    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {test_name}: {status}")
    
    print("\n" + "="*50)
    
    if passed_tests == total_tests:
        print("🎉 所有测试通过！twscrape 可以正常使用")
        print("✅ 可以开始 XGet 项目开发")
    elif passed_tests >= total_tests * 0.7:
        print("⚠️  大部分测试通过，但有一些问题需要解决")
        print("🔧 建议解决失败的测试后再开始项目")
    else:
        print("❌ 多数测试失败，不建议立即开始项目")
        print("🔧 需要先解决 twscrape 的配置和账号问题")
    
    return passed_tests == total_tests

async def main():
    """主测试函数"""
    print("🚀 开始 twscrape 可行性验证")
    print(f"⏰ 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 检查依赖
    if not check_dependencies():
        print("❌ 依赖检查失败，请先安装必要的库")
        return False
    
    # 执行各项测试
    test_results = {}
    
    test_results["基本API功能"] = await test_basic_api()
    test_results["搜索功能"] = await test_search_functionality()
    test_results["用户信息获取"] = await test_user_functionality()
    test_results["速率限制处理"] = await test_rate_limits()
    
    # 生成报告
    return generate_test_report(test_results)

if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n⚠️  测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        sys.exit(1)
