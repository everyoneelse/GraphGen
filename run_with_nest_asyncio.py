#!/usr/bin/env python3
"""
使用 nest_asyncio 修复事件循环问题的运行脚本
"""

import os
import sys
import asyncio

# 首先应用 nest_asyncio 来解决事件循环嵌套问题
try:
    import nest_asyncio
    nest_asyncio.apply()
    print("✅ nest_asyncio 已应用")
except ImportError:
    print("❌ nest_asyncio 未安装，请运行: pip install nest_asyncio")
    sys.exit(1)

# 添加当前目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 现在可以安全地导入和运行异步代码
from run_youtu_json_kg import run_graphgen_with_youtu_json, setup_environment

async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='使用 nest_asyncio 修复的 youtu-graphrag 运行器')
    
    # 输入文件参数
    parser.add_argument('--json', help='youtu-graphrag JSON 文件路径')
    parser.add_argument('--external-graph', help='已转换的 GraphML 文件路径')
    
    # 输出参数
    parser.add_argument('--working-dir', default='cache', help='工作目录 (默认: cache)')
    
    # 生成参数
    parser.add_argument('--mode', choices=['atomic', 'aggregated', 'multi_hop', 'cot'], 
                       default='atomic', help='生成模式 (默认: atomic)')
    parser.add_argument('--format', choices=['Alpaca', 'Sharegpt', 'ChatML'], 
                       default='Alpaca', help='数据格式 (默认: Alpaca)')
    parser.add_argument('--quiz-samples', type=int, default=0, help='测试样本数量 (默认: 0 禁用)')
    parser.add_argument('--disable-quiz', action='store_true', help='禁用问答测试和判断步骤')
    parser.add_argument('--max-depth', type=int, default=3, help='最大遍历深度 (默认: 3)')
    parser.add_argument('--max-extra-edges', type=int, default=5, help='最大额外边数 (默认: 5)')
    parser.add_argument('--enable-search', action='store_true', help='启用搜索增强')
    
    # 控制参数
    parser.add_argument('--skip-convert', action='store_true', help='跳过转换步骤')
    
    args = parser.parse_args()
    
    print("🚀 使用 nest_asyncio 修复版本运行...")
    
    # 检查环境
    if not setup_environment(disable_quiz=args.disable_quiz or args.quiz_samples == 0):
        return 1
    
    # 检查输入参数
    if not args.skip_convert and not args.json and not args.external_graph:
        print("❌ 请提供 --json 参数（youtu-graphrag JSON 文件）或 --external-graph 参数（已转换的 GraphML 文件）")
        return 1
    
    # 确定转换后的图谱路径
    converted_graph_path = os.path.join(args.working_dir, "youtu_graph.graphml")
    
    # 创建工作目录
    os.makedirs(args.working_dir, exist_ok=True)
    
    # 运行 GraphGen
    success = await run_graphgen_with_youtu_json(
        json_file=args.json,
        external_graph_path=args.external_graph or converted_graph_path,
        working_dir=args.working_dir,
        generation_mode=args.mode,
        data_format=args.format,
        quiz_samples=args.quiz_samples,
        disable_quiz=args.disable_quiz,
        max_depth=args.max_depth,
        max_extra_edges=args.max_extra_edges,
        enable_search=args.enable_search,
        skip_convert=args.skip_convert
    )
    
    return 0 if success else 1

if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(result)
    except Exception as e:
        print(f"❌ 运行失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)