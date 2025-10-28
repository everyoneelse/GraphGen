#!/usr/bin/env python3
"""
测试 youtu-graphrag JSON 转换功能的脚本
"""

import os
import sys
import json
import asyncio
from pathlib import Path

# 添加当前目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from youtu_json_converter import YoutuJSONConverter
from custom_graphgen import CustomGraphGen, create_custom_config


def test_conversion():
    """测试转换功能"""
    print("🧪 开始测试 youtu-graphrag JSON 转换功能...")
    
    # 使用示例数据
    input_file = "example_youtu_data.json"
    output_file = "cache/test_youtu_graph.graphml"
    stats_file = "cache/test_youtu_stats.json"
    
    # 确保输出目录存在
    os.makedirs("cache", exist_ok=True)
    
    try:
        # 步骤1: 转换数据
        print("\n📝 步骤1: 转换知识图谱格式...")
        converter = YoutuJSONConverter()
        data = converter.load_youtu_json_data(input_file)
        converter.parse_youtu_data(data)
        converter.convert_to_graphgen_format()
        converter.validate_graph()
        converter.save_to_graphml(output_file)
        converter.export_statistics(stats_file)
        
        # 步骤2: 验证转换结果
        print("\n🔍 步骤2: 验证转换结果...")
        if os.path.exists(output_file):
            print(f"✅ GraphML 文件生成成功: {output_file}")
            file_size = os.path.getsize(output_file)
            print(f"   文件大小: {file_size} bytes")
        else:
            print(f"❌ GraphML 文件生成失败")
            return False
        
        if os.path.exists(stats_file):
            print(f"✅ 统计文件生成成功: {stats_file}")
            with open(stats_file, 'r', encoding='utf-8') as f:
                stats = json.load(f)
            print(f"   节点数: {stats['basic_info']['nodes']}")
            print(f"   边数: {stats['basic_info']['edges']}")
            print(f"   实体类型: {list(stats['entity_types'].keys())}")
        
        # 步骤3: 测试图谱加载
        print("\n📊 步骤3: 测试图谱加载...")
        test_graph_gen = CustomGraphGen(
            external_graph_path=output_file,
            working_dir="cache",
            skip_kg_building=True
        )
        
        summary = test_graph_gen.get_graph_summary()
        print(f"✅ 图谱加载成功:")
        print(f"   - 节点数: {summary['nodes']}")
        print(f"   - 边数: {summary['edges']}")
        print(f"   - 图密度: {summary['density']:.4f}")
        
        if 'node_types' in summary:
            print(f"   - 节点类型分布:")
            for node_type, count in summary['node_types'].items():
                print(f"     * {node_type}: {count}")
        
        print("\n✅ 转换测试完成！")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_qa_generation():
    """测试问答生成功能"""
    print("\n🤖 开始测试问答生成功能...")
    
    # 检查环境变量
    required_vars = ['SYNTHESIZER_MODEL', 'SYNTHESIZER_API_KEY', 'SYNTHESIZER_BASE_URL']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"⚠️  跳过问答生成测试，缺少环境变量: {', '.join(missing_vars)}")
        print("如需测试问答生成，请设置以下环境变量:")
        for var in missing_vars:
            print(f"   export {var}=your_value")
        return True
    
    try:
        # 使用转换后的图谱
        external_graph_path = "cache/test_youtu_graph.graphml"
        
        if not os.path.exists(external_graph_path):
            print(f"❌ 图谱文件不存在: {external_graph_path}")
            print("请先运行转换测试")
            return False
        
        # 创建配置（使用较小的参数进行快速测试）
        config = create_custom_config(
            external_graph_path=external_graph_path,
            generation_mode="atomic",
            data_format="Alpaca",
            quiz_samples=2,  # 减少样本数量以加快测试
            max_depth=2,     # 减少深度
            max_extra_edges=2,  # 减少边数
            no_trainee_mode=True  # 测试使用无trainee模式
        )
        
        # 创建 GraphGen 实例
        graph_gen = CustomGraphGen(
            external_graph_path=external_graph_path,
            working_dir="cache",
            unique_id=int(time.time()),
            skip_kg_building=True
        )
        
        print("📝 开始生成问答数据（测试模式）...")
        
        # 执行生成流程
        await graph_gen.insert(config["read"], config["split"])
        
        # 跳过问答测试步骤以加快测试
        config["quiz_and_judge"]["enabled"] = False
        
        await graph_gen.generate(config["partition"], config["generate"])
        
        # 检查生成结果
        output_dir = os.path.join("cache", "data", "graphgen", str(graph_gen.unique_id))
        if os.path.exists(output_dir):
            files = os.listdir(output_dir)
            if files:
                print(f"✅ 问答数据生成成功:")
                for file in files:
                    file_path = os.path.join(output_dir, file)
                    if os.path.isfile(file_path):
                        size = os.path.getsize(file_path)
                        print(f"   - {file} ({size} bytes)")
                        
                        # 显示生成的问答示例
                        if file.endswith('.json') and size > 0:
                            try:
                                with open(file_path, 'r', encoding='utf-8') as f:
                                    data = json.load(f)
                                if isinstance(data, list) and len(data) > 0:
                                    print(f"     生成了 {len(data)} 个问答对")
                                    sample = data[0]
                                    if 'instruction' in sample:
                                        print(f"     示例问题: {sample['instruction'][:100]}...")
                                        print(f"     示例答案: {sample.get('output', '')[:100]}...")
                            except:
                                pass
            else:
                print("⚠️  输出目录为空")
                return False
        else:
            print("❌ 输出目录不存在")
            return False
        
        print("\n✅ 问答生成测试完成！")
        return True
        
    except Exception as e:
        print(f"❌ 问答生成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("🚀 开始完整功能测试...")
    
    # 测试1: 转换功能
    if not test_conversion():
        print("❌ 转换测试失败，停止后续测试")
        return 1
    
    # 测试2: 问答生成功能
    import time
    success = asyncio.run(test_qa_generation())
    
    if success:
        print("\n🎉 所有测试通过！")
        print("\n📋 接下来你可以:")
        print("1. 使用你的实际 youtu-graphrag JSON 文件:")
        print("   python youtu_json_converter.py --input your_data.json --output cache/your_graph.graphml")
        print("\n2. 生成问答数据:")
        print("   python run_youtu_json_kg.py --json your_data.json --mode atomic --format Alpaca")
        print("\n3. 或者直接使用转换后的图谱:")
        print("   python run_youtu_json_kg.py --external-graph cache/your_graph.graphml --skip-convert")
        return 0
    else:
        print("\n❌ 部分测试失败")
        return 1


if __name__ == "__main__":
    import time
    exit(main())