# 快速开始：使用 Youtu-GraphRAG 社区生成 COT 数据

## 30 秒快速开始

假设你有一个 youtu-graphrag 生成的 `graph.json` 文件，其中包含社区信息。

### 步骤 1：测试社区提取（可选但推荐）

```bash
python test_youtu_communities.py --json path/to/graph.json
```

**期望输出：**
```
✅ 发现 15 个社区
   匹配率: 95.2%
✅ 社区信息质量优秀，可以直接用于 COT 生成
```

### 步骤 2：生成 COT 数据

```bash
python run_youtu_json_kg.py \
  --json path/to/graph.json \
  --mode cot \
  --format Alpaca \
  --disable-quiz
```

**期望输出：**
```
✅ 已提取 15 个社区信息，包含 456 个节点
✅ 使用 youtu-graphrag 预计算的社区信息（15 个社区）
[Generating COT] Generating CoT data from communities: 100%|██████| 15/15
✅ 数据生成完成！
```

### 步骤 3：查看结果

```bash
# 查看生成的数据
cat cache/data/graphgen/*/qa.json | jq '.[0]'
```

**示例输出：**
```json
{
  "instruction": "基于以下知识图谱，请分析周期性运动如何影响MRI图像质量？",
  "input": "",
  "output": "根据知识图谱分析...\n\n推理步骤：\n1. ...\n2. ...",
}
```

## 完成！🎉

你已经成功使用 youtu-graphrag 的社区信息生成了 COT 训练数据。

---

## 进阶选项

### 调整社区大小

如果社区太大或太小，可以调整 `max_size` 参数：

```bash
# 创建自定义配置文件
cat > custom_cot_config.yaml <<EOF
partition:
  method: precomputed  # 使用预计算社区
  method_params:
    max_size: 15  # 社区最大成员数
generate:
  mode: cot
  data_format: Alpaca
EOF
```

### 查看社区详情

```bash
# 转换并导出社区信息
python youtu_json_converter.py \
  --input path/to/graph.json \
  --output cache/graph.graphml \
  --stats cache/stats.json

# 查看社区信息
cat cache/youtu_communities.json | jq '.'
```

### 使用不同的数据格式

```bash
# Sharegpt 格式
python run_youtu_json_kg.py \
  --json path/to/graph.json \
  --mode cot \
  --format Sharegpt \
  --disable-quiz

# ChatML 格式
python run_youtu_json_kg.py \
  --json path/to/graph.json \
  --mode cot \
  --format ChatML \
  --disable-quiz
```

## 故障排除

### ❌ "未发现社区节点"

**原因：** JSON 文件中没有 `label='community'` 的节点

**解决：** 系统会自动使用 Leiden 算法检测社区，无需担心

### ❌ "匹配率低于 70%"

**原因：** 社区成员名称与图谱节点不匹配

**解决：**
1. 检查 youtu-graphrag 的配置
2. 或者使用 Leiden 算法重新检测：

```bash
# 不使用预计算社区，使用 Leiden 算法
python run_youtu_json_kg.py \
  --external-graph cache/graph.graphml \
  --mode cot \
  --disable-quiz \
  --skip-convert
```

### ❌ "生成的问题质量不高"

**原因：** 社区大小不合适

**解决：** 调整 `max_size` 参数（见"进阶选项"）

## 环境变量

确保设置了必需的环境变量：

```bash
# .env 文件
SYNTHESIZER_MODEL=gpt-4
SYNTHESIZER_API_KEY=sk-...
SYNTHESIZER_BASE_URL=https://api.openai.com/v1
```

## 更多信息

- 📖 详细文档：`USE_YOUTU_COMMUNITIES.md`
- 🔧 修改说明：`YOUTU_COMMUNITIES_CHANGES.md`
- 🧪 测试脚本：`test_youtu_communities.py`
