# 🎯 使用 youtu-graphrag 知识图谱生成 QA 数据 - 完整指南

基于你提供的 youtu-graphrag JSON 数据格式，我已经创建了完整的解决方案。以下是详细的使用指南：

## 📊 你的数据格式分析

你的 youtu-graphrag 数据包含以下结构：
- **实体节点**: `FC Barcelona`、`Lionel Messi`、`Camp Nou`
- **属性节点**: `type: football club`、`position: forward`、`capacity: 99,354`
- **关系**: `has_attribute`、`played_for`、`home_stadium`

转换后将生成如下问答对：
- ❓ "What are the attributes of FC Barcelona?" 
- ✅ "FC Barcelona has the following attributes: type: football club, status: active."

## 🚀 快速开始

### 步骤 1: 环境准备

创建 `.env` 文件：
```bash
# 必需的环境变量
SYNTHESIZER_MODEL=gpt-4
SYNTHESIZER_API_KEY=your_api_key_here
SYNTHESIZER_BASE_URL=https://api.openai.com/v1

TRAINEE_MODEL=gpt-3.5-turbo
TRAINEE_API_KEY=your_api_key_here
TRAINEE_BASE_URL=https://api.openai.com/v1

# 可选
TOKENIZER_MODEL=cl100k_base
```

### 步骤 2: 安装依赖

```bash
pip install networkx pandas python-dotenv pyyaml tqdm
```

### 步骤 3: 转换和生成

#### 方法 A: 一键运行（推荐）

```bash
# 使用你的 JSON 文件替换 your_youtu_data.json
python3 run_youtu_json_kg.py \
    --json your_youtu_data.json \
    --working-dir cache \
    --mode atomic \
    --format Alpaca \
    --quiz-samples 5
```

#### 方法 B: 分步执行

```bash
# 1. 转换知识图谱格式
python3 youtu_json_converter.py \
    --input your_youtu_data.json \
    --output cache/your_graph.graphml \
    --validate \
    --stats cache/stats.json

# 2. 生成问答数据
python3 run_youtu_json_kg.py \
    --external-graph cache/your_graph.graphml \
    --working-dir cache \
    --mode atomic \
    --skip-convert
```

## 📋 生成模式选择

根据你的需求选择合适的生成模式：

| 模式 | 说明 | 示例问答 |
|------|------|----------|
| **atomic** | 基础实体属性问答 | Q: What type is FC Barcelona? A: FC Barcelona is a football club. |
| **aggregated** | 多实体综合问答 | Q: Tell me about FC Barcelona and its stadium. A: FC Barcelona is a football club with Camp Nou as home stadium... |
| **multi_hop** | 多跳推理问答 | Q: Where does Messi play and what's the capacity? A: Messi played for FC Barcelona, whose stadium Camp Nou has 99,354 capacity. |
| **cot** | 思维链推理问答 | Q: How are Messi and Camp Nou related? A: First, Messi played for FC Barcelona. Second, FC Barcelona's home stadium is Camp Nou... |

## 📄 输出格式

### Alpaca 格式（推荐用于指令微调）
```json
{
  "instruction": "What are the attributes of FC Barcelona?",
  "input": "",
  "output": "FC Barcelona is a football club that is currently active."
}
```

### Sharegpt 格式（用于对话训练）
```json
{
  "conversations": [
    {"from": "human", "value": "What are the attributes of FC Barcelona?"},
    {"from": "gpt", "value": "FC Barcelona is a football club that is currently active."}
  ]
}
```

### ChatML 格式（用于聊天模型）
```json
{
  "messages": [
    {"role": "user", "content": "What are the attributes of FC Barcelona?"},
    {"role": "assistant", "content": "FC Barcelona is a football club that is currently active."}
  ]
}
```

## 🔧 参数调优

### 基础参数
```bash
python3 run_youtu_json_kg.py \
    --json your_data.json \
    --mode atomic \              # 生成模式
    --format Alpaca \            # 输出格式
    --quiz-samples 5 \           # 测试样本数（影响质量）
    --max-depth 3 \              # 图遍历深度
    --max-extra-edges 5          # 每方向最大边数
```

### 质量优化参数
```bash
# 高质量生成（较慢）
python3 run_youtu_json_kg.py \
    --json your_data.json \
    --mode aggregated \
    --quiz-samples 10 \
    --max-depth 4 \
    --max-extra-edges 8 \
    --enable-search              # 启用网络搜索增强
```

### 快速生成参数
```bash
# 快速生成（较低质量）
python3 run_youtu_json_kg.py \
    --json your_data.json \
    --mode atomic \
    --quiz-samples 2 \
    --max-depth 2 \
    --max-extra-edges 3
```

## 📁 输出文件说明

运行完成后，你会在 `cache/` 目录下找到：

```
cache/
├── youtu_graph.graphml                    # 转换后的知识图谱
├── youtu_graph_stats.json                 # 图谱统计信息
├── final_graph_statistics_xxx.json        # 最终统计
├── youtu_json_kg_xxx_atomic.log          # 详细日志
└── data/graphgen/xxx/                     # 生成的问答数据
    └── qa.json                            # 问答对文件
```

## 🎯 实际使用示例

假设你有一个包含足球相关实体的 youtu-graphrag JSON 文件：

```bash
# 生成基础问答对（适合实体属性学习）
python3 run_youtu_json_kg.py \
    --json football_entities.json \
    --mode atomic \
    --format Alpaca \
    --quiz-samples 5

# 生成复杂推理问答（适合关系推理训练）
python3 run_youtu_json_kg.py \
    --json football_entities.json \
    --mode multi_hop \
    --format Sharegpt \
    --quiz-samples 8 \
    --max-depth 4
```

## 🐛 常见问题解决

### 1. 转换失败
```
❌ 转换失败: KeyError: 'name'
```
**解决方案**: 检查 JSON 中每个实体的 `properties.name` 字段

### 2. 生成数据为空
```
⚠️ 没有生成任何数据
```
**解决方案**: 
- 减少 `max-depth` 到 2
- 减少 `max-extra-edges` 到 3
- 检查图谱连通性

### 3. API 调用错误
```
❌ API 调用失败
```
**解决方案**:
- 验证 `.env` 文件中的 API 密钥
- 检查模型名称是否正确
- 确认网络连接正常

## 📈 质量提升建议

1. **数据预处理**:
   - 确保实体名称一致性
   - 补充缺失的属性描述
   - 验证关系的正确性

2. **参数调优**:
   - 增加 `quiz-samples` 提高质量评估
   - 使用更强的 `SYNTHESIZER_MODEL`
   - 启用 `--enable-search` 进行知识增强

3. **后处理**:
   - 人工审核生成的问答对
   - 过滤重复或低质量的数据
   - 平衡不同类型问题的比例

## 🎉 开始使用

现在你可以使用你的 youtu-graphrag JSON 数据生成高质量的问答训练数据了！

```bash
# 替换为你的实际文件路径
python3 run_youtu_json_kg.py \
    --json /path/to/your/youtu_graphrag_output.json \
    --mode atomic \
    --format Alpaca \
    --working-dir ./output
```

生成的数据可以直接用于：
- 🤖 **LLM 指令微调** (使用 Alpaca 格式)
- 💬 **对话模型训练** (使用 Sharegpt 格式)  
- 📚 **知识问答系统** (任何格式)
- 🧠 **推理能力训练** (使用 multi_hop 或 cot 模式)

祝你使用愉快！如有问题，请查看日志文件或联系支持。