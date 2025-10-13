#!/usr/bin/env python3
"""
youtu-graphrag JSON 转换演示（简化版，不依赖外部库）
"""

import json
import os


def demo_youtu_conversion():
    """演示 youtu-graphrag JSON 数据的转换过程"""
    
    print("🚀 youtu-graphrag JSON 知识图谱转换演示")
    print("=" * 50)
    
    # 读取示例数据
    with open('example_youtu_data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"📁 加载了 {len(data)} 条关系记录")
    
    # 解析数据结构
    entities = {}
    attributes = {}
    relations = []
    
    for item in data:
        # 解析起始节点
        start_node = item.get('start_node', {})
        start_props = start_node.get('properties', {})
        start_name = start_props.get('name', '')
        
        # 解析结束节点
        end_node = item.get('end_node', {})
        end_props = end_node.get('properties', {})
        end_name = end_props.get('name', '')
        
        # 解析关系
        relation = item.get('relation', '')
        
        # 存储实体
        if start_node.get('label') == 'entity' and start_name:
            entities[start_name] = {
                'name': start_name,
                'type': start_props.get('schema_type', 'unknown'),
                'chunk_id': start_props.get('chunk id', ''),
                'attributes': []
            }
        
        if end_node.get('label') == 'entity' and end_name:
            entities[end_name] = {
                'name': end_name,
                'type': end_props.get('schema_type', 'unknown'),
                'chunk_id': end_props.get('chunk id', ''),
                'attributes': []
            }
        
        # 存储属性
        if end_node.get('label') == 'attribute' and end_name:
            attributes[end_name] = {
                'name': end_name,
                'chunk_id': end_props.get('chunk id', '')
            }
        
        # 存储关系
        if start_name and end_name and relation:
            relations.append({
                'source': start_name,
                'target': end_name,
                'relation': relation,
                'source_type': start_node.get('label'),
                'target_type': end_node.get('label')
            })
    
    print(f"\n📊 数据解析结果:")
    print(f"   - 实体数量: {len(entities)}")
    print(f"   - 属性数量: {len(attributes)}")
    print(f"   - 关系数量: {len(relations)}")
    
    # 显示实体信息
    print(f"\n🏢 发现的实体:")
    for entity_name, entity_data in entities.items():
        print(f"   - {entity_name} ({entity_data['type']})")
    
    # 整合属性到实体
    for relation in relations:
        if (relation['relation'] == 'has_attribute' and 
            relation['source_type'] == 'entity' and 
            relation['target_type'] == 'attribute'):
            
            source_entity = relation['source']
            target_attribute = relation['target']
            
            if source_entity in entities and target_attribute in attributes:
                entities[source_entity]['attributes'].append(target_attribute)
    
    # 构建 GraphGen 兼容的节点数据
    print(f"\n🔄 转换为 GraphGen 格式:")
    graphgen_nodes = []
    
    for entity_name, entity_data in entities.items():
        # 构建描述
        description_parts = [f"Type: {entity_data['type']}"]
        for attr_name in entity_data['attributes']:
            if attr_name in attributes:
                description_parts.append(attributes[attr_name]['name'])
        
        description = "; ".join(description_parts)
        
        node = {
            'entity_name': entity_name,
            'entity_type': entity_data['type'],
            'description': description,
            'source_id': entity_data['chunk_id'] or 'youtu_graphrag'
        }
        
        graphgen_nodes.append(node)
        print(f"   ✅ {entity_name}: {description}")
    
    # 构建实体间关系
    entity_relations = []
    for relation in relations:
        if (relation['source_type'] == 'entity' and 
            relation['target_type'] == 'entity' and
            relation['relation'] != 'has_attribute'):
            entity_relations.append(relation)
    
    print(f"\n🔗 实体间关系:")
    for relation in entity_relations:
        print(f"   - {relation['source']} --[{relation['relation']}]--> {relation['target']}")
    
    # 如果没有实体间关系，基于共同 chunk_id 创建关系
    if not entity_relations:
        print(f"\n🔗 基于共同上下文创建关系:")
        chunk_groups = {}
        for entity_name, entity_data in entities.items():
            chunk_id = entity_data['chunk_id']
            if chunk_id:
                if chunk_id not in chunk_groups:
                    chunk_groups[chunk_id] = []
                chunk_groups[chunk_id].append(entity_name)
        
        for chunk_id, entity_list in chunk_groups.items():
            if len(entity_list) > 1:
                for i in range(len(entity_list)):
                    for j in range(i + 1, len(entity_list)):
                        entity1, entity2 = entity_list[i], entity_list[j]
                        print(f"   - {entity1} --[co_occurrence]--> {entity2} (chunk: {chunk_id})")
    
    # 生成可能的问答示例
    print(f"\n❓ 可能生成的问答示例:")
    
    for entity_name, entity_data in entities.items():
        if entity_data['attributes']:
            # 属性问题
            question = f"What are the attributes of {entity_name}?"
            answer_parts = []
            for attr_name in entity_data['attributes']:
                if attr_name in attributes:
                    answer_parts.append(attributes[attr_name]['name'])
            answer = f"{entity_name} has the following attributes: {', '.join(answer_parts)}."
            
            print(f"   Q: {question}")
            print(f"   A: {answer}")
            print()
    
    # 关系问题
    for relation in entity_relations:
        question = f"What is the relationship between {relation['source']} and {relation['target']}?"
        answer = f"{relation['source']} {relation['relation']} {relation['target']}."
        
        print(f"   Q: {question}")
        print(f"   A: {answer}")
        print()
    
    print("✅ 转换演示完成！")
    print("\n📋 接下来的步骤:")
    print("1. 设置环境变量（API 密钥等）")
    print("2. 安装完整依赖: pip install -r requirements.txt")
    print("3. 使用完整转换器:")
    print("   python youtu_json_converter.py --input your_data.json --output cache/graph.graphml")
    print("4. 生成问答数据:")
    print("   python run_youtu_json_kg.py --json your_data.json --mode atomic")


if __name__ == "__main__":
    demo_youtu_conversion()