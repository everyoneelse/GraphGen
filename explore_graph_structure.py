#!/usr/bin/env python3
"""
探索 graph.json 的实际数据结构
找出 community 信息的存储方式
"""

import json
import sys


def explore_graph_structure(json_file: str):
    """探索 graph.json 的数据结构"""
    print("=" * 70)
    print("探索 Graph.json 数据结构")
    print("=" * 70)
    
    # 1. 加载文件
    print(f"\n📝 加载文件: {json_file}")
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"✅ 成功加载")
    except Exception as e:
        print(f"❌ 加载失败: {e}")
        return False
    
    # 2. 检查数据类型
    print(f"\n📊 数据类型: {type(data)}")
    
    if isinstance(data, list):
        print(f"   - 列表长度: {len(data)}")
        if len(data) > 0:
            print(f"   - 第一个元素类型: {type(data[0])}")
    elif isinstance(data, dict):
        print(f"   - 字典键: {list(data.keys())[:10]}")
    
    # 3. 显示前几条记录的完整结构
    print("\n📝 前3条记录的完整结构:")
    
    if isinstance(data, list):
        for i, item in enumerate(data[:3]):
            print(f"\n{'='*60}")
            print(f"记录 {i+1}:")
            print(f"{'='*60}")
            print(json.dumps(item, ensure_ascii=False, indent=2))
    elif isinstance(data, dict):
        print(json.dumps(data, ensure_ascii=False, indent=2)[:2000])
        print("\n... (截断)")
    
    # 4. 查找包含 "community" 关键字的记录
    print("\n" + "="*70)
    print("🔍 查找包含 'community' 关键字的记录")
    print("="*70)
    
    community_records = []
    
    if isinstance(data, list):
        for i, item in enumerate(data):
            # 转为字符串搜索
            item_str = json.dumps(item, ensure_ascii=False).lower()
            if 'community' in item_str or '社区' in item_str:
                community_records.append((i, item))
                if len(community_records) <= 3:
                    print(f"\n发现包含 community 的记录 #{i+1}:")
                    print(json.dumps(item, ensure_ascii=False, indent=2))
    
    if community_records:
        print(f"\n✅ 总共发现 {len(community_records)} 条包含 'community' 或 '社区' 的记录")
    else:
        print("\n❌ 没有发现包含 'community' 或 '社区' 的记录")
        print("\n💡 可能的情况:")
        print("   1. community 信息使用了不同的字段名")
        print("   2. community 信息在单独的文件中")
        print("   3. 需要查看原始的 youtu-graphrag 输出目录")
    
    # 5. 分析所有可能的标签类型
    print("\n" + "="*70)
    print("📊 分析所有标签类型")
    print("="*70)
    
    all_labels = set()
    label_examples = {}
    
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                # 检查所有节点的 label
                for key in ['start_node', 'end_node', 'source', 'target', 'node']:
                    if key in item and isinstance(item[key], dict):
                        label = item[key].get('label', '')
                        if label:
                            all_labels.add(label)
                            if label not in label_examples:
                                label_examples[label] = item
    
    if all_labels:
        print("\n发现的所有 label 类型:")
        for label in sorted(all_labels):
            print(f"   - {label}")
        
        print("\n每种 label 的示例:")
        for label, example in list(label_examples.items())[:5]:
            print(f"\n   {label}:")
            print(f"   {json.dumps(example, ensure_ascii=False, indent=2)[:300]}...")
    
    # 6. 询问用户
    print("\n" + "="*70)
    print("❓ 请提供更多信息")
    print("="*70)
    print("\n请告诉我:")
    print("1. 你的 graph.json 中 community 信息是如何存储的？")
    print("2. 是否有单独的文件存储 community 信息？")
    print("3. 可以提供一个包含 community 的记录示例吗？")
    print("\n或者直接把包含 community 信息的一条 JSON 记录复制给我！")
    
    return True


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='探索 graph.json 数据结构')
    parser.add_argument('--json', required=True, help='graph.json 文件路径')
    
    args = parser.parse_args()
    
    explore_graph_structure(args.json)
    
    return 0


if __name__ == "__main__":
    exit(main())
