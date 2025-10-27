"""
Node和Edge选取调试工具

功能：
1. 拦截并记录batch构建过程
2. 计算覆盖率统计
3. 分析选取分布
4. 生成可视化报告
"""

import json
import os
from collections import defaultdict, Counter
from typing import Dict, List, Tuple
import asyncio


class NodeEdgeDebugger:
    """Node和Edge选取调试器"""
    
    def __init__(self, output_dir: str = "./debug_output"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # 统计数据
        self.total_nodes = 0
        self.total_edges = 0
        self.selected_nodes = set()
        self.selected_edges = set()
        self.node_frequency = Counter()
        self.edge_frequency = Counter()
        self.batch_info = []
        self.node_losses = {}
        self.edge_losses = {}
        
    def record_graph_info(self, nodes: list, edges: list):
        """记录图的基本信息"""
        self.total_nodes = len(nodes)
        self.total_edges = len(edges)
        
        # 记录loss值
        for node in nodes:
            node_id = node[0]
            if "loss" in node[1]:
                self.node_losses[node_id] = node[1]["loss"]
        
        for edge in edges:
            edge_id = (edge[0], edge[1])
            if "loss" in edge[2]:
                self.edge_losses[edge_id] = edge[2]["loss"]
        
        print(f"\n{'='*80}")
        print(f"图信息统计")
        print(f"{'='*80}")
        print(f"总节点数: {self.total_nodes}")
        print(f"总边数: {self.total_edges}")
        print(f"有loss值的节点: {len(self.node_losses)}")
        print(f"有loss值的边: {len(self.edge_losses)}")
    
    def record_batch(self, batch_id: int, nodes: list, edges: list, config: dict = None):
        """记录单个batch的信息"""
        node_ids = [n['node_id'] if isinstance(n, dict) else n[0] for n in nodes]
        edge_pairs = [(e[0], e[1]) for e in edges]
        
        # 更新频次统计
        for node_id in node_ids:
            self.selected_nodes.add(node_id)
            self.node_frequency[node_id] += 1
        
        for edge_pair in edge_pairs:
            self.selected_edges.add(edge_pair)
            self.edge_frequency[edge_pair] += 1
        
        # 计算batch的loss
        batch_losses = []
        for edge in edges:
            edge_id = (edge[0], edge[1])
            if edge_id in self.edge_losses:
                batch_losses.append(self.edge_losses[edge_id])
        
        avg_loss = sum(batch_losses) / len(batch_losses) if batch_losses else None
        
        batch_data = {
            'batch_id': batch_id,
            'node_ids': node_ids,
            'edge_pairs': edge_pairs,
            'node_count': len(node_ids),
            'edge_count': len(edge_pairs),
            'avg_loss': avg_loss,
            'config': config
        }
        
        self.batch_info.append(batch_data)
        
        # 实时输出进度
        if batch_id % 10 == 0:
            self._print_progress()
    
    def _print_progress(self):
        """打印当前进度"""
        node_coverage = len(self.selected_nodes) / self.total_nodes * 100 if self.total_nodes > 0 else 0
        edge_coverage = len(self.selected_edges) / self.total_edges * 100 if self.total_edges > 0 else 0
        
        print(f"\n当前进度:")
        print(f"  已处理batch: {len(self.batch_info)}")
        print(f"  节点覆盖率: {node_coverage:.2f}% ({len(self.selected_nodes)}/{self.total_nodes})")
        print(f"  边覆盖率: {edge_coverage:.2f}% ({len(self.selected_edges)}/{self.total_edges})")
    
    def generate_report(self):
        """生成完整的调试报告"""
        print(f"\n{'='*80}")
        print(f"生成最终报告")
        print(f"{'='*80}")
        
        # 1. 保存batch详细信息
        batch_file = os.path.join(self.output_dir, "batch_details.json")
        with open(batch_file, 'w', encoding='utf-8') as f:
            json.dump(self.batch_info, f, indent=2, ensure_ascii=False)
        print(f"✓ Batch详细信息已保存到: {batch_file}")
        
        # 2. 计算统计指标
        stats = self._calculate_statistics()
        stats_file = os.path.join(self.output_dir, "statistics.json")
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)
        print(f"✓ 统计指标已保存到: {stats_file}")
        
        # 3. 生成可读报告
        report_file = os.path.join(self.output_dir, "report.txt")
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(self._generate_text_report(stats))
        print(f"✓ 文本报告已保存到: {report_file}")
        
        # 4. 保存未覆盖的节点和边
        self._save_uncovered_elements()
        
        # 5. 打印摘要到控制台
        self._print_summary(stats)
        
        return stats
    
    def _calculate_statistics(self) -> dict:
        """计算详细统计指标"""
        stats = {}
        
        # 基本覆盖率
        stats['node_coverage'] = {
            'total': self.total_nodes,
            'selected': len(self.selected_nodes),
            'coverage_rate': len(self.selected_nodes) / self.total_nodes if self.total_nodes > 0 else 0,
            'uncovered': self.total_nodes - len(self.selected_nodes)
        }
        
        stats['edge_coverage'] = {
            'total': self.total_edges,
            'selected': len(self.selected_edges),
            'coverage_rate': len(self.selected_edges) / self.total_edges if self.total_edges > 0 else 0,
            'uncovered': self.total_edges - len(self.selected_edges)
        }
        
        # Batch统计
        batch_sizes_nodes = [b['node_count'] for b in self.batch_info]
        batch_sizes_edges = [b['edge_count'] for b in self.batch_info]
        
        stats['batch_statistics'] = {
            'total_batches': len(self.batch_info),
            'nodes_per_batch': {
                'min': min(batch_sizes_nodes) if batch_sizes_nodes else 0,
                'max': max(batch_sizes_nodes) if batch_sizes_nodes else 0,
                'avg': sum(batch_sizes_nodes) / len(batch_sizes_nodes) if batch_sizes_nodes else 0,
            },
            'edges_per_batch': {
                'min': min(batch_sizes_edges) if batch_sizes_edges else 0,
                'max': max(batch_sizes_edges) if batch_sizes_edges else 0,
                'avg': sum(batch_sizes_edges) / len(batch_sizes_edges) if batch_sizes_edges else 0,
            }
        }
        
        # 频次分析
        node_freq_values = list(self.node_frequency.values())
        edge_freq_values = list(self.edge_frequency.values())
        
        stats['frequency_analysis'] = {
            'node_frequency': {
                'min': min(node_freq_values) if node_freq_values else 0,
                'max': max(node_freq_values) if node_freq_values else 0,
                'avg': sum(node_freq_values) / len(node_freq_values) if node_freq_values else 0,
                'top_10_most_frequent': self.node_frequency.most_common(10)
            },
            'edge_frequency': {
                'min': min(edge_freq_values) if edge_freq_values else 0,
                'max': max(edge_freq_values) if edge_freq_values else 0,
                'avg': sum(edge_freq_values) / len(edge_freq_values) if edge_freq_values else 0,
                'top_10_most_frequent': [
                    (f"{e[0][0]} -> {e[0][1]}", e[1]) 
                    for e in self.edge_frequency.most_common(10)
                ]
            }
        }
        
        # Loss分布分析（如果有loss值）
        if self.node_losses or self.edge_losses:
            stats['loss_analysis'] = self._analyze_loss_distribution()
        
        return stats
    
    def _analyze_loss_distribution(self) -> dict:
        """分析loss值的分布"""
        analysis = {}
        
        if self.node_losses:
            selected_node_losses = [
                self.node_losses[node_id] 
                for node_id in self.selected_nodes 
                if node_id in self.node_losses
            ]
            all_node_losses = list(self.node_losses.values())
            
            analysis['nodes'] = {
                'selected_avg_loss': sum(selected_node_losses) / len(selected_node_losses) if selected_node_losses else None,
                'all_avg_loss': sum(all_node_losses) / len(all_node_losses) if all_node_losses else None,
                'selected_max_loss': max(selected_node_losses) if selected_node_losses else None,
                'selected_min_loss': min(selected_node_losses) if selected_node_losses else None,
            }
        
        if self.edge_losses:
            selected_edge_losses = [
                self.edge_losses[edge_id] 
                for edge_id in self.selected_edges 
                if edge_id in self.edge_losses
            ]
            all_edge_losses = list(self.edge_losses.values())
            
            analysis['edges'] = {
                'selected_avg_loss': sum(selected_edge_losses) / len(selected_edge_losses) if selected_edge_losses else None,
                'all_avg_loss': sum(all_edge_losses) / len(all_edge_losses) if all_edge_losses else None,
                'selected_max_loss': max(selected_edge_losses) if selected_edge_losses else None,
                'selected_min_loss': min(selected_edge_losses) if selected_edge_losses else None,
            }
        
        return analysis
    
    def _save_uncovered_elements(self):
        """保存未被覆盖的节点和边"""
        # 未覆盖的节点
        all_nodes = set(self.node_losses.keys()) if self.node_losses else set()
        uncovered_nodes = list(all_nodes - self.selected_nodes)
        
        # 未覆盖的边
        all_edges = set(self.edge_losses.keys()) if self.edge_losses else set()
        uncovered_edges = list(all_edges - self.selected_edges)
        
        uncovered_data = {
            'uncovered_nodes': uncovered_nodes,
            'uncovered_edges': [f"{e[0]} -> {e[1]}" for e in uncovered_edges],
            'uncovered_node_count': len(uncovered_nodes),
            'uncovered_edge_count': len(uncovered_edges)
        }
        
        uncovered_file = os.path.join(self.output_dir, "uncovered_elements.json")
        with open(uncovered_file, 'w', encoding='utf-8') as f:
            json.dump(uncovered_data, f, indent=2, ensure_ascii=False)
        
        print(f"✓ 未覆盖元素已保存到: {uncovered_file}")
    
    def _generate_text_report(self, stats: dict) -> str:
        """生成可读的文本报告"""
        report = []
        report.append("=" * 80)
        report.append("Node和Edge选取调试报告")
        report.append("=" * 80)
        report.append("")
        
        # 覆盖率
        report.append("## 1. 覆盖率统计")
        report.append("-" * 80)
        nc = stats['node_coverage']
        report.append(f"节点覆盖率: {nc['coverage_rate']*100:.2f}%")
        report.append(f"  - 总节点数: {nc['total']}")
        report.append(f"  - 已选节点数: {nc['selected']}")
        report.append(f"  - 未覆盖节点数: {nc['uncovered']}")
        report.append("")
        
        ec = stats['edge_coverage']
        report.append(f"边覆盖率: {ec['coverage_rate']*100:.2f}%")
        report.append(f"  - 总边数: {ec['total']}")
        report.append(f"  - 已选边数: {ec['selected']}")
        report.append(f"  - 未覆盖边数: {ec['uncovered']}")
        report.append("")
        
        # Batch统计
        report.append("## 2. Batch统计")
        report.append("-" * 80)
        bs = stats['batch_statistics']
        report.append(f"总Batch数: {bs['total_batches']}")
        report.append(f"每个Batch的节点数:")
        report.append(f"  - 最小: {bs['nodes_per_batch']['min']}")
        report.append(f"  - 最大: {bs['nodes_per_batch']['max']}")
        report.append(f"  - 平均: {bs['nodes_per_batch']['avg']:.2f}")
        report.append(f"每个Batch的边数:")
        report.append(f"  - 最小: {bs['edges_per_batch']['min']}")
        report.append(f"  - 最大: {bs['edges_per_batch']['max']}")
        report.append(f"  - 平均: {bs['edges_per_batch']['avg']:.2f}")
        report.append("")
        
        # 频次分析
        report.append("## 3. 重复度分析")
        report.append("-" * 80)
        fa = stats['frequency_analysis']
        report.append(f"节点重复度:")
        report.append(f"  - 最小: {fa['node_frequency']['min']}")
        report.append(f"  - 最大: {fa['node_frequency']['max']}")
        report.append(f"  - 平均: {fa['node_frequency']['avg']:.2f}")
        report.append(f"边重复度:")
        report.append(f"  - 最小: {fa['edge_frequency']['min']}")
        report.append(f"  - 最大: {fa['edge_frequency']['max']}")
        report.append(f"  - 平均: {fa['edge_frequency']['avg']:.2f}")
        report.append("")
        
        report.append("出现最频繁的10个节点:")
        for node_id, freq in fa['node_frequency']['top_10_most_frequent']:
            report.append(f"  - {node_id}: {freq}次")
        report.append("")
        
        report.append("出现最频繁的10条边:")
        for edge_str, freq in fa['edge_frequency']['top_10_most_frequent']:
            report.append(f"  - {edge_str}: {freq}次")
        report.append("")
        
        # Loss分析
        if 'loss_analysis' in stats:
            report.append("## 4. Loss分布分析")
            report.append("-" * 80)
            la = stats['loss_analysis']
            
            if 'nodes' in la:
                report.append("节点Loss:")
                report.append(f"  - 已选节点平均Loss: {la['nodes']['selected_avg_loss']:.4f}")
                report.append(f"  - 所有节点平均Loss: {la['nodes']['all_avg_loss']:.4f}")
                report.append(f"  - 已选节点Loss范围: [{la['nodes']['selected_min_loss']:.4f}, {la['nodes']['selected_max_loss']:.4f}]")
            
            if 'edges' in la:
                report.append("边Loss:")
                report.append(f"  - 已选边平均Loss: {la['edges']['selected_avg_loss']:.4f}")
                report.append(f"  - 所有边平均Loss: {la['edges']['all_avg_loss']:.4f}")
                report.append(f"  - 已选边Loss范围: [{la['edges']['selected_min_loss']:.4f}, {la['edges']['selected_max_loss']:.4f}]")
            report.append("")
        
        # 建议
        report.append("## 5. 优化建议")
        report.append("-" * 80)
        report.extend(self._generate_recommendations(stats))
        
        return "\n".join(report)
    
    def _generate_recommendations(self, stats: dict) -> List[str]:
        """基于统计数据生成优化建议"""
        recommendations = []
        
        node_coverage = stats['node_coverage']['coverage_rate']
        edge_coverage = stats['edge_coverage']['coverage_rate']
        
        if node_coverage < 0.5:
            recommendations.append("⚠ 节点覆盖率较低(<50%)，建议:")
            recommendations.append("  - 增加 max_extra_edges 参数")
            recommendations.append("  - 增加 max_depth 参数")
            recommendations.append("  - 将 isolated_node_strategy 设置为 'add'")
            recommendations.append("  - 考虑使用 bidirectional=true")
        
        if edge_coverage < 0.5:
            recommendations.append("⚠ 边覆盖率较低(<50%)，建议:")
            recommendations.append("  - 使用 max_width 模式并增大 max_extra_edges")
            recommendations.append("  - 增加 max_depth 以扩展更多跳")
        
        node_freq_max = stats['frequency_analysis']['node_frequency']['max']
        if node_freq_max > 10:
            recommendations.append("⚠ 存在高频重复节点(>10次)，建议:")
            recommendations.append("  - 减少 max_depth 避免重复访问hub节点")
            recommendations.append("  - 考虑添加采样上限")
        
        if 'loss_analysis' in stats:
            if 'edges' in stats['loss_analysis']:
                selected_avg = stats['loss_analysis']['edges'].get('selected_avg_loss')
                all_avg = stats['loss_analysis']['edges'].get('all_avg_loss')
                if selected_avg and all_avg and abs(selected_avg - all_avg) > 0.1:
                    recommendations.append("⚠ 选取的边的loss分布与整体不一致，建议:")
                    recommendations.append("  - 检查 edge_sampling 策略是否符合预期")
                    recommendations.append("  - 考虑使用 random 采样来平衡分布")
        
        if not recommendations:
            recommendations.append("✓ 当前配置较为合理，可以考虑:")
            recommendations.append("  - 多次运行并使用不同的edge_sampling策略")
            recommendations.append("  - 对比不同配置下的覆盖率差异")
        
        return recommendations
    
    def _print_summary(self, stats: dict):
        """打印摘要到控制台"""
        print(f"\n{'='*80}")
        print(f"最终统计摘要")
        print(f"{'='*80}")
        print(f"节点覆盖率: {stats['node_coverage']['coverage_rate']*100:.2f}%")
        print(f"边覆盖率: {stats['edge_coverage']['coverage_rate']*100:.2f}%")
        print(f"总Batch数: {stats['batch_statistics']['total_batches']}")
        print(f"平均每个Batch节点数: {stats['batch_statistics']['nodes_per_batch']['avg']:.2f}")
        print(f"平均每个Batch边数: {stats['batch_statistics']['edges_per_batch']['avg']:.2f}")
        print(f"{'='*80}")


