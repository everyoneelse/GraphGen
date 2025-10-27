#!/usr/bin/env python3
"""
检查 graph.json 文件格式，特别是 community 节点
"""

import json
import sys
from collections import Counter


def check_graph_format(json_file: str):
    """检查 graph.json 文件格式"""
    print("=" * 70)
    print("检查 Graph.json 文件格式")
    print("=" * 70)
    
    # 1. 加载文件
    print(f"\n📝 步骤 1: 加载文件: {json_file}")
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"✅ 成功加载，共 {len(data)} 条记录")
    except FileNotFoundError:
        print(f"❌ 文件不存在: {json_file}")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ JSON 格式错误: {e}")
        return False
    except Exception as e:
        print(f"❌ 加载失败: {e}")
        return False
    
    # 2. 统计节点类型
    print("\n📊 步骤 2: 统计节点类型")
    
    start_labels = []
    end_labels = []
    relations = []
    community_count = 0
    community_examples = []
    
    for item in data:
        # 起始节点
        start_node = item.get('start_node', {})
        start_label = start_node.get('label', '')
        if start_label:
            start_labels.append(start_label)
        
        # 结束节点
        end_node = item.get('end_node', {})
        end_label = end_node.get('label', '')
        if end_label:
            end_labels.append(end_label)
        
        # 关系
        relation = item.get('relation', '')
        if relation:
            relations.append(relation)
        
        # 检查是否是 community 节点
        if end_label == 'community':
            community_count += 1
            if len(community_examples) < 3:
                community_examples.append(item)
    
    # 显示统计
    print("\n   起始节点类型分布:")
    start_counter = Counter(start_labels)
    for label, count in start_counter.most_common(10):
        print(f"     - {label}: {count}")
    
    print("\n   结束节点类型分布:")
    end_counter = Counter(end_labels)
    for label, count in end_counter.most_common(10):
        marker = " ← COMMUNITY!" if label == 'community' else ""
        print(f"     - {label}: {count}{marker}")
    
    print("\n   关系类型分布:")
    relation_counter = Counter(relations)
    for rel, count in relation_counter.most_common(10):
        print(f"     - {rel}: {count}")
    
    # 3. 检查 community 节点
    print("\n🏘️  步骤 3: 检查 Community 节点")
    
    if community_count == 0:
        print("❌ 未发现 community 节点！")
        print("\n   可能的原因:")
        print("   1. end_node.label 不是 'community'")
        print("   2. community 信息存储在其他字段")
        print("   3. 文件格式不同于预期")
        print("\n   💡 提示: 请检查 JSON 文件中是否有类似的字段:")
        print('      "end_node": {"label": "community", ...}')
        
        return False
    
    print(f"✅ 发现 {community_count} 个 community 节点")
    
    # 4. 显示 community 示例
    print("\n📝 步骤 4: Community 节点示例")
    
    for i, example in enumerate(community_examples):
        print(f"\n   示例 {i+1}:")
        
        # 起始节点
        start_node = example.get('start_node', {})
        start_label = start_node.get('label', '')
        start_name = start_node.get('properties', {}).get('name', '')
        print(f"     起始: ({start_label}) {start_name}")
        
        # 关系
        relation = example.get('relation', '')
        print(f"     关系: {relation}")
        
        # 结束节点（community）
        end_node = example.get('end_node', {})
        end_props = end_node.get('properties', {})
        comm_name = end_props.get('name', '')
        comm_desc = end_props.get('description', '')
        comm_members = end_props.get('members', [])
        
        print(f"     社区: {comm_name}")
        print(f"     描述: {comm_desc[:80]}...")
        print(f"     成员数: {len(comm_members)}")
        print(f"     成员样例: {', '.join(comm_members[:3])}")
    
    # 5. 验证 community 格式
    print("\n🔍 步骤 5: 验证 Community 格式")
    
    valid_communities = 0
    issues = []
    
    for item in data:
        end_node = item.get('end_node', {})
        if end_node.get('label') == 'community':
            props = end_node.get('properties', {})
            
            # 检查必需字段
            has_name = 'name' in props
            has_description = 'description' in props
            has_members = 'members' in props and isinstance(props['members'], list)
            
            if has_name and has_description and has_members:
                valid_communities += 1
            else:
                issue = f"社区 '{props.get('name', 'UNKNOWN')}' 缺少字段:"
                if not has_name:
                    issue += " name"
                if not has_description:
                    issue += " description"
                if not has_members:
                    issue += " members"
                issues.append(issue)
    
    print(f"   有效的 community 节点: {valid_communities}/{community_count}")
    
    if issues:
        print(f"\n   ⚠️  发现 {len(issues)} 个问题:")
        for issue in issues[:5]:
            print(f"     - {issue}")
        if len(issues) > 5:
            print(f"     ... 还有 {len(issues) - 5} 个问题")
    
    # 6. 总结
    print("\n" + "=" * 70)
    print("📋 检查总结")
    print("=" * 70)
    
    if valid_communities >= 1:
        print(f"✅ 文件格式正确！")
        print(f"   - 发现 {community_count} 个 community 节点")
        print(f"   - 其中 {valid_communities} 个格式有效")
        print(f"\n💡 可以直接使用:")
        print(f"   python run_youtu_json_kg.py \\")
        print(f"     --json {json_file} \\")
        print(f"     --mode cot \\")
        print(f"     --disable-quiz")
        return True
    else:
        print(f"❌ Community 格式有问题")
        print(f"   请检查 JSON 文件中的 community 节点格式")
        return False


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='检查 graph.json 文件格式')
    parser.add_argument('--json', required=True, help='graph.json 文件路径')
    
    args = parser.parse_args()
    
    success = check_graph_format(args.json)
    
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
