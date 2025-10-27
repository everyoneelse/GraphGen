# Node和Edge选取机制梳理与调试指南

## 一、选取机制核心逻辑

### 1.1 选取流程概览

```
数据输入 → 构建知识图谱 → Quiz测评(可选) → 图分区与遍历 → 生成QA数据
                                        ↓
                              Node/Edge 选取发生在这里
```

### 1.2 关键选取环节

#### **环节1：批次构建（Batch Construction）**
- **位置**: `graphgen/operators/build_kg/split_kg.py` 中的 `get_batches_with_strategy()`
- **作用**: 决定哪些nodes和edges被组合成一个batch用于生成QA
- **核心逻辑**:
  1. 首先对所有edges进行排序（基于edge_sampling策略）
  2. 遍历每条edge，以其为中心进行图扩展
  3. 根据expand_method（max_width或max_tokens）决定扩展边界
  4. 通过max_depth控制扩展的跳数

#### **环节2：图遍历生成（Graph Traversal）**
- **位置**: `graphgen/operators/traverse_graph.py`
- **作用**: 将选取的nodes和edges生成为QA对
- **模式**:
  - `atomic`: 每个node/edge单独生成一个QA
  - `aggregated`: 将一个batch的nodes/edges聚合生成QA
  - `multi_hop`: 生成需要多跳推理的QA

---

## 二、关键配置参数详解

### 2.1 Edge采样策略 (edge_sampling)

```yaml
edge_sampling: max_loss  # random, max_loss, min_loss
```

- **random**: 随机选择edges（适合探索性分析）
- **max_loss**: 优先选择loss最高的edges（模型最难掌握的知识点）
- **min_loss**: 优先选择loss最低的edges（模型已掌握的知识点）

**注意**: 使用max_loss/min_loss需要开启`quiz_and_judge`功能来计算loss值

### 2.2 扩展方法 (expand_method)

#### max_width模式
```yaml
expand_method: max_width
max_depth: 5              # 最多扩展5跳
max_extra_edges: 20       # 每个方向最多额外选20条边
```

- 以某条edge为起点
- 向外扩展max_depth跳
- 每跳最多选max_extra_edges条边
- **优点**: 控制batch规模精确
- **缺点**: 可能遗漏相关但距离远的节点

#### max_tokens模式
```yaml
expand_method: max_tokens
max_depth: 5
max_tokens: 256           # 限制总token数
```

- 以token数量为边界限制
- 直到达到max_tokens或max_depth
- **优点**: 控制输入长度，适配模型能力
- **缺点**: 可能截断重要关系

### 2.3 Loss策略 (loss_strategy)

```yaml
loss_strategy: only_edge  # only_edge, both
```

- **only_edge**: 仅考虑edge的loss值进行排序
- **both**: 同时考虑edge和相关nodes的loss值

### 2.4 方向性 (bidirectional)

```yaml
bidirectional: true  # true表示双向扩展
```

- **true**: 从source和target双向扩展（更全面）
- **false**: 仅从target单向扩展（更聚焦）

### 2.5 孤立节点策略 (isolated_node_strategy)

```yaml
isolated_node_strategy: ignore  # ignore, add
```

- **ignore**: 忽略没有边的孤立节点
- **add**: 将孤立节点也加入生成（可能遗漏知识点）

---

## 三、如何判断选取是否全面

### 3.1 覆盖率指标

#### Node覆盖率
```
已选取的唯一节点数 / 图中总节点数
```

#### Edge覆盖率
```
已选取的唯一边数 / 图中总边数
```

#### 源文本覆盖率
```
被使用的原始文本块数 / 总文本块数
```

### 3.2 分布均衡性

- **度分布**: 高度节点（hub）是否被充分采样
- **社区分布**: 不同社区/主题的nodes是否均衡
- **Loss分布**: 各loss区间的nodes/edges是否都有覆盖

### 3.3 重复度分析

- 同一node/edge在不同batch中出现的次数
- 过高：可能导致数据冗余
- 过低：可能表示采样不足

---

## 四、调试方法

### 4.1 添加日志输出

**方法1**: 在`split_kg.py`中添加详细日志

在`get_batches_with_strategy()`函数中添加：

```python
logger.info("=" * 80)
logger.info(f"Total nodes: {len(nodes)}, Total edges: {len(edges)}")
logger.info(f"Edge sampling strategy: {edge_sampling}")
logger.info(f"Expand method: {expand_method}, Max depth: {max_depth}")

# 在循环中统计
selected_nodes = set()
selected_edges = set()

for batch in processing_batches:
    nodes_in_batch = [n['node_id'] for n in batch[0]]
    edges_in_batch = [(e[0], e[1]) for e in batch[1]]
    
    selected_nodes.update(nodes_in_batch)
    selected_edges.update(edges_in_batch)
    
    logger.info(f"Batch: {len(batch[0])} nodes, {len(batch[1])} edges")

logger.info(f"Node coverage: {len(selected_nodes)}/{len(nodes)} = {len(selected_nodes)/len(nodes)*100:.2f}%")
logger.info(f"Edge coverage: {len(selected_edges)}/{len(edges)} = {len(selected_edges)/len(edges)*100:.2f}%")
```

