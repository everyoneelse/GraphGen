#!/usr/bin/env python3
"""
使用外部知识图谱运行 GraphGen 的完整示例脚本
"""

import os
import sys
import time
import argparse
import yaml
from pathlib import Path
from dotenv import load_dotenv

# 添加当前目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from youtu_graphrag_converter import YoutuGraphRAGConverter
from custom_graphgen import CustomGraphGen, create_custom_config
from graphgen.utils import logger, set_logger


def setup_environment():
    """设置环境"""
    # 加载环境变量
    load_dotenv()
    
    # 检查必需的环境变量
    required_vars = [
        'SYNTHESIZER_MODEL', 'SYNTHESIZER_API_KEY', 'SYNTHESIZER_BASE_URL',
        'TRAINEE_MODEL', 'TRAINEE_API_KEY', 'TRAINEE_BASE_URL'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ 缺少必需的环境变量: {', '.join(missing_vars)}")
        print("请在 .env 文件中设置这些变量")
        return False
    
    return True


def convert_youtu_graphrag(entities_file: str, relationships_file: str, output_file: str):
    """转换 youtu-graphrag 知识图谱"""
    print("🔄 开始转换 youtu-graphrag 知识图谱...")
    
    try:
        converter = YoutuGraphRAGConverter()
        entities_df, relationships_df = converter.load_youtu_graphrag_data(
            entities_file, relationships_file
        )
        converter.convert_to_graphgen_format(entities_df, relationships_df)
        converter.validate_graph()
        converter.save_to_graphml(output_file)
        return True
    except Exception as e:
        print(f"❌ 转换失败: {e}")
        return False


async def run_graphgen_with_external_kg(
    external_graph_path: str,
    working_dir: str,
    generation_mode: str = "atomic",
    data_format: str = "Alpaca",
    quiz_samples: int = 5,
    max_depth: int = 3,
    max_extra_edges: int = 5,
    enable_search: bool = False
):
    """使用外部知识图谱运行 GraphGen"""
    
    print(f"🚀 开始使用外部知识图谱生成数据...")
    print(f"📁 外部图谱路径: {external_graph_path}")
    print(f"📁 工作目录: {working_dir}")
    print(f"🎯 生成模式: {generation_mode}")
    print(f"📄 数据格式: {data_format}")
    
    # 创建配置
    config = create_custom_config(
        external_graph_path=external_graph_path,
        generation_mode=generation_mode,
        data_format=data_format,
        quiz_samples=quiz_samples,
        max_depth=max_depth,
        max_extra_edges=max_extra_edges,
        no_trainee_mode=False  # 这个脚本使用完整的trainee模式
    )
    
    # 如果启用搜索，更新配置
    if enable_search:
        config["search"]["enabled"] = True
        config["search"]["search_types"] = ["google"]  # 可以根据需要调整
    
    # 设置日志
    unique_id = int(time.time())
    log_file = os.path.join(working_dir, f"external_kg_{unique_id}_{generation_mode}.log")
    set_logger(log_file, if_stream=True)
    
    # 创建自定义 GraphGen 实例
    graph_gen = CustomGraphGen(
        external_graph_path=external_graph_path,
        working_dir=working_dir,
        unique_id=unique_id,
        skip_kg_building=True
    )
    
    try:
        # 步骤1: 插入（跳过知识图谱构建）
        print("📝 步骤1: 初始化外部知识图谱...")
        await graph_gen.insert(
            read_config=config["read"], 
            split_config=config["split"]
        )
        
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
            print("⏭️  步骤3: 跳过问答测试")
        
        # 步骤4: 生成数据
        print(f"⚡ 步骤4: 生成 {generation_mode} 数据...")
        await graph_gen.generate(
            partition_config=config["partition"],
            generate_config=config["generate"]
        )
        
        # 步骤5: 导出统计信息
        stats_file = os.path.join(working_dir, f"graph_statistics_{unique_id}.json")
        graph_gen.export_graph_statistics(stats_file)
        
        # 显示结果
        output_dir = os.path.join(working_dir, "data", "graphgen", str(unique_id))
        print(f"\n✅ 数据生成完成！")
        print(f"📁 输出目录: {output_dir}")
        print(f"📊 统计文件: {stats_file}")
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
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 生成过程中出现错误: {e}")
        print(f"❌ 生成失败: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description='使用外部知识图谱运行 GraphGen')
    
    # 输入文件参数
    parser.add_argument('--entities', help='youtu-graphrag 实体文件路径')
    parser.add_argument('--relationships', help='youtu-graphrag 关系文件路径')
    parser.add_argument('--external-graph', help='已转换的外部知识图谱 GraphML 文件路径')
    
    # 输出参数
    parser.add_argument('--working-dir', default='cache', help='工作目录 (默认: cache)')
    parser.add_argument('--converted-graph', default='cache/external_graph.graphml', 
                       help='转换后的图谱文件路径 (默认: cache/external_graph.graphml)')
    
    # 生成参数
    parser.add_argument('--mode', choices=['atomic', 'aggregated', 'multi_hop', 'cot'], 
                       default='atomic', help='生成模式 (默认: atomic)')
    parser.add_argument('--format', choices=['Alpaca', 'Sharegpt', 'ChatML'], 
                       default='Alpaca', help='数据格式 (默认: Alpaca)')
    parser.add_argument('--quiz-samples', type=int, default=5, help='测试样本数量 (默认: 5)')
    parser.add_argument('--max-depth', type=int, default=3, help='最大遍历深度 (默认: 3)')
    parser.add_argument('--max-extra-edges', type=int, default=5, help='最大额外边数 (默认: 5)')
    parser.add_argument('--enable-search', action='store_true', help='启用搜索增强')
    
    # 控制参数
    parser.add_argument('--skip-convert', action='store_true', help='跳过转换步骤，直接使用现有的 GraphML 文件')
    
    args = parser.parse_args()
    
    # 检查环境
    if not setup_environment():
        return 1
    
    # 确定外部图谱路径
    external_graph_path = args.external_graph or args.converted_graph
    
    # 如果没有跳过转换且提供了原始文件，则进行转换
    if not args.skip_convert and args.entities and args.relationships:
        if not convert_youtu_graphrag(args.entities, args.relationships, external_graph_path):
            return 1
    
    # 检查外部图谱文件是否存在
    if not os.path.exists(external_graph_path):
        print(f"❌ 外部知识图谱文件不存在: {external_graph_path}")
        if not args.entities or not args.relationships:
            print("请提供 --entities 和 --relationships 参数来转换原始文件")
            print("或者使用 --external-graph 参数指定已存在的 GraphML 文件")
        return 1
    
    # 创建工作目录
    os.makedirs(args.working_dir, exist_ok=True)
    
    # 运行 GraphGen
    import asyncio
    success = asyncio.run(run_graphgen_with_external_kg(
        external_graph_path=external_graph_path,
        working_dir=args.working_dir,
        generation_mode=args.mode,
        data_format=args.format,
        quiz_samples=args.quiz_samples,
        max_depth=args.max_depth,
        max_extra_edges=args.max_extra_edges,
        enable_search=args.enable_search
    ))
    
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())