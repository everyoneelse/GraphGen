#!/usr/bin/env python3
"""
从转换后的 youtu-graphrag 数据创建问答对
"""

import json
import argparse
import os


def create_qa_from_converted_data(json_file: str, output_format: str = "Alpaca"):
    """从转换后的数据创建问答对"""
    
    print(f"📖 读取转换后的数据: {json_file}")
    
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    qa_pairs = []
    
    print(f"🔄 开始生成问答对...")
    
    # 从节点创建属性问答
    for node in data['nodes']:
        entity_name = node['entity_name']
        description = node['description']
        entity_type = node['entity_type']
        
        # 1. 类型问答
        if output_format == "Alpaca":
            qa_pairs.append({
                "instruction": f"What type of entity is {entity_name}?",
                "input": "",
                "output": f"{entity_name} is a {entity_type}."
            })
        elif output_format == "Sharegpt":
            qa_pairs.append({
                "conversations": [
                    {"from": "human", "value": f"What type of entity is {entity_name}?"},
                    {"from": "gpt", "value": f"{entity_name} is a {entity_type}."}
                ]
            })
        elif output_format == "ChatML":
            qa_pairs.append({
                "messages": [
                    {"role": "user", "content": f"What type of entity is {entity_name}?"},
                    {"role": "assistant", "content": f"{entity_name} is a {entity_type}."}
                ]
            })
        
        # 2. 属性问答
        if ";" in description:
            attributes = description.split(";")[1:]  # 跳过 "Type: xxx"
            if attributes:
                attr_text = ', '.join(attr.strip() for attr in attributes)
                
                if output_format == "Alpaca":
                    qa_pairs.append({
                        "instruction": f"What are the attributes of {entity_name}?",
                        "input": "",
                        "output": f"{entity_name} has the following attributes: {attr_text}."
                    })
                elif output_format == "Sharegpt":
                    qa_pairs.append({
                        "conversations": [
                            {"from": "human", "value": f"What are the attributes of {entity_name}?"},
                            {"from": "gpt", "value": f"{entity_name} has the following attributes: {attr_text}."}
                        ]
                    })
                elif output_format == "ChatML":
                    qa_pairs.append({
                        "messages": [
                            {"role": "user", "content": f"What are the attributes of {entity_name}?"},
                            {"role": "assistant", "content": f"{entity_name} has the following attributes: {attr_text}."}
                        ]
                    })
    
    # 从边创建关系问答
    for edge in data['edges']:
        source = edge['source']
        target = edge['target']
        relation = edge['relation_type']
        
        if output_format == "Alpaca":
            qa_pairs.append({
                "instruction": f"What is the relationship between {source} and {target}?",
                "input": "",
                "output": f"{source} {relation} {target}."
            })
        elif output_format == "Sharegpt":
            qa_pairs.append({
                "conversations": [
                    {"from": "human", "value": f"What is the relationship between {source} and {target}?"},
                    {"from": "gpt", "value": f"{source} {relation} {target}."}
                ]
            })
        elif output_format == "ChatML":
            qa_pairs.append({
                "messages": [
                    {"role": "user", "content": f"What is the relationship between {source} and {target}?"},
                    {"role": "assistant", "content": f"{source} {relation} {target}."}
                ]
            })
    
    # 创建复合问答（多跳推理）
    if len(data['edges']) >= 2:
        # 寻找可以连接的关系链
        entity_connections = {}
        for edge in data['edges']:
            source = edge['source']
            target = edge['target']
            relation = edge['relation_type']
            
            if source not in entity_connections:
                entity_connections[source] = []
            entity_connections[source].append((target, relation))
        
        # 生成多跳问答
        for entity, connections in entity_connections.items():
            if len(connections) > 0:
                # 创建一个综合问题
                connected_entities = [conn[0] for conn in connections]
                relations_text = ', '.join([f"{conn[1]} {conn[0]}" for conn in connections])
                
                if output_format == "Alpaca":
                    qa_pairs.append({
                        "instruction": f"What entities are connected to {entity} and how?",
                        "input": "",
                        "output": f"{entity} is connected to the following entities: {relations_text}."
                    })
                elif output_format == "Sharegpt":
                    qa_pairs.append({
                        "conversations": [
                            {"from": "human", "value": f"What entities are connected to {entity} and how?"},
                            {"from": "gpt", "value": f"{entity} is connected to the following entities: {relations_text}."}
                        ]
                    })
                elif output_format == "ChatML":
                    qa_pairs.append({
                        "messages": [
                            {"role": "user", "content": f"What entities are connected to {entity} and how?"},
                            {"role": "assistant", "content": f"{entity} is connected to the following entities: {relations_text}."}
                        ]
                    })
    
    print(f"✅ 生成了 {len(qa_pairs)} 个问答对")
    return qa_pairs


def main():
    parser = argparse.ArgumentParser(description='从转换后的数据创建问答对')
    parser.add_argument('--input', required=True, help='转换后的 JSON 文件路径')
    parser.add_argument('--output', required=True, help='输出问答文件路径')
    parser.add_argument('--format', choices=['Alpaca', 'Sharegpt', 'ChatML'], 
                       default='Alpaca', help='输出格式 (默认: Alpaca)')
    
    args = parser.parse_args()
    
    try:
        # 生成问答对
        qa_pairs = create_qa_from_converted_data(args.input, args.format)
        
        # 确保输出目录存在
        os.makedirs(os.path.dirname(args.output), exist_ok=True)
        
        # 保存问答对
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(qa_pairs, f, ensure_ascii=False, indent=2)
        
        print(f"\n📁 问答对已保存到: {args.output}")
        print(f"📊 格式: {args.format}")
        print(f"📈 数量: {len(qa_pairs)}")
        
        # 显示前几个示例
        print(f"\n📝 示例问答对:")
        for i, qa in enumerate(qa_pairs[:3]):
            print(f"\n{i+1}. ", end="")
            if args.format == "Alpaca":
                print(f"Q: {qa['instruction']}")
                print(f"   A: {qa['output']}")
            elif args.format == "Sharegpt":
                conv = qa['conversations']
                print(f"Q: {conv[0]['value']}")
                print(f"   A: {conv[1]['value']}")
            elif args.format == "ChatML":
                msgs = qa['messages']
                print(f"Q: {msgs[0]['content']}")
                print(f"   A: {msgs[1]['content']}")
        
        if len(qa_pairs) > 3:
            print(f"\n... 还有 {len(qa_pairs) - 3} 个问答对")
        
        print(f"\n🎉 问答对生成完成！可以直接用于模型训练。")
        
    except Exception as e:
        print(f"❌ 生成失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())