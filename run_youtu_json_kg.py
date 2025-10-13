#!/usr/bin/env python3
"""
专门针对 youtu-graphrag JSON 格式的完整运行脚本
"""

import os
import sys
import time
import argparse
import json
from pathlib import Path
from dotenv import load_dotenv

# 添加当前目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from youtu_json_converter import YoutuJSONConverter
except ImportError as e:
    print(f"❌ 导入错误: {e}")
    print("请确保 youtu_json_converter.py 文件在当前目录下")
    sys.exit(1)
from custom_graphgen import CustomGraphGen, create_custom_config
from graphgen.utils import logger, set_logger


def setup_environment(disable_quiz: bool = False):
    """设置环境"""
    # 加载环境变量
    load_dotenv()
    
    # 检查必需的环境变量
    required_vars = ['SYNTHESIZER_MODEL', 'SYNTHESIZER_API_KEY', 'SYNTHESIZER_BASE_URL']
    
    # 如果没有禁用 quiz，则需要 TRAINEE 相关变量
    if not disable_quiz:
        required_vars.extend(['TRAINEE_MODEL', 'TRAINEE_API_KEY', 'TRAINEE_BASE_URL'])
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ 缺少必需的环境变量: {', '.join(missing_vars)}")
        print("请在 .env 文件中设置这些变量")
        print("\n示例 .env 文件内容:")
        print("SYNTHESIZER_MODEL=gpt-4")
        print("SYNTHESIZER_API_KEY=your_api_key")
        print("SYNTHESIZER_BASE_URL=https://api.openai.com/v1")
        if not disable_quiz:
            print("TRAINEE_MODEL=gpt-3.5-turbo")
            print("TRAINEE_API_KEY=your_api_key")
            print("TRAINEE_BASE_URL=https://api.openai.com/v1")
        else:
            print("# TRAINEE 相关变量在禁用 quiz 时不是必需的")
        return False
    
    return True


