# 使用外部知识图谱（youtu-graphrag）进行 GraphGen 数据生成

基于对 GraphGen 架构的分析，以下是集成外部知识图谱的完整方案：

## 方案概述

GraphGen 使用 NetworkX 和 GraphML 格式存储知识图谱，支持通过自定义存储适配器集成外部知识图谱。

## 集成方案

### 方案 1: 格式转换（推荐）

将 youtu-graphrag 生成的知识图谱转换为 GraphGen 兼容的 GraphML 格式。

#### 步骤 1: 创建转换脚本

```python
import networkx as nx
import json
import pandas as pd
from typing import Dict, Any, List

class YoutuGraphRAGConverter:
    """将 youtu-graphrag 知识图谱转换为 GraphGen 格式"""
    
    def __init__(self):
        self.graph = nx.Graph()
    
    def load_youtu_graphrag_data(self, entities_file: str, relationships_file: str):
        """
        加载 youtu-graphrag 生成的实体和关系数据
        
        Args:
            entities_file: 实体文件路径 (通常是 CSV 或 JSON)
            relationships_file: 关系文件路径 (通常是 CSV 或 JSON)
        """
        # 根据 youtu-graphrag 的输出格式调整
        if entities_file.endswith('.csv'):
            entities_df = pd.read_csv(entities_file)
            relationships_df = pd.read_csv(relationships_file)
        elif entities_file.endswith('.json'):
            with open(entities_file, 'r', encoding='utf-8') as f:
                entities_data = json.load(f)
            with open(relationships_file, 'r', encoding='utf-8') as f:
                relationships_data = json.load(f)
            entities_df = pd.DataFrame(entities_data)
            relationships_df = pd.DataFrame(relationships_data)
        
        return entities_df, relationships_df
    
    def convert_to_graphgen_format(self, entities_df: pd.DataFrame, relationships_df: pd.DataFrame):
        """
        转换为 GraphGen 兼容的格式
        """
        # 添加节点
        for _, entity in entities_df.iterrows():
            node_id = str(entity.get('id', entity.get('name', entity.get('entity_name'))))
            node_data = {
                'entity_name': node_id,
                'entity_type': entity.get('type', entity.get('entity_type', 'unknown')),
                'description': entity.get('description', entity.get('summary', '')),
                'source_id': entity.get('source_id', 'external')
            }
            self.graph.add_node(node_id, **node_data)
        
        # 添加边
        for _, relation in relationships_df.iterrows():
            source = str(relation.get('source', relation.get('src_id', relation.get('source_entity'))))
            target = str(relation.get('target', relation.get('tgt_id', relation.get('target_entity'))))
            edge_data = {
                'weight': relation.get('weight', 1.0),
                'description': relation.get('description', relation.get('relationship_summary', '')),
                'source_id': relation.get('source_id', 'external')
            }
            self.graph.add_edge(source, target, **edge_data)
    
    def save_to_graphml(self, output_file: str):
        """保存为 GraphML 格式"""
        nx.write_graphml(self.graph, output_file)
        print(f"知识图谱已保存到: {output_file}")
        print(f"节点数: {self.graph.number_of_nodes()}")
        print(f"边数: {self.graph.number_of_edges()}")

# 使用示例
converter = YoutuGraphRAGConverter()
entities_df, relationships_df = converter.load_youtu_graphrag_data(
    "path/to/youtu_entities.csv", 
    "path/to/youtu_relationships.csv"
)
converter.convert_to_graphgen_format(entities_df, relationships_df)
converter.save_to_graphml("converted_knowledge_graph.graphml")
```

#### 步骤 2: 修改 GraphGen 配置

```python
# custom_graphgen.py
import os
from graphgen.graphgen import GraphGen
from graphgen.models.storage.networkx_storage import NetworkXStorage

class CustomGraphGen(GraphGen):
    def __init__(self, external_graph_path: str, **kwargs):
        super().__init__(**kwargs)
        self.external_graph_path = external_graph_path
        
    def __post_init__(self):
        super().__post_init__()
        # 使用外部知识图谱替换默认的图存储
        self.graph_storage = NetworkXStorage(
            self.working_dir, namespace="external_graph"
        )
        # 加载外部知识图谱
        self._load_external_graph()
    
    def _load_external_graph(self):
        """加载外部知识图谱"""
        if os.path.exists(self.external_graph_path):
            import networkx as nx
            external_graph = nx.read_graphml(self.external_graph_path)
            self.graph_storage._graph = external_graph
            print(f"已加载外部知识图谱: {external_graph.number_of_nodes()} 个节点, {external_graph.number_of_edges()} 条边")
        else:
            print(f"外部知识图谱文件不存在: {self.external_graph_path}")

# 使用自定义 GraphGen
graph_gen = CustomGraphGen(
    external_graph_path="converted_knowledge_graph.graphml",
    working_dir="cache"
)
```

### 方案 2: 自定义存储适配器

创建专门的存储适配器来直接读取 youtu-graphrag 数据。

