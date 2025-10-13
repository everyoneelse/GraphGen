#!/usr/bin/env python3
"""
自定义 GraphGen 类，支持使用外部知识图谱
"""

import os
import time
import networkx as nx
from dataclasses import dataclass
from typing import Dict

from graphgen.graphgen import GraphGen
from graphgen.models.storage.networkx_storage import NetworkXStorage
from graphgen.utils import logger


@dataclass
class CustomGraphGen(GraphGen):
    """支持外部知识图谱的 GraphGen"""
    
    external_graph_path: str = None
    skip_kg_building: bool = True  # 跳过知识图谱构建步骤
    
    def __post_init__(self):
        """初始化，加载外部知识图谱"""
        # 先调用父类初始化
        super().__post_init__()
        
        # 如果提供了外部图谱路径，则加载它
        if self.external_graph_path:
            self._load_external_graph()
    
    def _load_external_graph(self):
        """加载外部知识图谱"""
        if not os.path.exists(self.external_graph_path):
            raise FileNotFoundError(f"外部知识图谱文件不存在: {self.external_graph_path}")
        
        try:
            logger.info(f"正在加载外部知识图谱: {self.external_graph_path}")
            external_graph = nx.read_graphml(self.external_graph_path)
            
            # 替换默认的图存储
            self.graph_storage._graph = external_graph
            
            logger.info(
                f"✅ 外部知识图谱加载成功: {external_graph.number_of_nodes()} 个节点, "
                f"{external_graph.number_of_edges()} 条边"
            )
            
            # 显示一些统计信息
            self._show_graph_stats(external_graph)
            
        except Exception as e:
            logger.error(f"❌ 加载外部知识图谱失败: {e}")
            raise
    
    def _show_graph_stats(self, graph: nx.Graph):
        """显示图谱统计信息"""
        # 节点类型统计
        node_types = {}
        for node_id, node_data in graph.nodes(data=True):
            entity_type = node_data.get('entity_type', 'unknown')
            node_types[entity_type] = node_types.get(entity_type, 0) + 1
        
        logger.info("📊 节点类型分布:")
        for entity_type, count in sorted(node_types.items(), key=lambda x: x[1], reverse=True)[:10]:
            logger.info(f"   - {entity_type}: {count}")
        
        # 连通性统计
        if graph.number_of_nodes() > 0:
            connected_components = list(nx.connected_components(graph))
            logger.info(f"🔗 连通组件数: {len(connected_components)}")
            if connected_components:
                largest_component_size = max(len(cc) for cc in connected_components)
                logger.info(f"📈 最大连通组件大小: {largest_component_size}")
    
    async def insert(self, read_config: Dict = None, split_config: Dict = None):
        """
        重写插入方法，支持跳过知识图谱构建
        """
        if self.skip_kg_building and self.external_graph_path:
            logger.info("⏭️  跳过知识图谱构建步骤，使用外部知识图谱")
            # 直接调用插入完成回调
            await self._insert_done()
            return True
        else:
            # 调用原始的插入方法
            return await super().insert(read_config, split_config)
    
    async def insert_additional_data(self, read_config: Dict, split_config: Dict):
        """
        在外部知识图谱基础上插入额外数据
        """
        logger.info("📝 在外部知识图谱基础上插入额外数据...")
        return await super().insert(read_config, split_config)
    
    def get_graph_summary(self) -> Dict:
        """获取图谱摘要信息"""
        graph = self.graph_storage._graph
        
        # 基本统计
        summary = {
            'nodes': graph.number_of_nodes(),
            'edges': graph.number_of_edges(),
            'density': nx.density(graph) if graph.number_of_nodes() > 1 else 0,
        }
        
        # 节点类型分布
        node_types = {}
        for node_id, node_data in graph.nodes(data=True):
            entity_type = node_data.get('entity_type', 'unknown')
            node_types[entity_type] = node_types.get(entity_type, 0) + 1
        summary['node_types'] = node_types
        
        # 连通性信息
        if graph.number_of_nodes() > 0:
            connected_components = list(nx.connected_components(graph))
            summary['connected_components'] = len(connected_components)
            if connected_components:
                summary['largest_component_size'] = max(len(cc) for cc in connected_components)
        
        return summary
    
    def export_graph_statistics(self, output_file: str):
        """导出图谱统计信息到文件"""
        import json
        
        summary = self.get_graph_summary()
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        logger.info(f"📊 图谱统计信息已导出到: {output_file}")


