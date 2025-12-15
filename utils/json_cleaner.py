#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JSON清理工具
用于处理从数据库中提取的包含转义字符的JSON数据
"""

import json
import re
import sys
import argparse
from pathlib import Path


class JSONCleaner:
    """JSON数据清理器"""
    
    def __init__(self):
        self.cleaned_count = 0
        self.error_count = 0
    
    def extract_json_from_text(self, text):
        """
        从文本中提取JSON数据（处理包含Markdown或其他格式的文本）
        
        Args:
            text (str): 可能包含JSON的文本
            
        Returns:
            list: 提取到的JSON对象列表
        """
        json_objects = []
        
        # 方法1: 查找```json代码块
        import re
        json_blocks = re.findall(r'```json\s*(.*?)\s*```', text, re.DOTALL)
        for block in json_blocks:
            try:
                obj = json.loads(block.strip())
                json_objects.append(obj)
                self.cleaned_count += 1
            except json.JSONDecodeError:
                pass
        
        # 方法2: 查找直接的JSON对象（以{开始，以}结束）
        json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        matches = re.finditer(json_pattern, text, re.DOTALL)
        
        for match in matches:
            json_str = match.group()
            try:
                obj = json.loads(json_str)
                # 避免重复添加
                if obj not in json_objects:
                    json_objects.append(obj)
                    self.cleaned_count += 1
            except json.JSONDecodeError:
                pass
        
        # 方法3: 查找更复杂的嵌套JSON（允许更深层嵌套）
        def find_json_objects(text, start_pos=0):
            results = []
            pos = start_pos
            while pos < len(text):
                # 查找下一个'{'
                start = text.find('{', pos)
                if start == -1:
                    break
                
                # 找到匹配的'}'
                brace_count = 0
                end = start
                in_string = False
                escape_next = False
                
                for i in range(start, len(text)):
                    char = text[i]
                    
                    if escape_next:
                        escape_next = False
                        continue
                    
                    if char == '\\':
                        escape_next = True
                        continue
                    
                    if char == '"' and not escape_next:
                        in_string = not in_string
                        continue
                    
                    if not in_string:
                        if char == '{':
                            brace_count += 1
                        elif char == '}':
                            brace_count -= 1
                            if brace_count == 0:
                                end = i
                                break
                
                if brace_count == 0:
                    json_str = text[start:end + 1]
                    try:
                        obj = json.loads(json_str)
                        if obj not in results:
                            results.append(obj)
                    except json.JSONDecodeError:
                        pass
                    pos = end + 1
                else:
                    pos = start + 1
            
            return results
        
        complex_objects = find_json_objects(text)
        for obj in complex_objects:
            if obj not in json_objects:
                json_objects.append(obj)
                self.cleaned_count += 1
        
        return json_objects
    
    def clean_escaped_json(self, raw_data):
        """
        清理包含转义字符的JSON数据
        
        Args:
            raw_data (str): 原始的包含转义字符的JSON字符串
            
        Returns:
            dict or list: 解析后的JSON对象
        """
        try:
            # 移除首尾可能的额外引号
            if raw_data.startswith('"') and raw_data.endswith('"'):
                raw_data = raw_data[1:-1]
            
            # 处理双重转义的反斜杠
            raw_data = raw_data.replace('\\\\', '\\')
            
            # 处理转义的引号
            raw_data = raw_data.replace('\\"', '"')
            
            # 处理转义的换行符
            raw_data = raw_data.replace('\\n', '\n')
            raw_data = raw_data.replace('\\r', '\r')
            raw_data = raw_data.replace('\\t', '\t')
            
            # 首先尝试直接解析为JSON
            try:
                cleaned_json = json.loads(raw_data.strip())
                self.cleaned_count += 1
                return cleaned_json
            except json.JSONDecodeError:
                # 如果直接解析失败，尝试从文本中提取JSON
                extracted_objects = self.extract_json_from_text(raw_data)
                if extracted_objects:
                    return extracted_objects[0] if len(extracted_objects) == 1 else extracted_objects
                else:
                    print(f"JSON解析错误: 无法从文本中提取有效JSON")
                    self.error_count += 1
                    return None
            
        except Exception as e:
            print(f"处理错误: {e}")
            self.error_count += 1
            return None
    
    def clean_json_array(self, raw_array_str):
        """
        清理JSON数组字符串
        
        Args:
            raw_array_str (str): 包含转义字符的JSON数组字符串
            
        Returns:
            list: 解析后的JSON数组
        """
        # 特殊处理双层括号格式 {{[...]}}
        if raw_array_str.startswith('{{[') and raw_array_str.endswith(']}}'):
            # 移除外层双括号，保留内层数组
            inner_content = raw_array_str[2:-2]  # 去掉外层 {{ }}
            return self.clean_json_array(inner_content)
        
        # 特殊处理数组格式 ["\n{...}", "\n{...}"]
        elif raw_array_str.startswith('[[') and raw_array_str.endswith(']]'):
            # 移除外层方括号
            inner_content = raw_array_str[2:-2]
            
            # 分割各个JSON字符串
            json_strings = []
            current_str = ""
            in_quotes = False
            escape_next = False
            bracket_count = 0
            
            for char in inner_content:
                if escape_next:
                    current_str += char
                    escape_next = False
                    continue
                    
                if char == '\\':
                    escape_next = True
                    current_str += char
                    continue
                    
                if char == '"' and not escape_next:
                    in_quotes = not in_quotes
                    current_str += char
                    continue
                    
                if not in_quotes:
                    if char == '{':
                        bracket_count += 1
                    elif char == '}':
                        bracket_count -= 1
                    elif char == ',' and bracket_count == 0:
                        # 找到分隔符
                        json_strings.append(current_str.strip())
                        current_str = ""
                        continue
                
                current_str += char
            
            # 添加最后一个JSON字符串
            if current_str.strip():
                json_strings.append(current_str.strip())
            
            # 清理每个JSON字符串
            cleaned_objects = []
            for i, json_str in enumerate(json_strings):
                print(f"🔍 处理第{i+1}个字符串，长度: {len(json_str)} 字符")
                print(f"   前100字符: {json_str[:100]}...")
                
                cleaned_obj = self.clean_escaped_json(json_str)
                if cleaned_obj:
                    # 如果返回的是列表（多个JSON对象），展开添加
                    if isinstance(cleaned_obj, list):
                        print(f"   ✅ 从字符串{i+1}中提取了{len(cleaned_obj)}个JSON对象")
                        cleaned_objects.extend(cleaned_obj)
                    else:
                        print(f"   ✅ 从字符串{i+1}中提取了1个JSON对象")
                        cleaned_objects.append(cleaned_obj)
                else:
                    print(f"   ❌ 第{i+1}个字符串解析失败")
            
            return cleaned_objects
        
        # 处理标准数组格式 ["...", "..."]
        elif raw_array_str.startswith('[') and raw_array_str.endswith(']'):
            try:
                # 尝试直接解析
                array_data = json.loads(raw_array_str)
                if isinstance(array_data, list):
                    cleaned_objects = []
                    for item in array_data:
                        if isinstance(item, str):
                            # 如果是字符串，尝试解析为JSON
                            cleaned_obj = self.clean_escaped_json(item)
                            if cleaned_obj:
                                cleaned_objects.append(cleaned_obj)
                        else:
                            # 如果已经是对象，直接添加
                            cleaned_objects.append(item)
                            self.cleaned_count += 1
                    return cleaned_objects
                else:
                    return array_data
            except json.JSONDecodeError:
                # 如果直接解析失败，使用旧的方法
                pass
            
            # 分割各个JSON字符串的备用方法
            json_strings = []
            current_str = ""
            in_quotes = False
            escape_next = False
            bracket_count = 0
            
            # 移除首尾的方括号
            inner_content = raw_array_str[1:-1]
            
            for char in inner_content:
                if escape_next:
                    current_str += char
                    escape_next = False
                    continue
                    
                if char == '\\':
                    escape_next = True
                    current_str += char
                    continue
                    
                if char == '"' and not escape_next:
                    in_quotes = not in_quotes
                    current_str += char
                    continue
                    
                if not in_quotes:
                    if char == '{':
                        bracket_count += 1
                    elif char == '}':
                        bracket_count -= 1
                    elif char == ',' and bracket_count == 0:
                        # 找到分隔符
                        json_strings.append(current_str.strip())
                        current_str = ""
                        continue
                
                current_str += char
            
            # 添加最后一个JSON字符串
            if current_str.strip():
                json_strings.append(current_str.strip())
            
            # 清理每个JSON字符串
            cleaned_objects = []
            for i, json_str in enumerate(json_strings):
                print(f"🔍 处理备用方法第{i+1}个字符串，长度: {len(json_str)} 字符")
                
                cleaned_obj = self.clean_escaped_json(json_str)
                if cleaned_obj:
                    # 如果返回的是列表（多个JSON对象），展开添加
                    if isinstance(cleaned_obj, list):
                        print(f"   ✅ 从备用方法字符串{i+1}中提取了{len(cleaned_obj)}个JSON对象")
                        cleaned_objects.extend(cleaned_obj)
                    else:
                        print(f"   ✅ 从备用方法字符串{i+1}中提取了1个JSON对象")
                        cleaned_objects.append(cleaned_obj)
                else:
                    print(f"   ❌ 备用方法第{i+1}个字符串解析失败")
            
            return cleaned_objects
        else:
            # 直接处理为单个JSON对象
            return self.clean_escaped_json(raw_array_str)
    
    def process_file(self, input_file, output_file=None):
        """
        处理文件中的JSON数据
        
        Args:
            input_file (str): 输入文件路径
            output_file (str): 输出文件路径，如果为None则使用默认命名
        """
        input_path = Path(input_file)
        
        if not input_path.exists():
            print(f"错误: 输入文件 {input_file} 不存在")
            return False
        
        # 确定输出文件路径
        if output_file is None:
            output_path = input_path.parent / f"{input_path.stem}_cleaned{input_path.suffix}"
        else:
            output_path = Path(output_file)
        
        try:
            # 读取文件内容
            with open(input_path, 'r', encoding='utf-8') as f:
                raw_content = f.read().strip()
            
            print(f"正在处理文件: {input_file}")
            print(f"原始内容长度: {len(raw_content)} 字符")
            
            # 检测是否为JSON数组格式或特殊的双括号格式
            if raw_content.startswith('{{[') and raw_content.endswith(']}}'):
                print("🎯 检测到双括号格式 {{[...]}}")
                cleaned_data = self.clean_json_array(raw_content)
            elif raw_content.startswith('[') and raw_content.endswith(']'):
                print("🎯 检测到标准数组格式 [...]")
                cleaned_data = self.clean_json_array(raw_content)
            else:
                print("🎯 检测到单个JSON对象格式")
                cleaned_data = self.clean_escaped_json(raw_content)
            
            if cleaned_data is not None:
                # 写入清理后的JSON
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(cleaned_data, f, ensure_ascii=False, indent=2)
                
                print(f"✅ 处理完成!")
                print(f"📁 输出文件: {output_path}")
                print(f"📊 成功处理: {self.cleaned_count} 个JSON对象")
                
                if self.error_count > 0:
                    print(f"⚠️  错误数量: {self.error_count}")
                
                return True
            else:
                print("❌ 处理失败: 无法解析JSON数据")
                return False
                
        except Exception as e:
            print(f"❌ 文件处理错误: {e}")
            return False
    
    def process_text(self, raw_text):
        """
        直接处理文本中的JSON数据
        
        Args:
            raw_text (str): 包含转义字符的JSON文本
            
        Returns:
            str: 格式化后的JSON字符串
        """
        if raw_text.startswith('[') and raw_text.endswith(']'):
            cleaned_data = self.clean_json_array(raw_text)
        else:
            cleaned_data = self.clean_escaped_json(raw_text)
        
        if cleaned_data is not None:
            return json.dumps(cleaned_data, ensure_ascii=False, indent=2)
        else:
            return None


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="清理从数据库中提取的包含转义字符的JSON数据",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python json_cleaner.py input.txt                    # 处理文件，自动生成输出文件名
  python json_cleaner.py input.txt -o output.json     # 指定输出文件
  python json_cleaner.py -t '{"name": "test"}'        # 直接处理文本
        """
    )
    
    parser.add_argument('input_file', nargs='?', help='输入文件路径')
    parser.add_argument('-o', '--output', help='输出文件路径')
    parser.add_argument('-t', '--text', help='直接处理JSON文本')
    
    args = parser.parse_args()
    
    cleaner = JSONCleaner()
    
    if args.text:
        # 处理文本模式
        result = cleaner.process_text(args.text)
        if result:
            print("清理后的JSON:")
            print(result)
        else:
            print("❌ 处理失败")
            sys.exit(1)
    elif args.input_file:
        # 处理文件模式
        success = cleaner.process_file(args.input_file, args.output)
        if not success:
            sys.exit(1)
    else:
        parser.print_help()
        sys.exit(1)


