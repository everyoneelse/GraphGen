# Youtu-GraphRAG Chunks 上下文功能 - 完整总结

## 🎯 功能概述

新增功能允许从 youtu-graphrag 的 chunks 文件中加载原始文档内容，在生成训练数据时提供更丰富的上下文信息。

## ✅ 已完成的修改

### 修改的文件（3个）

1. **`youtu_json_converter.py`**
   - 添加 `chunks` 字典存储
   - 新增 `load_youtu_chunks()` 方法解析 chunks 文件
   - 新增 `get_chunks_dict()` 获取 chunks 字典
   - 新增 `export_chunks()` 导出 chunks 到 JSON

2. **`run_youtu_json_kg.py`**
   - 添加 `--chunks` 参数指定 chunks 文件路径
   - 添加 `--add-context` 参数启用上下文功能
   - 修改 `convert_youtu_json_kg()` 支持加载 chunks
   - 修改 `run_full_graphgen()` 集成 chunks 加载

3. **`custom_graphgen.py`**
   - 新增 `load_chunks_context()` 方法
   - 将 chunks 保存到 `text_chunks_storage`
   - 格式化 chunks 内容（标题+内容+来源）

### 新增的文件（3个）

1. **`ADD_CONTEXT_GUIDE.md`**
   - 详细使用指南
   - 包含格式说明、示例、故障排除

2. **`test_chunks_loading.py`**
   - 测试 chunks 加载功能
   - 验证文件格式和质量
   - 提供统计信息

3. **`CHUNKS_CONTEXT_SUMMARY.md`**
   - 功能总结文档（本文档）

## 🚀 使用方法

### 基本用法

```bash
python run_youtu_json_kg.py \
  --json path/to/graph.json \
  --chunks path/to/text \
  --mode cot \
  --add-context \
  --disable-quiz
```

### 测试 Chunks 文件

```bash
# 测试真实文件
python test_chunks_loading.py --chunks path/to/text

# 创建并测试示例文件
python test_chunks_loading.py --create-sample
```

## 📁 Chunks 文件格式

### youtu-graphrag 格式

```
id: CHUNK_ID	Chunk: {'title': '...', 'content': '...', 'source': '...'}
```

### 解析后的格式

```python
{
    'chunk_id': {
        'title': '标题',
        'content': '文档内容...',
        'source': '来源文件.md'
    }
}
```

### 存储格式（text_chunks_storage）

```python
{
    'chunk_id': {
        'content': '标题: ...\n文档内容...\n来源: ...',
        'title': '...',
        'source': '...'
    }
}
```

## 🔄 工作流程

```
youtu chunks file (text)
    ↓
YoutuJSONConverter.load_youtu_chunks()
    ↓
解析每行：id + Chunk 字典
    ↓
存储到 converter.chunks
    ↓
get_chunks_dict() 导出
    ↓
CustomGraphGen.load_chunks_context()
    ↓
格式化并保存到 text_chunks_storage
    ↓
在生成时可引用这些 chunks
```

## 🎨 关键特性

### 1. 灵活的格式支持
- ✅ 支持标准 youtu-graphrag 格式
- ✅ 容错解析（跳过错误行）
- ✅ 支持多种字段组合

### 2. 智能内容处理
- ✅ 自动组合 title + content + source
- ✅ 保留原始格式
- ✅ UTF-8 编码支持

### 3. 质量检查
- ✅ 测试脚本验证文件质量
- ✅ 统计信息（字段完整性、长度分布）
- ✅ 示例 chunks 展示

### 4. 集成度高
- ✅ 与社区功能无缝配合
- ✅ 支持所有生成模式
- ✅ 可选功能（不影响原有流程）

## 📊 示例输出

### 加载过程

```
🔄 开始转换 youtu-graphrag JSON 知识图谱...
正在加载 youtu-graphrag chunks 数据: path/to/text
加载完成 - 共 156 个 chunks
✅ 已加载 156 个文档 chunks

✅ 已提取 156 个文档 chunks，可用于提供上下文
✅ 启用文档上下文功能（156 个 chunks 可用）

📄 步骤1.5: 加载文档 chunks 上下文...
📄 正在加载 156 个文档 chunks 到存储...
✅ 已加载 156 个 chunks 到存储
```

### 生成效果

**不使用 --add-context：**
```
Q: 什么是魔角效应？
A: MRI成像中的一种信号增强现象。
```

**使用 --add-context：**
```
Q: 什么是魔角效应？
A: 根据文档（来源：公众号及网页_伪影_V3_Cleaned.md），魔角效应是指...

[包含完整的原始文档内容和详细解释]
```

## 🧪 测试验证

### 运行测试

```bash
# 测试加载功能
python test_chunks_loading.py --chunks your_text_file

# 创建示例并测试
python test_chunks_loading.py --create-sample
```

### 期望结果

```
✅ 成功加载 N 个 chunks
   包含标题: X%
   包含内容: 100%
   包含来源: Y%

✅ Chunks 文件质量优秀，可以用于添加文档上下文
```