```python
# youtu_graphrag_storage.py
import json
import pandas as pd
from typing import Union, List, Dict
from graphgen.bases.base_storage import BaseGraphStorage

class YoutuGraphRAGStorage(BaseGraphStorage):
    """youtu-graphrag 知识图谱存储适配器"""
    
    def __init__(self, entities_file: str, relationships_file: str, **kwargs):
        super().__init__(**kwargs)
        self.entities_file = entities_file
        self.relationships_file = relationships_file
        self._load_data()
    
    def _load_data(self):
        """加载 youtu-graphrag 数据"""
        # 加载实体数据
        if self.entities_file.endswith('.csv'):
            self.entities_df = pd.read_csv(self.entities_file)
        else:
            with open(self.entities_file, 'r', encoding='utf-8') as f:
                entities_data = json.load(f)
            self.entities_df = pd.DataFrame(entities_data)
        
        # 加载关系数据
        if self.relationships_file.endswith('.csv'):
            self.relationships_df = pd.read_csv(self.relationships_file)
        else:
            with open(self.relationships_file, 'r', encoding='utf-8') as f:
                relationships_data = json.load(f)
            self.relationships_df = pd.DataFrame(relationships_data)
    
    async def has_node(self, node_id: str) -> bool:
        return node_id in self.entities_df['id'].values
    
    async def get_node(self, node_id: str) -> Union[dict, None]:
        entity = self.entities_df[self.entities_df['id'] == node_id]
        if not entity.empty:
            return entity.iloc[0].to_dict()
        return None
    
    async def get_all_nodes(self) -> Union[List[dict], None]:
        return [(row['id'], row.to_dict()) for _, row in self.entities_df.iterrows()]
    
    async def get_all_edges(self) -> Union[List[dict], None]:
        edges = []
        for _, row in self.relationships_df.iterrows():
            edges.append((row['source'], row['target'], row.to_dict()))
        return edges
    
    # 实现其他必需的方法...
```

## 完整使用流程

### 1. 准备外部知识图谱数据

```bash
# 假设你已经使用 youtu-graphrag 生成了知识图谱
# 确保有以下文件：
# - entities.csv (实体文件)
# - relationships.csv (关系文件)
```

### 2. 转换数据格式

```python
# convert_kg.py
from external_kg_integration_guide import YoutuGraphRAGConverter

converter = YoutuGraphRAGConverter()
entities_df, relationships_df = converter.load_youtu_graphrag_data(
    "youtu_output/entities.csv", 
    "youtu_output/relationships.csv"
)
converter.convert_to_graphgen_format(entities_df, relationships_df)
converter.save_to_graphml("cache/external_graph.graphml")
```

### 3. 配置 GraphGen

```yaml
# external_kg_config.yaml
read:
  input_file: [] # 空文件列表，因为我们使用外部知识图谱
split:
  chunk_size: 1024
  chunk_overlap: 100
search:
  enabled: false # 禁用搜索，直接使用外部知识图谱
quiz_and_judge:
  enabled: true
  quiz_samples: 5
  re_judge: false
partition:
  method: ece
  method_params:
    bidirectional: true
    edge_sampling: max_loss
    expand_method: max_width
    max_depth: 3
    max_extra_edges: 5
    max_tokens: 256
    loss_strategy: only_edge
generate:
  mode: atomic # 可选: atomic, aggregated, multi_hop, cot
  data_format: Alpaca
```

### 4. 运行数据生成

```python
# generate_with_external_kg.py
import os
import yaml
from custom_graphgen import CustomGraphGen

# 加载配置
with open('external_kg_config.yaml', 'r', encoding='utf-8') as f:
    config = yaml.load(f, Loader=yaml.FullLoader)

# 创建自定义 GraphGen 实例
graph_gen = CustomGraphGen(
    external_graph_path="cache/external_graph.graphml",
    working_dir="cache"
)

# 跳过插入步骤，直接进行数据生成
# graph_gen.insert(read_config=config["read"], split_config=config["split"])  # 跳过

# 可选：搜索增强
if config["search"]["enabled"]:
    graph_gen.search(search_config=config["search"])

# 问答测试和判断
if config["quiz_and_judge"]["enabled"]:
    graph_gen.quiz_and_judge(quiz_and_judge_config=config["quiz_and_judge"])

# 生成数据
graph_gen.generate(
    partition_config=config["partition"],
    generate_config=config["generate"]
)

print("数据生成完成！检查 cache/data/graphgen/ 目录")
```

## 注意事项

1. **数据格式兼容性**: 确保 youtu-graphrag 输出的实体和关系字段与 GraphGen 期望的格式匹配
2. **节点 ID 一致性**: 确保实体 ID 在整个转换过程中保持一致
3. **编码问题**: 处理中文字符时注意编码格式
4. **性能考虑**: 大型知识图谱可能需要分批处理

## 故障排除

1. **图谱加载失败**: 检查 GraphML 文件格式是否正确
2. **节点不匹配**: 验证实体 ID 的一致性
3. **生成质量差**: 调整 partition 参数，特别是 max_depth 和 max_extra_edges

通过以上方案，你可以成功将 youtu-graphrag 生成的知识图谱集成到 GraphGen 中进行数据生成。