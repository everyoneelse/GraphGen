# GraphGen 快速启动指南 - 从知识图谱生成QA对

## 🎯 概述
本指南将帮助您使用GraphGen从知识图谱或文本数据生成高质量的QA对。

---

## 📦 步骤 1: 安装依赖

### 激活虚拟环境（根据服务器）
```bash
# 如果在 10.8.71.126 服务器
source activate py312

# 如果在 10.8.71.44 服务器
source activate py310
source /opt/rh/devtoolset-9/enable
```

### 安装项目依赖
```bash
pip install -r requirements.txt
```

### 或者安装开发版依赖
```bash
pip install -r requirements-dev.txt
```

---

## 🔑 步骤 2: 配置环境变量

创建 `.env` 文件：
```bash
cp .env.example .env
```

编辑 `.env` 文件，填入您的API配置：
```bash
# Synthesizer - 用于构建知识图谱和生成QA对
SYNTHESIZER_MODEL=gpt-4o-mini                    # 或其他模型
SYNTHESIZER_BASE_URL=https://api.openai.com/v1  # API地址
SYNTHESIZER_API_KEY=sk-xxxxx                     # 您的API密钥

# Trainee - 用于评估知识掌握情况
TRAINEE_MODEL=gpt-4o-mini                        # 可以与Synthesizer相同或不同
TRAINEE_BASE_URL=https://api.openai.com/v1
TRAINEE_API_KEY=sk-xxxxx
```

### 推荐的API提供商：
1. **OpenAI API** - https://api.openai.com/v1
2. **SiliconFlow API** (部分免费) - https://api.siliconflow.cn/v1
3. **本地模型** - 使用 vLLM/Ollama 等本地服务

### 从HuggingFace下载模型（可选）
```bash
export HF_ENDPOINT=https://hf-mirror.com
```

---

## 📝 步骤 3: 准备输入数据

### 支持的输入格式

#### 1. JSON格式 (`*.json`)
```json
[
  {"content": "您的知识内容1"},
  {"content": "您的知识内容2"}
]
```

#### 2. JSONL格式 (`*.jsonl`)
```jsonl
{"content": "您的知识内容1"}
{"content": "您的知识内容2"}
```

#### 3. CSV格式 (`*.csv`)
```csv
content
您的知识内容1
您的知识内容2
```

#### 4. TXT格式 (`*.txt`)
```text
您的知识内容1

您的知识内容2
```

### 使用示例数据
项目提供了示例文件：
- `resources/input_examples/json_demo.json`
- `resources/input_examples/jsonl_demo.jsonl`
- `resources/input_examples/csv_demo.csv`
- `resources/input_examples/txt_demo.txt`

---

## 🎯 步骤 4: 选择生成模式

GraphGen 提供4种QA生成模式：

| 模式 | 说明 | 适用场景 | 配置文件 |
|------|------|----------|----------|
| **atomic** | 原子问答对 | 基础知识点覆盖 | `configs/atomic_config.yaml` |
| **aggregated** | 聚合问答对 | 复杂知识整合 | `configs/aggregated_config.yaml` |
| **multi_hop** | 多跳问答对 | 推理链路训练 | `configs/multi_hop_config.yaml` |
| **cot** | 思维链问答对 | 逐步推理能力 | `configs/cot_config.yaml` |

### 配置文件说明

编辑 `graphgen/configs/<mode>_config.yaml`：

```yaml
read:
  input_file: resources/input_examples/json_demo.json  # 输入文件路径
  
split:
  chunk_size: 1024         # 文本分块大小（tokens）
  chunk_overlap: 100       # 分块重叠大小
  
search:
  enabled: false           # 是否启用网络搜索补充信息
  search_types: ["google"] # 搜索引擎类型
  
quiz_and_judge:
  enabled: true            # 是否启用知识测试（推荐开启）
  quiz_samples: 2          # 每个知识点的测试样本数
  re_judge: false          # 是否重新评估
  
partition:
  method: ece              # ECE分区方法（基于理解损失）
  method_params:
    bidirectional: true    # 是否双向遍历图
    edge_sampling: max_loss # 边采样策略（max_loss/min_loss/random）
    expand_method: max_width # 扩展方法（max_width/max_depth）
    max_depth: 3           # 图遍历最大深度
    max_extra_edges: 5     # 每个方向最多扩展边数
    loss_strategy: only_edge # 损失计算策略
    
generate:
  mode: atomic             # 生成模式
  data_format: ChatML      # 输出格式（ChatML/Alpaca/Sharegpt）
```

