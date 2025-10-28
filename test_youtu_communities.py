#!/usr/bin/env python3
"""
测试 youtu-graphrag 社区信息提取和使用
"""

import json
import sys
from pathlib import Path

# 添加当前目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

from youtu_json_converter import YoutuJSONConverter


def test_community_extraction(json_file: str):
    """测试社区信息提取"""
    print("=" * 70)
    print("测试 Youtu-GraphRAG 社区信息提取")
    print("=" * 70)
    
    # 1. 加载数据
    print("\n📝 步骤 1: 加载和解析数据")
    converter = YoutuJSONConverter()
    
    try:
        data = converter.load_youtu_json_data(json_file)
        converter.parse_youtu_data(data)
    except FileNotFoundError:
        print(f"❌ 文件不存在: {json_file}")
        return False
    except Exception as e:
        print(f"❌ 加载失败: {e}")
        return False
    
    # 2. 检查社区信息
    print("\n📊 步骤 2: 检查社区信息")
    if not converter.community_nodes:
        print("⚠️  警告: 未发现社区节点")
        print("   这可能意味着:")
        print("   - JSON 文件中不包含 label='community' 的节点")
        print("   - youtu-graphrag 在生成时没有进行社区检测")
        print("\n   💡 提示: 将回退到使用 Leiden 算法进行社区检测")
        return False
    
    print(f"✅ 发现 {len(converter.community_nodes)} 个社区")
    
    # 3. 显示社区详情
    print("\n🏘️  步骤 3: 社区详情")
    for i, (comm_name, comm_data) in enumerate(converter.community_nodes.items()):
        if i >= 5:  # 只显示前5个
            print(f"\n   ... 还有 {len(converter.community_nodes) - 5} 个社区未显示")
            break
        
        print(f"\n   社区 {i+1}: {comm_name}")
        print(f"   描述: {comm_data['description'][:80]}...")
        print(f"   成员数: {len(comm_data['members'])}")
        print(f"   成员样例: {', '.join(comm_data['members'][:5])}")
        if len(comm_data['members']) > 5:
            print(f"              ... 还有 {len(comm_data['members']) - 5} 个成员")
    
    # 4. 获取社区字典
    print("\n🔄 步骤 4: 转换为社区字典格式")
    communities_dict = converter.get_communities_dict()
    print(f"✅ 社区字典包含 {len(communities_dict)} 个节点")
    print(f"   分布在 {len(set(communities_dict.values()))} 个社区中")
    
    # 显示社区大小分布
    from collections import Counter
    community_sizes = Counter(communities_dict.values())
    print("\n   社区大小分布:")
    for comm_id, size in sorted(community_sizes.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"     社区 {comm_id}: {size} 个成员")
    
    # 5. 测试导出功能
    print("\n💾 步骤 5: 测试导出功能")
    test_output = "test_communities_output.json"
    try:
        converter.export_communities(test_output)
        print(f"✅ 社区信息已导出到: {test_output}")
        
        # 验证导出的文件
        with open(test_output, 'r', encoding='utf-8') as f:
            exported_data = json.load(f)
        print(f"   验证: 导出了 {len(exported_data)} 个社区")
        
        # 清理测试文件
        import os
        os.remove(test_output)
        print(f"   清理: 已删除测试文件")
        
    except Exception as e:
        print(f"❌ 导出失败: {e}")
        return False
    
    # 6. 验证与图谱的兼容性
    print("\n🔍 步骤 6: 验证与图谱的兼容性")
    converter.convert_to_graphgen_format()
    
    graph_nodes = set(converter.graph.nodes())
    community_members = set(communities_dict.keys())
    
    print(f"   图谱节点数: {len(graph_nodes)}")
    print(f"   社区成员数: {len(community_members)}")
    
    # 检查匹配度
    matched = graph_nodes & community_members
    unmatched_in_community = community_members - graph_nodes
    unmatched_in_graph = graph_nodes - community_members
    
    match_rate = len(matched) / len(community_members) * 100 if community_members else 0
    print(f"\n   匹配率: {match_rate:.1f}%")
    print(f"   - 匹配的节点: {len(matched)}")
    print(f"   - 社区中但不在图谱的: {len(unmatched_in_community)}")
    print(f"   - 图谱中但不在社区的: {len(unmatched_in_graph)}")
    
    if unmatched_in_community and len(unmatched_in_community) <= 10:
        print(f"\n   ⚠️  未匹配的社区成员样例:")
        for member in list(unmatched_in_community)[:10]:
            print(f"      - {member}")
    
    # 7. 总结
    print("\n" + "=" * 70)
    print("📋 测试总结")
    print("=" * 70)
    
    if match_rate >= 90:
        print("✅ 社区信息质量优秀，可以直接用于 COT 生成")
    elif match_rate >= 70:
        print("⚠️  社区信息质量良好，但有部分不匹配")
        print("   建议: 可以使用，但可能需要调整 max_size 参数")
    else:
        print("❌ 社区信息质量较差，可能需要重新检测")
        print("   建议: 考虑使用 Leiden 算法重新检测社区")
    
    print(f"\n使用方法:")
    print(f"  python run_youtu_json_kg.py \\")
    print(f"    --json {json_file} \\")
    print(f"    --mode cot \\")
    print(f"    --disable-quiz")
    
    return True


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='测试 youtu-graphrag 社区信息提取')
    parser.add_argument('--json', required=True, help='youtu-graphrag JSON 文件路径')
    
    args = parser.parse_args()
    
    success = test_community_extraction(args.json)
    
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
