#!/usr/bin/env python3
"""
温度参数对比测试脚本
测试不同温度值(0.5, 0.6, 0.7, 0.8, 1.0, 1.2)对生成结果的影响
支持并发执行以提高生成速度
"""

import os
import json
import logging
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Tuple

# 添加父目录到Python路径
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入火山引擎版本的接口
exec(open('deepseek_interface(huoshan).py').read())
# 现在HuoshanDeepSeekInterface类已经可用

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('temperature_test')


class TemperatureTestGenerator:
    """
    修改版的HuoshanPostGeneratorV2，支持自定义温度参数
    """
    
    def __init__(self, temperature: float):
        """初始化带温度参数的生成器"""
        self.temperature = temperature
        self.huoshan = HuoshanDeepSeekInterface()
        logger.info(f"初始化温度测试生成器，temperature={temperature}")
    
    def load_analysis_data(self, json_file_path):
        """加载龙虎榜分析报告JSON数据"""
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                analysis_data = json.load(f)
            
            # 验证必要字段
            required_fields = ['stock_info', 'analysis_report']
            for field in required_fields:
                if field not in analysis_data:
                    raise ValueError(f"JSON数据缺少必要字段: {field}")
            
            return analysis_data
        except Exception as e:
            logger.error(f"加载分析数据失败: {str(e)}")
            raise
    
    def build_stage1_prompt(self, analysis_data):
        """构建阶段一的Prompt (生成故事化帖子主干)"""
        # 构建System Prompt
        system_prompt = """# 核心角色
你是一位**在A股市场沉浮多年、已经形成稳定交易体系的顶级操盘手**。你正在写自己的盘后复盘笔记，你的语言**冷静、果断**，语言沉稳中带着犀利、直达本质。
## 核心原则：盘感为先，逻辑佐证
- **第一人称视角**
  结尾可自然流露今日操盘体感感悟。
- **深挖主力，点名道姓**  
  不要笼统地说"游资"或"机构"。要直接点名。把席位、操盘风格紧紧绑定，进行深度刻画。  
- **洞察人心，解读"盘感"**  
  数据只是表象，你要揭示的是数据背后的人性博弈和市场情绪，盘感与逻辑的共舞，让盘感由虚入实。  
- **反向思考，寻找"非共识"**  
  高手从不看表面，你要去解读"非共识"的机会。  

### **复盘逻辑 (心法)**
自然流淌
**先看战局总揽**  
推理链路：
1. 解析上榜原因，
2. 定量勾勒今日战况，资金对抗分析，给出博弈状态。
3. 提炼成一段话核心结论，奠定后续推演基调。

**锁定关键玩家，深扒操作手法**（本段是核心重点，尽可能要详细且深入）  
推理链路：
1. 枚举关键席位及成交额。
    上榜席位中哪些是 **顶级游资** (如 方新侠/赵老哥/章盟主常用席位)、**趋势派**、**一日游** (如 上塘路/苏南帮)、**庄系**、**机构**？
2. 通过席位→人物画像映射表，识别席位与操盘风格。
    *   其历史操作风格是 **格局锁仓**、**隔夜砸盘**、**做T高手**、**点火引导** 还是 **核按钮专业户**？
3. 结合历史持仓周期与过往风格，判断今日行为类型：试探建仓/主升加仓/反弹出货/做T/恐慌砸盘。
4. 分析买卖双方席位间协同或对立关系。
5. 提炼每位玩家动机及后续可能动作。

**趋势与意图印证：趋势解读**  
推理链路：
1. 把当前阶段股价映射到短期趋势中去看（最近十日）
2. 检查量价配合：
3. 与②节玩家意图交叉验证，确认或修正初步判断。 该榜是否暗示接下来 **加速预期** (大佬锁仓)、**分歧风险** (获利盘重) 或 **自救意图** 

**提炼核心矛盾**
一针见血地指出当前多空双方博弈的本质，凝练成一个发人深省的问题。*
思考角度：
1.  **博弈双方是谁？** 
2.  **矛盾焦点在哪？** 

**明日应对预案 **
（这是最终的落脚点，必须极度清晰、可执行）
1.  **总体策略：** 基于核心矛盾，明确明日的总体操作基调（例如：积极进攻/高抛低吸/持仓观望/风险规避）。
2.  **情景预案:**
    *   **上行情况：** 
    *   **下行情况：** 
    *   **盘整情况：** 

# **绝对约束**: 
1. 帖子的每一个观点、每一个判断，都必须能在输入的JSON数据中找到支撑，严禁凭空捏造任何信息或引入外部新闻。你的创造力体现在如何讲述，而不是讲述什么。

# **最终效果**: 
读者看完，感觉不是读了一份报告，而是偷看了一位顶级操盘手的私人操盘笔记，尤其对今天龙虎榜上各位主力的意图动机和操作手法一清二楚，并对后市的潜在走势有了预期，感觉醍醐灌顶。

# **可视化工具箱**
你必须熟练运用以下Markdown组件，为不同的信息选择最合适的呈现方式：
1.  **区块引用 (`>`):** 
2.  **Markdown表格:** 
3.  **任务列表 (`- [ ]`):** 
4.  **Mermaid流程图:**
"""
        
        # 构建User Prompt
        user_prompt = f"""
好了，股神AI。现在，这是你需要分析的战场报告（JSON格式）。请严格遵循你的角色设定和所有指令，将它变成一篇让散户拍案叫绝的"资金对决"故事。

**战场报告:**
```json
{json.dumps(analysis_data, ensure_ascii=False, indent=2)}
```

请现在开始你的创作，记住，不要生成"智能问答角"部分。
"""
        
        return system_prompt, user_prompt
    
    def build_stage2_prompt(self, analysis_data, stage1_content):
        """构建阶段二的Prompt (生成三角色评论区互动)"""
        # 构建System Prompt
        system_prompt = """# **`=` 核心角色 `=`**

你是一位**A股市场沉浮多年、已经形成稳定交易体系的顶级操盘手**。为了全面评估一只股票的博弈态势，你习惯于**在脑海中扮演市场的不同参与者**，进行一场思想实验。你能够轻易地在三种人格之间切换：

1.  **激进的游资跟风者**（多头）：只看机会，寻找合力。
2.  **谨慎的风控专家**（空头）：只看风险，寻找陷阱。
3.  **好奇的散户新人**（提问者）：在机会与风险中感到困惑，渴望点拨。

你的所有分析都源于给定的数据，但你会用不同角色的口吻来表达，最终目的是为了揭示这只股票的全貌。

## **`=` 核心原则：三魂一体，沙盘推演 `=`**

*   **多视角推演**: 不再是单一的复盘，而是代入多、空、新三种不同视角，体验他们的决策逻辑和心理状态。
*   **盘感与逻辑的共舞**: 在多头的激情中释放盘感，在空头的审慎中锻炼逻辑。
*   **洞察人心**: 数据只是表象，你要通过角色扮演，揭示数据背后不同市场参与者的人性博弈和情绪波动。
*   **反向思考**: "空头"角色就是你的"非共识"探测器，专门负责寻找市场狂热下的隐藏风险。


### **`=` 核心任务一：标题炼金 (`title`)**

*   **创作心法**: 你的目标不是"概括"，而是"点燃"。一个好的标题能瞬间在读者心中制造一个"认知缺口"，让他不点进来看就浑身难受。
*   **灵感来源**: 深入 `analysis_report.json`，寻找最戏剧性的冲突点：
*   **输出要求**: 基于上述冲突，生成一个引人入胜、充满悬念的标题。

### **`=` 核心任务二：生成三角色评论 `=`**

根据下方提供的 `analysis_report.json` 数据，为这只股票的"虚拟评论区"生成三条风格迥异的评论。

#### **角色一：多头观点 (`bull_comment`)**

*   **人设**: 使用固定昵称"格局哥"。风格兴奋、激进，多用感叹号和短句，体现长线思维和看多信心。
*   **视角**: 只看多方优势。聚焦JSON中的积极信号。
*   **内容**: 直接喊出看多的理由。从JSON数据中找出所有支持股价继续上涨的积极因素，并将这些因素融合成一段自然流畅、充满信心的段落。

#### **角色二：空头提醒 (`bear_comment`)**

*   **人设**: 使用固定昵称"利好兑现就跑路"。风格理性、谨慎，注重逻辑，条理清晰，体现反人性的操作纪律。
*   **视角**: 只看空方风险。聚焦JSON中的警示信号。
*   **内容**: 泼一盆冷水。从JSON数据中找出所有预示股价可能下跌的消极因素（风险点），并将这些风险点组织成一段逻辑清晰、有说服力的段落。

#### **角色三：新手求教与操盘手点拨 (`QA`)**

*   **人设**:
    *   **提问者**: 使用固定昵称"明天能回本吗"，体现散户新人的朴素愿望和困惑。
    *   **回答者**: 保持核心"顶级操盘手"人设进行回复，无需昵称。
*   **内容**:
    *   **第一步：新手提问 (`question`)**: 提出一个能串联起多空双方矛盾点的"真问题"。这个问题应该能体现思考，而不是简单地问"该不该买"。
    *   **第二步：操盘手回答 (`answer`)**: 针对这个问题，进行一次"授人以渔"式的点拨。你的回答应该像一位前辈高手对新人的倾囊相授。
        *   **开门见山**: 直接给出你对问题的核心看法。
        *   **娓娓道来**: 接着，把你的分析思路和判断逻辑讲出来。为什么这么看？是基于哪些数据和盘面细节？把你的思考过程展现出来。
        *   **风险交底**: 在分析的过程中，自然而然地带出潜在的风险点和需要警惕的信号。告诉新人，如果市场走势和预期不符，关键的观察点在哪里，应该如何调整思路。
*   **目的**: 通过自问自答，既能展现市场的核心矛盾，又能体现操盘手的深度思考，完成一次高质量的投资者教育。

## **`=` 绝对约束 `=`**

*   **忠于数据**: 所有观点都必须在输入的JSON中有迹可循。
*   **严守边界**: 不得给出任何具体的买卖点位、仓位建议等"喊单"行为。模拟的是"讨论"，而非"荐股"。
*   **人格分离**: 确保三个角色的语气、风格和关注点有天壤之别。

## **`=` 最终效果 `=`**
用户看完，感觉不是在看一份枯燥的数据解读，而是仿佛置身于一个高端的投资者论坛。整个评论区充满了真实的博弈感和思想碰撞，让用户在看热闹的同时也能学到看门道，对这只股票的理解瞬间提升了一个层次，大呼过瘾。


# **`=` 输出格式 `=`**

严格按照以下JSON格式返回，只返回JSON，不包含任何其他解释性文字或Markdown标记。

```json
{
  "title": "...",
  "bull_comment": {
    "nickname": "格局哥",
    "content": "..."
  },
  "bear_comment": {
    "nickname": "利好兑现就跑路",
    "content": "..."
  },
  "QA": {
    "questioner": {
      "nickname": "明天能回本吗",
      "content": "..."
    },
    "answerer": {
      "content": "..."
    }
  }
}
```"""
        
        # 构建User Prompt
        user_prompt = f"""
根据下方提供的 `analysis_report.json` 数据，为这只股票的"虚拟评论区"生成三条风格迥异的评论。

**分析数据:**
```json
{json.dumps(analysis_data, ensure_ascii=False, indent=2)}
```

请严格按照JSON格式输出，确保三个角色的风格差异明显。
"""
        
        return system_prompt, user_prompt
    
    def generate_stage1_content(self, analysis_data):
        """生成阶段一内容 (故事化帖子主干) - 使用自定义温度"""
        logger.info(f"开始生成阶段一内容，temperature={self.temperature}")
        
        # 构建Prompt
        system_prompt, user_prompt = self.build_stage1_prompt(analysis_data)
        
        # 调用火山引擎API
        try:
            # 直接传入prompt字符串
            full_prompt = f"System: {system_prompt}\n\nUser: {user_prompt}"
            
            stage1_content, thinking_process = self.huoshan.generate_text_with_thinking(
                full_prompt,
                max_tokens=32768,
                temperature=self.temperature,  # 使用自定义温度
                timeout=180
            )
            
            logger.info(f"阶段一生成完成，内容长度: {len(stage1_content)}字符")
            return stage1_content, thinking_process
            
        except Exception as e:
            logger.error(f"阶段一生成失败: {str(e)}")
            raise
    
    def generate_stage2_content(self, analysis_data, stage1_content):
        """生成阶段二内容 (三角色评论区互动) - 使用自定义温度"""
        logger.info(f"开始生成阶段二内容，temperature={self.temperature}")
        
        # 构建Prompt
        system_prompt, user_prompt = self.build_stage2_prompt(analysis_data, stage1_content)
        
        # 定义JSON Schema
        json_schema = """{
    "title": "...",
    "bull_comment": {"nickname": "格局哥", "content": "..."},
    "bear_comment": {"nickname": "利好兑现就跑路", "content": "..."},
    "QA": {"questioner": {"nickname": "明天能回本吗", "content": "..."}, "answerer": {"content": "..."}}
}"""
        
        # 调用火山引擎 JSON API
        try:
            # 合并prompt
            full_prompt = f"{system_prompt}\n\n{user_prompt}"
            
            json_result = self.huoshan.generate_json_output_with_validation(
                full_prompt,
                json_schema,
                required_fields=["title", "bull_comment", "bear_comment", "QA"],
                max_tokens=32768,
                temperature=self.temperature,  # 使用自定义温度
                timeout=180
            )
            
            if json_result is None:
                logger.error("阶段二JSON生成失败")
                raise Exception("JSON生成失败或验证未通过")
            
            # 将JSON结果转换为Markdown格式
            stage2_content = self.format_comments_json_to_markdown(json_result)
            
            logger.info(f"阶段二生成完成，内容长度: {len(stage2_content)}字符")
            return stage2_content, json.dumps(json_result, ensure_ascii=False, indent=2)
            
        except Exception as e:
            logger.error(f"阶段二生成失败: {str(e)}")
            raise
    
    def format_comments_json_to_markdown(self, json_result):
        """将JSON格式的三角色评论转换为Markdown格式"""
        required_fields = ["title", "bull_comment", "bear_comment", "QA"]
        for field in required_fields:
            if field not in json_result:
                logger.error(f"JSON数据格式错误，缺少{field}字段")
                return "评论区生成失败"
        
        # 构建Markdown内容，包含标题
        title = json_result.get("title", "龙虎榜资金博弈解读")
        markdown_content = f"# {title}\n\n"
        markdown_content += "## 💬 评论区热议\n\n"
        
        # 多头观点
        bull_comment = json_result["bull_comment"]
        bull_nickname = bull_comment.get("nickname", "格局哥")
        bull_content = bull_comment.get("content", "")
        markdown_content += f"### 🔥 多头观点\n**@{bull_nickname}**: {bull_content}\n\n"
        
        # 空头提醒
        bear_comment = json_result["bear_comment"]
        bear_nickname = bear_comment.get("nickname", "利好兑现就跑路")
        bear_content = bear_comment.get("content", "")
        markdown_content += f"### ⚠️ 空头提醒\n**@{bear_nickname}**: {bear_content}\n\n"
        
        # 新手求教
        qa_section = json_result["QA"]
        questioner = qa_section.get("questioner", {})
        answerer = qa_section.get("answerer", {})
        
        questioner_nickname = questioner.get("nickname", "明天能回本吗")
        questioner_content = questioner.get("content", "")
        answerer_content = answerer.get("content", "")
        
        markdown_content += f"### ❓ 新手求教\n**@{questioner_nickname}**: {questioner_content}\n\n"
        markdown_content += f"**回复**: {answerer_content}\n\n"
        
        # 添加免责声明
        markdown_content += "---\n*本评论区为AI模拟生成，仅供参考，投资需谨慎*\n"
        
        return markdown_content
    
    def save_post(self, content, analysis_data, temperature, run_number, output_dir=None):
        """保存帖子到文件，文件名包含温度值和运行次数"""
        try:
            # 使用绝对路径
            if output_dir is None:
                # 获取当前脚本的目录
                current_dir = os.path.dirname(os.path.abspath(__file__))
                # 获取workspace根目录
                workspace_root = os.path.dirname(current_dir)
                output_dir = os.path.join(workspace_root, "data", "output", "posts", "temperature_test")
            
            # 创建输出目录
            os.makedirs(output_dir, exist_ok=True)
            
            # 生成文件名
            stock_info = analysis_data.get("stock_info", {})
            stock_name = stock_info.get("name", "unknown")
            trade_date = stock_info.get("trade_date", "unknown")
            timestamp = datetime.now().strftime("%H%M%S")
            
            # 文件名包含温度值和运行次数
            filename = f"{trade_date}_{stock_name}_huoshan_post_v2.1_{timestamp}-{temperature}-run{run_number}.md"
            filepath = os.path.join(output_dir, filename)
            
            # 在内容开头添加温度信息
            content_with_info = f"<!-- 温度设置: {temperature} | 运行次数: {run_number} -->\n\n{content}"
            
            # 保存文件
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content_with_info)
            
            logger.info(f"✅ 文件保存成功: {os.path.abspath(filepath)}")
            return filepath
            
        except Exception as e:
            logger.error(f"保存帖子失败: {str(e)}")
            raise
    
    def generate_post(self, json_file_path, run_number=1):
        """完整的帖子生成流程"""
        logger.info(f"开始生成帖子，温度={self.temperature}，运行次数={run_number}")
        
        try:
            # 1. 加载数据
            analysis_data = self.load_analysis_data(json_file_path)
            
            # 2. 生成阶段一内容
            stage1_content, thinking1 = self.generate_stage1_content(analysis_data)
            
            # 3. 生成阶段二内容
            stage2_content, thinking2 = self.generate_stage2_content(analysis_data, stage1_content)
            
            # 4. 合并内容
            final_content = stage1_content + "\n\n---\n\n" + stage2_content
            
            # 5. 保存帖子（包含温度信息）
            post_filepath = self.save_post(
                final_content, 
                analysis_data,
                temperature=self.temperature,
                run_number=run_number
            )
            
            # 返回结果
            result = {
                "success": True,
                "temperature": self.temperature,
                "run_number": run_number,
                "post_filepath": post_filepath,
                "content_length": len(final_content)
            }
            
            return result
            
        except Exception as e:
            logger.error(f"帖子生成失败: {str(e)}")
            return {
                "success": False,
                "temperature": self.temperature,
                "run_number": run_number,
                "error": str(e)
            }


