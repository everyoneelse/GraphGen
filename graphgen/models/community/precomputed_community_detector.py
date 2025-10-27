"""
预计算社区检测器 - 使用外部提供的社区信息
用于 youtu-graphrag 等已经包含社区检测结果的知识图谱
"""

from typing import Dict, Any
from dataclasses import dataclass

from graphgen.models.storage.networkx_storage import NetworkXStorage


@dataclass
class PrecomputedCommunityDetector:
    """使用预计算的社区信息，而不是重新检测"""
    
    graph_storage: NetworkXStorage = None
    precomputed_communities: Dict[str, int] = None  # {node_name: community_id}
    method: str = "precomputed"
    method_params: Dict[str, Any] = None
    
    async def detect_communities(self) -> Dict[str, int]:
        """
        返回预计算的社区信息
        
        Returns:
            Dict[str, int]: {node_name: community_id} 的字典
        """
        if self.precomputed_communities is None:
            raise ValueError("预计算社区信息为空，请先加载社区数据")
        
        # 如果指定了 max_size，需要分割大社区
        max_size = None
        if self.method_params:
            max_size = self.method_params.get("max_size")
        
        if max_size and max_size > 0:
            return await self._split_communities(self.precomputed_communities, max_size)
        
        return self.precomputed_communities
    
    @staticmethod
    async def _split_communities(
        communities: Dict[str, int], max_size: int
    ) -> Dict[str, int]:
        """
        分割大于 max_size 的社区为更小的子社区
        
        Args:
            communities: 原始社区字典 {node: community_id}
            max_size: 最大社区大小
            
        Returns:
            分割后的社区字典
        """
        from collections import defaultdict
        
        # 按社区ID分组节点
        cid2nodes: Dict[int, list] = defaultdict(list)
        for node, cid in communities.items():
            cid2nodes[cid].append(node)
        
        # 分割大社区
        new_communities: Dict[str, int] = {}
        new_cid = 0
        
        for cid, nodes in cid2nodes.items():
            if len(nodes) <= max_size:
                # 社区大小符合要求，直接分配新ID
                for n in nodes:
                    new_communities[n] = new_cid
                new_cid += 1
            else:
                # 社区太大，分割成多个子社区
                for start in range(0, len(nodes), max_size):
                    sub_nodes = nodes[start : start + max_size]
                    for n in sub_nodes:
                        new_communities[n] = new_cid
                    new_cid += 1
        
        return new_communities
