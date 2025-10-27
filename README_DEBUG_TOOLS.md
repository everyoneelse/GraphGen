# Node/Edge选取调试工具套件 📊

## 概述

这是一套完整的调试工具，用于分析和优化GraphGen合成数据生成过程中的node和edge选取策略。

---

## 🎯 核心问题

在合成数据生成时，你可能想知道：

1. **选取是否全面？** 有多少节点和边被使用了？
2. **选取是否均衡？** 是否某些节点被重复太多次？
3. **选取是否符合预期？** 优先选择的是高loss还是低loss的edges？
4. **如何优化配置？** 应该调整哪些参数来改善选取效果？

**这套工具就是为了回答这些问题！**

---

## 📦 工具清单

### 1. 核心文档

| 文件 | 用途 | 何时查看 |
|------|------|----------|
| `DEBUG_NODE_EDGE_SELECTION.md` | 完整的技术文档，包含原理、配置、评估方法 | 需要深入理解机制时 |
| `QUICK_START_DEBUG_GUIDE.md` | 快速上手指南，包含实用示例和故障排查 | 第一次使用时 |
| `README_DEBUG_TOOLS.md` | 本文档，工具套件总览 | 了解工具全貌时 |

### 2. 核心工具

| 文件 | 功能 | 输入 | 输出 |
|------|------|------|------|
| `debug_node_edge_selection.py` | 调试器核心，记录和分析选取过程 | nodes, edges, batches | JSON统计数据 + 文本报告 |
| `integrate_debugger.py` | 集成脚本，三种使用方式 | 配置文件 或 batch数据 | 调试报告 |
| `visualize_selection.py` | 可视化工具，生成图表 | 调试数据 | PNG图表 |

---

## 🚀 快速开始（3步）

### 第1步: 运行调试

```bash
python integrate_debugger.py \
    --mode run \
    --config graphgen/configs/aggregated_config.yaml \
    --output_dir ./output
```

**输出**: `./debug_output/` 目录包含所有调试数据

### 第2步: 生成可视化

```bash
python visualize_selection.py \
    --debug_dir ./debug_output \
    --output_dir ./viz_output
```

**输出**: `./viz_output/` 目录包含所有图表

### 第3步: 查看结果

```bash
# 查看文本报告
cat ./debug_output/report.txt

# 查看仪表盘
open ./viz_output/summary_dashboard.png
```

**搞定！** 🎉

---

## 📊 输出说明

### 调试数据目录 (`./debug_output/`)

```
debug_output/
├── batch_details.json          # 每个batch的详细信息
│   └── 包含: batch_id, node_ids, edge_pairs, avg_loss等
│
├── statistics.json              # 完整的统计指标（机器可读）
│   └── 包含: 覆盖率、频次分析、loss分布等
│
├── report.txt                   # 可读的文本报告（人类可读）
│   └── 包含: 统计摘要、优化建议
│
└── uncovered_elements.json      # 未被覆盖的节点和边
    └── 包含: uncovered_nodes, uncovered_edges列表
```

### 可视化目录 (`./viz_output/`)

```
viz_output/
├── coverage_comparison.png      # 节点vs边覆盖率对比
├── batch_size_distribution.png  # Batch大小分布直方图
├── frequency_distribution.png   # Top 10高频节点和边
├── loss_distribution.png        # Loss值分布对比
├── batch_progression.png        # 覆盖率增长曲线
└── summary_dashboard.png        # 综合仪表盘（⭐推荐首先查看）
```

---

## 🎓 使用场景

### 场景A: 第一次使用，想了解基本情况

**步骤**:
1. 使用默认配置运行调试
2. 查看 `summary_dashboard.png` 了解全局
3. 阅读 `report.txt` 中的优化建议

**关注指标**:
- 节点和边的覆盖率
- Batch大小是否合理
- 有无明显的不均衡

---

### 场景B: 覆盖率不理想，想提高

**步骤**:
1. 查看 `uncovered_elements.json` 找出未覆盖的元素
2. 检查这些元素是否重要
3. 根据 `report.txt` 中的建议调整配置
4. 重新运行并对比

