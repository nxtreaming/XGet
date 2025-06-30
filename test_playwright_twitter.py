#!/usr/bin/env python3
"""
Playwright + Twitter 集成测试
测试浏览器自动化访问Twitter的能力
"""

import asyncio
from playwright.async_api import async_playwright

async def test_twitter_login_page():
    """测试Twitter登录页面访问"""
    print("🔍 测试Twitter登录页面访问...")
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            )
            page = await context.new_page()
            
            # 访问Twitter登录页面
            response = await page.goto("https://x.com/login", timeout=30000)
            
            if response and response.status == 200:
                print("✅ 成功访问Twitter登录页面")
                
                # 检查登录表单元素
                await page.wait_for_timeout(3000)  # 等待页面加载
                
                # 查找用户名输入框
                username_input = await page.query_selector('input[name="text"]')
                if username_input:
                    print("✅ 找到用户名输入框")
                else:
                    print("⚠️  未找到用户名输入框")
                
                # 检查页面标题
                title = await page.title()
                print(f"📄 页面标题: {title}")
                
                # 截图保存
                await page.screenshot(path="twitter_login_page.png")
                print("📸 已保存登录页面截图")
                
                result = True
            else:
                print(f"❌ 访问失败，状态码: {response.status if response else 'None'}")
                result = False
            
            await browser.close()
            return result
            
    except Exception as e:
        print(f"❌ Twitter登录页面测试失败: {e}")
        return False

async def test_twitter_public_page():
    """测试访问Twitter公开页面"""
    print("\n🔍 测试访问Twitter公开页面...")
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            )
            page = await context.new_page()
            
            # 访问Twitter主页
            response = await page.goto("https://x.com", timeout=30000)
            
            if response and response.status == 200:
                print("✅ 成功访问Twitter主页")
                
                # 等待页面加载
                await page.wait_for_timeout(5000)
                
                # 检查页面内容
                content = await page.content()
                
                # 查找Twitter相关元素
                if any(keyword in content.lower() for keyword in ['twitter', 'tweet', 'x.com']):
                    print("✅ 页面包含Twitter相关内容")
                else:
                    print("⚠️  页面内容可能不完整")
                
                # 查找登录按钮
                login_button = await page.query_selector('a[href="/login"]')
                if login_button:
                    print("✅ 找到登录按钮")
                else:
                    print("⚠️  未找到登录按钮")
                
                # 截图保存
                await page.screenshot(path="twitter_home_page.png")
                print("📸 已保存主页截图")
                
                result = True
            else:
                print(f"❌ 访问失败，状态码: {response.status if response else 'None'}")
                result = False
            
            await browser.close()
            return result
            
    except Exception as e:
        print(f"❌ Twitter主页测试失败: {e}")
        return False

async def test_twitter_search_page():
    """测试Twitter搜索页面"""
    print("\n🔍 测试Twitter搜索页面...")
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            )
            page = await context.new_page()
            
            # 访问Twitter搜索页面
            search_url = "https://x.com/search?q=python&src=typed_query"
            response = await page.goto(search_url, timeout=30000)
            
            if response and response.status == 200:
                print("✅ 成功访问Twitter搜索页面")
                
                # 等待页面加载
                await page.wait_for_timeout(5000)
                
                # 检查搜索结果
                content = await page.content()
                
                if "python" in content.lower():
                    print("✅ 搜索页面包含相关内容")
                else:
                    print("⚠️  搜索页面内容可能不完整")
                
                # 截图保存
                await page.screenshot(path="twitter_search_page.png")
                print("📸 已保存搜索页面截图")
                
                result = True
            else:
                print(f"❌ 访问失败，状态码: {response.status if response else 'None'}")
                result = False
            
            await browser.close()
            return result
            
    except Exception as e:
        print(f"❌ Twitter搜索页面测试失败: {e}")
        return False

async def test_cookies_extraction_demo():
    """演示cookies提取过程"""
    print("\n🍪 演示cookies提取过程...")
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            
            # 访问Twitter
            await page.goto("https://x.com", timeout=30000)
            await page.wait_for_timeout(3000)
            
            # 获取cookies
            cookies = await context.cookies()
            
            print(f"✅ 获取到 {len(cookies)} 个cookies")
            
            # 显示重要的cookies
            important_cookies = ['auth_token', 'ct0', 'guest_id', 'personalization_id']
            found_cookies = []
            
            for cookie in cookies:
                if cookie['name'] in important_cookies:
                    found_cookies.append(cookie['name'])
                    print(f"  🔑 {cookie['name']}: {cookie['value'][:20]}...")
            
            if found_cookies:
                print(f"✅ 找到重要cookies: {', '.join(found_cookies)}")
            else:
                print("⚠️  未找到重要的认证cookies")
            
            await browser.close()
            return len(found_cookies) > 0
            
    except Exception as e:
        print(f"❌ Cookies提取演示失败: {e}")
        return False

async def main():
    """主测试函数"""
    print("🎭 开始 Playwright + Twitter 集成测试")
    print("="*50)
    
    # 执行各项测试
    results = {}
    
    results["Twitter登录页面"] = await test_twitter_login_page()
    results["Twitter主页"] = await test_twitter_public_page()
    results["Twitter搜索页面"] = await test_twitter_search_page()
    results["Cookies提取演示"] = await test_cookies_extraction_demo()
    
    # 生成报告
    print("\n" + "="*50)
    print("📋 Playwright + Twitter 集成测试报告")
    print("="*50)
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    
    print(f"总测试数: {total_tests}")
    print(f"通过测试: {passed_tests}")
    print(f"成功率: {passed_tests/total_tests*100:.1f}%")
    
    print("\n详细结果:")
    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {test_name}: {status}")
    
    print("\n" + "="*50)
    
    if passed_tests == total_tests:
        print("🎉 所有测试通过！")
        print("✅ Playwright可以完美配合Twitter使用")
        print("🔧 可以用于高级浏览器自动化任务")
    elif passed_tests >= total_tests * 0.7:
        print("⚠️  大部分测试通过")
        print("🔧 Playwright基本可用，建议检查失败项")
    else:
        print("❌ 多数测试失败")
        print("🔧 需要检查网络连接和Twitter访问权限")
    
    # 清理截图文件
    import os
    for filename in ["twitter_login_page.png", "twitter_home_page.png", "twitter_search_page.png"]:
        if os.path.exists(filename):
            os.remove(filename)
    
    return passed_tests == total_tests

if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        print(f"\n🎯 测试完成，结果: {'成功' if result else '部分失败'}")
    except KeyboardInterrupt:
        print("\n⚠️  测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
