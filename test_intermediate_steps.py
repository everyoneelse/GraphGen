#!/usr/bin/env python3
"""
测试中间步骤保存功能的脚本

使用方法:
python test_intermediate_steps.py <qa_json_path>

例如:
python test_intermediate_steps.py cache/data/graphgen/1234567890/qa.json
"""

import json
import sys
from pathlib import Path


def test_intermediate_steps(qa_json_path):
    """测试qa.json中是否包含中间步骤信息"""
    
    print(f"🔍 正在检查: {qa_json_path}\n")
    
    if not Path(qa_json_path).exists():
        print(f"❌ 文件不存在: {qa_json_path}")
        return False
    
    # 加载数据
    with open(qa_json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if not data:
        print("❌ 文件为空")
        return False
    
    print(f"✅ 成功加载 {len(data)} 条数据\n")
    
    # 统计各模式的数据
    mode_counts = {}
    has_intermediate_steps = 0
    
    for idx, item in enumerate(data):
        # 检查intermediate_steps字段
        if "intermediate_steps" in item:
            has_intermediate_steps += 1
            mode = item["intermediate_steps"].get("mode", "unknown")
            mode_counts[mode] = mode_counts.get(mode, 0) + 1
    
    print(f"📊 统计信息:")
    print(f"   - 总数据量: {len(data)}")
    print(f"   - 包含中间步骤的数据: {has_intermediate_steps} ({has_intermediate_steps/len(data)*100:.1f}%)")
    print(f"\n📝 各模式分布:")
    for mode, count in sorted(mode_counts.items()):
        print(f"   - {mode}: {count}")
    
    # 显示第一条数据的详细信息
    if data:
        print(f"\n📄 第一条数据示例:")
        first_item = data[0]
        
        # 显示基本信息
        if "instruction" in first_item:
            print(f"\n   问题: {first_item['instruction'][:100]}...")
            print(f"   答案: {first_item.get('output', 'N/A')[:100]}...")
        elif "conversations" in first_item:
            print(f"\n   问题: {first_item['conversations'][0]['value'][:100]}...")
            print(f"   答案: {first_item['conversations'][1]['value'][:100]}...")
        elif "messages" in first_item:
            print(f"\n   问题: {first_item['messages'][0]['content'][:100]}...")
            print(f"   答案: {first_item['messages'][1]['content'][:100]}...")
        
        # 显示中间步骤信息
        if "intermediate_steps" in first_item:
            print(f"\n   ✅ 包含中间步骤信息")
            steps = first_item["intermediate_steps"]
            mode = steps.get("mode", "unknown")
            print(f"   模式: {mode}")
            
            # 根据模式显示不同的字段
            if mode == "atomic":
                print(f"\n   Atomic模式字段:")
                print(f"     - input_description: {'✅' if 'input_description' in steps else '❌'}")
                print(f"     - qa_generation_prompt: {'✅' if 'qa_generation_prompt' in steps else '❌'}")
                print(f"     - raw_qa_response: {'✅' if 'raw_qa_response' in steps else '❌'}")
                
                if 'qa_generation_prompt' in steps:
                    print(f"\n   Prompt预览:")
                    print(f"     {steps['qa_generation_prompt'][:200]}...")
            
            elif mode == "cot":
                print(f"\n   CoT模式字段:")
                print(f"     - entities: {'✅' if 'entities' in steps else '❌'}")
                print(f"     - relationships: {'✅' if 'relationships' in steps else '❌'}")
                print(f"     - step1_template_design_prompt: {'✅' if 'step1_template_design_prompt' in steps else '❌'}")
                print(f"     - step1_template_design_response: {'✅' if 'step1_template_design_response' in steps else '❌'}")
                print(f"     - step2_answer_generation_prompt: {'✅' if 'step2_answer_generation_prompt' in steps else '❌'}")
                print(f"     - step2_final_answer: {'✅' if 'step2_final_answer' in steps else '❌'}")
                
                if 'reasoning_path' in first_item:
                    print(f"\n   推理路径: {first_item['reasoning_path'][:200]}...")
            
            elif mode in ["aggregated", "aggregated_multi"]:
                print(f"\n   Aggregated模式字段:")
                print(f"     - entities: {'✅' if 'entities' in steps else '❌'}")
                print(f"     - relationships: {'✅' if 'relationships' in steps else '❌'}")
                print(f"     - step1_rephrasing_prompt: {'✅' if 'step1_rephrasing_prompt' in steps else '❌'}")
                print(f"     - step1_rephrased_context: {'✅' if 'step1_rephrased_context' in steps else '❌'}")
                
                if mode == "aggregated":
                    print(f"     - step2_question_generation_prompt: {'✅' if 'step2_question_generation_prompt' in steps else '❌'}")
                else:
                    print(f"     - step2_multi_qa_generation_prompt: {'✅' if 'step2_multi_qa_generation_prompt' in steps else '❌'}")
            
            elif mode == "multi_hop":
                print(f"\n   Multi-hop模式字段:")
                print(f"     - entities: {'✅' if 'entities' in steps else '❌'}")
                print(f"     - relationships: {'✅' if 'relationships' in steps else '❌'}")
                print(f"     - multi_hop_generation_prompt: {'✅' if 'multi_hop_generation_prompt' in steps else '❌'}")
                print(f"     - raw_response: {'✅' if 'raw_response' in steps else '❌'}")
        else:
            print(f"\n   ❌ 不包含中间步骤信息")
    
    print("\n" + "="*60)
    
    if has_intermediate_steps == len(data):
        print("✅ 测试通过：所有数据都包含中间步骤信息")
        return True
    elif has_intermediate_steps > 0:
        print(f"⚠️  部分通过：只有 {has_intermediate_steps}/{len(data)} 条数据包含中间步骤")
        return False
    else:
        print("❌ 测试失败：没有数据包含中间步骤信息")
        return False


def analyze_prompts(qa_json_path):
    """分析所有prompt的统计信息"""
    
    print(f"\n📈 分析Prompt统计信息...\n")
    
    with open(qa_json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    prompt_lengths = []
    prompt_types = {}
    
    for item in data:
        if "intermediate_steps" not in item:
            continue
        
        steps = item["intermediate_steps"]
        mode = steps.get("mode", "unknown")
        
        # 收集prompt
        if mode == "atomic":
            if "qa_generation_prompt" in steps:
                prompt = steps["qa_generation_prompt"]
                prompt_lengths.append(len(prompt))
                prompt_types[f"{mode}_qa"] = prompt_types.get(f"{mode}_qa", 0) + 1
        
        elif mode == "cot":
            if "step1_template_design_prompt" in steps:
                prompt = steps["step1_template_design_prompt"]
                prompt_lengths.append(len(prompt))
                prompt_types[f"{mode}_step1"] = prompt_types.get(f"{mode}_step1", 0) + 1
            
            if "step2_answer_generation_prompt" in steps:
                prompt = steps["step2_answer_generation_prompt"]
                prompt_lengths.append(len(prompt))
                prompt_types[f"{mode}_step2"] = prompt_types.get(f"{mode}_step2", 0) + 1
        
        elif mode in ["aggregated", "aggregated_multi"]:
            if "step1_rephrasing_prompt" in steps:
                prompt = steps["step1_rephrasing_prompt"]
                prompt_lengths.append(len(prompt))
                prompt_types[f"{mode}_step1"] = prompt_types.get(f"{mode}_step1", 0) + 1
            
            if "step2_question_generation_prompt" in steps:
                prompt = steps["step2_question_generation_prompt"]
                prompt_lengths.append(len(prompt))
                prompt_types[f"{mode}_step2_single"] = prompt_types.get(f"{mode}_step2_single", 0) + 1
            
            if "step2_multi_qa_generation_prompt" in steps:
                prompt = steps["step2_multi_qa_generation_prompt"]
                prompt_lengths.append(len(prompt))
                prompt_types[f"{mode}_step2_multi"] = prompt_types.get(f"{mode}_step2_multi", 0) + 1
        
        elif mode == "multi_hop":
            if "multi_hop_generation_prompt" in steps:
                prompt = steps["multi_hop_generation_prompt"]
                prompt_lengths.append(len(prompt))
                prompt_types[f"{mode}"] = prompt_types.get(f"{mode}", 0) + 1
    
    if prompt_lengths:
        print(f"Prompt长度统计:")
        print(f"  - 总数量: {len(prompt_lengths)}")
        print(f"  - 平均长度: {sum(prompt_lengths)/len(prompt_lengths):.0f} 字符")
        print(f"  - 最小长度: {min(prompt_lengths)} 字符")
        print(f"  - 最大长度: {max(prompt_lengths)} 字符")
        
        print(f"\nPrompt类型分布:")
        for ptype, count in sorted(prompt_types.items()):
            print(f"  - {ptype}: {count}")
    else:
        print("❌ 没有找到任何prompt")


def main():
    if len(sys.argv) < 2:
        print("使用方法: python test_intermediate_steps.py <qa_json_path>")
        print("\n示例:")
        print("  python test_intermediate_steps.py cache/data/graphgen/1234567890/qa.json")
        sys.exit(1)
    
    qa_json_path = sys.argv[1]
    
    # 运行测试
    success = test_intermediate_steps(qa_json_path)
    
    # 如果测试通过，进行详细分析
    if success:
        analyze_prompts(qa_json_path)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
