# 🚀 youtu-graphrag JSON 知识图谱快速开始指南

基于你提供的 youtu-graphrag JSON 数据格式，我已经创建了专门的转换工具。以下是完整的使用流程：

## 📋 你的数据格式分析

根据你提供的 JSON 片段，youtu-graphrag 的数据结构包含：

```json
{
  "start_node": {
    "label": "entity",           // 节点类型
    "properties": {
      "name": "FC Barcelona",    // 实体名称
      "chunk id": "0FCIUkTr",   // 文档块ID
      "schema_type": "organization"  // 实体类型
    }
  },
  "relation": "has_attribute",   // 关系类型
  "end_node": {
    "label": "attribute",        // 属性节点
    "properties": {
      "name": "type: football club"  // 属性描述
    }
  }
}
```

## 🛠️ 环境准备

1. **设置环境变量** (创建 `.env` 文件):
```bash
# 用于知识图谱构建和数据生成的模型
SYNTHESIZER_MODEL=gpt-4
SYNTHESIZER_API_KEY=your_synthesizer_api_key
SYNTHESIZER_BASE_URL=https://api.openai.com/v1

# 用于问答测试的模型
TRAINEE_MODEL=gpt-3.5-turbo
TRAINEE_API_KEY=your_trainee_api_key
TRAINEE_BASE_URL=https://api.openai.com/v1

# 可选：tokenizer 模型
TOKENIZER_MODEL=cl100k_base
```

2. **安装依赖**:
```bash
pip install -r requirements.txt
```

## 🎯 快速测试

使用提供的示例数据进行测试：

```bash
# 运行完整测试
python test_youtu_conversion.py
```

这个测试会：
- ✅ 转换示例 JSON 数据为 GraphML 格式
- ✅ 验证图谱结构
- ✅ 测试问答生成功能（如果设置了 API 密钥）

## 🚀 使用你的实际数据

### 方法1: 一键运行（推荐）

```bash
# 从你的 JSON 文件直接生成问答数据
python run_youtu_json_kg.py \
    --json path/to/your_youtu_data.json \
    --working-dir cache \
    --mode atomic \
    --format Alpaca \
    --quiz-samples 5
```

### 方法2: 分步执行

#### 步骤1: 转换知识图谱格式

```bash
python youtu_json_converter.py \
    --input path/to/your_youtu_data.json \
    --output cache/your_graph.graphml \
    --validate \
    --stats cache/graph_stats.json
```

#### 步骤2: 生成问答数据

```bash
python run_youtu_json_kg.py \
    --external-graph cache/your_graph.graphml \
    --working-dir cache \
    --mode atomic \
    --skip-convert
```

## 📊 生成模式说明

选择适合你需求的生成模式：

| 模式 | 说明 | 适用场景 |
|------|------|----------|
| `atomic` | 基础知识问答对 | 实体属性、基本关系 |
| `aggregated` | 复合知识问答对 | 多实体综合信息 |
| `multi_hop` | 多跳推理问答对 | 需要推理的复杂问题 |
| `cot` | 思维链问答对 | 需要逐步推理的问题 |

## 📄 输出格式

支持三种训练数据格式：

### Alpaca 格式
```json
{
  "instruction": "What type of organization is FC Barcelona?",
  "input": "",
  "output": "FC Barcelona is a football club that is currently active."
}
```

### Sharegpt 格式
```json
{
  "conversations": [
    {"from": "human", "value": "What type of organization is FC Barcelona?"},
    {"from": "gpt", "value": "FC Barcelona is a football club that is currently active."}
  ]
}
```

### ChatML 格式
```json
{
  "messages": [
    {"role": "user", "content": "What type of organization is FC Barcelona?"},
    {"role": "assistant", "content": "FC Barcelona is a football club that is currently active."}
  ]
}
```

## 🔧 高级配置

### 调整生成参数

```bash
python run_youtu_json_kg.py \
    --json your_data.json \
    --mode atomic \
    --format Alpaca \
    --quiz-samples 10 \        # 增加测试样本数
    --max-depth 4 \            # 增加图遍历深度
    --max-extra-edges 8 \      # 增加每个方向的边数
    --enable-search            # 启用网络搜索增强
```

### 自定义转换逻辑

如果你的数据格式有特殊需求，可以修改 `youtu_json_converter.py` 中的转换逻辑：

```python
class CustomYoutuConverter(YoutuJSONConverter):
    def _normalize_entity_type(self, entity_data):
        # 自定义实体类型映射
        type_mapping = {
            'organization': 'company',
            'person': 'individual',
            # 添加更多映射...
        }
        original_type = super()._normalize_entity_type(entity_data)
        return type_mapping.get(original_type, original_type)
```

## 📁 输出文件结构

运行完成后，你会得到以下文件：

```
cache/
├── youtu_graph.graphml              # 转换后的知识图谱
├── youtu_graph_stats.json           # 图谱统计信息
├── final_graph_statistics_xxx.json  # 最终统计
├── youtu_json_kg_xxx_atomic.log     # 运行日志
└── data/graphgen/xxx/               # 生成的问答数据
    └── qa.json                      # 问答对文件
```

## 🐛 常见问题解决

### 1. 转换失败
```
❌ 转换失败: KeyError: 'name'
```
**解决方案**: 检查 JSON 数据中实体的 `properties.name` 字段是否存在

### 2. 图谱为空
```
⚠️ 图谱验证发现的问题: 发现 X 个孤立节点
```
**解决方案**: 
- 检查是否有实体间关系（非 `has_attribute` 关系）
- 转换器会自动基于相同 `chunk id` 创建共现关系

### 3. 生成数据为空
```
⚠️ 没有生成任何数据
```
**解决方案**:
- 减少 `max-depth` 和 `max-extra-edges` 参数
- 确保图谱有足够的连通节点
- 检查实体描述是否为空

### 4. API 调用失败
```
❌ API 调用失败
```
**解决方案**:
- 检查 `.env` 文件中的 API 密钥和 URL
- 确认模型名称正确
- 检查网络连接

## 📈 性能优化建议

1. **大型图谱处理**:
   - 使用较小的 `quiz-samples` 值
   - 减少 `max-depth` 和 `max-extra-edges`
   - 分批处理大文件

2. **提高生成质量**:
   - 使用更强的 `SYNTHESIZER_MODEL`
   - 启用 `--enable-search` 进行知识增强
   - 增加 `quiz-samples` 进行更好的知识评估

3. **加快生成速度**:
   - 使用更快的模型作为 `TRAINEE_MODEL`
   - 减少测试样本数量
   - 跳过搜索增强步骤

## 🎉 开始使用

现在你可以开始使用你的 youtu-graphrag JSON 数据生成高质量的问答训练数据了！

```bash
# 使用你的数据文件替换 your_youtu_data.json
python run_youtu_json_kg.py \
    --json your_youtu_data.json \
    --mode atomic \
    --format Alpaca
```

生成的问答数据可以直接用于：
- 🤖 LLM 指令微调
- 💬 对话模型训练  
- 📚 知识问答系统
- 🧠 推理能力训练