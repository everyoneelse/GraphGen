#!/usr/bin/env python3
"""
演示关闭 quiz-samples 功能的脚本
"""

import argparse


def demo_disable_quiz():
    """演示如何关闭 quiz 功能"""
    
    print("🎯 关闭 quiz-samples/trainee 功能演示")
    print("=" * 50)
    
    parser = argparse.ArgumentParser(description='使用 youtu-graphrag JSON 知识图谱运行 GraphGen')
    
    # 输入文件参数
    parser.add_argument('--json', help='youtu-graphrag JSON 文件路径')
    parser.add_argument('--external-graph', help='已转换的 GraphML 文件路径')
    
    # 输出参数
    parser.add_argument('--working-dir', default='cache', help='工作目录 (默认: cache)')
    
    # 生成参数
    parser.add_argument('--mode', choices=['atomic', 'aggregated', 'multi_hop', 'cot'], 
                       default='atomic', help='生成模式 (默认: atomic)')
    parser.add_argument('--format', choices=['Alpaca', 'Sharegpt', 'ChatML'], 
                       default='Alpaca', help='数据格式 (默认: Alpaca)')
    parser.add_argument('--quiz-samples', type=int, default=5, help='测试样本数量 (默认: 5, 设为 0 禁用)')
    parser.add_argument('--disable-quiz', action='store_true', help='禁用问答测试和判断步骤')
    parser.add_argument('--max-depth', type=int, default=3, help='最大遍历深度 (默认: 3)')
    parser.add_argument('--max-extra-edges', type=int, default=5, help='最大额外边数 (默认: 5)')
    parser.add_argument('--enable-search', action='store_true', help='启用搜索增强')
    
    # 控制参数
    parser.add_argument('--skip-convert', action='store_true', help='跳过转换步骤')
    
    print("📋 新增的关闭 quiz 功能选项:")
    print("   --disable-quiz          完全禁用问答测试和判断")
    print("   --quiz-samples 0        设置测试样本数为 0（等同于禁用）")
    
    print("\n🎯 使用示例:")
    
    print("\n1️⃣ 方法1: 使用 --disable-quiz 参数（推荐）")
    print("python3 run_youtu_json_kg.py \\")
    print("    --json your_youtu_data.json \\")
    print("    --mode atomic \\")
    print("    --format Alpaca \\")
    print("    --disable-quiz")
    
    print("\n2️⃣ 方法2: 设置 --quiz-samples 0")
    print("python3 run_youtu_json_kg.py \\")
    print("    --json your_youtu_data.json \\")
    print("    --mode atomic \\")
    print("    --format Alpaca \\")
    print("    --quiz-samples 0")
    
    print("\n🔧 环境变量简化:")
    print("关闭 quiz 功能后，只需要设置 SYNTHESIZER 相关变量：")
    print()
    print("# .env 文件内容（简化版）")
    print("SYNTHESIZER_MODEL=gpt-4")
    print("SYNTHESIZER_API_KEY=your_api_key")
    print("SYNTHESIZER_BASE_URL=https://api.openai.com/v1")
    print("TOKENIZER_MODEL=cl100k_base")
    print()
    print("# 不再需要 TRAINEE 相关变量：")
    print("# TRAINEE_MODEL=...")
    print("# TRAINEE_API_KEY=...")
    print("# TRAINEE_BASE_URL=...")
    
    print("\n⚡ 优势:")
    print("   ✅ 更快的运行速度 - 跳过问答测试步骤")
    print("   ✅ 更少的 API 调用 - 只使用 SYNTHESIZER 模型")
    print("   ✅ 更低的成本 - 减少 LLM API 使用")
    print("   ✅ 简化配置 - 不需要配置 TRAINEE 环境变量")
    
    print("\n📊 运行流程变化:")
    print("   原流程: 转换 → 搜索 → 问答测试 → 生成数据")
    print("   新流程: 转换 → 搜索 → [跳过问答测试] → 生成数据")
    
    print("\n🎉 现在你可以:")
    print("   1. 只设置 SYNTHESIZER 相关的环境变量")
    print("   2. 使用 --disable-quiz 或 --quiz-samples 0 关闭测试")
    print("   3. 享受更快、更简单的问答数据生成过程！")


if __name__ == "__main__":
    demo_disable_quiz()