**方法2**: 开启详细日志级别

在运行脚本前设置：
```python
import logging
logging.getLogger('graphgen').setLevel(logging.DEBUG)
```

### 4.2 保存中间数据

修改代码保存batch信息：

```python
import json

# 在 get_batches_with_strategy() 返回前
batch_info = []
for i, (nodes, edges) in enumerate(processing_batches):
    batch_info.append({
        'batch_id': i,
        'node_ids': [n['node_id'] for n in nodes],
        'edge_pairs': [(e[0], e[1]) for e in edges],
        'node_count': len(nodes),
        'edge_count': len(edges),
        'avg_loss': get_average_loss((nodes, edges), traverse_strategy['loss_strategy'])
    })

with open('batch_debug_info.json', 'w') as f:
    json.dump(batch_info, f, indent=2, ensure_ascii=False)
```

### 4.3 创建调试脚本

创建独立的分析脚本，读取保存的数据进行分析。

---

## 五、提升全面性的建议

### 5.1 配置调优

#### 提高覆盖率的配置
```yaml
partition:
  method_params:
    bidirectional: true          # 双向扩展
    max_depth: 3                 # 适中的深度
    max_extra_edges: 15          # 中等数量
    isolated_node_strategy: add  # 包含孤立节点
```

#### 聚焦重点的配置
```yaml
partition:
  method_params:
    edge_sampling: max_loss      # 优先难点
    bidirectional: false         # 单向，更聚焦
    max_depth: 5                 # 深度遍历
    max_extra_edges: 30          # 多选边
```

### 5.2 多次运行策略

```python
# 运行多次，使用不同的edge_sampling策略
strategies = ['random', 'max_loss', 'min_loss']
for strategy in strategies:
    config['partition']['method_params']['edge_sampling'] = strategy
    # 运行生成
    # 合并结果
```

### 5.3 分层采样

```python
# 1. 先用max_loss覆盖难点
# 2. 再用random覆盖遗漏
# 3. 最后用min_loss补充简单案例
```

---

## 六、实践检查清单

### 运行前检查
- [ ] 确认quiz_and_judge是否启用（影响loss值）
- [ ] 检查edge_sampling是否与quiz配置匹配
- [ ] 确认expand_method和相关参数是否合理
- [ ] 查看图的规模（nodes/edges数量）

### 运行中监控
- [ ] 观察日志中的batch数量
- [ ] 检查是否有"visited"标记的警告
- [ ] 监控node/edge覆盖率
- [ ] 查看生成的QA数量

### 运行后分析
- [ ] 计算node/edge覆盖率
- [ ] 分析batch大小分布
- [ ] 检查是否有孤立节点被忽略
- [ ] 评估QA质量与知识点覆盖

---

## 七、常见问题

### Q1: 为什么覆盖率很低？
**可能原因**:
1. max_extra_edges设置过小
2. max_depth设置过小
3. 图本身分散，社区间连接少
4. 使用了min_loss但很多edges的loss都很高

**解决方案**:
- 增加max_extra_edges
- 使用max_width模式并调大参数
- isolated_node_strategy改为add

### Q2: 为什么有的节点被重复采样很多次？
**可能原因**:
1. 这些是高度节点(hub)
2. bidirectional=true导致多次访问
3. max_depth太大，反复遍历到

**解决方案**:
- 降低max_depth
- 考虑使用社区检测预处理
- 在代码中添加采样上限

### Q3: 如何平衡覆盖率和数据质量？
**建议**:
1. 不要盲目追求100%覆盖率
2. 优先保证核心知识点的多样性
3. 使用多种策略组合
4. 根据下游任务需求调整

---

## 八、快速诊断命令

### 检查图统计信息
```python
# 在generate完成后
import networkx as nx
G = graph_storage._graph

print(f"Nodes: {G.number_of_nodes()}")
print(f"Edges: {G.number_of_edges()}")
print(f"Density: {nx.density(G)}")
print(f"Is connected: {nx.is_connected(G.to_undirected())}")
print(f"Number of components: {nx.number_connected_components(G.to_undirected())}")
```

### 分析度分布
```python
import matplotlib.pyplot as plt
degrees = [G.degree(n) for n in G.nodes()]
plt.hist(degrees, bins=50)
plt.xlabel('Degree')
plt.ylabel('Count')
plt.title('Node Degree Distribution')
plt.savefig('degree_distribution.png')
```

---

## 九、下一步行动

1. **启用详细日志**: 在运行时添加调试输出
2. **保存中间结果**: 导出batch信息到JSON
3. **编写分析脚本**: 计算覆盖率和分布指标
4. **可视化**: 绘制图结构和采样结果
5. **迭代优化**: 根据分析结果调整配置
