#!/bin/bash
# XGet项目Python 3.12环境激活脚本

echo "🚀 激活Python 3.12虚拟环境..."
source venv_py312/bin/activate

echo "✅ Python 3.12环境已激活"
echo "📍 当前Python版本: $(python --version)"
echo "📍 当前pip版本: $(pip --version)"
echo ""
echo "💡 常用命令:"
echo "   python --version          # 查看Python版本"
echo "   pip list                  # 查看已安装的包"
echo "   python python_version_test.py  # 运行环境验证"
echo "   python test_twscrape.py   # 运行twscrape验证"
echo "   deactivate                # 退出虚拟环境"
echo ""
echo "🎯 现在可以开始XGet项目开发了！"
