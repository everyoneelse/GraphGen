#!/bin/bash

# GraphGen 运行示例脚本

echo "==================================="
echo "GraphGen 快速启动"
echo "==================================="

# 检查 .env 文件
if [ ! -f .env ]; then
    echo "❌ 错误：未找到 .env 文件"
    echo "请先创建 .env 文件并配置环境变量"
    echo ""
    echo "示例："
    echo "cp .env.example .env"
    echo "# 然后编辑 .env 文件，填入您的配置"
    exit 1
fi

# 检查必需的环境变量
source .env

if [ -z "$TOKENIZER_MODEL" ]; then
    echo "❌ 错误：TOKENIZER_MODEL 未设置"
    echo "请在 .env 文件中添加："
    echo "TOKENIZER_MODEL=cl100k_base"
    exit 1
fi

if [ -z "$SYNTHESIZER_MODEL" ] || [ -z "$SYNTHESIZER_API_KEY" ]; then
    echo "❌ 错误：SYNTHESIZER_MODEL 或 SYNTHESIZER_API_KEY 未设置"
    echo "请在 .env 文件中配置完整的API信息"
    exit 1
fi

echo "✅ 环境检查通过"
echo ""
echo "📝 当前配置："
echo "  Tokenizer: $TOKENIZER_MODEL"
echo "  Synthesizer: $SYNTHESIZER_MODEL"
echo "  Base URL: $SYNTHESIZER_BASE_URL"
echo ""

# 询问用户选择模式
echo "请选择生成模式："
echo "  1) atomic - 原子问答对（基础知识，不需要Trainee）"
echo "  2) multi_hop - 多跳问答对（推理能力，不需要Trainee）"
echo "  3) cot - 思维链问答对（逐步推理，不需要Trainee）"
echo "  4) aggregated - 聚合问答对（复杂知识，需要Trainee）"
echo ""
read -p "请输入选项 [1-4, 默认1]: " choice
choice=${choice:-1}

case $choice in
    1)
        echo "🚀 运行 atomic 模式（使用无Trainee配置）..."
        python3 -m graphgen.generate \
            --config_file graphgen/configs/atomic_config_no_trainee.yaml \
            --output_dir cache/
        ;;
    2)
        echo "🚀 运行 multi_hop 模式..."
        bash scripts/generate/generate_multi_hop.sh
        ;;
    3)
        echo "🚀 运行 cot 模式..."
        bash scripts/generate/generate_cot.sh
        ;;
    4)
        echo "⚠️ aggregated 模式需要配置 TRAINEE_MODEL"
        if [ -z "$TRAINEE_MODEL" ]; then
            echo "❌ 错误：TRAINEE_MODEL 未设置"
            echo "请在 .env 文件中配置 TRAINEE 相关变量"
            exit 1
        fi
        echo "🚀 运行 aggregated 模式..."
        bash scripts/generate/generate_aggregated.sh
        ;;
    *)
        echo "❌ 无效选项"
        exit 1
        ;;
esac

echo ""
echo "==================================="
echo "✅ 生成完成！"
echo "==================================="
echo ""
echo "📊 查看结果："
echo "ls -lt cache/data/graphgen/"
