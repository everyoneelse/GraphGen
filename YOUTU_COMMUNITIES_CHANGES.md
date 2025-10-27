# Youtu-GraphRAG 社区集成 - 修改总结

## 概述

为支持使用 youtu-graphrag 预计算的社区信息来生成 COT 数据，对以下文件进行了修改和新增。

## 修改的文件

### 1. `youtu_json_converter.py`

**修改内容：**
- 添加 `community_nodes` 字典存储社区节点信息
- 在 `parse_youtu_data()` 中识别 `label='community'` 的节点
- 添加 `export_communities()` 方法导出社区信息到 JSON
- 添加 `get_communities_dict()` 方法转换社区格式为 `{node_name: community_id}`
- 在统计信息中包含社区数量

**关键方法：**
```python
def get_communities_dict(self) -> Dict[str, int]:
    """将社区信息转换为 CommunityDetector 格式"""
    communities_dict = {}
    for comm_id, (comm_name, comm_data) in enumerate(self.community_nodes.items()):
        members = comm_data.get('members', [])
        for member in members:
            communities_dict[member] = comm_id
    return communities_dict
```

### 2. `run_youtu_json_kg.py`

**修改内容：**
- 修改 `convert_youtu_json_kg()` 函数：
  - 添加 `communities_file` 参数
  - 导出社区信息到单独的 JSON 文件
  - 返回 converter 对象而非布尔值
  
- 修改 `run_full_graphgen()` 函数：
  - 在转换后提取社区信息
  - 在 COT 模式下自动使用预计算社区
  - 将社区信息添加到配置的 `partition["precomputed_communities"]`

**关键代码：**
```python
# 提取社区信息（如果用于 COT 模式）
if generation_mode == "cot" and hasattr(converter, 'get_communities_dict'):
    communities_dict = converter.get_communities_dict()
    if communities_dict:
        print(f"✅ 已提取 {len(set(communities_dict.values()))} 个社区信息")

# 添加到配置
if generation_mode == "cot" and communities_dict:
    config["partition"]["precomputed_communities"] = communities_dict
```

### 3. `graphgen/graphgen.py`

**修改内容：**
- 在 `generate()` 方法的 COT 分支中：
  - 从配置中读取 `precomputed_communities`
  - 传递给 `generate_cot()` 函数

**修改代码：**
```python
elif mode == "cot":
    # 检查是否有预计算的社区信息
    precomputed_communities = partition_config.get("precomputed_communities")
    results = await generate_cot(
        self.graph_storage,
        self.synthesizer_llm_client,
        method_params=partition_config["method_params"],
        precomputed_communities=precomputed_communities,
    )
```

### 4. `graphgen/operators/generate/generate_cot.py`

**修改内容：**
- 添加 `precomputed_communities` 参数
- 导入 `PrecomputedCommunityDetector`
- 根据是否有预计算社区选择使用 `PrecomputedCommunityDetector` 或 `CommunityDetector`

**修改代码：**
```python
async def generate_cot(
    graph_storage: NetworkXStorage,
    synthesizer_llm_client: OpenAIClient,
    method_params: Dict = None,
    precomputed_communities: Dict[str, int] = None,  # 新增参数
):
    if precomputed_communities:
        detector = PrecomputedCommunityDetector(
            graph_storage=graph_storage,
            precomputed_communities=precomputed_communities,
            method="precomputed",
            method_params=method_params or {}
        )
    else:
        # 使用默认的 Leiden 算法
        ...
```

## 新增的文件

### 1. `graphgen/models/community/precomputed_community_detector.py`

**功能：**
- 实现 `PrecomputedCommunityDetector` 类
- 使用外部提供的社区信息而非重新检测
- 支持 `max_size` 参数来分割过大的社区

**核心类：**
```python
@dataclass
class PrecomputedCommunityDetector:
    graph_storage: NetworkXStorage = None
    precomputed_communities: Dict[str, int] = None
    method: str = "precomputed"
    method_params: Dict[str, Any] = None
    
    async def detect_communities(self) -> Dict[str, int]:
        """返回预计算的社区信息"""
        if self.precomputed_communities is None:
            raise ValueError("预计算社区信息为空")
        
        max_size = self.method_params.get("max_size") if self.method_params else None
        if max_size and max_size > 0:
            return await self._split_communities(self.precomputed_communities, max_size)
        
        return self.precomputed_communities
```

### 2. `graphgen/models/community/__init__.py`

**功能：**
- 导出 `CommunityDetector` 和 `PrecomputedCommunityDetector`

### 3. `USE_YOUTU_COMMUNITIES.md`

**功能：**
- 完整的使用指南
- 包含背景、功能特点、使用方法、配置选项
- 故障排除和示例输出

### 4. `test_youtu_communities.py`

**功能：**
- 测试脚本，验证社区信息提取
- 检查社区与图谱节点的匹配度
- 提供使用建议

## 使用流程

### 完整流程（推荐）

```bash
# 一键运行，自动检测和使用社区信息
python run_youtu_json_kg.py \
  --json path/to/youtu_graph.json \
  --mode cot \
  --disable-quiz
```

### 测试流程

```bash
# 1. 测试社区提取
python test_youtu_communities.py --json path/to/youtu_graph.json

# 2. 如果测试通过，运行完整流程
python run_youtu_json_kg.py \
  --json path/to/youtu_graph.json \
  --mode cot \
  --disable-quiz
```

## 工作原理

```
youtu_graph.json
    │
    ├─> YoutuJSONConverter.parse_youtu_data()
    │   └─> 识别 label='community' 节点
    │       └─> 存储到 community_nodes
    │
    ├─> YoutuJSONConverter.get_communities_dict()
    │   └─> 转换为 {node_name: community_id}
    │
    └─> run_full_graphgen()
        └─> 添加到 config["partition"]["precomputed_communities"]
            └─> GraphGen.generate() [mode='cot']
                └─> generate_cot(precomputed_communities=...)
                    └─> PrecomputedCommunityDetector.detect_communities()
                        └─> 直接返回预计算的社区
                            └─> 生成 COT 数据
```

## 优势

1. **性能提升**：跳过 Leiden 算法计算，直接使用预计算结果
2. **一致性**：保持与 youtu-graphrag 相同的社区划分
3. **灵活性**：
   - 如果没有预计算社区，自动回退到 Leiden 算法
   - 支持 `max_size` 参数分割过大的社区
4. **可追溯性**：导出的社区 JSON 文件便于检查和调试

## 兼容性

- ✅ 兼容原有的 Leiden 算法社区检测
- ✅ 兼容所有现有的生成模式（atomic、aggregated、multi_hop）
- ✅ COT 模式自动检测并使用预计算社区
- ✅ 向后兼容：如果没有社区信息，自动回退到算法检测

## 测试建议

使用 `test_youtu_communities.py` 脚本验证：

```bash
python test_youtu_communities.py --json your_graph.json
```

检查输出的：
- 社区数量
- 成员匹配率（应 >= 70%）
- 社区大小分布

## 参考

- `USE_YOUTU_COMMUNITIES.md` - 详细使用指南
- `test_youtu_communities.py` - 测试脚本
- youtu-graphrag 社区格式示例见 `USE_YOUTU_COMMUNITIES.md`
