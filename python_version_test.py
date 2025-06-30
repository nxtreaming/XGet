#!/usr/bin/env python3
"""
Python版本和依赖验证脚本
验证Python 3.12环境是否满足XGet项目需求
"""

import sys
import subprocess
import importlib

def check_python_version():
    """检查Python版本"""
    print("🔍 检查Python版本...")
    version = sys.version_info
    print(f"当前Python版本: {version.major}.{version.minor}.{version.micro}")
    
    if version.major == 3 and version.minor >= 9:
        print("✅ Python版本满足要求 (>= 3.9)")
        return True
    else:
        print("❌ Python版本不满足要求，需要Python 3.9或更高版本")
        return False

def check_dependencies():
    """检查必需的依赖"""
    print("\n🔍 检查必需的依赖...")
    required_packages = [
        'twscrape',
        'httpx', 
        'playwright'
    ]
    
    optional_packages = [
        'aiohttp',
        'motor',
        'redis',
        'celery',
        'fastapi'
    ]
    
    success_count = 0
    
    # 检查必需依赖
    print("\n必需依赖:")
    for package in required_packages:
        try:
            importlib.import_module(package)
            print(f"✅ {package} - 已安装")
            success_count += 1
        except ImportError:
            print(f"❌ {package} - 未安装")
    
    # 检查可选依赖
    print("\n可选依赖:")
    optional_count = 0
    for package in optional_packages:
        try:
            importlib.import_module(package)
            print(f"✅ {package} - 已安装")
            optional_count += 1
        except ImportError:
            print(f"⚠️  {package} - 未安装 (可选)")
    
    print(f"\n📊 依赖检查结果:")
    print(f"   必需依赖: {success_count}/{len(required_packages)} 已安装")
    print(f"   可选依赖: {optional_count}/{len(optional_packages)} 已安装")
    
    return success_count == len(required_packages)

def test_twscrape_basic():
    """测试twscrape基本功能"""
    print("\n🔍 测试twscrape基本功能...")
    try:
        from twscrape import API
        api = API()
        print("✅ twscrape API对象创建成功")
        return True
    except Exception as e:
        print(f"❌ twscrape测试失败: {e}")
        return False

def main():
    """主函数"""
    print("🚀 XGet项目Python环境验证")
    print("=" * 50)
    
    # 检查Python版本
    version_ok = check_python_version()
    
    # 检查依赖
    deps_ok = check_dependencies()
    
    # 测试twscrape
    twscrape_ok = test_twscrape_basic()
    
    # 总结
    print("\n" + "=" * 50)
    print("📋 验证结果总结:")
    
    if version_ok and deps_ok and twscrape_ok:
        print("🎉 所有检查通过！")
        print("✅ Python 3.12环境已准备就绪")
        print("✅ 可以开始XGet项目开发")
        print("\n💡 下一步建议:")
        print("   1. 激活虚拟环境: source venv_py312/bin/activate")
        print("   2. 运行完整验证: python test_twscrape.py")
        print("   3. 开始项目开发")
    else:
        print("⚠️  部分检查未通过")
        if not version_ok:
            print("   - 需要升级Python版本")
        if not deps_ok:
            print("   - 需要安装缺失的依赖")
        if not twscrape_ok:
            print("   - twscrape配置有问题")
        
        print("\n🔧 解决方案:")
        print("   1. 确保使用Python 3.12虚拟环境")
        print("   2. 安装缺失的依赖: pip install twscrape httpx playwright")
        print("   3. 检查网络连接和防火墙设置")

if __name__ == "__main__":
    main()