### 关键参数调优建议：

#### 对于 atomic 模式（基础知识）：
- `max_depth: 1-3` - 较浅的图遍历
- `max_extra_edges: 2-5` - 较少的边扩展
- `quiz_samples: 2` - 适中的测试样本

#### 对于 aggregated 模式（复杂知识）：
- `max_depth: 5-10` - 较深的图遍历
- `max_extra_edges: 10-20` - 更多的边扩展
- `quiz_samples: 3-5` - 更多测试样本

#### 对于 multi_hop 模式（多跳推理）：
- `max_depth: 1-3` - 中等深度
- `max_extra_edges: 2-5` - 控制推理链长度
- `edge_sampling: max_loss` - 聚焦难点

#### 对于 cot 模式（思维链）：
- 使用社区发现算法
- 关注推理步骤的连贯性

---

## 🚀 步骤 5: 运行生成

### 方式一：使用Shell脚本（推荐）

```bash
# 生成原子问答对（基础知识）
bash scripts/generate/generate_atomic.sh

# 生成聚合问答对（复杂知识）
bash scripts/generate/generate_aggregated.sh

# 生成多跳问答对（推理能力）
bash scripts/generate/generate_multi_hop.sh

# 生成思维链问答对（逐步推理）
bash scripts/generate/generate_cot.sh
```

### 方式二：直接运行Python模块

```bash
python3 -m graphgen.generate \
  --config_file graphgen/configs/atomic_config.yaml \
  --output_dir cache/
```

### 方式三：使用自定义配置

```bash
# 复制并修改配置文件
cp graphgen/configs/atomic_config.yaml my_custom_config.yaml
# 编辑 my_custom_config.yaml

# 运行
python3 -m graphgen.generate \
  --config_file my_custom_config.yaml \
  --output_dir my_output/
```

---

## 📊 步骤 6: 查看生成结果

### 输出目录结构
```
cache/data/graphgen/<timestamp>/
├── qa_pairs.json              # 生成的QA对
├── knowledge_graph.json       # 知识图谱数据
├── config.yaml                # 配置文件备份
├── <timestamp>_<mode>.log     # 运行日志
└── metrics.json               # 评估指标
```

### 查看生成的QA对
```bash
# 查看最新生成的数据
ls -lt cache/data/graphgen/

# 查看QA对内容
cat cache/data/graphgen/<timestamp>/qa_pairs.json | jq '.[0]'
```

### QA对数据格式示例

#### ChatML格式
```json
{
  "messages": [
    {"role": "system", "content": "你是一个专业的助手..."},
    {"role": "user", "content": "问题内容"},
    {"role": "assistant", "content": "回答内容"}
  ]
}
```

#### Alpaca格式
```json
{
  "instruction": "问题内容",
  "input": "",
  "output": "回答内容"
}
```

#### ShareGPT格式
```json
{
  "conversations": [
    {"from": "human", "value": "问题内容"},
    {"from": "gpt", "value": "回答内容"}
  ]
}
```

---

## 🔧 步骤 7: 使用生成的数据进行微调

生成QA对后，可以使用以下工具进行模型微调：

### 使用 LLaMA-Factory
```bash
git clone https://github.com/hiyouga/LLaMA-Factory
cd LLaMA-Factory

# 准备数据集配置
# 将生成的QA对添加到 data/dataset_info.json

# 运行微调
llamafactory-cli train examples/train_lora/llama3_lora_sft.yaml
```

