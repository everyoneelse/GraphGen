"""
Node和Edge选取可视化工具

功能：
1. 可视化图结构和选取结果
2. 生成覆盖率热力图
3. 绘制频次分布图
4. 展示loss分布对比
"""

import json
import os
from typing import Dict, List, Tuple
import matplotlib
matplotlib.use('Agg')  # 使用非交互式后端
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
import numpy as np


class SelectionVisualizer:
    """选取结果可视化器"""
    
    def __init__(self, debug_output_dir: str = "./debug_output", 
                 viz_output_dir: str = "./viz_output"):
        self.debug_output_dir = debug_output_dir
        self.viz_output_dir = viz_output_dir
        os.makedirs(viz_output_dir, exist_ok=True)
        
        # 设置中文字体支持
        plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
        
        # 加载数据
        self.stats = None
        self.batch_details = None
        self.uncovered = None
        self._load_data()
    
    def _load_data(self):
        """加载调试数据"""
        stats_file = os.path.join(self.debug_output_dir, "statistics.json")
        batch_file = os.path.join(self.debug_output_dir, "batch_details.json")
        uncovered_file = os.path.join(self.debug_output_dir, "uncovered_elements.json")
        
        try:
            with open(stats_file, 'r', encoding='utf-8') as f:
                self.stats = json.load(f)
            print(f"✓ 加载统计数据: {stats_file}")
        except FileNotFoundError:
            print(f"⚠ 未找到统计数据文件: {stats_file}")
        
        try:
            with open(batch_file, 'r', encoding='utf-8') as f:
                self.batch_details = json.load(f)
            print(f"✓ 加载batch详情: {batch_file}")
        except FileNotFoundError:
            print(f"⚠ 未找到batch详情文件: {batch_file}")
        
        try:
            with open(uncovered_file, 'r', encoding='utf-8') as f:
                self.uncovered = json.load(f)
            print(f"✓ 加载未覆盖数据: {uncovered_file}")
        except FileNotFoundError:
            print(f"⚠ 未找到未覆盖数据文件: {uncovered_file}")
    
    def plot_coverage_comparison(self):
        """绘制覆盖率对比图"""
        if not self.stats:
            print("⚠ 缺少统计数据，跳过覆盖率对比图")
            return
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        categories = ['Nodes', 'Edges']
        coverage_rates = [
            self.stats['node_coverage']['coverage_rate'] * 100,
            self.stats['edge_coverage']['coverage_rate'] * 100
        ]
        
        bars = ax.bar(categories, coverage_rates, color=['#3498db', '#e74c3c'], alpha=0.7)
        
        # 添加数值标签
        for i, (bar, rate) in enumerate(zip(bars, coverage_rates)):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{rate:.1f}%',
                   ha='center', va='bottom', fontsize=12, fontweight='bold')
        
        ax.set_ylabel('Coverage Rate (%)', fontsize=12)
        ax.set_title('Node and Edge Coverage Rate', fontsize=14, fontweight='bold')
        ax.set_ylim(0, 110)
        ax.grid(axis='y', alpha=0.3, linestyle='--')
        
        # 添加参考线
        ax.axhline(y=50, color='orange', linestyle='--', alpha=0.5, label='50% threshold')
        ax.axhline(y=80, color='green', linestyle='--', alpha=0.5, label='80% threshold')
        ax.legend()
        
        plt.tight_layout()
        output_file = os.path.join(self.viz_output_dir, "coverage_comparison.png")
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"✓ 覆盖率对比图已保存: {output_file}")
    
    def plot_batch_size_distribution(self):
        """绘制batch大小分布"""
        if not self.batch_details:
            print("⚠ 缺少batch详情，跳过batch大小分布图")
            return
        
        node_counts = [b['node_count'] for b in self.batch_details]
        edge_counts = [b['edge_count'] for b in self.batch_details]
        
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        
        # 节点数分布
        axes[0].hist(node_counts, bins=30, color='#3498db', alpha=0.7, edgecolor='black')
        axes[0].axvline(np.mean(node_counts), color='red', linestyle='--', 
                       linewidth=2, label=f'Mean: {np.mean(node_counts):.1f}')
        axes[0].set_xlabel('Number of Nodes per Batch', fontsize=11)
        axes[0].set_ylabel('Frequency', fontsize=11)
        axes[0].set_title('Distribution of Nodes per Batch', fontsize=12, fontweight='bold')
        axes[0].legend()
        axes[0].grid(alpha=0.3)
        
        # 边数分布
        axes[1].hist(edge_counts, bins=30, color='#e74c3c', alpha=0.7, edgecolor='black')
        axes[1].axvline(np.mean(edge_counts), color='red', linestyle='--', 
                       linewidth=2, label=f'Mean: {np.mean(edge_counts):.1f}')
        axes[1].set_xlabel('Number of Edges per Batch', fontsize=11)
        axes[1].set_ylabel('Frequency', fontsize=11)
        axes[1].set_title('Distribution of Edges per Batch', fontsize=12, fontweight='bold')
        axes[1].legend()
        axes[1].grid(alpha=0.3)
        
        plt.tight_layout()
        output_file = os.path.join(self.viz_output_dir, "batch_size_distribution.png")
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"✓ Batch大小分布图已保存: {output_file}")
    
    def plot_frequency_distribution(self):
        """绘制频次分布"""
        if not self.stats:
            print("⚠ 缺少统计数据，跳过频次分布图")
            return
        
        fa = self.stats['frequency_analysis']
        
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        
        # 从top_10数据中提取
        node_top10 = fa['node_frequency']['top_10_most_frequent']
        edge_top10 = fa['edge_frequency']['top_10_most_frequent']
        
        # 节点频次（Top 10）
        if node_top10:
            node_ids = [str(item[0])[:20] for item in node_top10]  # 截断长ID
            node_freqs = [item[1] for item in node_top10]
            
            axes[0].barh(range(len(node_ids)), node_freqs, color='#3498db', alpha=0.7)
            axes[0].set_yticks(range(len(node_ids)))
            axes[0].set_yticklabels(node_ids, fontsize=9)
            axes[0].set_xlabel('Frequency', fontsize=11)
            axes[0].set_title('Top 10 Most Frequent Nodes', fontsize=12, fontweight='bold')
            axes[0].invert_yaxis()
            axes[0].grid(axis='x', alpha=0.3)
        
        # 边频次（Top 10）
        if edge_top10:
            edge_labels = [str(item[0])[:30] for item in edge_top10]  # 截断长标签
            edge_freqs = [item[1] for item in edge_top10]
            
            axes[1].barh(range(len(edge_labels)), edge_freqs, color='#e74c3c', alpha=0.7)
            axes[1].set_yticks(range(len(edge_labels)))
            axes[1].set_yticklabels(edge_labels, fontsize=9)
            axes[1].set_xlabel('Frequency', fontsize=11)
            axes[1].set_title('Top 10 Most Frequent Edges', fontsize=12, fontweight='bold')
            axes[1].invert_yaxis()
            axes[1].grid(axis='x', alpha=0.3)
        
        plt.tight_layout()
        output_file = os.path.join(self.viz_output_dir, "frequency_distribution.png")
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"✓ 频次分布图已保存: {output_file}")
    
    def plot_loss_distribution(self):
        """绘制loss分布对比"""
        if not self.stats or 'loss_analysis' not in self.stats:
            print("⚠ 缺少loss数据，跳过loss分布图")
            return
        
        la = self.stats['loss_analysis']
        
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        
        # 节点loss对比
        if 'nodes' in la:
            node_data = la['nodes']
            categories = ['Selected\nNodes', 'All\nNodes']
            values = [
                node_data.get('selected_avg_loss', 0),
                node_data.get('all_avg_loss', 0)
            ]
            
            bars = axes[0].bar(categories, values, color=['#3498db', '#95a5a6'], alpha=0.7)
            for bar, val in zip(bars, values):
                height = bar.get_height()
                axes[0].text(bar.get_x() + bar.get_width()/2., height,
                           f'{val:.4f}',
                           ha='center', va='bottom', fontsize=10)
            
            axes[0].set_ylabel('Average Loss', fontsize=11)
            axes[0].set_title('Node Loss Comparison', fontsize=12, fontweight='bold')
            axes[0].grid(axis='y', alpha=0.3)
        
        # 边loss对比
        if 'edges' in la:
            edge_data = la['edges']
            categories = ['Selected\nEdges', 'All\nEdges']
            values = [
                edge_data.get('selected_avg_loss', 0),
                edge_data.get('all_avg_loss', 0)
            ]
            
            bars = axes[1].bar(categories, values, color=['#e74c3c', '#95a5a6'], alpha=0.7)
            for bar, val in zip(bars, values):
                height = bar.get_height()
                axes[1].text(bar.get_x() + bar.get_width()/2., height,
                           f'{val:.4f}',
                           ha='center', va='bottom', fontsize=10)
            
            axes[1].set_ylabel('Average Loss', fontsize=11)
            axes[1].set_title('Edge Loss Comparison', fontsize=12, fontweight='bold')
            axes[1].grid(axis='y', alpha=0.3)
        
        plt.tight_layout()
        output_file = os.path.join(self.viz_output_dir, "loss_distribution.png")
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"✓ Loss分布对比图已保存: {output_file}")
    
    def plot_batch_progression(self):
        """绘制batch处理进度图（累积覆盖率）"""
        if not self.batch_details:
            print("⚠ 缺少batch详情，跳过进度图")
            return
        
        # 计算累积覆盖
        selected_nodes_cumulative = set()
        selected_edges_cumulative = set()
        node_coverage_over_time = []
        edge_coverage_over_time = []
        
        total_nodes = self.stats['node_coverage']['total'] if self.stats else 1
        total_edges = self.stats['edge_coverage']['total'] if self.stats else 1
        
        for batch in self.batch_details:
            selected_nodes_cumulative.update(batch['node_ids'])
            selected_edges_cumulative.update([tuple(e) if isinstance(e, list) else e 
                                             for e in batch['edge_pairs']])
            
            node_coverage_over_time.append(len(selected_nodes_cumulative) / total_nodes * 100)
            edge_coverage_over_time.append(len(selected_edges_cumulative) / total_edges * 100)
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        batch_indices = range(1, len(self.batch_details) + 1)
        ax.plot(batch_indices, node_coverage_over_time, 
               marker='o', label='Node Coverage', linewidth=2, markersize=3, color='#3498db')
        ax.plot(batch_indices, edge_coverage_over_time, 
               marker='s', label='Edge Coverage', linewidth=2, markersize=3, color='#e74c3c')
        
        ax.set_xlabel('Batch Number', fontsize=12)
        ax.set_ylabel('Cumulative Coverage Rate (%)', fontsize=12)
        ax.set_title('Coverage Rate Progression Over Batches', fontsize=14, fontweight='bold')
        ax.legend(fontsize=11)
        ax.grid(alpha=0.3)
        ax.set_ylim(0, 105)
        
        # 添加参考线
        ax.axhline(y=50, color='orange', linestyle='--', alpha=0.3)
        ax.axhline(y=80, color='green', linestyle='--', alpha=0.3)
        
        plt.tight_layout()
        output_file = os.path.join(self.viz_output_dir, "batch_progression.png")
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"✓ Batch进度图已保存: {output_file}")
    
    def plot_summary_dashboard(self):
        """生成综合仪表盘"""
        if not self.stats:
            print("⚠ 缺少统计数据，跳过综合仪表盘")
            return
        
        fig = plt.figure(figsize=(16, 10))
        gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
        
        # 1. 覆盖率仪表盘（左上）
        ax1 = fig.add_subplot(gs[0, 0])
        node_cov = self.stats['node_coverage']['coverage_rate'] * 100
        edge_cov = self.stats['edge_coverage']['coverage_rate'] * 100
        
        categories = ['Nodes', 'Edges']
        values = [node_cov, edge_cov]
        colors = ['#3498db', '#e74c3c']
        
        bars = ax1.barh(categories, values, color=colors, alpha=0.7)
        ax1.set_xlim(0, 100)
        ax1.set_xlabel('Coverage (%)')
        ax1.set_title('Coverage Rate', fontweight='bold')
        ax1.grid(axis='x', alpha=0.3)
        
        for bar, val in zip(bars, values):
            width = bar.get_width()
            ax1.text(width + 2, bar.get_y() + bar.get_height()/2,
                    f'{val:.1f}%', va='center', fontsize=10)
        
        # 2. Batch统计（右上）
        ax2 = fig.add_subplot(gs[0, 1:])
        bs = self.stats['batch_statistics']
        
        metrics = ['Total\nBatches', 'Avg Nodes\nper Batch', 'Avg Edges\nper Batch']
        metric_values = [
            bs['total_batches'],
            bs['nodes_per_batch']['avg'],
            bs['edges_per_batch']['avg']
        ]
        
        bars = ax2.bar(metrics, metric_values, color=['#9b59b6', '#3498db', '#e74c3c'], alpha=0.7)
        ax2.set_title('Batch Statistics', fontweight='bold')
        ax2.grid(axis='y', alpha=0.3)
        
        for bar, val in zip(bars, metric_values):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                    f'{val:.1f}', ha='center', va='bottom', fontsize=10)
        
        # 3. 频次分析（中间行）
        ax3 = fig.add_subplot(gs[1, :])
        fa = self.stats['frequency_analysis']
        
        freq_metrics = [
            'Node Freq\n(Min)', 'Node Freq\n(Max)', 'Node Freq\n(Avg)',
            'Edge Freq\n(Min)', 'Edge Freq\n(Max)', 'Edge Freq\n(Avg)'
        ]
        freq_values = [
            fa['node_frequency']['min'],
            fa['node_frequency']['max'],
            fa['node_frequency']['avg'],
            fa['edge_frequency']['min'],
            fa['edge_frequency']['max'],
            fa['edge_frequency']['avg'],
        ]
        freq_colors = ['#3498db'] * 3 + ['#e74c3c'] * 3
        
        bars = ax3.bar(freq_metrics, freq_values, color=freq_colors, alpha=0.7)
        ax3.set_title('Frequency Analysis', fontweight='bold')
        ax3.set_ylabel('Frequency')
        ax3.grid(axis='y', alpha=0.3)
        
        for bar, val in zip(bars, freq_values):
            height = bar.get_height()
            ax3.text(bar.get_x() + bar.get_width()/2., height,
                    f'{val:.1f}', ha='center', va='bottom', fontsize=9)
        
        # 4. Loss对比（如果有）
        if 'loss_analysis' in self.stats:
            ax4 = fig.add_subplot(gs[2, :])
            la = self.stats['loss_analysis']
            
            loss_labels = []
            loss_values = []
            loss_colors = []
            
            if 'nodes' in la:
                loss_labels.extend(['Selected\nNodes', 'All\nNodes'])
                loss_values.extend([
                    la['nodes'].get('selected_avg_loss', 0),
                    la['nodes'].get('all_avg_loss', 0)
                ])
                loss_colors.extend(['#3498db', '#95a5a6'])
            
            if 'edges' in la:
                loss_labels.extend(['Selected\nEdges', 'All\nEdges'])
                loss_values.extend([
                    la['edges'].get('selected_avg_loss', 0),
                    la['edges'].get('all_avg_loss', 0)
                ])
                loss_colors.extend(['#e74c3c', '#95a5a6'])
            
            bars = ax4.bar(loss_labels, loss_values, color=loss_colors, alpha=0.7)
            ax4.set_title('Loss Distribution', fontweight='bold')
            ax4.set_ylabel('Average Loss')
            ax4.grid(axis='y', alpha=0.3)
            
            for bar, val in zip(bars, loss_values):
                height = bar.get_height()
                ax4.text(bar.get_x() + bar.get_width()/2., height,
                        f'{val:.4f}', ha='center', va='bottom', fontsize=9)
        
        plt.suptitle('Node/Edge Selection Analysis Dashboard', 
                    fontsize=16, fontweight='bold', y=0.98)
        
        output_file = os.path.join(self.viz_output_dir, "summary_dashboard.png")
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"✓ 综合仪表盘已保存: {output_file}")
    
    def generate_all_visualizations(self):
        """生成所有可视化图表"""
        print(f"\n{'='*80}")
        print(f"开始生成可视化图表")
        print(f"{'='*80}\n")
        
        self.plot_coverage_comparison()
        self.plot_batch_size_distribution()
        self.plot_frequency_distribution()
        self.plot_loss_distribution()
        self.plot_batch_progression()
        self.plot_summary_dashboard()
        
        print(f"\n{'='*80}")
        print(f"✅ 所有可视化图表已生成")
        print(f"📁 输出目录: {self.viz_output_dir}")
        print(f"{'='*80}")
        
        # 列出生成的文件
        viz_files = [f for f in os.listdir(self.viz_output_dir) if f.endswith('.png')]
        print(f"\n生成的图表文件:")
        for f in sorted(viz_files):
            print(f"  - {f}")


# 使用示例
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Node/Edge选取可视化工具")
    parser.add_argument(
        "--debug_dir",
        type=str,
        default="./debug_output",
        help="调试数据目录"
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="./viz_output",
        help="可视化输出目录"
    )
    
    args = parser.parse_args()
    
    visualizer = SelectionVisualizer(
        debug_output_dir=args.debug_dir,
        viz_output_dir=args.output_dir
    )
    
    visualizer.generate_all_visualizations()
