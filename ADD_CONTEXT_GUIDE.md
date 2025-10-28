# 添加文档上下文功能使用指南

## 概述

此功能允许你从 youtu-graphrag 的 chunks 文件中加载原始文档内容，在生成训练数据时提供更丰富的上下文信息。

## Youtu-GraphRAG Chunks 文件格式

youtu-graphrag 在构建知识图谱时，会保存一个 `text` 文件（或类似名称），其中包含所有的文档 chunks。

### 格式示例

每行包含一个 chunk，格式如下：

```
id: NI_-omMs	Chunk: {'title': '魔角效应：', 'content': '人体内的一些部位...', 'source': '公众号及网页_伪影_V3_Cleaned.md'}
```

**字段说明：**
- `id`: chunk 的唯一标识符
- `Chunk`: 包含以下字段的字典：
  - `title`: 文档标题或章节标题
  - `content`: 文档的实际内容
  - `source`: 文档来源文件名

## 使用方法

### 方法 1：完整流程（推荐）

```bash
python run_youtu_json_kg.py \
  --json path/to/graph.json \
  --chunks path/to/text \
  --mode cot \
  --add-context \
  --disable-quiz
```

**参数说明：**
- `--json`: youtu-graphrag 的 graph.json 文件
- `--chunks`: youtu-graphrag 的 chunks 文件（通常命名为 `text`）
- `--add-context`: 启用文档上下文功能
- `--mode cot`: 推荐使用 COT 模式（也支持其他模式）

### 方法 2：使用已转换的图谱

如果你已经转换了图谱：

```bash
python run_youtu_json_kg.py \
  --external-graph cache/youtu_graph.graphml \
  --json path/to/graph.json \
  --chunks path/to/text \
  --mode cot \
  --add-context \
  --disable-quiz \
  --skip-convert
```

## 工作流程

1. **加载 chunks 文件**
   ```
   正在加载 youtu-graphrag chunks 数据: path/to/text
   加载完成 - 共 156 个 chunks
   ```

2. **提取 chunks 信息**
   ```
   ✅ 已提取 156 个文档 chunks，可用于提供上下文
   ✅ 启用文档上下文功能（156 个 chunks 可用）
   ```

3. **加载到存储**
   ```
   📄 步骤1.5: 加载文档 chunks 上下文...
   📄 正在加载 156 个文档 chunks 到存储...
   ✅ 已加载 156 个 chunks 到存储
   ```

4. **生成时使用上下文**
   - 系统会自动在生成时引用相关的 chunks
   - 提供更丰富的背景信息
   - 生成更准确和详细的问答对

## 文件输出

启用 `--add-context` 后，系统会生成以下额外文件：

1. **`cache/youtu_chunks.json`**
   - 导出的 chunks 信息
   - JSON 格式，便于检查

   ```json
   {
     "NI_-omMs": {
       "title": "魔角效应：",
       "content": "人体内的一些部位...",
       "source": "公众号及网页_伪影_V3_Cleaned.md"
     },
     ...
   }
   ```

## 效果对比

### 不使用 add-context

```json
{
  "instruction": "什么是魔角效应？",
  "output": "魔角效应是指在特定角度下MRI信号增强的现象。"
}
```

### 使用 add-context

```json
{
  "instruction": "什么是魔角效应？",
  "output": "魔角效应是指在特定角度下MRI信号增强的现象。具体来说：\n\n根据原始文档（来源：公众号及网页_伪影_V3_Cleaned.md）：\n\n人体内的一些部位由于一些特殊组织成分的影响，在进行MRI成像时测得的MRI信号强度会随着测量方向的改变而变化。当这些结构与主磁场夹角在54.74°(约55°)时，信号增高程度达到最大，这种现象称为"魔角效应"。\n\n魔角效应常出现在含有致密且呈各向异性的特殊组织结构的部位，如常见于由胶原纤维构成的肌腱、韧带及关节软骨等部位。"
}
```

## 配置选项

### Chunks 文件位置

youtu-graphrag 通常将 chunks 保存在以下位置：

```
youtu-graphrag-output/
  ├── graph.json          # 知识图谱
  └── text                # chunks 文件（或 chunks.txt）
```

### 常见 Chunks 文件名

- `text`
- `chunks.txt`
- `text_chunks.txt`
- `documents.txt`

如果你不确定文件名，可以查看 youtu-graphrag 的输出目录。

## 高级用法

### 仅导出 Chunks（不生成数据）

如果只想查看 chunks 内容：

```bash
python youtu_json_converter.py \
  --input graph.json \
  --output output.graphml

# 然后查看导出的 chunks
cat cache/youtu_chunks.json | jq '.'
```

