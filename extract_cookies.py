#!/usr/bin/env python3
"""
Twitter Cookies提取和导入工具
手动获取cookies并导入到twscrape
"""

import json
import asyncio
from twscrape import API

def print_cookie_extraction_guide():
    """打印cookies提取指南"""
    print("🍪 Twitter Cookies 提取指南")
    print("=" * 60)
    
    print("\n📋 步骤1: 在浏览器中登录Twitter")
    print("1. 打开Chrome/Firefox浏览器")
    print("2. 访问: https://x.com/login")
    print("3. 使用您的账号登录:")
    print("   用户名: wiretunnel")
    print("   密码: Fuck.xget.2048!@#$")
    print("4. 确保成功登录并可以正常浏览")
    
    print("\n📋 步骤2: 提取Cookies (Chrome方法)")
    print("1. 在x.com页面按F12打开开发者工具")
    print("2. 点击 'Application' 标签页")
    print("3. 在左侧找到 'Storage' -> 'Cookies' -> 'https://x.com'")
    print("4. 复制以下重要的cookies值:")
    print("   - auth_token")
    print("   - ct0")
    print("   - guest_id")
    print("   - personalization_id")
    print("   - twid")
    
    print("\n📋 步骤2: 提取Cookies (Firefox方法)")
    print("1. 在x.com页面按F12打开开发者工具")
    print("2. 点击 'Storage' 标签页")
    print("3. 在左侧找到 'Cookies' -> 'https://x.com'")
    print("4. 复制相同的cookies值")
    
    print("\n📋 步骤3: 格式化Cookies")
    print("将cookies格式化为以下JSON格式:")
    print("""
{
    "auth_token": "您的auth_token值",
    "ct0": "您的ct0值",
    "guest_id": "您的guest_id值",
    "personalization_id": "您的personalization_id值",
    "twid": "您的twid值"
}
    """)

def save_cookies_template():
    """保存cookies模板文件"""
    template = {
        "auth_token": "YOUR_AUTH_TOKEN_HERE",
        "ct0": "YOUR_CT0_HERE", 
        "guest_id": "YOUR_GUEST_ID_HERE",
        "personalization_id": "YOUR_PERSONALIZATION_ID_HERE",
        "twid": "YOUR_TWID_HERE"
    }
    
    with open("cookies_template.json", "w") as f:
        json.dump(template, f, indent=4)
    
    print("✅ 已创建 cookies_template.json 模板文件")
    print("💡 请编辑此文件，填入您从浏览器获取的真实cookies值")

async def import_cookies_to_account():
    """将cookies导入到twscrape账号"""
    print("\n🔄 导入cookies到twscrape账号...")
    
    # 检查cookies文件
    try:
        with open("cookies.json", "r") as f:
            cookies_data = json.load(f)
    except FileNotFoundError:
        print("❌ 未找到 cookies.json 文件")
        print("💡 请先创建cookies.json文件并填入真实的cookies值")
        return False
    except json.JSONDecodeError:
        print("❌ cookies.json 格式错误")
        return False
    
    # 验证必要的cookies
    required_cookies = ["auth_token", "ct0"]
    missing_cookies = [cookie for cookie in required_cookies if not cookies_data.get(cookie) or cookies_data[cookie] == f"YOUR_{cookie.upper()}_HERE"]
    
    if missing_cookies:
        print(f"❌ 缺少必要的cookies: {missing_cookies}")
        print("💡 请确保填入了真实的cookies值")
        return False
    
    # 导入到twscrape
    try:
        api = API()
        accounts = await api.pool.get_all()
        
        if not accounts:
            print("❌ 没有找到账号")
            return False
        
        account = accounts[0]
        print(f"📊 正在为账号 {account.username} 导入cookies...")
        
        # 构建cookies字典格式
        cookies_dict = {}
        for k, v in cookies_data.items():
            if v and not v.startswith("YOUR_"):
                cookies_dict[k] = v

        # 更新账号的cookies - 使用正确的格式
        account.cookies = cookies_dict

        # 保存账号
        await api.pool.save(account)
        
        # 设置为活跃
        await api.pool.set_active(account.username, True)
        
        print("✅ Cookies导入成功!")
        print("💡 现在可以测试功能了")
        
        return True
        
    except Exception as e:
        print(f"❌ 导入cookies失败: {e}")
        return False

async def test_cookies():
    """测试cookies是否有效"""
    print("\n🧪 测试cookies有效性...")
    
    api = API()
    
    try:
        # 测试用户查找
        print("👤 测试用户查找: @wstunnel")
        user = await api.user_by_login("wstunnel")
        
        if user:
            print(f"✅ 成功! 找到用户: @{user.username}")
            print(f"   显示名: {user.displayname}")
            print(f"   粉丝数: {user.followersCount:,}")
            return True
        else:
            print("❌ 未找到用户")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def main():
    """主函数"""
    print("🚀 Twitter Cookies 提取和导入工具")
    print("=" * 60)
    
    while True:
        print("\n请选择操作:")
        print("1. 查看cookies提取指南")
        print("2. 创建cookies模板文件")
        print("3. 导入cookies到twscrape")
        print("4. 测试cookies有效性")
        print("5. 退出")
        
        choice = input("\n请输入选择 (1-5): ").strip()
        
        if choice == "1":
            print_cookie_extraction_guide()
        elif choice == "2":
            save_cookies_template()
        elif choice == "3":
            result = asyncio.run(import_cookies_to_account())
            if result:
                print("\n🎉 导入成功! 可以继续测试功能")
        elif choice == "4":
            result = asyncio.run(test_cookies())
            if result:
                print("\n🎉 Cookies有效! twscrape可以正常工作")
            else:
                print("\n❌ Cookies可能已过期，请重新获取")
        elif choice == "5":
            print("👋 再见!")
            break
        else:
            print("❌ 无效选择，请重试")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  操作被用户中断")
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
