#!/usr/bin/env python3
"""
专门针对 youtu-graphrag JSON 格式的知识图谱转换器
"""

import networkx as nx
import json
import argparse
import os
from typing import Dict, Any, List, Union
from pathlib import Path


class YoutuJSONConverter:
    """将 youtu-graphrag JSON 格式的知识图谱转换为 GraphGen 格式"""
    
    def __init__(self):
        self.graph = nx.Graph()
        self.entity_nodes = {}  # 存储实体节点信息
        self.attribute_nodes = {}  # 存储属性节点信息
        self.community_nodes = {}  # 存储社区节点信息
        self.relations = []  # 存储关系信息
        self.chunks = {}  # 存储 chunk 信息 {chunk_id: chunk_data}
    
    def load_youtu_json_data(self, json_file: str):
        """
        加载 youtu-graphrag JSON 格式的知识图谱数据
        
        Args:
            json_file: JSON 文件路径
        """
        print(f"正在加载 youtu-graphrag JSON 数据: {json_file}")
        
        if not os.path.exists(json_file):
            raise FileNotFoundError(f"文件不存在: {json_file}")
        
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if not isinstance(data, list):
            raise ValueError("JSON 数据应该是一个列表格式")
        
        print(f"加载完成 - 共 {len(data)} 条关系记录")
        return data
    
    def load_youtu_chunks(self, chunks_file: str):
        """
        加载 youtu-graphrag 的 chunks 文件
        
        格式: id: CHUNK_ID\tChunk: {'title': '...', 'content': '...', 'source': '...'}
        
        Args:
            chunks_file: chunks 文件路径 (通常是 text 文件)
        """
        print(f"正在加载 youtu-graphrag chunks 数据: {chunks_file}")
        
        if not os.path.exists(chunks_file):
            raise FileNotFoundError(f"Chunks 文件不存在: {chunks_file}")
        
        chunks_loaded = 0
        with open(chunks_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                
                try:
                    # 解析格式: id: CHUNK_ID\tChunk: {...}
                    if '\t' in line:
                        parts = line.split('\t', 1)
                        if len(parts) == 2:
                            # 提取 chunk_id
                            id_part = parts[0].strip()
                            if id_part.startswith('id:'):
                                chunk_id = id_part[3:].strip()
                            else:
                                chunk_id = id_part
                            
                            # 提取 chunk 数据
                            chunk_part = parts[1].strip()
                            if chunk_part.startswith('Chunk:'):
                                chunk_str = chunk_part[6:].strip()
                                # 使用 eval 或 json.loads 解析字典
                                try:
                                    chunk_data = eval(chunk_str)  # 因为是 Python 字典格式
                                except:
                                    chunk_data = json.loads(chunk_str)
                                
                                self.chunks[chunk_id] = chunk_data
                                chunks_loaded += 1
                except Exception as e:
                    print(f"⚠️  警告: 无法解析第 {line_num} 行: {str(e)[:50]}")
                    continue
        
        print(f"加载完成 - 共 {chunks_loaded} 个 chunks")
        return chunks_loaded
    
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
            elif end_label == 'community' and end_name:
                # 解析社区节点
                self.community_nodes[end_name] = {
                    'name': end_name,
                    'label': end_label,
                    'description': end_props.get('description', ''),
                    'members': end_props.get('members', []),
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
        print(f"  - 社区节点: {len(self.community_nodes)}")
        print(f"  - 关系: {len(self.relations)}")
    
    def convert_to_graphgen_format(self):
        """转换为 GraphGen 兼容的格式"""
        print("开始转换为 GraphGen 格式...")
        
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
            
            # 添加节点到图中
            node_data = {
                'entity_name': entity_name,
                'entity_type': entity_data['schema_type'],
                'description': description,
                'source_id': entity_data['chunk_id'] or 'youtu_graphrag',
                'original_label': entity_data['label']
            }
            
            self.graph.add_node(entity_name, **node_data)
        
        print(f"已添加 {self.graph.number_of_nodes()} 个实体节点")
        
        # 添加实体间的关系（跳过 has_attribute 关系，因为已经整合到实体描述中）
        entity_relations = []
        for relation in self.relations:
            if (relation['source_type'] == 'entity' and 
                relation['target_type'] == 'entity' and
                relation['relation'] != 'has_attribute'):
                entity_relations.append(relation)
        
        # 添加边
        valid_edges = 0
        for relation in entity_relations:
            source = relation['source']
            target = relation['target']
            relation_type = relation['relation']
            
            if source in self.entity_nodes and target in self.entity_nodes:
                edge_data = {
                    'weight': 1.0,
                    'description': f"{source} {relation_type} {target}",
                    'relation_type': relation_type,
                    'source_id': 'youtu_graphrag'
                }
                
                self.graph.add_edge(source, target, **edge_data)
                valid_edges += 1
        
        print(f"已添加 {valid_edges} 条实体间关系")
        
        # 如果没有实体间关系，创建一些基于共同属性的关系
        if valid_edges == 0:
            print("没有发现实体间关系，基于共同属性创建关系...")
            self._create_attribute_based_relations()
    
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
        edges_added = 0
        for chunk_id, entities in chunk_groups.items():
            if len(entities) > 1:
                # 为每对实体创建关系
                for i in range(len(entities)):
                    for j in range(i + 1, len(entities)):
                        entity1, entity2 = entities[i], entities[j]
                        
                        edge_data = {
                            'weight': 0.8,
                            'description': f"{entity1} and {entity2} appear in the same context",
                            'relation_type': 'co_occurrence',
                            'source_id': chunk_id
                        }
                        
                        self.graph.add_edge(entity1, entity2, **edge_data)
                        edges_added += 1
        
        print(f"基于共同上下文添加了 {edges_added} 条关系")
    
    def save_to_graphml(self, output_file: str):
        """保存为 GraphML 格式"""
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # 确保所有属性都是字符串类型（GraphML 要求）
        for node_id, node_data in self.graph.nodes(data=True):
            for key, value in node_data.items():
                node_data[key] = str(value)
        
        for source, target, edge_data in self.graph.edges(data=True):
            for key, value in edge_data.items():
                edge_data[key] = str(value)
        
        nx.write_graphml(self.graph, output_file, encoding='utf-8')
        print(f"\n✅ 知识图谱转换完成！")
        print(f"📁 输出文件: {output_file}")
        print(f"📊 统计信息:")
        print(f"   - 节点数: {self.graph.number_of_nodes()}")
        print(f"   - 边数: {self.graph.number_of_edges()}")
        
        # 显示一些示例节点和边
        self._show_examples()
    
    def _show_examples(self):
        """显示示例节点和边"""
        if self.graph.number_of_nodes() > 0:
            print(f"\n📝 示例节点:")
            for i, (node_id, node_data) in enumerate(self.graph.nodes(data=True)):
                if i >= 3:  # 只显示前3个
                    break
                entity_type = node_data.get('entity_type', 'unknown')
                description = node_data.get('description', '')[:80]
                print(f"   - {node_id} ({entity_type}): {description}...")
        
        if self.graph.number_of_edges() > 0:
            print(f"\n🔗 示例关系:")
            for i, (source, target, edge_data) in enumerate(self.graph.edges(data=True)):
                if i >= 3:  # 只显示前3个
                    break
                relation_type = edge_data.get('relation_type', 'unknown')
                print(f"   - {source} --[{relation_type}]--> {target}")
    
    def validate_graph(self):
        """验证转换后的图谱"""
        issues = []
        
        # 检查孤立节点
        isolated_nodes = list(nx.isolates(self.graph))
        if isolated_nodes:
            issues.append(f"发现 {len(isolated_nodes)} 个孤立节点")
        
        # 检查节点属性
        nodes_without_description = 0
        for node_id, node_data in self.graph.nodes(data=True):
            if not node_data.get('description', '').strip():
                nodes_without_description += 1
        
        if nodes_without_description > 0:
            issues.append(f"{nodes_without_description} 个节点缺少描述")
        
        # 检查连通性
        if self.graph.number_of_nodes() > 1:
            connected_components = list(nx.connected_components(self.graph))
            if len(connected_components) > 1:
                largest_component = max(len(cc) for cc in connected_components)
                issues.append(f"图谱有 {len(connected_components)} 个连通组件，最大组件包含 {largest_component} 个节点")
        
        if issues:
            print(f"\n⚠️  验证发现的问题:")
            for issue in issues:
                print(f"   - {issue}")
        else:
            print(f"\n✅ 图谱验证通过，没有发现问题")
    
    def export_statistics(self, output_file: str):
        """导出详细统计信息"""
        stats = {
            'basic_info': {
                'nodes': self.graph.number_of_nodes(),
                'edges': self.graph.number_of_edges(),
                'density': nx.density(self.graph) if self.graph.number_of_nodes() > 1 else 0
            },
            'entity_types': {},
            'relation_types': {},
            'chunk_distribution': {},
            'communities': len(self.community_nodes)
        }
        
        # 统计实体类型
        for node_id, node_data in self.graph.nodes(data=True):
            entity_type = node_data.get('entity_type', 'unknown')
            stats['entity_types'][entity_type] = stats['entity_types'].get(entity_type, 0) + 1
        
        # 统计关系类型
        for source, target, edge_data in self.graph.edges(data=True):
            relation_type = edge_data.get('relation_type', 'unknown')
            stats['relation_types'][relation_type] = stats['relation_types'].get(relation_type, 0) + 1
        
        # 统计 chunk 分布
        for node_id, node_data in self.graph.nodes(data=True):
            chunk_id = node_data.get('source_id', 'unknown')
            stats['chunk_distribution'][chunk_id] = stats['chunk_distribution'].get(chunk_id, 0) + 1
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        
        print(f"📊 统计信息已导出到: {output_file}")
    
    def export_communities(self, output_file: str):
        """导出社区信息为JSON格式"""
        communities_data = []
        for comm_name, comm_data in self.community_nodes.items():
            communities_data.append({
                'name': comm_name,
                'description': comm_data['description'],
                'members': comm_data['members'],
                'member_count': len(comm_data['members'])
            })
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(communities_data, f, ensure_ascii=False, indent=2)
        
        print(f"🏘️  社区信息已导出到: {output_file}")
        print(f"   - 社区数量: {len(communities_data)}")
        
        return communities_data
    
    def get_communities_dict(self) -> Dict[str, int]:
        """
        将社区信息转换为 CommunityDetector 格式
        返回: {node_name: community_id} 的字典
        """
        communities_dict = {}
        
        for comm_id, (comm_name, comm_data) in enumerate(self.community_nodes.items()):
            members = comm_data.get('members', [])
            for member in members:
                communities_dict[member] = comm_id
        
        return communities_dict
    
    def get_chunks_dict(self) -> Dict[str, Dict]:
        """
        获取 chunks 字典，用于在生成时提供文档上下文
        
        Returns:
            Dict[str, Dict]: {chunk_id: {'content': ..., 'title': ..., 'source': ...}}
        """
        return self.chunks.copy()
    
    def export_chunks(self, output_file: str):
        """导出 chunks 信息为 JSON 格式"""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.chunks, f, ensure_ascii=False, indent=2)
        
        print(f"📄 Chunks 信息已导出到: {output_file}")
        print(f"   - Chunks 数量: {len(self.chunks)}")
        
        return self.chunks


def main():
    parser = argparse.ArgumentParser(description='将 youtu-graphrag JSON 知识图谱转换为 GraphGen 格式')
    parser.add_argument('--input', required=True, help='输入 JSON 文件路径')
    parser.add_argument('--output', required=True, help='输出 GraphML 文件路径')
    parser.add_argument('--validate', action='store_true', help='验证转换后的图谱')
    parser.add_argument('--stats', help='导出统计信息到指定文件')
    
    args = parser.parse_args()
    
    try:
        converter = YoutuJSONConverter()
        data = converter.load_youtu_json_data(args.input)
        converter.parse_youtu_data(data)
        converter.convert_to_graphgen_format()
        
        if args.validate:
            converter.validate_graph()
        
        converter.save_to_graphml(args.output)
        
        if args.stats:
            converter.export_statistics(args.stats)
        
    except Exception as e:
        print(f"❌ 转换失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())