### 使用 xtuner
```bash
git clone https://github.com/InternLM/xtuner
cd xtuner

# 运行微调
xtuner train internlm2_chat_7b_qlora_oasst1_e3 --deepspeed deepspeed_zero2
```

---

## 🎨 步骤 8: 使用Web界面（可选）

启动Gradio界面：
```bash
python -m webui.app
```

访问 `http://localhost:7860` 进行可视化操作。

在线体验：
- [HuggingFace Demo](https://huggingface.co/spaces/chenzihong/GraphGen)
- [ModelScope Demo](https://modelscope.cn/studios/chenzihong/GraphGen)
- [OpenXLab Demo](https://g-app-center-120612-6433-jpdvmvp.openxlab.space)

---

## 🐛 常见问题排查

### 1. API调用失败
```bash
# 检查环境变量
cat .env

# 测试API连接
curl $SYNTHESIZER_BASE_URL/models \
  -H "Authorization: Bearer $SYNTHESIZER_API_KEY"
```

### 2. 内存不足
- 减小 `chunk_size`
- 减少 `max_extra_edges`
- 降低 `max_depth`

### 3. 生成速度慢
- 关闭 `quiz_and_judge.enabled`（不推荐，会影响质量）
- 减少 `quiz_samples`
- 使用更快的模型

### 4. QA质量不佳
- 增加 `quiz_samples`
- 启用 `search.enabled` 补充信息
- 尝试更强的SYNTHESIZER模型
- 调整 `edge_sampling` 策略

### 5. 依赖安装失败
```bash
# 升级pip
pip install --upgrade pip

# 单独安装可能有问题的包
pip install leidenalg
pip install python-igraph
```

---

## 📈 进阶技巧

### 1. 混合多种生成模式
```bash
# 生成不同类型的QA对并合并
bash scripts/generate/generate_atomic.sh
bash scripts/generate/generate_aggregated.sh
bash scripts/generate/generate_multi_hop.sh

# 合并数据
python -c "
import json
from pathlib import Path

qa_files = list(Path('cache/data/graphgen').rglob('qa_pairs.json'))
all_qas = []
for f in qa_files:
    all_qas.extend(json.load(f.open()))
    
with open('merged_qa_pairs.json', 'w') as out:
    json.dump(all_qas, out, ensure_ascii=False, indent=2)
"
```

### 2. 批量处理多个文档
```bash
# 创建批处理脚本
for file in data/*.json; do
  sed "s|input_file:.*|input_file: $file|" \
    graphgen/configs/atomic_config.yaml > temp_config.yaml
  python3 -m graphgen.generate \
    --config_file temp_config.yaml \
    --output_dir cache/
done
```

### 3. 自定义prompt模板
编辑 `graphgen/templates/question_generation.py` 等文件来自定义QA生成的提示词。

---

## 📚 更多资源

- **论文**: https://arxiv.org/abs/2505.20416
- **文档**: https://graphgen-cookbook.readthedocs.io/
- **GitHub**: https://github.com/open-sciencelab/GraphGen
- **FAQ**: https://github.com/open-sciencelab/GraphGen/issues/10
- **最佳实践**: https://github.com/open-sciencelab/GraphGen/issues/17

---

## 💡 快速开始示例

### 最小化配置运行
```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置API（使用您的密钥）
export SYNTHESIZER_MODEL=gpt-4o-mini
export SYNTHESIZER_BASE_URL=https://api.openai.com/v1
export SYNTHESIZER_API_KEY=sk-xxxxx
export TRAINEE_MODEL=gpt-4o-mini
export TRAINEE_BASE_URL=https://api.openai.com/v1
export TRAINEE_API_KEY=sk-xxxxx

# 3. 使用示例数据生成
bash scripts/generate/generate_atomic.sh

# 4. 查看结果
ls -lt cache/data/graphgen/
```

---

## 🎯 下一步

1. ✅ 完成环境配置
2. ✅ 准备您的知识数据
3. ✅ 运行第一次生成
4. 📊 评估QA质量
5. 🔧 调优参数
6. 🚀 大规模生成
7. 🤖 模型微调

祝您使用愉快！ 🎉
