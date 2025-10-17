# 图采样模式在问题生成中的应用分析

**对话时间**: 2025-10-13  
**主题**: 图采样在问题生成中的不同模式介绍  
**分析范围**: atomic、aggregated、multi_hop、cot等模式

---

## 用户问题

在生成问题时，是如何对图进行采样的，帮我按照atomic、集成模式等等不同的模式介绍下

---

## 分析结果

### 1. 核心采样策略

在问题生成过程中，图采样主要通过以下几个维度进行控制：

#### **边采样策略 (Edge Sampling)**
- **`random`**: 随机采样边
- **`max_loss`**: 优先选择损失值高的边（基于理解困难度）
- **`min_loss`**: 优先选择损失值低的边

#### **扩展方法 (Expand Method)**
- **`max_width`**: 基于最大宽度扩展，控制每个方向的最大边数
- **`max_tokens`**: 基于token限制扩展，控制输入长度

### 2. 四种问题生成模式

#### **Atomic 模式（原子模式）**
```yaml
mode: atomic
max_depth: 3
max_extra_edges: 5
edge_sampling: max_loss
```

**特点：**
- 针对图中的**单个节点或边**生成问题
- 每个实体或关系独立生成一个问答对
- 覆盖基础知识点，问题相对简单
- 适合知识点的细粒度学习

**采样过程：**
```python
# 来源: graphgen/operators/traverse_graph.py (行 387-395)
for node in nodes:
    if "<SEP>" in node[1]["description"]:
        description_list = node[1]["description"].split("<SEP>")
        for item in description_list:
            tasks.append((node[0], {"description": item}))
            if "loss" in node[1]:
                tasks[-1][1]["loss"] = node[1]["loss"]
    else:
        tasks.append((node[0], node[1]))
```

#### **Aggregated 模式（聚合模式）**
```yaml
mode: aggregated  
max_depth: 5
max_extra_edges: 20
edge_sampling: max_loss
```

**特点：**
- 基于**图分割策略**，将相关的节点和边组合成批次
- 每个批次包含多个相互关联的实体和关系
- 生成整合复杂知识的综合性问答对
- 问题复杂度较高，需要理解多个概念间的关系

**采样过程：**
```python
# 来源: graphgen/operators/traverse_graph.py (行 281-283)
processing_batches = await get_batches_with_strategy(
    nodes, edges, graph_storage, traverse_strategy
)
```

#### **Multi-hop 模式（多跳模式）**
```yaml
mode: multi_hop
max_depth: 1
max_extra_edges: 2  
edge_sampling: max_loss
```

**特点：**
- 专门设计用于生成**多跳推理**问答对
- 需要通过多个实体和关系进行推理才能得到答案
- 深度相对较浅但关系复杂
- 培养逻辑推理能力

**采样过程：**
```python
# 来源: graphgen/operators/traverse_graph.py (行 451-453)
processing_batches = await get_batches_with_strategy(
    nodes, edges, graph_storage, traverse_strategy
)
```

#### **CoT 模式（思维链模式）**
```yaml
mode: cot
method: leiden  # 使用社区检测算法
```

**特点：**
- 使用**社区检测算法**（如Leiden）对图进行分割
- 为每个社区生成包含推理路径的问答对
- 不仅提供答案，还展示推理过程
- 培养逐步推理的思维能力

**采样过程：**
```python
# 来源: graphgen/operators/generate/generate_cot.py (行 16-21)
detector = CommunityDetector(
    graph_storage=graph_storage, method=method, method_params=method_params
)
results = await detector.detect_communities()
```

### 3. 图分割策略详解

#### **ECE分割方法**
所有模式（除CoT外）都使用ECE（基于理解损失的自定义分割方法）：

**工作原理：**
1. 从源边开始，根据`bidirectional`参数决定遍历方向
2. 按照`edge_sampling`策略对候选边进行排序
3. 根据`max_depth`和`max_extra_edges`限制扩展范围
4. 使用`loss_strategy`决定损失计算方式

#### **边排序机制**
```python
# 来源: graphgen/operators/build_kg/split_kg.py (行 201-225)
def _sort_tuples(er_tuples: list, edge_sampling: str) -> list:
    if edge_sampling == "random":
        er_tuples = random.sample(er_tuples, len(er_tuples))
    elif edge_sampling == "min_loss":
        er_tuples = sorted(
            er_tuples,
            key=lambda x: sum(node[1]["loss"] for node in x[0]) + x[1][2]["loss"],
        )
    elif edge_sampling == "max_loss":
        er_tuples = sorted(
            er_tuples,
            key=lambda x: sum(node[1]["loss"] for node in x[0]) + x[1][2]["loss"],
            reverse=True,
        )
```

### 4. 配置文件对比

#### Atomic配置
```yaml
# graphgen/configs/atomic_config.yaml
partition:
  method: ece
  method_params:
    bidirectional: true
    edge_sampling: max_loss
    expand_method: max_width
    max_depth: 3
    max_extra_edges: 5
    max_tokens: 256
generate:
  mode: atomic
```

#### Aggregated配置
```yaml
# graphgen/configs/aggregated_config.yaml
partition:
  method: ece
  method_params:
    bidirectional: true
    edge_sampling: max_loss
    expand_method: max_width
    max_depth: 5
    max_extra_edges: 20
    max_tokens: 256
generate:
  mode: aggregated
```

#### Multi-hop配置
```yaml
# graphgen/configs/multi_hop_config.yaml
partition:
  method: ece
  method_params:
    bidirectional: true
    edge_sampling: max_loss
    expand_method: max_width
    max_depth: 1
    max_extra_edges: 2
    max_tokens: 256
generate:
  mode: multi_hop
```

#### CoT配置
```yaml
# graphgen/configs/cot_config.yaml
partition:
  method: leiden
  method_params:
    max_size: 20
    use_lcc: false
    random_seed: 42
generate:
  mode: cot
```

### 5. 模式对比总结

| 模式 | 采样粒度 | 复杂度 | 适用场景 | 分割策略 | 深度 | 边数 |
|------|----------|--------|----------|----------|------|------|
| **Atomic** | 单个节点/边 | 低 | 基础知识学习 | 逐个处理 | - | - |
| **Aggregated** | 节点-边批次 | 高 | 综合知识理解 | ECE图分割 | 5 | 20 |
| **Multi-hop** | 小型子图 | 中-高 | 推理能力训练 | ECE图分割 | 1 | 2 |
| **CoT** | 社区 | 高 | 思维链训练 | 社区检测 | - | - |

### 6. 关键代码文件

- **图分割核心逻辑**: `graphgen/operators/build_kg/split_kg.py`
- **遍历策略实现**: `graphgen/operators/traverse_graph.py`
- **CoT生成逻辑**: `graphgen/operators/generate/generate_cot.py`
- **配置文件目录**: `graphgen/configs/`

---

## 总结

每种模式都通过不同的图采样策略来适应特定的学习目标：

1. **Atomic模式**: 最细粒度，适合基础知识点学习
2. **Aggregated模式**: 最大规模采样，适合复杂知识整合
3. **Multi-hop模式**: 精确小规模采样，专注推理链条
4. **CoT模式**: 基于社区结构，培养思维链能力

这些模式形成了从简单的知识点记忆到复杂的推理能力培养的完整问题生成体系。