#!/usr/bin/env python3
"""
测试用户查找功能
"""

import asyncio
from twscrape import API

async def test_user_lookup():
    print("🔍 测试用户查找功能...")
    
    api = API()
    
    # 检查账号池
    accounts = await api.pool.get_all()
    print(f"📊 账号池状态: {len(accounts)} 个账号")
    
    if len(accounts) == 0:
        print("❌ 没有Twitter账号，无法进行用户查找")
        print("💡 需要先添加Twitter账号:")
        print("   twscrape add_account username password email email_password")
        print("   twscrape login_accounts")
        return False
    
    # 显示账号状态
    for account in accounts:
        status = "✅ 活跃" if account.active else "❌ 不活跃"
        print(f"   账号: {account.username} - {status}")
    
    active_accounts = [acc for acc in accounts if acc.active]
    if len(active_accounts) == 0:
        print("❌ 没有活跃的Twitter账号")
        print("💡 请先登录账号: twscrape login_accounts")
        return False
    
    # 测试用户查找
    test_usernames = ["wstunnel", "twitter", "elonmusk"]
    
    for username in test_usernames:
        print(f"\n🔍 查找用户: @{username}")
        try:
            user = await api.user_by_login(username)
            if user:
                print(f"✅ 找到用户: @{user.username}")
                print(f"   显示名: {user.displayname}")
                print(f"   粉丝数: {user.followersCount:,}")
                print(f"   关注数: {user.friendsCount:,}")
                print(f"   推文数: {user.statusesCount:,}")
                print(f"   认证状态: {'✅ 已认证' if user.verified else '❌ 未认证'}")
                print(f"   创建时间: {user.created}")
                print(f"   位置: {user.location if user.location else '未设置'}")
                return True
            else:
                print(f"❌ 未找到用户: @{username}")
        except Exception as e:
            print(f"❌ 查找失败: {e}")
            print(f"   错误类型: {type(e).__name__}")
    
    return False

if __name__ == "__main__":
    asyncio.run(test_user_lookup())
