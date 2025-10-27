#!/usr/bin/env python3
"""
测试 youtu-graphrag chunks 文件加载功能
"""

import sys
import os
from pathlib import Path

# 添加当前目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

from youtu_json_converter import YoutuJSONConverter


def test_chunks_loading(chunks_file: str):
    """测试 chunks 文件加载"""
    print("=" * 70)
    print("测试 Youtu-GraphRAG Chunks 文件加载")
    print("=" * 70)
    
    # 1. 创建转换器
    print("\n📝 步骤 1: 创建转换器")
    converter = YoutuJSONConverter()
    
    # 2. 加载 chunks 文件
    print(f"\n📄 步骤 2: 加载 chunks 文件: {chunks_file}")
    try:
        chunks_count = converter.load_youtu_chunks(chunks_file)
    except FileNotFoundError:
        print(f"❌ 文件不存在: {chunks_file}")
        return False
    except Exception as e:
        print(f"❌ 加载失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    if chunks_count == 0:
        print("⚠️  警告: 没有加载到任何 chunks")
        print("   可能原因:")
        print("   - 文件格式不正确")
        print("   - 文件为空")
        print("   - 解析错误")
        return False
    
    print(f"✅ 成功加载 {chunks_count} 个 chunks")
    
    # 3. 显示 chunks 统计
    print("\n📊 步骤 3: Chunks 统计")
    chunks_dict = converter.get_chunks_dict()
    
    # 统计字段
    has_title = sum(1 for c in chunks_dict.values() if c.get('title'))
    has_content = sum(1 for c in chunks_dict.values() if c.get('content'))
    has_source = sum(1 for c in chunks_dict.values() if c.get('source'))
    
    print(f"   总 chunks 数: {len(chunks_dict)}")
    print(f"   包含标题: {has_title} ({has_title/len(chunks_dict)*100:.1f}%)")
    print(f"   包含内容: {has_content} ({has_content/len(chunks_dict)*100:.1f}%)")
    print(f"   包含来源: {has_source} ({has_source/len(chunks_dict)*100:.1f}%)")
    
    # 统计内容长度
    content_lengths = [len(c.get('content', '')) for c in chunks_dict.values()]
    if content_lengths:
        avg_length = sum(content_lengths) / len(content_lengths)
        min_length = min(content_lengths)
        max_length = max(content_lengths)
        
        print(f"\n   内容长度统计:")
        print(f"     平均: {avg_length:.0f} 字符")
        print(f"     最短: {min_length} 字符")
        print(f"     最长: {max_length} 字符")
    
    # 4. 显示示例 chunks
    print("\n📝 步骤 4: 示例 Chunks（前3个）")
    for i, (chunk_id, chunk_data) in enumerate(list(chunks_dict.items())[:3]):
        print(f"\n   Chunk {i+1}: {chunk_id}")
        
        if 'title' in chunk_data and chunk_data['title']:
            print(f"   标题: {chunk_data['title'][:60]}...")
        
        if 'content' in chunk_data and chunk_data['content']:
            content_preview = chunk_data['content'][:150].replace('\n', ' ')
            print(f"   内容: {content_preview}...")
        
        if 'source' in chunk_data and chunk_data['source']:
            print(f"   来源: {chunk_data['source']}")
    
    # 5. 测试导出功能
    print("\n💾 步骤 5: 测试导出功能")
    test_output = "test_chunks_output.json"
    try:
        converter.export_chunks(test_output)
        print(f"✅ Chunks 已导出到: {test_output}")
        
        # 验证文件大小
        file_size = os.path.getsize(test_output)
        print(f"   文件大小: {file_size:,} 字节 ({file_size/1024:.1f} KB)")
        
        # 清理测试文件（可选）
        print(f"   保留测试文件供检查: {test_output}")
        
    except Exception as e:
        print(f"❌ 导出失败: {e}")
        return False
    
    # 6. 检查 chunk IDs 格式
    print("\n🔍 步骤 6: 检查 Chunk IDs 格式")
    chunk_ids = list(chunks_dict.keys())
    
    # 显示 ID 样例
    print(f"   示例 IDs: {', '.join(chunk_ids[:5])}")
    
    # 检查 ID 长度分布
    id_lengths = [len(cid) for cid in chunk_ids]
    from collections import Counter
    length_dist = Counter(id_lengths)
    
    print(f"\n   ID 长度分布:")
    for length, count in sorted(length_dist.items())[:5]:
        print(f"     长度 {length}: {count} 个")
    
    # 7. 总结
    print("\n" + "=" * 70)
    print("📋 测试总结")
    print("=" * 70)
    
    if chunks_count >= 10 and has_content == len(chunks_dict):
        print("✅ Chunks 文件质量优秀，可以用于添加文档上下文")
    elif chunks_count >= 5:
        print("⚠️  Chunks 文件质量良好，但数量较少")
    else:
        print("❌ Chunks 文件质量较差或数量太少")
    
    print(f"\n使用方法:")
    print(f"  python run_youtu_json_kg.py \\")
    print(f"    --json your_graph.json \\")
    print(f"    --chunks {chunks_file} \\")
    print(f"    --mode cot \\")
    print(f"    --add-context \\")
    print(f"    --disable-quiz")
    
    print(f"\n💡 提示:")
    print(f"  - 导出的 JSON 文件位于: {test_output}")
    print(f"  - 可以用 jq 或文本编辑器查看内容")
    print(f"  - 命令: cat {test_output} | jq '.' | less")
    
    return True


def create_sample_chunks_file():
    """创建示例 chunks 文件用于测试"""
    sample_file = "sample_chunks.txt"
    
    sample_content = """id: chunk_001	Chunk: {'title': '测试标题1', 'content': '这是第一个测试chunk的内容。它包含了一些示例文本。', 'source': 'test_source.md'}
id: chunk_002	Chunk: {'title': '测试标题2', 'content': '这是第二个测试chunk的内容。\\n它可以包含多行。\\n每行都是内容的一部分。', 'source': 'test_source.md'}
id: chunk_003	Chunk: {'title': '', 'content': '没有标题的chunk也是可以的。只要有内容就行。', 'source': 'another_source.txt'}
"""
    
    with open(sample_file, 'w', encoding='utf-8') as f:
        f.write(sample_content)
    
    print(f"✅ 已创建示例 chunks 文件: {sample_file}")
    print(f"   包含 3 个示例 chunks")
    print(f"\n可以使用以下命令测试:")
    print(f"  python test_chunks_loading.py --chunks {sample_file}")
    
    return sample_file


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='测试 youtu-graphrag chunks 文件加载')
    parser.add_argument('--chunks', help='youtu-graphrag chunks 文件路径')
    parser.add_argument('--create-sample', action='store_true', 
                       help='创建示例 chunks 文件并测试')
    
    args = parser.parse_args()
    
    if args.create_sample:
        sample_file = create_sample_chunks_file()
        print("\n" + "=" * 70)
        print("测试示例文件")
        print("=" * 70)
        success = test_chunks_loading(sample_file)
    elif args.chunks:
        success = test_chunks_loading(args.chunks)
    else:
        parser.print_help()
        print("\n示例用法:")
        print("  1. 测试真实文件:")
        print("     python test_chunks_loading.py --chunks path/to/text")
        print("\n  2. 创建并测试示例文件:")
        print("     python test_chunks_loading.py --create-sample")
        return 1
    
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