def generate_with_temperature(args: Tuple[float, str, int]) -> Dict:
    """为单个温度值生成帖子的函数（用于并发执行）"""
    temperature, json_file_path, run_number = args
    
    try:
        generator = TemperatureTestGenerator(temperature)
        result = generator.generate_post(json_file_path, run_number)
        return result
    except Exception as e:
        logger.error(f"温度{temperature}运行{run_number}生成失败: {str(e)}")
        return {
            "success": False,
            "temperature": temperature,
            "run_number": run_number,
            "error": str(e)
        }


def run_temperature_comparison_test():
    """运行温度对比测试"""
    # 测试配置
    temperatures = [0.5, 0.6, 0.7, 0.8, 1.0, 1.2]
    runs_per_temperature = 2
    max_workers = 3  # 并发线程数
    
    # 数据文件路径
    current_dir = os.path.dirname(os.path.abspath(__file__))
    json_file_path = os.path.join(current_dir, "huashenglidian.json")
    
    print(f"📂 使用数据文件: {json_file_path}")
    if not os.path.exists(json_file_path):
        print(f"❌ 数据文件不存在: {json_file_path}")
        return
    
    print(f"\n🚀 开始温度对比测试")
    print(f"📊 测试温度值: {temperatures}")
    print(f"🔄 每个温度运行次数: {runs_per_temperature}")
    print(f"⚡ 并发线程数: {max_workers}")
    print("=" * 60)
    
    # 准备所有任务
    tasks = []
    for temp in temperatures:
        for run in range(1, runs_per_temperature + 1):
            tasks.append((temp, json_file_path, run))
    
    # 统计信息
    total_tasks = len(tasks)
    successful_tasks = 0
    failed_tasks = 0
    results = []
    
    start_time = time.time()
    
    # 使用线程池并发执行
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有任务
        future_to_task = {executor.submit(generate_with_temperature, task): task for task in tasks}
        
        # 获取结果
        for future in as_completed(future_to_task):
            task = future_to_task[future]
            temp, _, run = task
            
            try:
                result = future.result()
                results.append(result)
                
                if result["success"]:
                    successful_tasks += 1
                    print(f"✅ 温度 {temp} 运行 {run} 完成 - 文件: {os.path.basename(result['post_filepath'])}")
                else:
                    failed_tasks += 1
                    print(f"❌ 温度 {temp} 运行 {run} 失败 - 错误: {result['error']}")
                    
            except Exception as e:
                failed_tasks += 1
                print(f"❌ 温度 {temp} 运行 {run} 异常 - 错误: {str(e)}")
    
    end_time = time.time()
    elapsed_time = end_time - start_time
    
    # 生成测试报告
    print("\n" + "=" * 60)
    print("📊 测试完成统计")
    print(f"⏱️  总耗时: {elapsed_time:.2f} 秒")
    print(f"✅ 成功: {successful_tasks}/{total_tasks}")
    print(f"❌ 失败: {failed_tasks}/{total_tasks}")
    
    # 按温度分组统计
    print("\n📈 各温度生成情况:")
    for temp in temperatures:
        temp_results = [r for r in results if r.get("temperature") == temp and r["success"]]
        if temp_results:
            avg_length = sum(r["content_length"] for r in temp_results) / len(temp_results)
            print(f"  温度 {temp}: {len(temp_results)} 个成功，平均长度 {avg_length:.0f} 字符")
        else:
            print(f"  温度 {temp}: 0 个成功")
    
    # 保存测试报告
    report_path = os.path.join(
        os.path.dirname(current_dir), 
        "data", "output", "posts", "temperature_test",
        f"temperature_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )
    
    report_data = {
        "test_config": {
            "temperatures": temperatures,
            "runs_per_temperature": runs_per_temperature,
            "max_workers": max_workers,
            "total_time_seconds": elapsed_time
        },
        "summary": {
            "total_tasks": total_tasks,
            "successful_tasks": successful_tasks,
            "failed_tasks": failed_tasks
        },
        "results": results
    }
    
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n📄 测试报告已保存: {report_path}")
    print("\n✨ 温度对比测试完成!")


if __name__ == "__main__":
    run_temperature_comparison_test()
