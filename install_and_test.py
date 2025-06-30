#!/usr/bin/env python3
"""
XGet 技术验证自动安装和测试脚本
自动安装依赖并运行验证测试
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description=""):
    """运行命令并处理结果"""
    print(f"🔄 {description}")
    print(f"   命令: {command}")
    
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True,
            timeout=300  # 5分钟超时
        )
        
        if result.returncode == 0:
            print(f"✅ {description} - 成功")
            if result.stdout.strip():
                print(f"   输出: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ {description} - 失败")
            if result.stderr.strip():
                print(f"   错误: {result.stderr.strip()}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏰ {description} - 超时")
        return False
    except Exception as e:
        print(f"❌ {description} - 异常: {e}")
        return False

def check_python_version():
    """检查Python版本"""
    print("🐍 检查Python版本...")
    
    version = sys.version_info
    print(f"   当前版本: Python {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 9):
        print("❌ Python版本过低，需要Python 3.9或更高版本")
        return False
    
    print("✅ Python版本符合要求")
    return True

def install_dependencies():
    """安装依赖库"""
    print("\n📦 安装依赖库...")
    
    dependencies = [
        "twscrape",
        "httpx",
        "playwright",
        "aiohttp",
        "motor",
        "redis",
        "celery",
        "fastapi",
        "uvicorn",
        "pydantic"
    ]
    
    success_count = 0
    
    for dep in dependencies:
        if run_command(f"pip install {dep}", f"安装 {dep}"):
            success_count += 1
        else:
            print(f"⚠️  {dep} 安装失败，可能影响某些功能")
    
    print(f"\n📊 依赖安装结果: {success_count}/{len(dependencies)} 成功")
    
    # 安装Playwright浏览器
    if "playwright" in [dep for dep in dependencies[:3]]:  # 如果playwright安装成功
        print("\n🌐 安装Playwright浏览器...")
        run_command("playwright install chromium", "安装Chromium浏览器")
    
    return success_count >= len(dependencies) * 0.8  # 80%成功率

def setup_twscrape():
    """设置twscrape基本配置"""
    print("\n⚙️  设置twscrape...")
    
    # 检查twscrape是否可用
    if not run_command("python -c \"import twscrape; print('twscrape imported successfully')\"", "检查twscrape导入"):
        return False
    
    # 检查账号池
    if run_command("twscrape accounts", "检查账号池状态"):
        print("✅ twscrape基本配置完成")
        print("ℹ️  如需添加账号，请运行:")
        print("   twscrape add_account username password email email_password")
        print("   twscrape login_accounts")
        return True
    else:
        print("⚠️  twscrape配置可能有问题")
        return False

def run_verification_test():
    """运行验证测试"""
    print("\n🧪 运行验证测试...")
    
    # 检查测试脚本是否存在
    test_script = Path("test_twscrape.py")
    if not test_script.exists():
        print("❌ 测试脚本 test_twscrape.py 不存在")
        return False
    
    # 运行测试脚本
    return run_command("python test_twscrape.py", "执行twscrape验证测试")

def create_sample_config():
    """创建示例配置文件"""
    print("\n📝 创建示例配置文件...")
    
    config_content = """# XGet 项目配置示例
# 复制此文件为 .env 并填入实际值

# 数据库配置
MONGODB_URI=mongodb://localhost:27017/xget
REDIS_URL=redis://localhost:6379

# Twitter账号配置 (示例)
# TWITTER_USERNAME_1=your_username
# TWITTER_PASSWORD_1=your_password
# TWITTER_EMAIL_1=your_email
# TWITTER_EMAIL_PASSWORD_1=your_email_password

# 代理配置 (可选)
# PROXY_API_KEY=your_proxy_api_key
# PROXY_ENDPOINT=https://your-proxy-provider.com/api

# 日志配置
LOG_LEVEL=INFO
ENVIRONMENT=development

# API配置
API_HOST=0.0.0.0
API_PORT=8000
"""
    
    try:
        with open("config.env.example", "w", encoding="utf-8") as f:
            f.write(config_content)
        print("✅ 创建示例配置文件: config.env.example")
        return True
    except Exception as e:
        print(f"❌ 创建配置文件失败: {e}")
        return False

def create_requirements_file():
    """创建requirements.txt文件"""
    print("\n📋 创建requirements.txt文件...")
    
    requirements = """# XGet 项目依赖
twscrape>=1.7.0
httpx>=0.24.0
playwright>=1.35.0
aiohttp>=3.8.0
motor>=3.2.0
redis>=4.5.0
celery>=5.3.0
fastapi>=0.100.0
uvicorn>=0.22.0
pydantic>=2.0.0
pymongo>=4.4.0
python-multipart>=0.0.6
python-dotenv>=1.0.0
"""
    
    try:
        with open("requirements.txt", "w", encoding="utf-8") as f:
            f.write(requirements)
        print("✅ 创建requirements.txt文件")
        return True
    except Exception as e:
        print(f"❌ 创建requirements.txt失败: {e}")
        return False

def print_next_steps(verification_passed):
    """打印下一步操作指南"""
    print("\n" + "="*60)
    print("📋 验证完成 - 下一步操作指南")
    print("="*60)
    
    if verification_passed:
        print("🎉 恭喜！技术验证通过，可以开始XGet项目开发")
        print("\n✅ 建议的下一步操作:")
        print("1. 准备更多Twitter账号 (建议10-20个)")
        print("2. 配置代理IP服务 (可选但推荐)")
        print("3. 设置MongoDB和Redis数据库")
        print("4. 开始XGet项目开发")
        
        print("\n📚 有用的命令:")
        print("   # 添加Twitter账号")
        print("   twscrape add_account username password email email_password")
        print("   twscrape login_accounts")
        print("   ")
        print("   # 测试搜索功能")
        print("   python test_twscrape.py")
        
    else:
        print("⚠️  技术验证未完全通过，建议解决问题后再开始项目")
        print("\n🔧 可能需要的操作:")
        print("1. 检查网络连接")
        print("2. 添加有效的Twitter账号")
        print("3. 解决依赖安装问题")
        print("4. 查看详细错误信息")
        
        print("\n📖 参考文档:")
        print("   - setup_verification.md (详细验证指南)")
        print("   - XGet_simplified.md (项目实施方案)")
    
    print("\n💡 提示:")
    print("   - 使用测试账号，避免使用重要账号")
    print("   - 遵守Twitter服务条款")
    print("   - 合理控制请求频率")
    
    print("\n" + "="*60)

def main():
    """主函数"""
    print("🚀 XGet 技术验证自动安装程序")
    print("=" * 50)
    
    # 检查Python版本
    if not check_python_version():
        print("❌ 环境检查失败，请升级Python版本")
        return False
    
    # 安装依赖
    if not install_dependencies():
        print("❌ 依赖安装失败，请检查网络连接和pip配置")
        return False
    
    # 设置twscrape
    twscrape_ok = setup_twscrape()
    
    # 创建配置文件
    create_sample_config()
    create_requirements_file()
    
    # 运行验证测试
    verification_passed = False
    if twscrape_ok:
        verification_passed = run_verification_test()
    
    # 打印下一步指南
    print_next_steps(verification_passed)
    
    return verification_passed

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️  安装过程被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 安装过程中发生错误: {e}")
        sys.exit(1)
