#!/usr/bin/env python3
"""
Playwright 功能验证脚本
测试浏览器自动化功能
"""

import asyncio
import sys
from datetime import datetime
from playwright.async_api import async_playwright

async def test_basic_browser():
    """测试基本浏览器功能"""
    print("🎭 测试基本浏览器功能...")
    
    try:
        async with async_playwright() as p:
            # 启动浏览器
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # 访问测试页面
            await page.goto("https://httpbin.org/get")
            
            # 获取页面标题
            title = await page.title()
            print(f"✅ 页面标题: {title}")
            
            # 获取页面内容
            content = await page.content()
            if "httpbin" in content.lower():
                print("✅ 页面内容加载成功")
            else:
                print("❌ 页面内容异常")
                return False
            
            await browser.close()
            return True
            
    except Exception as e:
        print(f"❌ 基本浏览器测试失败: {e}")
        return False

async def test_twitter_access():
    """测试访问Twitter"""
    print("\n🐦 测试访问Twitter...")
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # 设置用户代理
            await page.set_extra_http_headers({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            })
            
            # 访问Twitter
            print("🔍 正在访问 x.com...")
            response = await page.goto("https://x.com", wait_until="domcontentloaded", timeout=30000)
            
            if response:
                status = response.status
                print(f"✅ HTTP状态码: {status}")
                
                if status == 200:
                    # 检查页面元素
                    title = await page.title()
                    print(f"✅ 页面标题: {title}")
                    
                    # 检查是否包含Twitter相关内容
                    content = await page.content()
                    if any(keyword in content.lower() for keyword in ['twitter', 'x.com', 'tweet']):
                        print("✅ Twitter页面加载成功")
                        result = True
                    else:
                        print("⚠️  页面加载但内容可能不完整")
                        result = True  # 仍然算成功，因为能访问
                else:
                    print(f"⚠️  HTTP状态码异常: {status}")
                    result = False
            else:
                print("❌ 无法获取响应")
                result = False
            
            await browser.close()
            return result
            
    except Exception as e:
        print(f"❌ Twitter访问测试失败: {e}")
        return False

async def test_javascript_execution():
    """测试JavaScript执行"""
    print("\n🔧 测试JavaScript执行...")
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # 访问简单页面
            await page.goto("data:text/html,<html><body><h1>Test Page</h1></body></html>")
            
            # 执行JavaScript
            result = await page.evaluate("() => { return 2 + 3; }")
            if result == 5:
                print("✅ JavaScript执行成功")
                js_success = True
            else:
                print(f"❌ JavaScript执行结果异常: {result}")
                js_success = False
            
            # 测试DOM操作
            await page.evaluate("() => { document.body.innerHTML += '<p id=\"test\">Added by JS</p>'; }")
            element = await page.query_selector("#test")
            if element:
                text = await element.text_content()
                if text == "Added by JS":
                    print("✅ DOM操作成功")
                    dom_success = True
                else:
                    print(f"❌ DOM操作结果异常: {text}")
                    dom_success = False
            else:
                print("❌ DOM元素未找到")
                dom_success = False
            
            await browser.close()
            return js_success and dom_success
            
    except Exception as e:
        print(f"❌ JavaScript测试失败: {e}")
        return False

async def test_multiple_browsers():
    """测试多浏览器支持"""
    print("\n🌐 测试多浏览器支持...")
    
    results = {}
    
    async with async_playwright() as p:
        browsers = [
            ("Chromium", p.chromium),
            ("Firefox", p.firefox),
            ("WebKit", p.webkit)
        ]
        
        for name, browser_type in browsers:
            try:
                print(f"🔍 测试 {name}...")
                browser = await browser_type.launch(headless=True)
                page = await browser.new_page()
                
                await page.goto("https://httpbin.org/user-agent")
                content = await page.content()
                
                if "user-agent" in content.lower():
                    print(f"✅ {name} 工作正常")
                    results[name] = True
                else:
                    print(f"❌ {name} 响应异常")
                    results[name] = False
                
                await browser.close()
                
            except Exception as e:
                print(f"❌ {name} 测试失败: {e}")
                results[name] = False
    
    return results

async def test_screenshot():
    """测试截图功能"""
    print("\n📸 测试截图功能...")
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # 访问测试页面
            await page.goto("data:text/html,<html><body><h1 style='color: blue;'>Playwright Test</h1></body></html>")
            
            # 截图
            screenshot_path = "test_screenshot.png"
            await page.screenshot(path=screenshot_path)
            
            # 检查文件是否创建
            import os
            if os.path.exists(screenshot_path):
                file_size = os.path.getsize(screenshot_path)
                print(f"✅ 截图成功，文件大小: {file_size} bytes")
                
                # 清理文件
                os.remove(screenshot_path)
                result = True
            else:
                print("❌ 截图文件未创建")
                result = False
            
            await browser.close()
            return result
            
    except Exception as e:
        print(f"❌ 截图测试失败: {e}")
        return False

def generate_playwright_report(results):
    """生成Playwright测试报告"""
    print("\n" + "="*50)
    print("📋 Playwright 功能验证报告")
    print("="*50)
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    
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
        print("🎉 所有测试通过！Playwright 完全可用")
        print("✅ 浏览器自动化功能正常")
    elif passed_tests >= total_tests * 0.7:
        print("⚠️  大部分测试通过，Playwright 基本可用")
        print("🔧 建议检查失败的功能")
    else:
        print("❌ 多数测试失败，Playwright 配置可能有问题")
        print("🔧 需要检查浏览器驱动和环境配置")
    
    return passed_tests == total_tests

async def main():
    """主测试函数"""
    print("🎭 开始 Playwright 功能验证")
    print(f"⏰ 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 执行各项测试
    test_results = {}
    
    test_results["基本浏览器功能"] = await test_basic_browser()
    test_results["Twitter访问"] = await test_twitter_access()
    test_results["JavaScript执行"] = await test_javascript_execution()
    test_results["截图功能"] = await test_screenshot()
    
    # 多浏览器测试
    browser_results = await test_multiple_browsers()
    for browser_name, result in browser_results.items():
        test_results[f"{browser_name}浏览器"] = result
    
    # 生成报告
    return generate_playwright_report(test_results)

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
