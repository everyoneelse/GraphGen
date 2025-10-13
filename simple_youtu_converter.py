#!/usr/bin/env python3
"""
简化版 youtu-graphrag JSON 转换器（减少依赖）
"""

import json
import os
from typing import Dict, Any, List


class SimpleYoutuConverter:
    """简化版 youtu-graphrag JSON 格式转换器"""
    
    def __init__(self):
        self.entity_nodes = {}
        self.attribute_nodes = {}
        self.relations = []
    
    def load_youtu_json_data(self, json_file: str):
        """加载 youtu-graphrag JSON 数据"""
        print(f"正在加载 youtu-graphrag JSON 数据: {json_file}")
        
        if not os.path.exists(json_file):
            raise FileNotFoundError(f"文件不存在: {json_file}")
        
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if not isinstance(data, list):
            raise ValueError("JSON 数据应该是一个列表格式")
        
        print(f"加载完成 - 共 {len(data)} 条关系记录")
        return data
    
    def parse_youtu_data(self, data: List[Dict]):
        """解析 youtu-graphrag 数据结构"""
        print("开始解析数据结构...")
        
        for item in data:
            # 解析起始节点
            start_node = item.get('start_node', {})
            start_label = start_node.get('label', '')
            start_props = start_node.get('properties', {})
            start_name = start_props.get('name', '')
            
            # 解析结束节点
            end_node = item.get('end_node', {})
            end_label = end_node.get('label', '')
            end_props = end_node.get('properties', {})
            end_name = end_props.get('name', '')
            
            # 解析关系
            relation = item.get('relation', '')
            
            # 存储节点信息
            if start_label == 'entity' and start_name:
                self.entity_nodes[start_name] = {
                    'name': start_name,
                    'label': start_label,
                    'chunk_id': start_props.get('chunk id', ''),
                    'schema_type': start_props.get('schema_type', 'unknown'),
                    'properties': start_props
                }
            
            if end_label == 'attribute' and end_name:
                self.attribute_nodes[end_name] = {
                    'name': end_name,
                    'label': end_label,
                    'chunk_id': end_props.get('chunk id', ''),
                    'properties': end_props
                }
            elif end_label == 'entity' and end_name:
                self.entity_nodes[end_name] = {
                    'name': end_name,
                    'label': end_label,
                    'chunk_id': end_props.get('chunk id', ''),
                    'schema_type': end_props.get('schema_type', 'unknown'),
                    'properties': end_props
                }
            
            # 存储关系信息
            if start_name and end_name and relation:
                self.relations.append({
                    'source': start_name,
                    'target': end_name,
                    'relation': relation,
                    'source_type': start_label,
                    'target_type': end_label
                })
        
        print(f"解析完成:")
        print(f"  - 实体节点: {len(self.entity_nodes)}")
        print(f"  - 属性节点: {len(self.attribute_nodes)}")
        print(f"  - 关系: {len(self.relations)}")
    
    def convert_to_graphgen_format(self):
        """转换为 GraphGen 兼容的格式"""
        print("开始转换为 GraphGen 格式...")
        
        # 构建节点数据
        nodes_data = []
        
        # 添加实体节点
        for entity_name, entity_data in self.entity_nodes.items():
            # 收集该实体的所有属性
            entity_attributes = []
            for relation in self.relations:
                if (relation['source'] == entity_name and 
                    relation['relation'] == 'has_attribute' and
                    relation['target_type'] == 'attribute'):
                    attr_name = relation['target']
                    if attr_name in self.attribute_nodes:
                        entity_attributes.append(attr_name)
            
            # 构建实体描述
            description_parts = []
            if entity_data['schema_type'] != 'unknown':
                description_parts.append(f"Type: {entity_data['schema_type']}")
            
            # 添加属性信息到描述中
            for attr_name in entity_attributes:
                if attr_name in self.attribute_nodes:
                    attr_info = self.attribute_nodes[attr_name]['name']
                    description_parts.append(attr_info)
            
            description = "; ".join(description_parts) if description_parts else f"Entity: {entity_name}"
            
            # 添加节点数据
            node_data = {
                'id': entity_name,
                'entity_name': entity_name,
                'entity_type': entity_data['schema_type'],
                'description': description,
                'source_id': entity_data['chunk_id'] or 'youtu_graphrag',
                'original_label': entity_data['label']
            }
            
            nodes_data.append(node_data)
        
        print(f"已处理 {len(nodes_data)} 个实体节点")
        
        # 构建边数据
        edges_data = []
        entity_relations = []
        for relation in self.relations:
            if (relation['source_type'] == 'entity' and 
                relation['target_type'] == 'entity' and
                relation['relation'] != 'has_attribute'):
                entity_relations.append(relation)
        
        # 添加边
        for relation in entity_relations:
            source = relation['source']
            target = relation['target']
            relation_type = relation['relation']
            
            if source in self.entity_nodes and target in self.entity_nodes:
                edge_data = {
                    'source': source,
                    'target': target,
                    'weight': 1.0,
                    'description': f"{source} {relation_type} {target}",
                    'relation_type': relation_type,
                    'source_id': 'youtu_graphrag'
                }
                
                edges_data.append(edge_data)
        
        print(f"已处理 {len(edges_data)} 条实体间关系")
        
        # 如果没有实体间关系，创建一些基于共同属性的关系
        if not edges_data:
            print("没有发现实体间关系，基于共同上下文创建关系...")
            edges_data = self._create_attribute_based_relations()
        
        return nodes_data, edges_data
    
    def _create_attribute_based_relations(self):
        """基于共同属性创建实体间关系"""
        # 按 chunk_id 分组实体
        chunk_groups = {}
        for entity_name, entity_data in self.entity_nodes.items():
            chunk_id = entity_data['chunk_id']
            if chunk_id:
                if chunk_id not in chunk_groups:
                    chunk_groups[chunk_id] = []
                chunk_groups[chunk_id].append(entity_name)
        
        # 为同一 chunk 中的实体创建关系
        edges_data = []
        for chunk_id, entities in chunk_groups.items():
            if len(entities) > 1:
                # 为每对实体创建关系
                for i in range(len(entities)):
                    for j in range(i + 1, len(entities)):
                        entity1, entity2 = entities[i], entities[j]
                        
                        edge_data = {
                            'source': entity1,
                            'target': entity2,
                            'weight': 0.8,
                            'description': f"{entity1} and {entity2} appear in the same context",
                            'relation_type': 'co_occurrence',
                            'source_id': chunk_id
                        }
                        
                        edges_data.append(edge_data)
        
        print(f"基于共同上下文添加了 {len(edges_data)} 条关系")
        return edges_data
    
    def save_to_json(self, output_file: str):
        """保存为 JSON 格式（用于后续处理）"""
        nodes_data, edges_data = self.convert_to_graphgen_format()
        
        result = {
            'nodes': nodes_data,
            'edges': edges_data,
            'statistics': {
                'node_count': len(nodes_data),
                'edge_count': len(edges_data),
                'entity_types': {}
            }
        }
        
        # 统计实体类型
        for node in nodes_data:
            entity_type = node.get('entity_type', 'unknown')
            result['statistics']['entity_types'][entity_type] = \
                result['statistics']['entity_types'].get(entity_type, 0) + 1
        
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ 转换完成！")
        print(f"📁 输出文件: {output_file}")
        print(f"📊 统计信息:")
        print(f"   - 节点数: {len(nodes_data)}")
        print(f"   - 边数: {len(edges_data)}")
        
        # 显示实体类型分布
        print(f"   - 实体类型分布:")
        for entity_type, count in result['statistics']['entity_types'].items():
            print(f"     * {entity_type}: {count}")
        
        return result


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='简化版 youtu-graphrag JSON 转换器')
    parser.add_argument('--input', required=True, help='输入 JSON 文件路径')
    parser.add_argument('--output', required=True, help='输出 JSON 文件路径')
    
    args = parser.parse_args()
    
    try:
        converter = SimpleYoutuConverter()
        data = converter.load_youtu_json_data(args.input)
        converter.parse_youtu_data(data)
        result = converter.save_to_json(args.output)
        
        print(f"\n🎯 转换成功！你可以使用生成的 JSON 文件进行后续处理。")
        
    except Exception as e:
        print(f"❌ 转换失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())