### 自定义 Chunks 处理

在代码中，chunks 会被转换为以下格式并保存到 `text_chunks_storage`：

```python
{
    'chunk_id': {
        'content': '标题: ...\n文档内容...\n来源: ...',
        'title': '...',
        'source': '...'
    }
}
```

## 注意事项

### 1. Chunks 文件大小

- 大型 chunks 文件可能需要较长的加载时间
- 建议在首次使用时查看文件大小

### 2. 内存使用

- Chunks 会被完整加载到内存
- 如果文件很大，确保有足够的内存

### 3. Chunk ID 匹配

- 系统会尝试匹配 chunk_id 与图谱中的 `chunk id` 属性
- 如果匹配不上，chunks 仍会被加载但可能不会被使用

### 4. 编码问题

- Chunks 文件必须是 UTF-8 编码
- 如果遇到编码错误，尝试转换文件编码：

```bash
iconv -f GBK -t UTF-8 text > text.utf8
```

## 故障排除

### 问题 1：无法找到 chunks 文件

**症状：**
```
⚠️  加载 chunks 失败: Chunks 文件不存在
```

**解决方案：**
- 检查文件路径是否正确
- 确认 youtu-graphrag 确实生成了 chunks 文件
- 尝试不同的文件名（text、chunks.txt 等）

### 问题 2：解析 chunks 失败

**症状：**
```
⚠️  警告: 无法解析第 N 行
```

**解决方案：**
- 检查文件格式是否正确
- 确认是 youtu-graphrag 生成的标准格式
- 查看具体的错误信息

### 问题 3：Chunks 未被使用

**症状：** 生成的数据中没有包含原始文档内容

**可能原因：**
- Chunk IDs 与图谱节点的 `chunk id` 不匹配
- 生成模式不支持上下文引用
- 需要在提示词模板中添加上下文引用

**解决方案：**
- 检查 `cache/youtu_chunks.json` 确认 chunks 已加载
- 确认实体节点包含 `chunk id` 属性
- 对于 COT 模式，chunks 会自动关联到社区

## 示例场景

### 场景 1：医学知识图谱

```bash
# 假设有医学文档的知识图谱
python run_youtu_json_kg.py \
  --json medical_kg/graph.json \
  --chunks medical_kg/text \
  --mode cot \
  --add-context \
  --format Alpaca \
  --disable-quiz
```

**效果：** 生成的医学问答会包含原始文档的详细解释

### 场景 2：技术文档

```bash
# 技术文档知识图谱
python run_youtu_json_kg.py \
  --json tech_docs/graph.json \
  --chunks tech_docs/text \
  --mode atomic \
  --add-context \
  --format Sharegpt
```

**效果：** 生成的技术问答包含代码示例和详细说明

### 场景 3：法律文档

```bash
# 法律条文知识图谱
python run_youtu_json_kg.py \
  --json legal/graph.json \
  --chunks legal/text \
  --mode cot \
  --add-context \
  --format ChatML \
  --disable-quiz
```

**效果：** 生成的法律问答包含完整的条文引用

## API 使用

在 Python 代码中使用：

```python
from youtu_json_converter import YoutuJSONConverter
from custom_graphgen import CustomGraphGen

# 1. 加载数据
converter = YoutuJSONConverter()
data = converter.load_youtu_json_data("graph.json")
converter.parse_youtu_data(data)

# 2. 加载 chunks
converter.load_youtu_chunks("text")
chunks_dict = converter.get_chunks_dict()

# 3. 创建 GraphGen 实例
graph_gen = CustomGraphGen(
    external_graph_path="graph.graphml",
    working_dir="cache",
    skip_kg_building=True,
    no_trainee_mode=True
)

# 4. 加载 chunks 到存储
import asyncio
asyncio.run(graph_gen.load_chunks_context(chunks_dict))

# 5. 生成数据（chunks 会自动被引用）
# ... 继续生成流程
```

## 相关文件

- `youtu_json_converter.py` - Chunks 加载实现
- `run_youtu_json_kg.py` - 命令行接口
- `custom_graphgen.py` - Chunks 存储管理
- `USE_YOUTU_COMMUNITIES.md` - 社区功能说明

## 参考

- [youtu-graphrag 文档](https://github.com/youtu-project/graphrag)
- [GraphGen 文档](./README.md)
- [社区功能指南](./USE_YOUTU_COMMUNITIES.md)

---

**提示：** 结合 `--add-context` 和预计算社区功能，可以生成最高质量的 COT 训练数据！

```bash
python run_youtu_json_kg.py \
  --json graph.json \
  --chunks text \
  --mode cot \
  --add-context \
  --disable-quiz
```
