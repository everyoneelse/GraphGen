# 中间步骤保存功能说明

## 概述

现在使用 `run_youtu_json_kg.py` 运行不同模式（atomic/aggregated/multi_hop/cot）时，会在最终的 `qa.json` 中保存中间步骤的详细信息，包括：
- 各步骤使用的 prompt
- 各步骤的生成结果
- 输入的实体和关系信息

## 修改的文件

### 1. `/workspace/graphgen/operators/traverse_graph.py`
修改了三个生成函数以保存中间步骤：
- `traverse_graph_for_atomic`: Atomic模式
- `traverse_graph_for_aggregated`: Aggregated模式  
- `traverse_graph_for_multi_hop`: Multi-hop模式

### 2. `/workspace/graphgen/operators/generate/generate_cot.py`
修改了CoT生成函数以保存中间步骤：
- `generate_cot`: CoT模式

### 3. `/workspace/graphgen/utils/format.py`
修改了格式化函数以保留中间步骤信息：
- `format_generation_results`: 确保不同格式（Alpaca/Sharegpt/ChatML）都保留中间步骤

## 各模式的中间步骤结构

### Atomic 模式

```json
{
  "instruction": "问题文本",
  "input": "",
  "output": "答案文本",
  "intermediate_steps": {
    "mode": "atomic",
    "input_description": "实体或关系的描述",
    "qa_generation_prompt": "生成问答的完整prompt",
    "raw_qa_response": "LLM返回的原始响应"
  }
}
```

### Aggregated 模式（单问答）

```json
{
  "instruction": "问题文本",
  "input": "",
  "output": "答案文本",
  "intermediate_steps": {
    "mode": "aggregated",
    "entities": ["实体1: 描述1", "实体2: 描述2", ...],
    "relationships": ["实体A -- 实体B: 关系描述", ...],
    "step1_rephrasing_prompt": "重述文本的prompt",
    "step1_rephrased_context": "重述后的上下文",
    "step2_question_generation_prompt": "生成问题的prompt",
    "step2_generated_question": "生成的问题"
  }
}
```

### Aggregated 模式（多问答）

```json
{
  "instruction": "问题文本",
  "input": "",
  "output": "答案文本",
  "intermediate_steps": {
    "mode": "aggregated_multi",
    "entities": ["实体1: 描述1", "实体2: 描述2", ...],
    "relationships": ["实体A -- 实体B: 关系描述", ...],
    "step1_rephrasing_prompt": "重述文本的prompt",
    "step1_rephrased_context": "重述后的上下文",
    "step2_multi_qa_generation_prompt": "生成多个问答的prompt",
    "step2_raw_multi_qa_response": "LLM返回的原始多问答响应"
  }
}
```

### Multi-hop 模式

```json
{
  "instruction": "问题文本",
  "input": "",
  "output": "答案文本",
  "intermediate_steps": {
    "mode": "multi_hop",
    "entities": ["实体1: 描述1", "实体2: 描述2", ...],
    "relationships": ["实体A -- 实体B: 关系描述", ...],
    "entities_formatted": "格式化的实体列表字符串",
    "relationships_formatted": "格式化的关系列表字符串",
    "multi_hop_generation_prompt": "多跳推理生成的prompt",
    "raw_response": "LLM返回的原始响应"
  }
}
```

### CoT 模式

```json
{
  "instruction": "问题文本",
  "input": "",
  "output": "推理链答案",
  "reasoning_path": "推理路径设计",
  "intermediate_steps": {
    "mode": "cot",
    "community_id": 1,
    "entities": ["(实体名: 描述)", ...],
    "relationships": ["(源实体) - [关系描述] -> (目标实体)", ...],
    "entities_str": "实体字符串（用于prompt）",
    "relationships_str": "关系字符串（用于prompt）",
    "step1_template_design_prompt": "设计问题和推理路径的prompt",
    "step1_template_design_response": "LLM返回的问题和推理路径设计",
    "step1_extracted_question": "提取的问题",
    "step1_extracted_reasoning_path": "提取的推理路径",
    "step2_answer_generation_prompt": "生成最终答案的prompt",
    "step2_final_answer": "最终的CoT答案"
  }
}
```

