# 🔧 事件循环冲突问题解决方案

## 🚨 问题描述

你遇到的错误 `This event loop is already running` 是因为：

1. **GraphGen 使用同步包装器** - 内部使用 `loop.run_until_complete()`
2. **在异步环境中调用** - 我们的脚本已经在 `asyncio.run()` 中运行
3. **事件循环嵌套冲突** - 不能在已运行的事件循环中再次调用 `run_until_complete()`

## 🛠️ 解决方案

我提供了 **3 种解决方案**，按推荐程度排序：

### 方案 1: 使用简化版转换器（🌟 最推荐）

**优势**: 无依赖、快速、稳定、免费

```bash
# 步骤 1: 转换数据
python3 simple_youtu_converter.py \
    --input your_youtu_data.json \
    --output cache/converted_data.json

# 步骤 2: 生成问答对
python3 create_qa_from_converted.py \
    --input cache/converted_data.json \
    --output cache/qa_pairs.json \
    --format Alpaca
```

### 方案 2: 使用 nest_asyncio 修复

**优势**: 保持原有功能、支持 LLM 增强

```bash
# 安装 nest_asyncio
pip install nest_asyncio

# 使用修复版脚本
python3 run_with_nest_asyncio.py \
    --json your_youtu_data.json \
    --mode atomic \
    --format Alpaca \
    --disable-quiz
```

### 方案 3: 使用同步版本

**优势**: 避免异步问题、功能完整

```bash
# 使用同步生成脚本（已自动创建）
python3 run_sync_generation.py \
    --json your_youtu_data.json \
    --mode atomic \
    --format Alpaca
```

## 🎯 推荐使用方案 1

**为什么推荐方案 1？**

1. **🚀 零依赖** - 只使用 Python 标准库
2. **⚡ 快速** - 直接转换，无需 LLM API 调用
3. **💰 免费** - 不需要任何 API 费用
4. **🔧 稳定** - 没有异步冲突问题
5. **📊 透明** - 每步都可以检查和调试

## 📋 方案 1 详细步骤

### 步骤 1: 转换你的数据

```bash
python3 simple_youtu_converter.py \
    --input your_youtu_data.json \
    --output cache/converted_data.json
```

**输出示例**:
```
正在加载 youtu-graphrag JSON 数据: your_youtu_data.json
加载完成 - 共 X 条关系记录
解析完成:
  - 实体节点: X
  - 属性节点: X
  - 关系: X
✅ 转换完成！
```

### 步骤 2: 生成问答对

```bash
python3 create_qa_from_converted.py \
    --input cache/converted_data.json \
    --output cache/qa_pairs.json \
    --format Alpaca
```

**输出示例**:
```
✅ 生成了 X 个问答对
📁 问答对已保存到: cache/qa_pairs.json
📊 格式: Alpaca
📈 数量: X

📝 示例问答对:
1. Q: What type of entity is FC Barcelona?
   A: FC Barcelona is a organization.
```

### 步骤 3: 查看结果

```bash
# 查看生成的问答对
head -20 cache/qa_pairs.json

# 检查数据质量
python3 -c "
import json
with open('cache/qa_pairs.json', 'r') as f:
    data = json.load(f)
print(f'总计: {len(data)} 个问答对')
print('前3个示例:')
for i, qa in enumerate(data[:3]):
    print(f'{i+1}. Q: {qa[\"instruction\"]}')
    print(f'   A: {qa[\"output\"]}')
    print()
"
```

## 🔍 故障排除

### 如果方案 1 失败

```bash
# 检查文件是否存在
ls -la simple_youtu_converter.py create_qa_from_converted.py

# 检查 Python 版本
python3 --version

# 测试转换器
python3 simple_youtu_converter.py --input example_youtu_data.json --output test.json
```

### 如果需要使用方案 2

```bash
# 确保安装了 nest_asyncio
pip install nest_asyncio

# 检查是否正确安装
python3 -c "import nest_asyncio; print('✅ nest_asyncio 可用')"

# 运行修复版脚本
python3 run_with_nest_asyncio.py --json your_data.json --disable-quiz
```

## 📊 性能对比

| 方案 | 速度 | 成本 | 复杂度 | 质量 | 推荐度 |
|------|------|------|--------|------|--------|
| 方案1 (简化版) | ⚡⚡⚡ | 💰免费 | 🔧简单 | ⭐⭐⭐ | 🌟🌟🌟🌟🌟 |
| 方案2 (nest_asyncio) | ⚡⚡ | 💰付费 | 🔧中等 | ⭐⭐⭐⭐ | 🌟🌟🌟 |
| 方案3 (同步版) | ⚡⚡ | 💰付费 | 🔧中等 | ⭐⭐⭐⭐ | 🌟🌟🌟 |

## 🎉 开始使用

**立即开始使用方案 1**:

```bash
# 一键运行（替换为你的文件路径）
python3 simple_youtu_converter.py --input your_youtu_data.json --output cache/converted.json && \
python3 create_qa_from_converted.py --input cache/converted.json --output cache/qa_pairs.json --format Alpaca && \
echo "🎉 问答数据生成完成！查看 cache/qa_pairs.json"
```

这样你就可以快速、稳定地从 youtu-graphrag 数据生成问答训练数据了！