## 💡 使用场景

### 场景 1：医学知识图谱 + 文档上下文

```bash
python run_youtu_json_kg.py \
  --json medical_kg/graph.json \
  --chunks medical_kg/text \
  --mode cot \
  --add-context \
  --disable-quiz
```

**效果：** 生成的问答包含原始医学文献的详细内容

### 场景 2：技术文档 + 社区 + 上下文

```bash
python run_youtu_json_kg.py \
  --json tech_docs/graph.json \
  --chunks tech_docs/text \
  --mode cot \
  --add-context \
  --disable-quiz
```

**效果：**
- 使用预计算的社区（避免重复检测）
- 包含原始文档的代码示例和详细说明
- 最高质量的 COT 训练数据

### 场景 3：仅加载 Chunks（不使用社区）

```bash
python run_youtu_json_kg.py \
  --json graph.json \
  --chunks text \
  --mode atomic \
  --add-context
```

**效果：** atomic 模式 + 文档上下文

## 📖 文档导航

| 需求 | 文档 |
|------|------|
| 📖 详细使用指南 | `ADD_CONTEXT_GUIDE.md` |
| 🧪 测试和验证 | `test_chunks_loading.py` |
| 📋 功能总结 | `CHUNKS_CONTEXT_SUMMARY.md`（本文档） |
| 🏘️ 社区功能 | `USE_YOUTU_COMMUNITIES.md` |
| 🚀 快速开始 | `QUICK_START_COMMUNITIES.md` |

## ⚠️ 注意事项

### 1. 文件格式
- 必须是 youtu-graphrag 标准格式
- 每行一个 chunk
- Tab 分隔 ID 和数据

### 2. 编码
- 文件必须是 UTF-8 编码
- 如有编码问题，使用 `iconv` 转换

### 3. 文件大小
- 大文件加载需要时间
- 注意内存使用

### 4. Chunk ID 匹配
- 系统会尝试匹配 `chunk id` 属性
- 不匹配的 chunks 仍会被加载

## 🔧 技术实现

### 核心方法

1. **`YoutuJSONConverter.load_youtu_chunks()`**
   ```python
   def load_youtu_chunks(self, chunks_file: str):
       # 逐行解析
       # 提取 id 和 Chunk 字典
       # 存储到 self.chunks
   ```

2. **`CustomGraphGen.load_chunks_context()`**
   ```python
   async def load_chunks_context(self, chunks_dict: Dict):
       # 格式化内容
       # 保存到 text_chunks_storage
       # 调用 index_done_callback()
   ```

### 数据流

```python
# 1. 加载 chunks
converter.load_youtu_chunks("text")

# 2. 获取字典
chunks_dict = converter.get_chunks_dict()

# 3. 保存到存储
await graph_gen.load_chunks_context(chunks_dict)

# 4. 生成时自动引用
# 系统会在需要时从 text_chunks_storage 读取
```

## 🎓 最佳实践

### 推荐配置

```bash
# 完整功能：社区 + 上下文
python run_youtu_json_kg.py \
  --json graph.json \
  --chunks text \
  --mode cot \
  --add-context \
  --disable-quiz \
  --format Alpaca
```

### 测试流程

1. **验证 chunks 文件**
   ```bash
   python test_chunks_loading.py --chunks text
   ```

2. **验证社区信息**
   ```bash
   python test_youtu_communities.py --json graph.json
   ```

3. **生成数据**
   ```bash
   python run_youtu_json_kg.py ...
   ```

### 输出文件检查

```bash
# 查看 chunks
cat cache/youtu_chunks.json | jq '.' | less

# 查看社区
cat cache/youtu_communities.json | jq '.' | less

# 查看生成的数据
cat cache/data/graphgen/*/qa.json | jq '.[0]' | less
```

## 🆕 与社区功能的配合

两个功能可以同时使用，获得最佳效果：

| 功能 | 作用 | 参数 |
|------|------|------|
| 社区信息 | 跳过社区检测，使用预计算结果 | 自动检测 |
| Chunks 上下文 | 提供原始文档内容 | `--chunks` + `--add-context` |

**完整命令：**
```bash
python run_youtu_json_kg.py \
  --json graph.json \
  --chunks text \
  --mode cot \
  --add-context \
  --disable-quiz
```

## 📈 性能影响

- **加载时间：** 取决于 chunks 文件大小（通常 < 30秒）
- **内存使用：** chunks 会被加载到内存（注意大文件）
- **生成速度：** 基本无影响（chunks 在后台引用）

## 🙏 致谢

感谢使用本功能！如有问题，请参考：
- 详细指南：`ADD_CONTEXT_GUIDE.md`
- 测试脚本：`test_chunks_loading.py`
- 社区功能：`USE_YOUTU_COMMUNITIES.md`

---

**最后更新：** 2025-10-27  
**版本：** 1.0
