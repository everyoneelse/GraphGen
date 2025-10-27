"""
集成调试器的示例脚本

展示如何将NodeEdgeDebugger集成到现有的graphgen流程中
"""

import sys
import os

# 方案1: 通过Monkey Patching的方式集成调试器（无需修改源代码）
def patch_split_kg_with_debugger():
    """
    通过monkey patching的方式给split_kg添加调试功能
    这种方式不需要修改源代码
    """
    from graphgen.operators.build_kg import split_kg
    from debug_node_edge_selection import NodeEdgeDebugger
    
    # 保存原始函数
    original_get_batches = split_kg.get_batches_with_strategy
    
    # 创建调试器实例
    debugger = NodeEdgeDebugger(output_dir="./debug_output")
    
    # 包装原始函数
    async def wrapped_get_batches(nodes, edges, graph_storage, traverse_strategy):
        # 记录图信息
        debugger.record_graph_info(nodes, edges)
        print("\n🔍 调试模式已启用，正在监控node和edge选取过程...")
        
        # 调用原始函数
        processing_batches = await original_get_batches(
            nodes, edges, graph_storage, traverse_strategy
        )
        
        # 记录每个batch
        for i, (batch_nodes, batch_edges) in enumerate(processing_batches):
            debugger.record_batch(i, batch_nodes, batch_edges, traverse_strategy)
        
        # 生成报告
        print("\n📊 生成调试报告...")
        stats = debugger.generate_report()
        
        return processing_batches
    
    # 替换原始函数
    split_kg.get_batches_with_strategy = wrapped_get_batches
    print("✅ 调试器已通过monkey patching方式集成")


# 方案2: 创建自定义的generate函数
def run_generate_with_debug(config_file: str, output_dir: str):
    """
    运行带调试功能的generate流程
    
    Args:
        config_file: 配置文件路径
        output_dir: 输出目录
    """
    import yaml
    from graphgen.graphgen import GraphGen
    from graphgen.utils import set_logger, logger
    import time
    
    # 首先集成调试器
    patch_split_kg_with_debugger()
    
    # 加载配置
    with open(config_file, 'r', encoding='utf-8') as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
    
    mode = config["generate"]["mode"]
    unique_id = int(time.time())
    
    output_path = os.path.join(output_dir, "data", "graphgen", f"{unique_id}")
    os.makedirs(output_path, exist_ok=True)
    
    set_logger(
        os.path.join(output_path, f"{unique_id}_{mode}.log"),
        if_stream=True,
    )
    
    logger.info("🐛 调试模式: 启动GraphGen with debug")
    
    # 创建GraphGen实例
    graph_gen = GraphGen(unique_id=unique_id, working_dir=output_dir)
    
    # 执行流程
    graph_gen.insert(read_config=config["read"], split_config=config["split"])
    graph_gen.search(search_config=config["search"])
    
    # 根据模式执行
    if mode in ["atomic", "aggregated", "multi_hop"]:
        if "quiz_and_judge" in config and config["quiz_and_judge"]["enabled"]:
            graph_gen.quiz_and_judge(quiz_and_judge_config=config["quiz_and_judge"])
        else:
            logger.warning("Quiz and Judge disabled, edge sampling fallback to random")
            config["partition"]["method_params"]["edge_sampling"] = "random"
    
    # 生成（这里会调用被patched的函数）
    graph_gen.generate(
        partition_config=config["partition"],
        generate_config=config["generate"],
    )
    
    logger.info("✅ GraphGen completed with debug info at %s", output_path)
    logger.info("📁 Debug reports saved to ./debug_output/")


# 方案3: 仅分析已有的batch数据（事后分析）
def analyze_existing_batch_data(batch_file: str):
    """
    分析已经保存的batch数据
    
    Args:
        batch_file: batch数据文件路径（JSON格式）
    """
    import json
    from debug_node_edge_selection import NodeEdgeDebugger
    
    print(f"📖 读取batch数据: {batch_file}")
    
    with open(batch_file, 'r', encoding='utf-8') as f:
        batch_data = json.load(f)
    
    debugger = NodeEdgeDebugger(output_dir="./analysis_output")
    
    # 手动构建数据
    all_nodes = set()
    all_edges = set()
    
    for i, batch in enumerate(batch_data):
        nodes = [{'node_id': nid} for nid in batch['node_ids']]
        edges = [(ep.split(' -> ')[0], ep.split(' -> ')[1], {}) 
                 for ep in batch['edge_pairs']]
        
        all_nodes.update(batch['node_ids'])
        all_edges.update([tuple(ep.split(' -> ')) for ep in batch['edge_pairs']])
        
        debugger.record_batch(i, nodes, edges)
    
    # 设置总数
    debugger.total_nodes = len(all_nodes)
    debugger.total_edges = len(all_edges)
    
    # 生成报告
    stats = debugger.generate_report()
    
    print(f"\n✅ 分析完成，报告保存在 ./analysis_output/")


# 使用示例
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Node/Edge选取调试工具集成脚本")
    parser.add_argument(
        "--mode",
        choices=["run", "analyze"],
        default="run",
        help="运行模式: run=运行带调试的generate, analyze=分析已有数据"
    )
    parser.add_argument(
        "--config",
        type=str,
        default="graphgen/configs/aggregated_config.yaml",
        help="配置文件路径 (run模式使用)"
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="./",
        help="输出目录 (run模式使用)"
    )
    parser.add_argument(
        "--batch_file",
        type=str,
        help="batch数据文件路径 (analyze模式使用)"
    )
    
    args = parser.parse_args()
    
    if args.mode == "run":
        print("=" * 80)
        print("启动调试模式运行GraphGen")
        print("=" * 80)
        run_generate_with_debug(args.config, args.output_dir)
        
    elif args.mode == "analyze":
        if not args.batch_file:
            print("❌ analyze模式需要提供 --batch_file 参数")
            sys.exit(1)
        
        print("=" * 80)
        print("分析已有batch数据")
        print("=" * 80)
        analyze_existing_batch_data(args.batch_file)