def test_hsld_file():
    """测试处理HSLD.txt文件"""
    print("=" * 50)
    print("🧪 测试处理 HSLD.txt 文件")
    print("=" * 50)
    
    # HSLD.txt文件路径
    hsld_file = Path(__file__).parent.parent / "HSLD.txt"
    
    if not hsld_file.exists():
        print(f"❌ 错误: 文件 {hsld_file} 不存在")
        return
    
    try:
        # 读取文件内容
        with open(hsld_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f"📁 文件路径: {hsld_file}")
        print(f"📊 文件大小: {len(content)} 字符")
        
        # 查找JSON数据部分（从```json开始到```结束）
        json_start = content.find('```json\n{{[')
        json_end = content.find('}}\n```', json_start)
        
        if json_start == -1 or json_end == -1:
            print("❌ 未找到JSON数据块")
            return
        
        # 提取JSON数据
        json_content = content[json_start + 8:json_end + 2]  # +8 跳过 '```json\n', +2 包含 '}}'
        
        print(f"🔍 找到JSON数据块:")
        print(f"   起始位置: {json_start}")
        print(f"   结束位置: {json_end}")
        print(f"   JSON长度: {len(json_content)} 字符")
        print(f"   JSON前100字符: {json_content[:100]}...")
        
        # 创建清理器
        cleaner = JSONCleaner()
        
        # 处理JSON数据
        print("\n🧹 开始清理JSON数据...")
        cleaned_data = cleaner.clean_json_array(json_content)
        
        if cleaned_data is not None:
            print(f"✅ 清理成功!")
            print(f"📊 处理结果:")
            print(f"   - 清理的JSON对象数量: {cleaner.cleaned_count}")
            print(f"   - 错误数量: {cleaner.error_count}")
            print(f"   - 数据类型: {type(cleaned_data)}")
            
            if isinstance(cleaned_data, list):
                print(f"   - 数组长度: {len(cleaned_data)}")
                for i, item in enumerate(cleaned_data):
                    print(f"   - 对象{i+1}的键: {list(item.keys()) if isinstance(item, dict) else 'Not a dict'}")
            
            # 保存清理后的数据
            output_file = hsld_file.parent / "HSLD_cleaned.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(cleaned_data, f, ensure_ascii=False, indent=2)
            
            print(f"💾 清理后的数据已保存到: {output_file}")
            
            # 显示清理后数据的预览
            print(f"\n📄 清理后数据预览:")
            preview = json.dumps(cleaned_data, ensure_ascii=False, indent=2)
            if len(preview) > 500:
                print(preview[:500] + "...")
            else:
                print(preview)
                
        else:
            print("❌ 清理失败")
            
    except Exception as e:
        print(f"❌ 处理错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import sys
    
    # 检查是否有 --test-hsld 参数
    if "--test-hsld" in sys.argv:
        test_hsld_file()
    else:
        main() 