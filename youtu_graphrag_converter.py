#!/usr/bin/env python3
"""
youtu-graphrag 知识图谱转换器
将 youtu-graphrag 生成的知识图谱转换为 GraphGen 兼容格式
"""

import networkx as nx
import json
import pandas as pd
import argparse
import os
from typing import Dict, Any, List, Union
from pathlib import Path


class YoutuGraphRAGConverter:
    """将 youtu-graphrag 知识图谱转换为 GraphGen 格式"""
    
    def __init__(self):
        self.graph = nx.Graph()
        self.entity_mapping = {}  # 用于处理实体名称映射
    
    def load_youtu_graphrag_data(self, entities_file: str, relationships_file: str):
        """
        加载 youtu-graphrag 生成的实体和关系数据
        
        Args:
            entities_file: 实体文件路径 (支持 CSV, JSON, JSONL)
            relationships_file: 关系文件路径 (支持 CSV, JSON, JSONL)
        """
        print(f"正在加载实体数据: {entities_file}")
        entities_df = self._load_file(entities_file)
        
        print(f"正在加载关系数据: {relationships_file}")
        relationships_df = self._load_file(relationships_file)
        
        print(f"加载完成 - 实体: {len(entities_df)}, 关系: {len(relationships_df)}")
        return entities_df, relationships_df
    
    def _load_file(self, file_path: str) -> pd.DataFrame:
        """加载不同格式的文件"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        file_ext = Path(file_path).suffix.lower()
        
        if file_ext == '.csv':
            return pd.read_csv(file_path, encoding='utf-8')
        elif file_ext == '.json':
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if isinstance(data, list):
                return pd.DataFrame(data)
            elif isinstance(data, dict):
                # 如果是嵌套字典，尝试展平
                return pd.DataFrame([data])
        elif file_ext == '.jsonl':
            data = []
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        data.append(json.loads(line))
            return pd.DataFrame(data)
        else:
            raise ValueError(f"不支持的文件格式: {file_ext}")
    
    def _normalize_entity_id(self, entity_data: pd.Series) -> str:
        """标准化实体ID"""
        # 尝试不同的字段名
        possible_id_fields = ['id', 'entity_id', 'name', 'entity_name', 'title']
        
        for field in possible_id_fields:
            if field in entity_data and pd.notna(entity_data[field]):
                return str(entity_data[field]).strip()
        
        # 如果没有找到合适的ID，使用索引
        return f"entity_{entity_data.name}"
    
    def _normalize_entity_type(self, entity_data: pd.Series) -> str:
        """标准化实体类型"""
        possible_type_fields = ['type', 'entity_type', 'category', 'class']
        
        for field in possible_type_fields:
            if field in entity_data and pd.notna(entity_data[field]):
                return str(entity_data[field]).strip()
        
        return "unknown"
    
    def _normalize_entity_description(self, entity_data: pd.Series) -> str:
        """标准化实体描述"""
        possible_desc_fields = ['description', 'summary', 'content', 'text', 'details']
        
        for field in possible_desc_fields:
            if field in entity_data and pd.notna(entity_data[field]):
                return str(entity_data[field]).strip()
        
        return ""
    
    def _normalize_relationship_data(self, relation_data: pd.Series) -> tuple:
        """标准化关系数据"""
        # 源实体
        source_fields = ['source', 'src_id', 'source_entity', 'from', 'subject']
        source = None
        for field in source_fields:
            if field in relation_data and pd.notna(relation_data[field]):
                source = str(relation_data[field]).strip()
                break
        
        # 目标实体
        target_fields = ['target', 'tgt_id', 'target_entity', 'to', 'object']
        target = None
        for field in target_fields:
            if field in relation_data and pd.notna(relation_data[field]):
                target = str(relation_data[field]).strip()
                break
        
        # 关系描述
        desc_fields = ['description', 'relationship_summary', 'relation', 'predicate', 'label']
        description = ""
        for field in desc_fields:
            if field in relation_data and pd.notna(relation_data[field]):
                description = str(relation_data[field]).strip()
                break
        
        # 权重
        weight_fields = ['weight', 'strength', 'confidence', 'score']
        weight = 1.0
        for field in weight_fields:
            if field in relation_data and pd.notna(relation_data[field]):
                try:
                    weight = float(relation_data[field])
                    break
                except (ValueError, TypeError):
                    continue
        
        return source, target, description, weight
    
    def convert_to_graphgen_format(self, entities_df: pd.DataFrame, relationships_df: pd.DataFrame):
        """
        转换为 GraphGen 兼容的格式
        """
        print("开始转换实体数据...")
        
        # 添加节点
        for idx, entity in entities_df.iterrows():
            node_id = self._normalize_entity_id(entity)
            entity_type = self._normalize_entity_type(entity)
            description = self._normalize_entity_description(entity)
            
            # 存储实体映射
            self.entity_mapping[node_id] = node_id
            
            node_data = {
                'entity_name': node_id,
                'entity_type': entity_type,
                'description': description,
                'source_id': 'youtu_graphrag'
            }
            
            # 添加其他可能的属性
            for col in entity.index:
                if col not in ['id', 'entity_id', 'name', 'entity_name', 'type', 'entity_type', 'description', 'summary']:
                    if pd.notna(entity[col]):
                        node_data[f'extra_{col}'] = str(entity[col])
            
            self.graph.add_node(node_id, **node_data)
        
        print(f"已添加 {self.graph.number_of_nodes()} 个节点")
        print("开始转换关系数据...")
        
        # 添加边
        valid_edges = 0
        for idx, relation in relationships_df.iterrows():
            source, target, description, weight = self._normalize_relationship_data(relation)
            
            if not source or not target:
                print(f"跳过无效关系 (行 {idx}): source={source}, target={target}")
                continue
            
            # 检查节点是否存在
            if not self.graph.has_node(source):
                print(f"警告: 源节点不存在，创建节点: {source}")
                self.graph.add_node(source, entity_name=source, entity_type="unknown", 
                                  description="", source_id="youtu_graphrag_missing")
            
            if not self.graph.has_node(target):
                print(f"警告: 目标节点不存在，创建节点: {target}")
                self.graph.add_node(target, entity_name=target, entity_type="unknown", 
                                  description="", source_id="youtu_graphrag_missing")
            
            edge_data = {
                'weight': weight,
                'description': description,
                'source_id': 'youtu_graphrag'
            }
            
            # 添加其他可能的属性
            for col in relation.index:
                if col not in ['source', 'target', 'src_id', 'tgt_id', 'description', 'weight']:
                    if pd.notna(relation[col]):
                        edge_data[f'extra_{col}'] = str(relation[col])
            
            self.graph.add_edge(source, target, **edge_data)
            valid_edges += 1
        
        print(f"已添加 {valid_edges} 条有效边")
    
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
        if self.graph.number_of_nodes() > 0:
            print(f"\n📝 示例节点:")
            for i, (node_id, node_data) in enumerate(self.graph.nodes(data=True)):
                if i >= 3:  # 只显示前3个
                    break
                print(f"   - {node_id}: {node_data.get('entity_type', 'unknown')} - {node_data.get('description', '')[:50]}...")
        
        if self.graph.number_of_edges() > 0:
            print(f"\n🔗 示例关系:")
            for i, (source, target, edge_data) in enumerate(self.graph.edges(data=True)):
                if i >= 3:  # 只显示前3个
                    break
                print(f"   - {source} -> {target}: {edge_data.get('description', '')[:50]}...")
    
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
        
        # 检查边属性
        edges_without_description = 0
        for source, target, edge_data in self.graph.edges(data=True):
            if not edge_data.get('description', '').strip():
                edges_without_description += 1
        
        if edges_without_description > 0:
            issues.append(f"{edges_without_description} 条边缺少描述")
        
        if issues:
            print(f"\n⚠️  验证发现的问题:")
            for issue in issues:
                print(f"   - {issue}")
        else:
            print(f"\n✅ 图谱验证通过，没有发现问题")


def main():
    parser = argparse.ArgumentParser(description='将 youtu-graphrag 知识图谱转换为 GraphGen 格式')
    parser.add_argument('--entities', required=True, help='实体文件路径')
    parser.add_argument('--relationships', required=True, help='关系文件路径')
    parser.add_argument('--output', required=True, help='输出 GraphML 文件路径')
    parser.add_argument('--validate', action='store_true', help='验证转换后的图谱')
    
    args = parser.parse_args()
    
    try:
        converter = YoutuGraphRAGConverter()
        entities_df, relationships_df = converter.load_youtu_graphrag_data(
            args.entities, args.relationships
        )
        converter.convert_to_graphgen_format(entities_df, relationships_df)
        
        if args.validate:
            converter.validate_graph()
        
        converter.save_to_graphml(args.output)
        
    except Exception as e:
        print(f"❌ 转换失败: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())