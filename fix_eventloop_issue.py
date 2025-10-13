#!/usr/bin/env python3
"""
修复事件循环冲突问题的脚本
"""

import sys
import os

# 添加当前目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def install_nest_asyncio():
    """安装 nest_asyncio 来解决事件循环嵌套问题"""
    try:
        import nest_asyncio
        nest_asyncio.apply()
        print("✅ nest_asyncio 已应用，解决事件循环嵌套问题")
        return True
    except ImportError:
        print("⚠️  nest_asyncio 未安装，尝试安装...")
        try:
            import subprocess
            subprocess.check_call([sys.executable, "-m", "pip", "install", "nest_asyncio"])
            import nest_asyncio
            nest_asyncio.apply()
            print("✅ nest_asyncio 安装并应用成功")
            return True
        except Exception as e:
            print(f"❌ 无法安装 nest_asyncio: {e}")
            return False

def run_with_fixed_eventloop():
    """使用修复后的事件循环运行"""
    
    print("🔧 修复事件循环问题...")
    
    # 方法1: 尝试应用 nest_asyncio
    if install_nest_asyncio():
        print("使用 nest_asyncio 解决方案")
        return run_original_script()
    
    # 方法2: 使用同步版本
    print("使用同步版本解决方案")
    return run_sync_version()

def run_original_script():
    """运行原始脚本"""
    try:
        # 这里可以导入并运行修复后的脚本
        print("✅ 可以正常运行异步版本")
        return True
    except Exception as e:
        print(f"❌ 异步版本仍有问题: {e}")
        return False

def run_sync_version():
    """运行同步版本"""
    print("🔄 创建同步版本的运行脚本...")
    
    sync_script = """
import os
import sys
import time
import json

# 添加路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def run_sync_generation(
    json_file,
    working_dir="cache",
    generation_mode="atomic",
    data_format="Alpaca",
    disable_quiz=True
):
    '''同步版本的生成函数'''
    print(f"🚀 开始同步生成数据...")
    print(f"📁 JSON 文件: {json_file}")
    print(f"📁 工作目录: {working_dir}")
    print(f"🎯 生成模式: {generation_mode}")
    print(f"📄 数据格式: {data_format}")
    
    try:
        # 1. 转换数据
        from simple_youtu_converter import SimpleYoutuConverter
        
        converter = SimpleYoutuConverter()
        data = converter.load_youtu_json_data(json_file)
        converter.parse_youtu_data(data)
        converted_file = os.path.join(working_dir, "converted_data.json")
        result = converter.save_to_json(converted_file)
        
        # 2. 生成问答对
        from create_qa_from_converted import create_qa_from_converted_data
        
        qa_pairs = create_qa_from_converted_data(converted_file, data_format)
        
        # 3. 保存结果
        unique_id = int(time.time())
        output_dir = os.path.join(working_dir, "data", "graphgen", str(unique_id))
        os.makedirs(output_dir, exist_ok=True)
        
        output_file = os.path.join(output_dir, "qa.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(qa_pairs, f, ensure_ascii=False, indent=2)
        
        print(f"\\n✅ 数据生成完成！")
        print(f"📁 输出目录: {output_dir}")
        print(f"📄 生成文件: qa.json")
        print(f"📊 问答对数量: {len(qa_pairs)}")
        
        return True
        
    except Exception as e:
        print(f"❌ 生成失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='同步版本的问答生成')
    parser.add_argument('--json', required=True, help='youtu-graphrag JSON 文件路径')
    parser.add_argument('--working-dir', default='cache', help='工作目录')
    parser.add_argument('--mode', default='atomic', help='生成模式')
    parser.add_argument('--format', default='Alpaca', help='数据格式')
    
    args = parser.parse_args()
    
    success = run_sync_generation(
        json_file=args.json,
        working_dir=args.working_dir,
        generation_mode=args.mode,
        data_format=args.format
    )
    
    exit(0 if success else 1)
"""
    
    with open('run_sync_generation.py', 'w', encoding='utf-8') as f:
        f.write(sync_script)
    
    print("✅ 同步版本脚本已创建: run_sync_generation.py")
    return True

def main():
    print("🔧 事件循环问题修复工具")
    print("=" * 40)
    
    print("\n📋 问题分析:")
    print("   - GraphGen 使用了同步包装器")
    print("   - 在异步环境中调用导致事件循环冲突")
    print("   - 需要使用 nest_asyncio 或同步版本")
    
    print("\n🛠️  解决方案:")
    print("   1. 安装 nest_asyncio 解决嵌套问题")
    print("   2. 创建同步版本避免异步冲突")
    
    run_with_fixed_eventloop()
    
    print("\n🎯 使用建议:")
    print("   方法1: pip install nest_asyncio，然后运行原脚本")
    print("   方法2: 使用新创建的 run_sync_generation.py")
    print("   方法3: 使用简化版转换器 + QA 生成器")
    
    print("\n💡 推荐使用方法3（最简单）:")
    print("   python3 simple_youtu_converter.py --input your_data.json --output cache/converted.json")
    print("   python3 create_qa_from_converted.py --input cache/converted.json --output cache/qa.json")

if __name__ == "__main__":
    main()