def convert_youtu_json_kg(json_file: str, output_file: str, stats_file: str = None):
    """转换 youtu-graphrag JSON 知识图谱"""
    print("🔄 开始转换 youtu-graphrag JSON 知识图谱...")
    
    try:
        converter = YoutuJSONConverter()
        data = converter.load_youtu_json_data(json_file)
        converter.parse_youtu_data(data)
        converter.convert_to_graphgen_format()
        converter.validate_graph()
        converter.save_to_graphml(output_file)
        
        if stats_file:
            converter.export_statistics(stats_file)
        
        return True
    except Exception as e:
        print(f"❌ 转换失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def run_graphgen_with_youtu_json(
    json_file: str = None,
    external_graph_path: str = None,
    working_dir: str = "cache",
    generation_mode: str = "atomic",
    data_format: str = "Alpaca",
    quiz_samples: int = 5,
    disable_quiz: bool = False,
    max_depth: int = 3,
    max_extra_edges: int = 5,
    enable_search: bool = False,
    skip_convert: bool = False
):
    """使用 youtu-graphrag JSON 知识图谱运行 GraphGen"""
    
    print(f"🚀 开始使用 youtu-graphrag JSON 知识图谱生成数据...")
    
    # 确定图谱文件路径
    if not external_graph_path:
        external_graph_path = os.path.join(working_dir, "youtu_graph.graphml")
    
    # 如果需要转换且提供了 JSON 文件
    if not skip_convert and json_file:
        stats_file = os.path.join(working_dir, "youtu_graph_stats.json")
        if not convert_youtu_json_kg(json_file, external_graph_path, stats_file):
            return False
    
    # 检查图谱文件是否存在
    if not os.path.exists(external_graph_path):
        print(f"❌ 知识图谱文件不存在: {external_graph_path}")
        return False
    
    print(f"📁 使用知识图谱: {external_graph_path}")
    print(f"📁 工作目录: {working_dir}")
    print(f"🎯 生成模式: {generation_mode}")
    print(f"📄 数据格式: {data_format}")
    
    # 创建配置
    config = create_custom_config(
        external_graph_path=external_graph_path,
        generation_mode=generation_mode,
        data_format=data_format,
        quiz_samples=quiz_samples if not disable_quiz else 0,
        max_depth=max_depth,
        max_extra_edges=max_extra_edges
    )
    
    # 如果禁用 quiz 或 quiz_samples 为 0，则禁用问答测试
    if disable_quiz or quiz_samples == 0:
        config["quiz_and_judge"]["enabled"] = False
        print("⏭️  问答测试和判断已禁用")
    
    # 如果启用搜索，更新配置
    if enable_search:
        config["search"]["enabled"] = True
        config["search"]["search_types"] = ["google"]
    
    # 设置日志
    unique_id = int(time.time())
    log_file = os.path.join(working_dir, f"youtu_json_kg_{unique_id}_{generation_mode}.log")
    set_logger(log_file, if_stream=True)
    
    # 创建自定义 GraphGen 实例
    graph_gen = CustomGraphGen(
        external_graph_path=external_graph_path,
        working_dir=working_dir,
        unique_id=unique_id,
        skip_kg_building=True
    )
    
    try:
        # 步骤1: 初始化外部知识图谱
        print("📝 步骤1: 初始化外部知识图谱...")
        await graph_gen.insert(
            read_config=config["read"], 
            split_config=config["split"]
        )
        
        # 显示图谱摘要
        summary = graph_gen.get_graph_summary()
        print(f"\n📊 知识图谱摘要:")
        print(f"   - 节点数: {summary['nodes']}")
        print(f"   - 边数: {summary['edges']}")
        print(f"   - 图密度: {summary['density']:.4f}")
        print(f"   - 连通组件: {summary.get('connected_components', 'N/A')}")
        
        if 'node_types' in summary:
            print(f"   - 节点类型分布:")
            for node_type, count in sorted(summary['node_types'].items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"     * {node_type}: {count}")
        
        # 步骤2: 可选的搜索增强
        if config["search"]["enabled"]:
            print("🔍 步骤2: 搜索增强...")
            await graph_gen.search(search_config=config["search"])
        else:
            print("⏭️  步骤2: 跳过搜索增强")
        
        # 步骤3: 问答测试和判断
        if config["quiz_and_judge"]["enabled"]:
            print("🧠 步骤3: 问答测试和判断...")
            await graph_gen.quiz_and_judge(quiz_and_judge_config=config["quiz_and_judge"])
        else:
            print("⏭️  步骤3: 跳过问答测试和判断（已禁用）")
        
        # 步骤4: 生成数据
        print(f"⚡ 步骤4: 生成 {generation_mode} 数据...")
        await graph_gen.generate(
            partition_config=config["partition"],
            generate_config=config["generate"]
        )
        
        # 步骤5: 导出统计信息
        final_stats_file = os.path.join(working_dir, f"final_graph_statistics_{unique_id}.json")
        graph_gen.export_graph_statistics(final_stats_file)
        
        # 显示结果
        output_dir = os.path.join(working_dir, "data", "graphgen", str(unique_id))
        print(f"\n✅ 数据生成完成！")
        print(f"📁 输出目录: {output_dir}")
        print(f"📊 统计文件: {final_stats_file}")
        print(f"📝 日志文件: {log_file}")
        
        # 显示生成的文件
        if os.path.exists(output_dir):
            files = os.listdir(output_dir)
            if files:
                print(f"📄 生成的文件:")
                for file in files:
                    file_path = os.path.join(output_dir, file)
                    if os.path.isfile(file_path):
                        size = os.path.getsize(file_path)
                        print(f"   - {file} ({size} bytes)")
                        
                        # 如果是 JSON 文件，显示前几条数据
                        if file.endswith('.json') and size > 0:
                            try:
                                with open(file_path, 'r', encoding='utf-8') as f:
                                    data = json.load(f)
                                if isinstance(data, list) and len(data) > 0:
                                    print(f"     样本数量: {len(data)}")
                                    if len(data) > 0:
                                        sample = data[0]
                                        if isinstance(sample, dict):
                                            if 'instruction' in sample:
                                                print(f"     示例指令: {sample['instruction'][:100]}...")
                                            elif 'conversations' in sample:
                                                print(f"     对话轮数: {len(sample['conversations'])}")
                            except:
                                pass
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 生成过程中出现错误: {e}")
        print(f"❌ 生成失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    parser = argparse.ArgumentParser(description='使用 youtu-graphrag JSON 知识图谱运行 GraphGen')
    
    # 输入文件参数
    parser.add_argument('--json', help='youtu-graphrag JSON 文件路径')
    parser.add_argument('--external-graph', help='已转换的 GraphML 文件路径')
    
    # 输出参数
    parser.add_argument('--working-dir', default='cache', help='工作目录 (默认: cache)')
    parser.add_argument('--converted-graph', help='转换后的图谱文件路径')
    
    # 生成参数
    parser.add_argument('--mode', choices=['atomic', 'aggregated', 'multi_hop', 'cot'], 
                       default='atomic', help='生成模式 (默认: atomic)')
    parser.add_argument('--format', choices=['Alpaca', 'Sharegpt', 'ChatML'], 
                       default='Alpaca', help='数据格式 (默认: Alpaca)')
    parser.add_argument('--quiz-samples', type=int, default=5, help='测试样本数量 (默认: 5, 设为 0 禁用)')
    parser.add_argument('--disable-quiz', action='store_true', help='禁用问答测试和判断步骤')
    parser.add_argument('--max-depth', type=int, default=3, help='最大遍历深度 (默认: 3)')
    parser.add_argument('--max-extra-edges', type=int, default=5, help='最大额外边数 (默认: 5)')
    parser.add_argument('--enable-search', action='store_true', help='启用搜索增强')
    
    # 控制参数
    parser.add_argument('--skip-convert', action='store_true', help='跳过转换步骤')
    
    args = parser.parse_args()
    
    # 检查环境
    if not setup_environment(disable_quiz=args.disable_quiz or args.quiz_samples == 0):
        return 1
    
    # 检查输入参数
    if not args.skip_convert and not args.json and not args.external_graph:
        print("❌ 请提供 --json 参数（youtu-graphrag JSON 文件）或 --external-graph 参数（已转换的 GraphML 文件）")
        return 1
    
    # 确定转换后的图谱路径
    if args.converted_graph:
        converted_graph_path = args.converted_graph
    else:
        converted_graph_path = os.path.join(args.working_dir, "youtu_graph.graphml")
    
    # 创建工作目录
    os.makedirs(args.working_dir, exist_ok=True)
    
    # 运行 GraphGen
    import asyncio
    success = asyncio.run(run_graphgen_with_youtu_json(
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
    ))
    
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())