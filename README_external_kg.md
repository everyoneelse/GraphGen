# 使用外部知识图谱（youtu-graphrag）进行 GraphGen 数据生成

本指南详细介绍如何将 `youtu-graphrag` 生成的知识图谱集成到 GraphGen 中进行数据生成。

## 🎯 概述

GraphGen 原本会从文本自动构建知识图谱，但通过我们提供的工具，你可以：
1. 使用 `youtu-graphrag` 预先构建的知识图谱
2. 跳过 GraphGen 的知识图谱构建步骤
3. 直接基于外部知识图谱生成训练数据

## 📋 前置要求

1. **环境配置**：
   ```bash
   # 安装 GraphGen 依赖
   pip install -r requirements.txt
   
   # 确保有以下环境变量
   export SYNTHESIZER_MODEL="your_model_name"
   export SYNTHESIZER_API_KEY="your_api_key"
   export SYNTHESIZER_BASE_URL="your_base_url"
   export TRAINEE_MODEL="your_trainee_model"
   export TRAINEE_API_KEY="your_trainee_api_key"
   export TRAINEE_BASE_URL="your_trainee_base_url"
   ```

2. **youtu-graphrag 输出文件**：
   - 实体文件（CSV/JSON/JSONL 格式）
   - 关系文件（CSV/JSON/JSONL 格式）

## 🚀 快速开始

### 方法 1: 一键运行脚本

```bash
# 从 youtu-graphrag 原始文件开始
python run_with_external_kg.py \
    --entities path/to/youtu_entities.csv \
    --relationships path/to/youtu_relationships.csv \
    --working-dir cache \
    --mode atomic \
    --format Alpaca \
    --quiz-samples 5

# 如果已有转换好的 GraphML 文件
python run_with_external_kg.py \
    --external-graph cache/external_graph.graphml \
    --working-dir cache \
    --mode atomic \
    --skip-convert
```

### 方法 2: 分步执行

#### 步骤 1: 转换知识图谱格式

```bash
python youtu_graphrag_converter.py \
    --entities path/to/youtu_entities.csv \
    --relationships path/to/youtu_relationships.csv \
    --output cache/external_graph.graphml \
    --validate
```

#### 步骤 2: 使用自定义 GraphGen 生成数据

```python
import asyncio
from custom_graphgen import CustomGraphGen, create_custom_config

async def main():
    # 创建配置
    config = create_custom_config(
        external_graph_path="cache/external_graph.graphml",
        generation_mode="atomic",  # atomic, aggregated, multi_hop, cot
        data_format="Alpaca",      # Alpaca, Sharegpt, ChatML
        quiz_samples=5,
        max_depth=3,
        max_extra_edges=5
    )
    
    # 创建 GraphGen 实例
    graph_gen = CustomGraphGen(
        external_graph_path="cache/external_graph.graphml",
        working_dir="cache"
    )
    
    # 执行生成流程
    await graph_gen.insert(config["read"], config["split"])
    await graph_gen.quiz_and_judge(config["quiz_and_judge"])
    await graph_gen.generate(config["partition"], config["generate"])
    
    print("✅ 数据生成完成！")

# 运行
asyncio.run(main())
```

## 📊 支持的数据格式

### youtu-graphrag 输入格式

**实体文件字段映射**：
- `id`/`entity_id`/`name`/`entity_name` → 实体ID
- `type`/`entity_type`/`category` → 实体类型
- `description`/`summary`/`content` → 实体描述

**关系文件字段映射**：
- `source`/`src_id`/`source_entity` → 源实体
- `target`/`tgt_id`/`target_entity` → 目标实体
- `description`/`relationship_summary` → 关系描述
- `weight`/`strength`/`confidence` → 关系权重

### 输出格式

支持多种训练数据格式：
- **Alpaca**: 适用于指令微调
- **Sharegpt**: 适用于对话训练
- **ChatML**: 适用于聊天模型

## 🎛️ 配置参数详解

### 生成模式 (mode)
- `atomic`: 生成基础知识的原子问答对
- `aggregated`: 生成整合复杂知识的聚合问答对
- `multi_hop`: 生成多跳推理问答对
- `cot`: 生成思维链问答对