## 使用示例

### 运行不同模式

```bash
# Atomic 模式
python run_youtu_json_kg.py --json data.json --mode atomic --format Alpaca

# Aggregated 模式
python run_youtu_json_kg.py --json data.json --mode aggregated --format Alpaca

# Multi-hop 模式
python run_youtu_json_kg.py --json data.json --mode multi_hop --format Alpaca

# CoT 模式
python run_youtu_json_kg.py --json data.json --mode cot --format Sharegpt
```

### 查看结果

生成的 `qa.json` 文件位于：
```
cache/data/graphgen/{unique_id}/qa.json
```

每条数据都会包含 `intermediate_steps` 字段（以及CoT模式下的 `reasoning_path` 字段），其中保存了完整的生成过程信息。

## 分析中间步骤

可以使用以下Python代码来分析中间步骤：

```python
import json

# 加载qa.json
with open('cache/data/graphgen/{unique_id}/qa.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 查看第一条数据的中间步骤
first_item = data[0]
print("Mode:", first_item['intermediate_steps']['mode'])

# Atomic模式
if first_item['intermediate_steps']['mode'] == 'atomic':
    print("\n=== Atomic Mode ===")
    print("Input:", first_item['intermediate_steps']['input_description'])
    print("\nPrompt:", first_item['intermediate_steps']['qa_generation_prompt'])
    print("\nResponse:", first_item['intermediate_steps']['raw_qa_response'])

# CoT模式
elif first_item['intermediate_steps']['mode'] == 'cot':
    print("\n=== CoT Mode ===")
    print("Step 1 Prompt:", first_item['intermediate_steps']['step1_template_design_prompt'])
    print("\nStep 1 Response:", first_item['intermediate_steps']['step1_template_design_response'])
    print("\nStep 2 Prompt:", first_item['intermediate_steps']['step2_answer_generation_prompt'])
    print("\nStep 2 Response:", first_item['intermediate_steps']['step2_final_answer'])

# Aggregated模式
elif first_item['intermediate_steps']['mode'] == 'aggregated':
    print("\n=== Aggregated Mode ===")
    print("Entities:", first_item['intermediate_steps']['entities'])
    print("\nStep 1 Prompt:", first_item['intermediate_steps']['step1_rephrasing_prompt'])
    print("\nStep 1 Response:", first_item['intermediate_steps']['step1_rephrased_context'])
    print("\nStep 2 Prompt:", first_item['intermediate_steps']['step2_question_generation_prompt'])

# Multi-hop模式
elif first_item['intermediate_steps']['mode'] == 'multi_hop':
    print("\n=== Multi-hop Mode ===")
    print("Entities:", first_item['intermediate_steps']['entities'])
    print("\nPrompt:", first_item['intermediate_steps']['multi_hop_generation_prompt'])
    print("\nResponse:", first_item['intermediate_steps']['raw_response'])
```

## 注意事项

1. **存储空间**: 由于保存了所有中间步骤，生成的 `qa.json` 文件会比之前大很多。建议根据需要定期清理不需要的中间数据。

2. **兼容性**: 所有三种输出格式（Alpaca、Sharegpt、ChatML）都支持保存中间步骤。

3. **调试**: 中间步骤信息对于调试和优化prompt非常有用，可以帮助理解模型在每个步骤的输入和输出。

4. **数据分析**: 可以使用中间步骤数据来分析：
   - 哪些prompt产生了更好的结果
   - 实体和关系信息如何影响最终输出
   - 不同步骤之间的转换是否合理

## 向后兼容性

这些修改不会影响现有代码的功能，只是添加了额外的信息字段。如果不需要中间步骤信息，可以简单地忽略 `intermediate_steps` 字段。
