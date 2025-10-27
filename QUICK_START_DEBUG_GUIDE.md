# Node/Edge选取调试 - 快速开始指南

## 🎯 目标

本指南帮助你快速上手调试合成数据生成过程中的node和edge选取，评估选取的全面性。

---

## 📋 准备工作

### 1. 确认文件位置

确保以下文件在你的工作目录中：
- ✅ `debug_node_edge_selection.py` - 调试工具核心
- ✅ `integrate_debugger.py` - 集成脚本
- ✅ `visualize_selection.py` - 可视化工具
- ✅ `DEBUG_NODE_EDGE_SELECTION.md` - 详细文档

### 2. 安装依赖（如果需要可视化）

```bash
pip install matplotlib seaborn numpy
```

---

## 🚀 三种使用方式

### 方式1: 运行时调试（推荐）⭐

**适用场景**: 想在generate过程中实时监控选取过程

```bash
# 1. 使用集成脚本运行
python integrate_debugger.py \
    --mode run \
    --config graphgen/configs/aggregated_config.yaml \
    --output_dir ./output
```

**输出结果**:
- 控制台实时显示覆盖率进度
- `./debug_output/` 目录包含详细数据
  - `batch_details.json` - 每个batch的详情
  - `statistics.json` - 完整统计指标
  - `report.txt` - 可读文本报告
  - `uncovered_elements.json` - 未覆盖的节点和边

**特点**:
- ✅ 无需修改源代码（使用monkey patching）
- ✅ 实时监控
- ✅ 完整的调试信息

---

### 方式2: 修改源码集成

**适用场景**: 需要深度定制或持久化集成

#### 步骤1: 修改 `split_kg.py`

在 `graphgen/operators/build_kg/split_kg.py` 开头添加：

```python
from debug_node_edge_selection import NodeEdgeDebugger

# 创建全局调试器实例
_debugger = None
```

#### 步骤2: 在 `get_batches_with_strategy()` 函数中集成

```python
async def get_batches_with_strategy(nodes, edges, graph_storage, traverse_strategy):
    global _debugger
    
    # 初始化调试器
    if _debugger is None:
        _debugger = NodeEdgeDebugger(output_dir="./debug_output")
    
    # 记录图信息
    _debugger.record_graph_info(nodes, edges)
    
    # ... 原有代码 ...
    
    # 在生成processing_batches后记录
    for i, (batch_nodes, batch_edges) in enumerate(processing_batches):
        _debugger.record_batch(i, batch_nodes, batch_edges, traverse_strategy)
    
    # 生成报告
    _debugger.generate_report()
    
    return processing_batches
```

#### 步骤3: 正常运行

```bash
python graphgen/generate.py \
    --config_file graphgen/configs/aggregated_config.yaml \
    --output_dir ./output
```

**特点**:
- ✅ 持久化集成
- ✅ 可以深度定制
- ❌ 需要修改源代码

---

### 方式3: 事后分析

**适用场景**: 已经运行完成，想分析历史数据

#### 如果你已经有batch数据

```bash
python integrate_debugger.py \
    --mode analyze \
    --batch_file path/to/your/batch_data.json
```

#### 如果需要从头开始

1. 先按方式1或2运行一次generate
2. 使用生成的debug数据进行分析

**特点**:
- ✅ 不影响当前运行
- ✅ 可以反复分析
- ❌ 需要已有数据

---

## 📊 生成可视化报告

在获得调试数据后，生成可视化图表：

```bash
python visualize_selection.py \
    --debug_dir ./debug_output \
    --output_dir ./viz_output
```

**生成的图表**:

1. **coverage_comparison.png** - 节点和边的覆盖率对比
2. **batch_size_distribution.png** - Batch大小分布
3. **frequency_distribution.png** - Top 10高频节点和边
4. **loss_distribution.png** - Loss值分布对比
5. **batch_progression.png** - 覆盖率随batch增长的曲线
6. **summary_dashboard.png** - 综合仪表盘

---

## 🔍 如何解读结果

### 1. 查看文本报告

```bash
cat ./debug_output/report.txt
```

重点关注：
- **节点覆盖率**: 应该 > 70%（取决于你的需求）
- **边覆盖率**: 应该 > 60%
- **重复度**: 平均重复度在 1-3 之间较为合理

### 2. 检查未覆盖元素

```bash
cat ./debug_output/uncovered_elements.json
```

分析：
- 未覆盖的节点是否重要？
- 是否都是孤立节点？
- 是否需要调整策略覆盖这些节点？

### 3. 查看可视化仪表盘

打开 `./viz_output/summary_dashboard.png`

一图了解：
- 整体覆盖率状况
- Batch统计分布
- 频次分析
- Loss分布（如果启用quiz）

---

## ⚙️ 常见调试场景

### 场景1: 覆盖率太低怎么办？

**现象**: 节点覆盖率 < 50%

**诊断步骤**:
1. 查看配置中的 `max_extra_edges` 和 `max_depth`
2. 检查 `isolated_node_strategy` 是否为 `ignore`
3. 查看未覆盖元素是否都是孤立节点

**解决方案**:
```yaml
# 在配置文件中调整
partition:
  method_params:
    max_extra_edges: 30        # 增加（原值可能是10-20）
    max_depth: 5               # 增加（原值可能是3）
    isolated_node_strategy: add  # 改为add
    bidirectional: true        # 启用双向
```

重新运行并对比覆盖率变化。

