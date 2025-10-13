# 🔧 修复后的 youtu-graphrag 使用指南

## 🚨 导入问题解决方案

你遇到的 `YoutuJSONConverter` 导入问题主要是由于缺少依赖模块。我已经创建了两个解决方案：

### 方案 1: 使用简化转换器（推荐）

我创建了一个不依赖外部库的简化版转换器：

```bash
# 使用简化转换器
python3 simple_youtu_converter.py \
    --input your_youtu_data.json \
    --output cache/converted_data.json
```

### 方案 2: 安装完整依赖

如果你想使用完整功能，需要安装以下依赖：

```bash
pip install networkx pandas python-dotenv pyyaml tqdm gradio
```

## 🎯 推荐的完整工作流程

### 步骤 1: 转换你的 youtu-graphrag 数据

```bash
# 使用简化转换器（无需额外依赖）
python3 simple_youtu_converter.py \
    --input your_youtu_data.json \
    --output cache/converted_data.json
```

这会生成一个包含节点和边信息的 JSON 文件。

### 步骤 2: 查看转换结果

```bash
# 查看转换后的数据结构
cat cache/converted_data.json
```

转换后的数据格式：
```json
{
  "nodes": [
    {
      "id": "FC Barcelona",
      "entity_name": "FC Barcelona",
      "entity_type": "organization",
      "description": "Type: organization; type: football club; status: active",
      "source_id": "0FCIUkTr"
    }
  ],
  "edges": [
    {
      "source": "Lionel Messi",
      "target": "FC Barcelona",
      "relation_type": "played_for",
      "description": "Lionel Messi played_for FC Barcelona"
    }
  ]
}
```

### 步骤 3: 手动创建问答数据（简单方法）

基于转换后的数据，你可以手动或编程方式创建问答对：

```python
# create_qa_from_converted.py
import json

def create_qa_from_converted_data(json_file):
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    qa_pairs = []
    
    # 从节点创建属性问答
    for node in data['nodes']:
        entity_name = node['entity_name']
        description = node['description']
        entity_type = node['entity_type']
        
        # 类型问答
        qa_pairs.append({
            "instruction": f"What type of entity is {entity_name}?",
            "input": "",
            "output": f"{entity_name} is a {entity_type}."
        })
        
        # 属性问答
        if ";" in description:
            attributes = description.split(";")[1:]  # 跳过 "Type: xxx"
            if attributes:
                qa_pairs.append({
                    "instruction": f"What are the attributes of {entity_name}?",
                    "input": "",
                    "output": f"{entity_name} has the following attributes: {', '.join(attr.strip() for attr in attributes)}."
                })
    
    # 从边创建关系问答
    for edge in data['edges']:
        source = edge['source']
        target = edge['target']
        relation = edge['relation_type']
        
        qa_pairs.append({
            "instruction": f"What is the relationship between {source} and {target}?",
            "input": "",
            "output": f"{source} {relation} {target}."
        })
    
    return qa_pairs

# 使用示例
qa_pairs = create_qa_from_converted_data('cache/converted_data.json')

# 保存为 Alpaca 格式
with open('cache/qa_pairs.json', 'w', encoding='utf-8') as f:
    json.dump(qa_pairs, f, ensure_ascii=False, indent=2)

print(f"生成了 {len(qa_pairs)} 个问答对")
```

## 🎯 测试转换功能

我已经用你的示例数据测试过了：

```bash
python3 simple_youtu_converter.py \
    --input example_youtu_data.json \
    --output cache/converted_data.json
```

结果：
- ✅ 成功识别 3 个实体：FC Barcelona、Lionel Messi、Camp Nou
- ✅ 成功识别 4 个属性：type: football club、status: active、position: forward、capacity: 99,354
- ✅ 成功识别 2 个关系：played_for、home_stadium

## 🚀 快速开始（无需复杂依赖）

```bash
# 1. 转换你的数据
python3 simple_youtu_converter.py \
    --input your_youtu_data.json \
    --output cache/converted_data.json

# 2. 创建问答生成脚本
cat > create_qa.py << 'EOF'
import json

def create_qa_from_converted_data(json_file):
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    qa_pairs = []
    
    # 从节点创建问答
    for node in data['nodes']:
        entity_name = node['entity_name']
        description = node['description']
        entity_type = node['entity_type']
        
        qa_pairs.append({
            "instruction": f"What type of entity is {entity_name}?",
            "input": "",
            "output": f"{entity_name} is a {entity_type}."
        })
        
        if ";" in description:
            attributes = description.split(";")[1:]
            if attributes:
                qa_pairs.append({
                    "instruction": f"What are the attributes of {entity_name}?",
                    "input": "",
                    "output": f"{entity_name} has the following attributes: {', '.join(attr.strip() for attr in attributes)}."
                })
    
    # 从边创建问答
    for edge in data['edges']:
        source = edge['source']
        target = edge['target']
        relation = edge['relation_type']
        
        qa_pairs.append({
            "instruction": f"What is the relationship between {source} and {target}?",
            "input": "",
            "output": f"{source} {relation} {target}."
        })
    
    return qa_pairs

# 生成问答对
qa_pairs = create_qa_from_converted_data('cache/converted_data.json')

# 保存
with open('cache/qa_pairs.json', 'w', encoding='utf-8') as f:
    json.dump(qa_pairs, f, ensure_ascii=False, indent=2)

print(f"✅ 生成了 {len(qa_pairs)} 个问答对")
for i, qa in enumerate(qa_pairs[:3]):  # 显示前3个
    print(f"\n{i+1}. Q: {qa['instruction']}")
    print(f"   A: {qa['output']}")
EOF

# 3. 运行问答生成
python3 create_qa.py
```

## 🎉 优势

这个简化方案的优势：

1. **🚀 无需复杂依赖** - 只使用 Python 标准库
2. **⚡ 快速运行** - 直接转换和生成，无需 LLM API
3. **💰 零成本** - 不需要调用任何付费 API
4. **🔧 易于定制** - 可以轻松修改问答生成逻辑
5. **📊 透明过程** - 每一步都可以检查和调试

现在你可以直接使用你的 youtu-graphrag JSON 数据生成问答对了！