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
    """支持外部知识图谱的 GraphGen，无trainee模式"""
    
    external_graph_path: str = None
    skip_kg_building: bool = True  # 跳过知识图谱构建步骤
    no_trainee_mode: bool = True   # 无trainee模式，不使用trainee客户端
    
    def __post_init__(self):
        """初始化，加载外部知识图谱"""
        if self.no_trainee_mode:
            # 无trainee模式，直接使用最小化初始化
            logger.info("🚀 启用无trainee模式，使用最小化初始化")
            self._init_minimal()
        else:
            # 标准模式，先尝试调用父类初始化
            try:
                super().__post_init__()
            except Exception as e:
                # 如果 trainee 相关环境变量缺失，创建一个最小化的实例
                logger.warning(f"Trainee 客户端初始化失败，可能是环境变量缺失: {e}")
                self._init_minimal()
        
        # 如果提供了外部图谱路径，则加载它
        if self.external_graph_path:
            self._load_external_graph()
    
    def _init_minimal(self):
        """最小化初始化，不依赖 trainee 客户端"""
        from graphgen.models import JsonKVStorage, JsonListStorage, NetworkXStorage, OpenAIClient, Tokenizer
        
        self.tokenizer_instance: Tokenizer = self.tokenizer_instance or Tokenizer(
            model_name=os.getenv("TOKENIZER_MODEL", "cl100k_base")
        )

        # 只有在提供了 API key 时才创建 OpenAI 客户端
        synthesizer_api_key = os.getenv("SYNTHESIZER_API_KEY")
        if synthesizer_api_key:
            self.synthesizer_llm_client: OpenAIClient = (
                self.synthesizer_llm_client
                or OpenAIClient(
                    model_name=os.getenv("SYNTHESIZER_MODEL", "gpt-3.5-turbo"),
                    api_key=synthesizer_api_key,
                    base_url=os.getenv("SYNTHESIZER_BASE_URL"),
                    tokenizer=self.tokenizer_instance,
                )
            )
            logger.info("✅ Synthesizer LLM 客户端初始化成功")
        else:
            logger.warning("⚠️  未提供 SYNTHESIZER_API_KEY，synthesizer_llm_client 将设为 None")
            logger.info("💡 如需完整功能，请设置环境变量: export SYNTHESIZER_API_KEY='your_api_key'")
            self.synthesizer_llm_client = None

        # 无trainee模式：trainee_llm_client 始终设为 None
        self.trainee_llm_client = None
        logger.info("🚫 无trainee模式：trainee_llm_client 设为 None")

        self.full_docs_storage: JsonKVStorage = JsonKVStorage(
            self.working_dir, namespace="full_docs"
        )
        self.text_chunks_storage: JsonKVStorage = JsonKVStorage(
            self.working_dir, namespace="text_chunks"
        )
        self.graph_storage: NetworkXStorage = NetworkXStorage(
            self.working_dir, namespace="graph"
        )
        self.search_storage: JsonKVStorage = JsonKVStorage(
            self.working_dir, namespace="search"
        )
        self.rephrase_storage: JsonKVStorage = JsonKVStorage(
            self.working_dir, namespace="rephrase"
        )
        self.qa_storage: JsonListStorage = JsonListStorage(
            os.path.join(self.working_dir, "data", "graphgen", f"{self.unique_id}"),
            namespace="qa",
        )
    
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
        重写插入方法，支持跳过知识图谱构建和无trainee模式
        """
        if self.skip_kg_building:
            if self.external_graph_path:
                logger.info("⏭️  跳过知识图谱构建步骤，使用外部知识图谱")
                # 直接调用插入完成回调
                await self._insert_done()
                return True
            else:
                logger.info("⏭️  跳过知识图谱构建步骤（无外部图谱）")
                return True
        
        # 如果需要构建知识图谱，检查参数和客户端
        if read_config is None or split_config is None:
            logger.warning("⚠️  read_config 或 split_config 为空，跳过知识图谱构建")
            return True
            
        if self.synthesizer_llm_client is None:
            logger.warning("⚠️  synthesizer_llm_client 未初始化，跳过知识图谱构建")
            logger.info("💡 如需构建知识图谱，请设置环境变量: export SYNTHESIZER_API_KEY='your_openai_api_key'")
            return True
        
        # 调用原始的插入方法
        return await super().insert(read_config, split_config)
    
    async def insert_additional_data(self, read_config: Dict, split_config: Dict):
        """
        在外部知识图谱基础上插入额外数据
        """
        if self.synthesizer_llm_client is None:
            logger.warning("⚠️  synthesizer_llm_client 未初始化，跳过额外数据插入")
            logger.info("💡 如需插入额外数据，请设置环境变量: export SYNTHESIZER_API_KEY='your_openai_api_key'")
            return
            
        logger.info("📝 在外部知识图谱基础上插入额外数据...")
        return await super().insert(read_config, split_config)
    
    def search(self, search_config: Dict):
        """
        重写搜索方法，无trainee模式下仍可正常工作
        注意：父类的search方法被@async_to_sync_method装饰，所以这里不需要async/await
        """
        logger.info("🔍 执行搜索操作（无trainee模式）...")
        return super().search(search_config)
    
    def quiz_and_judge(self, quiz_and_judge_config: Dict):
        """
        重写问答测试方法，无trainee模式下跳过此步骤
        注意：父类的quiz_and_judge方法被@async_to_sync_method装饰，所以这里不需要async/await
        """
        if self.no_trainee_mode or self.trainee_llm_client is None:
            if self.no_trainee_mode:
                logger.info("🚫 无trainee模式：跳过问答测试和判断步骤")
            else:
                logger.warning("⚠️  Trainee 客户端未初始化，跳过问答测试和判断步骤")
            return
        
        return super().quiz_and_judge(quiz_and_judge_config)
    
    def generate(self, partition_config: Dict, generate_config: Dict):
        """
        重写生成方法，处理无trainee模式和缺少synthesizer客户端的情况
        注意：父类的generate方法被@async_to_sync_method装饰，所以这里不需要async/await
        """
        if self.synthesizer_llm_client is None:
            logger.error("❌ 无法生成数据：synthesizer_llm_client 未初始化")
            logger.info("💡 请设置环境变量: export SYNTHESIZER_API_KEY='your_openai_api_key'")
            logger.info("💡 或者使用简化版生成方案")
            raise ValueError("synthesizer_llm_client 未初始化，无法进行数据生成")
        
        # 在无trainee模式下，如果使用了基于loss的edge_sampling，需要改为random
        if (self.no_trainee_mode or self.trainee_llm_client is None):
            if (partition_config.get("method") == "ece" 
                and "method_params" in partition_config
                and partition_config["method_params"].get("edge_sampling") in ["max_loss", "min_loss"]):
                logger.warning("无trainee模式下，edge_sampling从 '%s' 改为 'random'，因为没有loss属性", 
                             partition_config["method_params"]["edge_sampling"])
                partition_config["method_params"]["edge_sampling"] = "random"
        
        logger.info("🚀 开始生成数据（无trainee模式）...")
        return super().generate(partition_config, generate_config)
    
    def generate_sync(self, partition_config: Dict, generate_config: Dict):
        """
        同步版本的生成方法，避免事件循环冲突
        """
        import asyncio
        
        # 检查是否已经在事件循环中
        try:
            loop = asyncio.get_running_loop()
            # 如果已经在事件循环中，创建一个任务并等待
            logger.warning("检测到正在运行的事件循环，创建异步任务")
            
            # 创建异步任务
            task = loop.create_task(super().generate(partition_config, generate_config))
            
            # 使用 nest_asyncio 来运行任务
            try:
                import nest_asyncio
                nest_asyncio.apply()
                return loop.run_until_complete(task)
            except ImportError:
                # 如果没有 nest_asyncio，抛出错误让上层处理
                raise RuntimeError("需要安装 nest_asyncio 来处理嵌套事件循环")
            
        except RuntimeError as e:
            if "no running event loop" in str(e):
                # 没有运行中的事件循环，可以安全地创建新的
                return asyncio.run(super().generate(partition_config, generate_config))
            else:
                raise
    
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
            else:
                # 如果禁用了问答测试，需要将edge_sampling设为random，因为没有loss属性
                logger.warning("Quiz and Judge strategy is disabled. Edge sampling falls back to random.")
                if (config["partition"]["method"] == "ece" 
                    and "method_params" in config["partition"]):
                    config["partition"]["method_params"]["edge_sampling"] = "random"
            
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