---

### 场景2: 某些节点重复太多次

**现象**: 报告中显示某个节点出现了 20+ 次

**诊断步骤**:
1. 查看 `frequency_distribution.png` 找出高频节点
2. 检查这些节点是否是hub节点（连接很多边）
3. 查看配置中的 `max_depth` 是否过大

**解决方案**:
```yaml
partition:
  method_params:
    max_depth: 3               # 减小深度
    bidirectional: false       # 改为单向
```

或者在代码中添加采样上限（需要修改源码）。

---

### 场景3: 想优先覆盖难点知识

**需求**: 优先选择模型最难掌握的edges

**配置方案**:
```yaml
quiz_and_judge:
  enabled: true               # 必须启用
  quiz_samples: 2

partition:
  method_params:
    edge_sampling: max_loss   # 优先高loss
    loss_strategy: both       # 同时考虑node和edge的loss
```

**验证方法**:
1. 运行后查看 `loss_distribution.png`
2. 确认 "Selected Edges" 的平均loss高于 "All Edges"

---

### 场景4: 想要更均衡的采样

**需求**: 不要偏向某种策略，尽量均衡覆盖

**配置方案**:
```yaml
partition:
  method_params:
    edge_sampling: random     # 随机采样
    bidirectional: true       # 双向扩展
    max_depth: 4              # 适中深度
```

**多次运行策略**:
```bash
# 运行3次，每次用不同策略
for strategy in random max_loss min_loss; do
    # 修改配置中的edge_sampling
    # 运行generate
    # 合并结果
done
```

---

## 📈 评估全面性的检查清单

运行完调试后，按此清单评估：

### ✅ 覆盖率指标
- [ ] 节点覆盖率 > 70%
- [ ] 边覆盖率 > 60%
- [ ] 孤立节点是否需要覆盖（根据业务决定）

### ✅ 分布均衡性
- [ ] Batch大小分布是否合理（不要差异太大）
- [ ] 节点/边的重复度分布是否合理（1-3次为宜）
- [ ] 没有单个节点/边被过度采样（> 10次）

### ✅ Loss分布（如果启用）
- [ ] 选取的edges的loss分布是否符合预期
  - 使用max_loss: 选取的平均loss应该 > 全体平均loss
  - 使用min_loss: 选取的平均loss应该 < 全体平均loss
  - 使用random: 选取的平均loss应该 ≈ 全体平均loss

### ✅ 质量评估
- [ ] 抽查生成的QA是否包含多样的知识点
- [ ] 检查未覆盖的节点是否包含重要信息
- [ ] 确认没有大量重复的QA对

---

## 🎓 最佳实践建议

### 1. 首次运行

```yaml
# 使用这个配置作为baseline
partition:
  method_params:
    edge_sampling: random
    expand_method: max_width
    max_depth: 4
    max_extra_edges: 20
    bidirectional: true
    isolated_node_strategy: add
```

目标: 建立覆盖率基准

### 2. 迭代优化

基于baseline结果，逐步调整：
- 如果覆盖率低 → 增加max_extra_edges和max_depth
- 如果重复度高 → 减少max_depth
- 如果想聚焦难点 → 改用max_loss + 启用quiz

### 3. 多策略组合

```bash
# 运行3轮，每轮不同策略
# 第1轮: 覆盖难点
edge_sampling: max_loss

# 第2轮: 补充简单案例  
edge_sampling: min_loss

# 第3轮: 随机补充
edge_sampling: random

# 合并所有结果
```

### 4. 持续监控

每次运行都：
1. 保存调试报告
2. 对比不同运行的覆盖率
3. 记录配置和结果的对应关系

---

## 🐛 故障排查

### 问题1: ModuleNotFoundError

```
ModuleNotFoundError: No module named 'debug_node_edge_selection'
```

**解决**: 确保 `debug_node_edge_selection.py` 在Python path中

```bash
export PYTHONPATH="${PYTHONPATH}:/path/to/workspace"
```

或直接在工作目录运行。

### 问题2: 没有生成debug文件

**原因**: 可能是调试器没有被正确调用

**检查**:
1. 确认看到了 "调试模式已启用" 的日志
2. 查看是否有错误信息
3. 尝试使用方式1（monkey patching）

### 问题3: 可视化图表中文乱码

**解决**:
```python
# 在 visualize_selection.py 中修改
plt.rcParams['font.sans-serif'] = ['Arial']  # 使用英文字体
```

### 问题4: 内存不足

**现象**: 图很大时，调试过程内存占用高

**解决**:
- 只记录关键信息，不要保存完整的node/edge内容
- 定期写入文件，不要全部留在内存中
- 考虑采样分析，不需要100%的batch都记录

---

## 📞 更多帮助

- 详细文档: 查看 `DEBUG_NODE_EDGE_SELECTION.md`
- 代码注释: 查看各个脚本中的docstring
- 输出日志: 查看 `./debug_output/report.txt`

---

## 🎉 快速命令备忘

```bash
# 一键运行调试
python integrate_debugger.py --mode run --config <your_config> --output_dir ./output

# 生成可视化
python visualize_selection.py --debug_dir ./debug_output --output_dir ./viz_output

# 查看报告
cat ./debug_output/report.txt

# 查看未覆盖元素
cat ./debug_output/uncovered_elements.json | jq '.uncovered_node_count, .uncovered_edge_count'
```

---

**祝调试顺利！** 🚀