**可能的调整**:
```yaml
partition:
  method_params:
    max_extra_edges: 30      # ⬆️ 增加
    max_depth: 5             # ⬆️ 增加
    isolated_node_strategy: add  # 改为add
```

---

### 场景C: 想聚焦模型的弱点

**步骤**:
1. 确保启用 `quiz_and_judge`
2. 设置 `edge_sampling: max_loss`
3. 运行调试并查看 `loss_distribution.png`
4. 验证选取的edges的平均loss是否高于全体

**验证方法**:
- 查看图表中 "Selected Edges" vs "All Edges"
- 选取的平均loss应该明显更高

---

### 场景D: 对比不同配置的效果

**步骤**:
```bash
# 配置A: 随机采样
# 修改config: edge_sampling: random
python integrate_debugger.py --mode run --config config_A.yaml --output_dir output_A
mv debug_output debug_output_A
mv viz_output viz_output_A

# 配置B: 最大loss
# 修改config: edge_sampling: max_loss
python integrate_debugger.py --mode run --config config_B.yaml --output_dir output_B
mv debug_output debug_output_B
mv viz_output viz_output_B

# 对比两个summary_dashboard.png
```

**对比维度**:
- 覆盖率差异
- Loss分布差异
- Batch大小分布差异

---

## 📈 关键指标解读

### 1. 节点覆盖率 (Node Coverage Rate)

**定义**: 被选中的唯一节点数 / 图中总节点数

**理想值**: 
- > 80%: 优秀 ✅
- 60-80%: 良好 ⚠️
- < 60%: 需要优化 ❌

**影响因素**:
- `max_extra_edges`: 越大覆盖率越高
- `max_depth`: 越大覆盖率越高
- `isolated_node_strategy`: add会提高覆盖率

---

### 2. 边覆盖率 (Edge Coverage Rate)

**定义**: 被选中的唯一边数 / 图中总边数

**理想值**:
- > 70%: 优秀 ✅
- 50-70%: 良好 ⚠️
- < 50%: 需要优化 ❌

**注意**: 通常边覆盖率会低于节点覆盖率（因为一个batch可能包含多个节点但更少的边）

---

### 3. 节点/边重复度 (Frequency)

**定义**: 平均每个节点/边出现在多少个batch中

**理想值**:
- 1-3次: 合理 ✅
- 3-5次: 可接受 ⚠️
- > 5次: 可能过度重复 ❌

**说明**:
- 过低（接近1）: 可能数据不够丰富
- 过高（> 10）: 可能某些hub节点被过度采样

---

### 4. Loss分布偏差

**定义**: 选取的elements的平均loss vs 全体平均loss

**根据策略判断**:

| edge_sampling | 期望结果 | 验证方法 |
|--------------|---------|---------|
| max_loss | 选取的平均loss > 全体平均loss | 查看loss_distribution.png |
| min_loss | 选取的平均loss < 全体平均loss | 查看loss_distribution.png |
| random | 选取的平均loss ≈ 全体平均loss | 偏差应 < 10% |

---

## ⚙️ 配置优化速查表

| 问题 | 症状 | 调整方向 | 配置参数 |
|------|------|---------|---------|
| 覆盖率低 | < 60% | ⬆️ 增加扩展范围 | `max_extra_edges` ⬆️, `max_depth` ⬆️ |
| 重复度高 | 平均 > 5 | ⬇️ 减少扩展深度 | `max_depth` ⬇️, `bidirectional: false` |
| 遗漏孤立节点 | 未覆盖节点多 | ✅ 包含孤立节点 | `isolated_node_strategy: add` |
| 想聚焦难点 | loss分布不符 | 🎯 改变采样策略 | `edge_sampling: max_loss` |
| Batch太大 | 生成慢/质量差 | ⬇️ 限制大小 | `max_extra_edges` ⬇️, `max_tokens` ⬇️ |
| Batch太小 | 上下文不足 | ⬆️ 增加大小 | `max_extra_edges` ⬆️, `max_depth` ⬆️ |

---

## 🔧 高级用法

### 1. 自定义统计指标

修改 `debug_node_edge_selection.py` 中的 `_calculate_statistics()`:

