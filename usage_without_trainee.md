# 🚀 关闭 trainee/quiz-samples 功能使用指南

现在 `run_youtu_json_kg.py` 已经支持关闭 quiz-samples 和 trainee 功能了！以下是具体的使用方法：

## 🎯 关闭方式

### 方法 1: 使用 `--disable-quiz` 参数（推荐）

```bash
python3 run_youtu_json_kg.py \
    --json your_youtu_data.json \
    --mode atomic \
    --format Alpaca \
    --disable-quiz
```

### 方法 2: 设置 `--quiz-samples 0`

```bash
python3 run_youtu_json_kg.py \
    --json your_youtu_data.json \
    --mode atomic \
    --format Alpaca \
    --quiz-samples 0
```

## 🔧 环境变量简化

当关闭 quiz 功能时，你只需要设置 SYNTHESIZER 相关的环境变量：

```bash
# .env 文件内容（简化版）
SYNTHESIZER_MODEL=gpt-4
SYNTHESIZER_API_KEY=your_api_key
SYNTHESIZER_BASE_URL=https://api.openai.com/v1

# 可选
TOKENIZER_MODEL=cl100k_base

# 不再需要 TRAINEE 相关变量：
# TRAINEE_MODEL=...
# TRAINEE_API_KEY=...
# TRAINEE_BASE_URL=...
```

## 📊 运行效果

关闭 quiz 功能后，运行过程会显示：

```
🚀 开始使用 youtu-graphrag JSON 知识图谱生成数据...
⏭️  问答测试和判断已禁用
📁 使用知识图谱: cache/youtu_graph.graphml
📁 工作目录: cache
🎯 生成模式: atomic
📄 数据格式: Alpaca

📝 步骤1: 初始化外部知识图谱...
⏭️  步骤2: 跳过搜索增强
⏭️  步骤3: 跳过问答测试和判断（已禁用）
⚡ 步骤4: 生成 atomic 数据...
```

## ⚡ 优势

关闭 quiz 功能后：

1. **更快的运行速度** - 跳过问答测试和判断步骤
2. **更少的 API 调用** - 只使用 SYNTHESIZER 模型
3. **更低的成本** - 减少 LLM API 使用
4. **简化配置** - 不需要配置 TRAINEE 相关环境变量

## 🎯 完整示例

```bash
# 1. 创建简化的 .env 文件
cat > .env << EOF
SYNTHESIZER_MODEL=gpt-4
SYNTHESIZER_API_KEY=your_api_key_here
SYNTHESIZER_BASE_URL=https://api.openai.com/v1
TOKENIZER_MODEL=cl100k_base
EOF

# 2. 运行转换和生成（关闭 quiz）
python3 run_youtu_json_kg.py \
    --json your_youtu_data.json \
    --working-dir cache \
    --mode atomic \
    --format Alpaca \
    --disable-quiz \
    --max-depth 3 \
    --max-extra-edges 5
```

## 🔄 其他生成模式

关闭 quiz 功能对所有生成模式都有效：

```bash
# 原子问答（基础）
python3 run_youtu_json_kg.py --json data.json --mode atomic --disable-quiz

# 聚合问答（复合）
python3 run_youtu_json_kg.py --json data.json --mode aggregated --disable-quiz

# 多跳推理问答
python3 run_youtu_json_kg.py --json data.json --mode multi_hop --disable-quiz

# 思维链问答
python3 run_youtu_json_kg.py --json data.json --mode cot --disable-quiz
```

## 📋 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--disable-quiz` | 完全禁用问答测试和判断 | False |
| `--quiz-samples 0` | 设置测试样本数为 0（等同于禁用） | 5 |
| `--max-depth` | 图遍历最大深度 | 3 |
| `--max-extra-edges` | 每方向最大边数 | 5 |

## 🎉 开始使用

现在你可以更简单、更快速地使用 youtu-graphrag 数据生成问答对了：

```bash
python3 run_youtu_json_kg.py \
    --json your_youtu_data.json \
    --disable-quiz \
    --mode atomic
```

这样就完全跳过了 trainee 和 quiz 相关的步骤，只专注于从知识图谱生成问答数据！