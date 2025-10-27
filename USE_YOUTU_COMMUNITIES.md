# 使用 Youtu-GraphRAG 预计算的社区信息

本指南说明如何使用 youtu-graphrag 生成的知识图谱中已有的社区（community）信息来生成 COT (Chain-of-Thought) 训练数据。

## 背景

youtu-graphrag 在生成知识图谱时会自动进行社区检测，并将社区信息存储在 `graph.json` 中。社区节点的格式如下：

```json
{
  "start_node": {
    "label": "keyword",
    "properties": {
      "name": "周期性运动"
    }
  },
  "relation": "keyword_of",
  "end_node": {
    "label": "community",
    "properties": {
      "name": "周期性伪影分析",
      "description": "该社区研究周期性运动导致的伪影特征...",
      "members": [
        "纤维性组织",
        "诊断准确性",
        "周期性鬼影",
        ...
      ]
    }
  }
}
```

## 功能特点

现在系统支持：

1. **自动识别社区信息**：从 youtu-graphrag JSON 中自动提取社区节点和成员信息
2. **跳过重复检测**：使用已有的社区信息，无需重新运行 Leiden 算法
3. **无缝集成**：在 COT 模式下自动使用预计算的社区
4. **社区导出**：可以导出社区信息到单独的 JSON 文件

## 使用方法

### 方法 1：完整流程（推荐）

使用 COT 模式时，系统会自动检测并使用 youtu-graphrag 的社区信息：

```bash
python run_youtu_json_kg.py \
  --json path/to/youtu_graph.json \
  --working-dir cache \
  --mode cot \
  --format Alpaca \
  --disable-quiz
```

**输出示例：**
```
🔄 开始转换 youtu-graphrag JSON 知识图谱...
正在加载 youtu-graphrag JSON 数据: path/to/youtu_graph.json
加载完成 - 共 1234 条关系记录
开始解析数据结构...
解析完成:
  - 实体节点: 456
  - 属性节点: 123
  - 社区节点: 15
  - 关系: 789

✅ 已提取 15 个社区信息，包含 456 个节点
✅ 使用 youtu-graphrag 预计算的社区信息（15 个社区）

[Generating COT] Generating CoT data from communities: 100%|██████| 15/15
```

### 方法 2：分步执行

如果需要分步执行或检查社区信息：

#### 步骤 1：转换图谱并导出社区

```bash
python youtu_json_converter.py \
  --input path/to/youtu_graph.json \
  --output cache/youtu_graph.graphml \
  --stats cache/stats.json
```

这会生成：
- `cache/youtu_graph.graphml` - 转换后的图谱
- `cache/stats.json` - 包含社区数量的统计信息
- `cache/youtu_communities.json` - 社区详细信息（自动生成）

#### 步骤 2：查看社区信息

```bash
cat cache/youtu_communities.json
```

输出格式：
```json
[
  {
    "name": "周期性伪影分析",
    "description": "该社区研究周期性运动导致的伪影特征...",
    "members": ["纤维性组织", "诊断准确性", "周期性鬼影", ...],
    "member_count": 10
  },
  ...
]
```

#### 步骤 3：使用转换后的图谱生成 COT 数据

```bash
python run_youtu_json_kg.py \
  --external-graph cache/youtu_graph.graphml \
  --json path/to/youtu_graph.json \
  --working-dir cache \
  --mode cot \
  --format Alpaca \
  --disable-quiz \
  --skip-convert
```

## 配置选项

### COT 模式特定配置

在 `cot_config.yaml` 或自定义配置中：

```yaml
partition:
  method: leiden  # 如果没有预计算社区，将使用此方法
  method_params:
    max_size: 20  # 最大社区大小，如果社区超过此大小会被分割
    use_lcc: false
    random_seed: 42
```

### 使用预计算社区时的优势

1. **更快的处理速度**：跳过社区检测算法（Leiden）的计算
2. **保持一致性**：使用与 youtu-graphrag 相同的社区划分
3. **领域知识保留**：youtu-graphrag 的社区可能基于领域特定的规则

## 代码实现细节

### 新增的类和方法

1. **`PrecomputedCommunityDetector`**
   - 位置：`graphgen/models/community/precomputed_community_detector.py`
   - 功能：使用预计算的社区信息而非重新检测

2. **`YoutuJSONConverter` 新方法**
   - `export_communities()`: 导出社区信息到 JSON
   - `get_communities_dict()`: 获取社区字典格式 `{node_name: community_id}`

3. **`generate_cot` 新参数**
   - `precomputed_communities`: 可选的预计算社区字典

### 集成流程

```python
# 1. 转换图谱并提取社区
converter = YoutuJSONConverter()
data = converter.load_youtu_json_data("graph.json")
converter.parse_youtu_data(data)

# 2. 获取社区字典
communities_dict = converter.get_communities_dict()
# 格式: {"实体1": 0, "实体2": 0, "实体3": 1, ...}

# 3. 在 COT 生成中使用
config["partition"]["precomputed_communities"] = communities_dict

# 4. 生成 COT 数据
graph_gen.generate(
    partition_config=config["partition"],
    generate_config=config["generate"]
)
```

## 故障排除

### 问题 1：没有检测到社区

**症状：**
```
解析完成:
  - 社区节点: 0
```

**原因：** youtu-graphrag JSON 中没有社区节点（label="community"）

**解决方案：**
- 确保使用的是包含社区信息的完整 graph.json
- 如果 youtu-graphrag 没有生成社区，系统会自动回退到 Leiden 算法

### 问题 2：社区成员与图谱节点不匹配

**症状：** 生成的 COT 数据很少或为空

**原因：** 社区成员名称与图谱中的实体名称不一致

**解决方案：**
- 检查 `youtu_communities.json` 中的成员名称
- 确保社区成员在转换后的图谱中存在

### 问题 3：社区过大或过小

**症状：** 生成的问题质量不高

**解决方案：** 调整 `max_size` 参数

```yaml
partition:
  method_params:
    max_size: 20  # 调整此值，较小的社区产生更具体的问题
```

## 示例输出

使用预计算社区生成的 COT 数据示例：

```json
{
  "instruction": "基于以下实体和关系，请分析周期性运动如何影响MRI图像质量？",
  "input": "",
  "output": "根据提供的知识图谱...\n\n推理步骤：\n1. 周期性运动会产生条纹伪影\n2. 这些伪影沿频率编码轴分布\n3. 影响骨皮质的诊断准确性...",
  "reasoning_path": "实体识别 -> 关系分析 -> 影响评估 -> 结论总结"
}
```

## 相关文件

- `youtu_json_converter.py` - 转换器主文件（已修改）
- `run_youtu_json_kg.py` - 运行脚本（已修改）
- `graphgen/operators/generate/generate_cot.py` - COT 生成器（已修改）
- `graphgen/models/community/precomputed_community_detector.py` - 新增
- `graphgen/graphgen.py` - GraphGen 主类（已修改）

## 参考

- [youtu-graphrag 文档](https://github.com/youtu-project/graphrag)
- [Leiden 算法](https://www.nature.com/articles/s41598-019-41695-z)
- [COT (Chain-of-Thought) 提示技术](https://arxiv.org/abs/2201.11903)