```python
def _calculate_statistics(self):
    stats = {}
    
    # 添加自定义指标
    stats['custom_metric'] = {
        'my_value': self._compute_my_metric()
    }
    
    return stats
```

### 2. 导出数据供外部分析

```python
# 读取statistics.json
import json
with open('./debug_output/statistics.json', 'r') as f:
    stats = json.load(f)

# 导出为CSV供Excel分析
import pandas as pd
df = pd.DataFrame({
    'metric': ['node_coverage', 'edge_coverage'],
    'value': [
        stats['node_coverage']['coverage_rate'],
        stats['edge_coverage']['coverage_rate']
    ]
})
df.to_csv('coverage_report.csv', index=False)
```

### 3. 集成到CI/CD

```bash
#!/bin/bash
# ci_check_coverage.sh

# 运行调试
python integrate_debugger.py --mode run --config config.yaml --output_dir ./output

# 检查覆盖率
node_cov=$(jq '.node_coverage.coverage_rate' ./debug_output/statistics.json)
edge_cov=$(jq '.edge_coverage.coverage_rate' ./debug_output/statistics.json)

# 设定阈值
if (( $(echo "$node_cov < 0.7" | bc -l) )); then
    echo "❌ Node coverage too low: $node_cov"
    exit 1
fi

echo "✅ Coverage check passed"
```

---

## 🐛 常见问题

### Q1: 调试工具会影响性能吗？

**A**: 会有轻微影响（约5-10%），因为需要额外的记录和计算。建议：
- 开发/调试时使用
- 生产环境可以关闭或降低记录频率

### Q2: 可以只分析部分batch吗？

**A**: 可以，修改 `record_batch()` 添加采样：

```python
if batch_id % 10 == 0:  # 只记录每10个batch
    debugger.record_batch(batch_id, nodes, edges, config)
```

### Q3: 数据太大，生成的JSON文件很大怎么办？

**A**: 可以只保存汇总信息，不保存详细的node_ids和edge_pairs：

```python
batch_data = {
    'batch_id': batch_id,
    'node_count': len(node_ids),
    'edge_count': len(edge_pairs),
    'avg_loss': avg_loss,
    # 'node_ids': node_ids,  # 注释掉
    # 'edge_pairs': edge_pairs,  # 注释掉
}
```

### Q4: 如何保存多次运行的对比？

**A**: 使用时间戳命名：

```bash
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
python integrate_debugger.py --mode run --config config.yaml --output_dir ./output
mv debug_output debug_output_$TIMESTAMP
mv viz_output viz_output_$TIMESTAMP
```

---

## 📚 学习路径

**新手** (第一次使用):
1. 阅读 `QUICK_START_DEBUG_GUIDE.md`
2. 运行一次完整流程
3. 查看 `summary_dashboard.png`
4. 理解基本概念

**进阶** (需要优化):
1. 阅读 `DEBUG_NODE_EDGE_SELECTION.md` 理解原理
2. 尝试调整配置参数
3. 对比不同配置的效果
4. 根据建议迭代优化

**专家** (深度定制):
1. 修改源码集成调试器
2. 自定义统计指标
3. 开发新的可视化图表
4. 集成到自动化流程

---

## 🤝 贡献和反馈

### 发现Bug?

请提供：
- 配置文件
- 错误日志
- 预期 vs 实际行为

### 功能建议?

欢迎提出：
- 新的统计指标
- 新的可视化图表
- 新的使用场景

### 改进建议?

随时反馈：
- 文档不清晰的地方
- 工具使用困难的地方
- 性能问题

---

## 📄 许可证

与GraphGen项目保持一致。

---

## 🎉 总结

这套工具帮助你：

✅ **了解** - 知道选取了哪些nodes和edges  
✅ **评估** - 判断选取是否全面和均衡  
✅ **优化** - 根据数据驱动的建议调整配置  
✅ **验证** - 确认优化后的效果

**现在开始使用吧！** 🚀

---

**快速链接**:
- [📖 快速开始](./QUICK_START_DEBUG_GUIDE.md)
- [📚 完整文档](./DEBUG_NODE_EDGE_SELECTION.md)
- [🔧 核心工具](./debug_node_edge_selection.py)
- [📊 可视化](./visualize_selection.py)