def create_custom_config(
    external_graph_path: str,
    generation_mode: str = "atomic",
    data_format: str = "Alpaca",
    quiz_samples: int = 5,
    max_depth: int = 3,
    max_extra_edges: int = 5
) -> Dict:
    """
    创建适用于外部知识图谱的配置
    
    Args:
        external_graph_path: 外部知识图谱路径
        generation_mode: 生成模式 (atomic, aggregated, multi_hop, cot)
        data_format: 数据格式 (Alpaca, Sharegpt, ChatML)
        quiz_samples: 测试样本数量
        max_depth: 最大遍历深度
        max_extra_edges: 最大额外边数
    """
    config = {
        "read": {
            "input_file": []  # 空文件列表，因为使用外部知识图谱
        },
        "split": {
            "chunk_size": 1024,
            "chunk_overlap": 100
        },
        "search": {
            "enabled": False,  # 禁用搜索，直接使用外部知识图谱
            "search_types": []
        },
        "quiz_and_judge": {
            "enabled": True,
            "quiz_samples": quiz_samples,
            "re_judge": False
        },
        "partition": {
            "method": "ece",
            "method_params": {
                "bidirectional": True,
                "edge_sampling": "max_loss",
                "expand_method": "max_width",
                "isolated_node_strategy": "ignore",
                "max_depth": max_depth,
                "max_extra_edges": max_extra_edges,
                "max_tokens": 256,
                "loss_strategy": "only_edge"
            }
        },
        "generate": {
            "mode": generation_mode,
            "data_format": data_format
        }
    }
    
    return config


# 使用示例
if __name__ == "__main__":
    import yaml
    import asyncio
    from dotenv import load_dotenv
    
    # 加载环境变量
    load_dotenv()
    
    # 配置参数
    EXTERNAL_GRAPH_PATH = "cache/external_graph.graphml"
    WORKING_DIR = "cache"
    
    async def main():
        # 创建配置
        config = create_custom_config(
            external_graph_path=EXTERNAL_GRAPH_PATH,
            generation_mode="atomic",
            data_format="Alpaca",
            quiz_samples=3,
            max_depth=2,
            max_extra_edges=3
        )
        
        # 创建自定义 GraphGen 实例
        graph_gen = CustomGraphGen(
            external_graph_path=EXTERNAL_GRAPH_PATH,
            working_dir=WORKING_DIR,
            unique_id=int(time.time())
        )
        
        try:
            # 插入步骤（跳过知识图谱构建）
            await graph_gen.insert(
                read_config=config["read"], 
                split_config=config["split"]
            )
            
            # 可选：搜索增强
            if config["search"]["enabled"]:
                await graph_gen.search(search_config=config["search"])
            
            # 问答测试和判断
            if config["quiz_and_judge"]["enabled"]:
                await graph_gen.quiz_and_judge(quiz_and_judge_config=config["quiz_and_judge"])
            
            # 生成数据
            await graph_gen.generate(
                partition_config=config["partition"],
                generate_config=config["generate"]
            )
            
            # 导出统计信息
            graph_gen.export_graph_statistics("cache/graph_statistics.json")
            
            print("✅ 数据生成完成！检查 cache/data/graphgen/ 目录")
            
        except Exception as e:
            logger.error(f"❌ 生成过程中出现错误: {e}")
            raise
    
    # 运行示例
    # asyncio.run(main())