### 分区参数 (partition)
- `max_depth`: 图遍历的最大深度（默认: 3）
- `max_extra_edges`: 每个方向的最大额外边数（默认: 5）
- `edge_sampling`: 边采样策略（`random`, `max_loss`, `min_loss`）
- `expand_method`: 扩展方法（`max_width`, `max_depth`）

### 测试参数 (quiz_and_judge)
- `quiz_samples`: 生成的测试样本数量
- `re_judge`: 是否重新判断现有样本

## 📁 文件结构

```
project/
├── youtu_graphrag_converter.py    # 格式转换器
├── custom_graphgen.py             # 自定义 GraphGen 类
├── run_with_external_kg.py        # 一键运行脚本
├── cache/                         # 工作目录
│   ├── external_graph.graphml     # 转换后的知识图谱
│   ├── graph_statistics.json      # 图谱统计信息
│   └── data/graphgen/             # 生成的训练数据
└── .env                          # 环境变量配置
```

## 🔧 高级用法

### 1. 自定义实体类型映射

```python
# 在转换器中自定义映射逻辑
class CustomConverter(YoutuGraphRAGConverter):
    def _normalize_entity_type(self, entity_data):
        # 自定义实体类型映射
        type_mapping = {
            'PERSON': 'person',
            'ORG': 'organization',
            'LOC': 'location',
            # 添加更多映射...
        }
        original_type = super()._normalize_entity_type(entity_data)
        return type_mapping.get(original_type, original_type)
```

### 2. 批量处理多个图谱

```python
import glob

# 批量转换多个 youtu-graphrag 输出
for entities_file in glob.glob("youtu_output/*/entities.csv"):
    relationships_file = entities_file.replace("entities.csv", "relationships.csv")
    output_file = f"cache/graph_{os.path.basename(os.path.dirname(entities_file))}.graphml"
    
    converter = YoutuGraphRAGConverter()
    # ... 转换逻辑
```

### 3. 混合知识图谱

```python
# 合并多个知识图谱
import networkx as nx

def merge_graphs(graph_files):
    merged = nx.Graph()
    for graph_file in graph_files:
        g = nx.read_graphml(graph_file)
        merged = nx.compose(merged, g)
    return merged

# 使用合并后的图谱
merged_graph = merge_graphs(["graph1.graphml", "graph2.graphml"])
nx.write_graphml(merged_graph, "merged_graph.graphml")
```

## 🐛 故障排除

### 常见问题

1. **转换失败**：
   ```
   ❌ 转换失败: KeyError: 'id'
   ```
   **解决方案**：检查实体文件是否包含 `id`、`name` 或 `entity_name` 字段

2. **图谱加载失败**：
   ```
   ❌ 加载外部知识图谱失败: not well-formed
   ```
   **解决方案**：检查 GraphML 文件格式，确保所有属性值都是字符串类型

3. **生成数据为空**：
   ```
   ⚠️ 没有生成任何数据
   ```
   **解决方案**：
   - 检查图谱是否有足够的连通节点
   - 调整 `max_depth` 和 `max_extra_edges` 参数
   - 确保节点有有效的描述信息

### 调试技巧

1. **启用详细日志**：
   ```python
   from graphgen.utils import set_logger
   set_logger("debug.log", if_stream=True)
   ```

2. **检查图谱统计**：
   ```python
   graph_gen = CustomGraphGen(external_graph_path="cache/external_graph.graphml")
   summary = graph_gen.get_graph_summary()
   print(summary)
   ```

3. **验证转换结果**：
   ```bash
   python youtu_graphrag_converter.py --validate
   ```

## 📈 性能优化

1. **大型图谱处理**：
   - 使用 `max_tokens` 限制输入长度
   - 调整 `chunk_size` 和 `chunk_overlap`
   - 考虑图谱分区处理

2. **并发优化**：
   - 调整 LLM 客户端的并发参数
   - 使用更快的存储后端

3. **内存优化**：
   - 对于超大图谱，考虑使用数据库存储
   - 实现懒加载机制

## 📚 参考资料

- [GraphGen 官方文档](https://github.com/open-sciencelab/GraphGen)
- [NetworkX 文档](https://networkx.org/)
- [youtu-graphrag 项目](https://github.com/youtu-graphrag)

## 🤝 贡献

欢迎提交 Issue 和 Pull Request 来改进这个集成方案！