# 使用示例和说明
if __name__ == "__main__":
    print("""
    Node和Edge选取调试工具使用说明
    ================================
    
    这个工具需要集成到graphgen的代码中使用。主要有两种集成方式：
    
    方式1: 修改 split_kg.py（推荐）
    --------------------------------
    在 graphgen/operators/build_kg/split_kg.py 的 get_batches_with_strategy() 函数中添加：
    
    ```python
    from debug_node_edge_selection import NodeEdgeDebugger
    
    async def get_batches_with_strategy(nodes, edges, graph_storage, traverse_strategy):
        # 创建调试器
        debugger = NodeEdgeDebugger(output_dir="./debug_output")
        
        # 记录图信息
        debugger.record_graph_info(nodes, edges)
        
        # ... 原有代码 ...
        
        # 在生成processing_batches的循环中
        for i, batch in enumerate(processing_batches):
            debugger.record_batch(i, batch[0], batch[1], traverse_strategy)
        
        # 生成报告
        stats = debugger.generate_report()
        
        return processing_batches
    ```
    
    方式2: 后处理分析
    --------------------------------
    如果不想修改源代码，可以在generate完成后分析保存的数据：
    
    ```python
    import json
    from debug_node_edge_selection import NodeEdgeDebugger
    
    # 假设你已经保存了batch信息到JSON文件
    with open('batch_info.json', 'r') as f:
        batch_data = json.load(f)
    
    debugger = NodeEdgeDebugger()
    # 手动加载数据进行分析
    # ...
    ```
    
    输出文件说明
    --------------------------------
    - batch_details.json: 每个batch的详细信息
    - statistics.json: 完整的统计指标（JSON格式）
    - report.txt: 可读的文本报告
    - uncovered_elements.json: 未被覆盖的节点和边列表
    """)
