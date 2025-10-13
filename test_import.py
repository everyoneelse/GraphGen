#!/usr/bin/env python3
"""
测试导入功能
"""

import sys
import os

print("🧪 测试导入功能")
print("=" * 30)

# 检查文件是否存在
files_to_check = [
    'youtu_json_converter.py',
    'custom_graphgen.py',
    'run_youtu_json_kg.py'
]

print("📁 检查文件存在性:")
for file in files_to_check:
    exists = os.path.exists(file)
    status = "✅" if exists else "❌"
    print(f"   {status} {file}")

print("\n🔍 检查类定义:")

# 检查 youtu_json_converter.py 中的类
try:
    with open('youtu_json_converter.py', 'r', encoding='utf-8') as f:
        content = f.read()
        if 'class YoutuJSONConverter:' in content:
            print("   ✅ YoutuJSONConverter 类定义存在")
        else:
            print("   ❌ YoutuJSONConverter 类定义不存在")
            # 查找实际的类名
            import re
            classes = re.findall(r'class\s+(\w+):', content)
            if classes:
                print(f"   📋 找到的类: {classes}")
except Exception as e:
    print(f"   ❌ 读取文件失败: {e}")

print("\n🔄 测试导入:")

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from youtu_json_converter import YoutuJSONConverter
    print("   ✅ YoutuJSONConverter 导入成功")
    
    # 测试实例化
    converter = YoutuJSONConverter()
    print("   ✅ YoutuJSONConverter 实例化成功")
    
except ImportError as e:
    print(f"   ❌ 导入失败: {e}")
except Exception as e:
    print(f"   ❌ 其他错误: {e}")

try:
    from custom_graphgen import CustomGraphGen
    print("   ✅ CustomGraphGen 导入成功")
except ImportError as e:
    print(f"   ❌ CustomGraphGen 导入失败: {e}")

print("\n🎯 结论:")
print("如果看到导入成功的消息，说明类定义正确")
print("如果看到导入失败，请检查:")
print("   1. 文件是否在当前目录")
print("   2. 文件中是否有语法错误")
print("   3. 依赖模块是否已安装")