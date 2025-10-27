# Youtu-GraphRAG 集成功能

## 🎯 快速开始

如果你有 youtu-graphrag 生成的知识图谱，可以直接使用以下命令生成高质量的 COT 训练数据：

```bash
python run_youtu_json_kg.py \
  --json path/to/graph.json \
  --chunks path/to/text \
  --mode cot \
  --add-context \
  --disable-quiz
```

**这个命令会：**
- ✅ 自动使用 youtu-graphrag 预计算的社区（无需重新检测）
- ✅ 加载原始文档内容作为上下文
- ✅ 生成包含详细解释的 COT 训练数据

## 📁 文件要求

你需要准备以下文件（通常由 youtu-graphrag 生成）：

1. **`graph.json`** - 知识图谱文件
   - 包含实体、关系、社区信息

2. **`text`** - 文档 chunks 文件（可选）
   - 每行一个 chunk
   - 格式：`id: CHUNK_ID\tChunk: {...}`

## 📖 完整文档

| 文档 | 内容 |
|------|------|
| **[快速开始](QUICK_START_COMMUNITIES.md)** | 30秒上手指南 |
| **[社区功能](USE_YOUTU_COMMUNITIES.md)** | 社区集成详细说明 |
| **[上下文功能](ADD_CONTEXT_GUIDE.md)** | 文档上下文详细说明 |
| **[完整总结](FINAL_UPDATE_SUMMARY.md)** | 所有功能总结 |

## 🧪 测试工具

在使用前，建议先测试文件质量：

```bash
# 测试社区信息
python test_youtu_communities.py --json graph.json

# 测试 chunks 文件
python test_chunks_loading.py --chunks text
```

## 💡 使用场景

### 场景 1：快速生成（仅社区）

```bash
python run_youtu_json_kg.py \
  --json graph.json \
  --mode cot \
  --disable-quiz
```

### 场景 2：高质量生成（社区 + 上下文）

```bash
python run_youtu_json_kg.py \
  --json graph.json \
  --chunks text \
  --mode cot \
  --add-context \
  --disable-quiz
```

## 🎨 功能对比

| 功能 | 命令 | 质量 | 速度 |
|------|------|------|------|
| 基础 | `--json graph.json --mode cot` | ⭐⭐⭐ | ⚡⚡ |
| +社区 | 自动检测，无需额外参数 | ⭐⭐⭐ | ⚡⚡⚡ |
| +上下文 | `--chunks text --add-context` | ⭐⭐⭐⭐⭐ | ⚡⚡ |

## 🔧 参数说明

```bash
python run_youtu_json_kg.py \
  --json graph.json \        # [必需] 知识图谱文件
  --chunks text \             # [可选] Chunks 文件
  --mode cot \                # [推荐] 生成模式
  --add-context \             # [可选] 启用文档上下文
  --format Alpaca \           # [可选] 数据格式
  --disable-quiz              # [推荐] 禁用测试步骤
```

## ⚡ 示例输出

### 不使用上下文

```json
{
  "instruction": "什么是魔角效应？",
  "output": "MRI成像中的信号增强现象。"
}
```

### 使用上下文

```json
{
  "instruction": "什么是魔角效应？",
  "output": "根据文档（来源：公众号及网页_伪影_V3_Cleaned.md）：\n\n魔角效应是指在特定角度下MRI信号增强的现象。具体来说，当组织结构与主磁场夹角在54.74°时，信号增高程度达到最大...\n\n[包含完整的原始文档内容]"
}
```

## 🆘 常见问题

### Q1: 找不到社区信息？

**A:** 系统会自动使用 Leiden 算法检测社区，无需担心。

### Q2: 没有 chunks 文件？

**A:** 可以不使用 `--chunks` 和 `--add-context` 参数，仍然可以生成数据。

### Q3: 文件格式错误？

**A:** 使用测试脚本检查：
```bash
python test_youtu_communities.py --json graph.json
python test_chunks_loading.py --chunks text
```

## 📞 获取帮助

```bash
# 查看所有参数
python run_youtu_json_kg.py --help

# 测试社区
python test_youtu_communities.py --help

# 测试 chunks
python test_chunks_loading.py --help
```

## 🎓 进阶用法

详见完整文档：
- [USE_YOUTU_COMMUNITIES.md](USE_YOUTU_COMMUNITIES.md) - 社区功能详解
- [ADD_CONTEXT_GUIDE.md](ADD_CONTEXT_GUIDE.md) - 上下文功能详解
- [FINAL_UPDATE_SUMMARY.md](FINAL_UPDATE_SUMMARY.md) - 完整技术总结

---

**开始使用：**

```bash
python run_youtu_json_kg.py \
  --json your_graph.json \
  --chunks your_text_file \
  --mode cot \
  --add-context \
  --disable-quiz
```

祝使用愉快！🚀
