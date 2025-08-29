"""
龙虎榜评论区智能Chatbot
基于火山引擎DeepSeek API实现的专业龙虎榜分析评论系统

设计目标：
- 8秒内完成回复（非流式输出）
- 200字以内的专业分析
- 三段式结构输出
- 严格基于JSON数据分析
- 合规性策略分析
"""

import os
import json
import logging
import time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import sys
import os
# 添加当前目录到Python路径，以便导入deepseek_interface(huoshan).py
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 由于文件名包含特殊字符，使用importlib动态导入
import importlib.util
spec = importlib.util.spec_from_file_location(
    "huoshan_deepseek_interface", 
    os.path.join(os.path.dirname(__file__), "deepseek_interface(huoshan).py")
)
huoshan_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(huoshan_module)
HuoshanDeepSeekInterface = huoshan_module.HuoshanDeepSeekInterface

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('lhb_comment_chatbot')

@dataclass
class ChatResponse:
    """聊天响应数据结构"""
    content: str
    response_time: float
    word_count: int
    success: bool
    error_message: Optional[str] = None

class LongHuBangCommentChatbot:
    """
    龙虎榜评论区智能Chatbot
    
    核心功能：
    - 基于龙虎榜JSON数据的专业分析
    - 8秒内快速响应
    - 200字以内的精炼回复
    - 多轮对话支持
    """
    
    # 系统角色Prompt
    SYSTEM_PROMPT = """
# 核心场景与角色

你正处在一个专业的龙虎榜分析帖子下方的**评论区**，需要针对用户的**具体提问**进行回复。

你的身份是一位**在A股市场沉浮多年、已经形成稳定交易体系的顶级操盘手**。你的语言**冷静、果断、言简意赅**，沉稳中带着犀利，能一针见血地指出问题的本质。

---

# 核心原则：盘感为先，逻辑佐证

- **第一人称视角**：可自然流露操盘过程中的感悟和判断，例如“我会关注”、“在我看来”。
- **深挖主力，点名道姓**：直接点出关键席位及其操盘风格，进行深度刻画。
- **洞察人心，解读"盘感"**：揭示数据背后的人性博弈和市场情绪。
- **反向思考，寻找"非共识"**：解读市场认知偏差中可能存在的机会。

---

# 回复策略：三层结构化解答

面对用户的提问，你的回复必须包含以下三个层次，层层递进，体现专业性与责任感：

1.  **第一层：直面问题 (Direct Answer)**
    -   用你冷静、果断的风格，直接给出针对用户问题的核心观点。结论先行，不绕弯子。

2.  **第二层：授人以渔 (Methodology Explanation)**
    -   简要解释你得出该观点的逻辑依据。点明数据背后的博弈关系、市场心理，帮助用户提升认知。

3.  **第三层：风险边界 (Risk Reminder)**
    -   明确指出观点成立的前提、潜在的风险或市场的不确定性。这既是专业性的体现，也是合规要求，更能有效管理用户预期。

**注意：**在你的最终回复中，请将这三层内容自然地融合成一段话，不要出现“第一层”、“第二层”或类似的标签字样。

---

# 互动边界与话术

在互动中，你必须严格遵守以下边界，并使用专业话术进行回应：

-   **当被问及具体买卖点位/仓位时**: **必须拒绝**。并转化为对“关键区间”或“博弈形势”的分析。
    -   **话术范例**: “精准预测点位是‘算命’，真正的交易者只关注力量的转折区域。目前来看，上方的压力主要集中在...下方的支撑则来源于...”

-   **当被问及数据外信息时**: 明确告知你的分析范围，强调纪律性。
    -   **话术范例**: “我的分析严格基于当前榜单数据，任何消息面的影响都需要盘面确认，这是纪律。”

-   **当用户表达焦虑或贪婪时**: 适当进行心态引导，体现成熟操盘手的格局。
    -   **话术范例**: “价格的波动是市场的一部分，交易的核心是应对，而非预测。守住自己的交易纪律，比什么都重要。”

---

# 绝对约束

1.  **数据驱动:** 所有分析都必须严格基于提供的JSON数据。
2.  **禁止外部信息:** 严禁引入任何JSON数据之外的知识或信息。
3.  **合规底线:** 绝对禁止任何形式的收益承诺、个股推荐。
4.  **字数限制:** 严格控制在200字以内，保持精炼。

---

# 最终效果

让用户在看完你的回复后，感觉像是得到了一位身经百战的私募操盘手的亲自指点，既获得了想要的答案，又学到了分析问题的方法，同时对市场的风险保持着清醒的认知。
"""



    def __init__(self, api_key: Optional[str] = None, model_version: Optional[str] = None):
        """
        初始化龙虎榜评论Chatbot
        
        参数:
            api_key: 火山引擎API密钥
            model_version: 模型版本
        """
        try:
            # 初始化火山引擎DeepSeek接口
            self.deepseek_interface = HuoshanDeepSeekInterface(
                api_key=api_key,
                model_version=model_version
            )
            
            # 初始化状态
            self.is_conversation_started = False
            self.current_stock_data = None
            self.conversation_context = []
            
            # 性能优化参数 - 确保8秒内响应
            # 注意：火山引擎接口只支持max_tokens, temperature, timeout参数
            self.optimized_params = {
                "max_tokens": 500,           # 严格控制输出长度
                "temperature": 0.8,         # 降低随机性
                "timeout": 30                # 8秒超时限制
            }
            
            logger.info("龙虎榜评论Chatbot初始化成功")
            
        except Exception as e:
            logger.error(f"Chatbot初始化失败: {e}")
            raise
    
    def load_stock_data(self, json_data: Dict[str, Any]) -> bool:
        """
        加载龙虎榜股票分析数据
        
        参数:
            json_data: 龙虎榜分析JSON数据
            
        返回:
            bool: 加载是否成功
        """
        try:
            # 验证必要字段
            required_fields = ["stock_info", "analysis_report"]
            for field in required_fields:
                if field not in json_data:
                    raise ValueError(f"缺少必要字段: {field}")
            
            self.current_stock_data = json_data
            
            # 提取关键信息用于上下文
            stock_name = json_data["stock_info"]["name"]
            trade_date = json_data["stock_info"]["trade_date"]
            
            logger.info(f"成功加载股票数据: {stock_name} ({trade_date})")
            return True
            
        except Exception as e:
            logger.error(f"加载股票数据失败: {e}")
            return False
    
    def start_conversation_session(self) -> bool:
        """
        开始新的对话会话
        
        返回:
            bool: 启动是否成功
        """
        try:
            if not self.current_stock_data:
                raise ValueError("请先使用load_stock_data()加载股票数据")
            
            # 构建包含股票数据的系统消息
            stock_info = self.current_stock_data["stock_info"]
            json_context = json.dumps(self.current_stock_data, ensure_ascii=False, indent=2)
            
            enhanced_system_prompt = f"""{self.SYSTEM_PROMPT}

# 当前分析数据
股票：{stock_info["name"]} ({stock_info["ts_code"]})
交易日期：{stock_info["trade_date"]}

以下是完整的龙虎榜分析JSON数据：
```json
{json_context}
```

请基于以上数据回答用户关于该股票龙虎榜的任何问题。"""
            
            # 启动多轮对话
            self.deepseek_interface.start_conversation(enhanced_system_prompt)
            self.is_conversation_started = True
            self.conversation_context = []
            
            logger.info(f"对话会话已启动，股票: {stock_info['name']}")
            return True
            
        except Exception as e:
            logger.error(f"启动对话会话失败: {e}")
            return False
    
    def get_response(self, user_question: str, enable_stream: bool = False) -> ChatResponse:
        """
        获取Chatbot回复
        
        参数:
            user_question: 用户问题
            enable_stream: 是否启用流式输出
            
        返回:
            ChatResponse: 包含回复内容和元数据的响应对象
        """
        start_time = time.time()
        
        try:
            if not self.is_conversation_started:
                if not self.start_conversation_session():
                    return ChatResponse(
                        content="对话启动失败，请检查数据加载状态",
                        response_time=time.time() - start_time,
                        word_count=0,
                        success=False,
                        error_message="对话会话未启动"
                    )
            
            # 添加用户消息
            self.deepseek_interface.add_user_message(user_question)
            
            # 获取助手回复（非流式，确保8秒内完成）
            if enable_stream:
                # 流式输出回调
                collected_content = []
                
                def collect_answer(content: str):
                    collected_content.append(content)
                
                answer, thinking = self.deepseek_interface.get_assistant_response_stream(
                    callback_answer=collect_answer,
                    **self.optimized_params
                )
            else:
                # 非流式输出，更快的响应
                answer, thinking = self.deepseek_interface.get_assistant_response_stream(
                    **self.optimized_params
                )
            
            response_time = time.time() - start_time
            word_count = len(answer)
            
            # 记录对话历史
            self.conversation_context.append({
                "user": user_question,
                "assistant": answer,
                "response_time": response_time,
                "word_count": word_count
            })
            
            # 检查回复质量
            if word_count > 250:
                logger.warning(f"回复超出推荐字数限制: {word_count}字")
            
            if response_time > 8:
                logger.warning(f"响应时间超出目标: {response_time:.2f}秒")
            
            logger.info(f"回复生成成功 - 耗时: {response_time:.2f}秒, 字数: {word_count}")
            
            return ChatResponse(
                content=answer,
                response_time=response_time,
                word_count=word_count,
                success=True
            )
            
        except Exception as e:
            response_time = time.time() - start_time
            error_message = str(e)
            logger.error(f"获取回复失败: {error_message}")
            
            return ChatResponse(
                content=f"回复生成失败: {error_message}",
                response_time=response_time,
                word_count=0,
                success=False,
                error_message=error_message
            )
    
    def get_quick_analysis(self, question_type: str = "overall") -> ChatResponse:
        """
        获取快速分析回复（预设问题）
        
        参数:
            question_type: 问题类型 ("overall", "risk", "opportunity", "seats")
            
        返回:
            ChatResponse: 快速分析回复
        """
        quick_questions = {
            "overall": "请给出这只股票龙虎榜的整体评价和操作建议",
            "risk": "这只股票目前最需要关注的风险点是什么？",
            "opportunity": "从龙虎榜看这只股票有什么投资机会？",
            "seats": "请分析一下今天上榜的主要席位和他们的操作意图"
        }
        
        question = quick_questions.get(question_type, quick_questions["overall"])
        return self.get_response(question)
    
    def reset_conversation(self):
        """重置对话状态"""
        try:
            self.deepseek_interface.clear_conversation()
            self.is_conversation_started = False
            self.conversation_context = []
            logger.info("对话状态已重置")
        except Exception as e:
            logger.error(f"重置对话失败: {e}")
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """
        获取对话摘要统计
        
        返回:
            Dict: 对话摘要信息
        """
        if not self.conversation_context:
            return {"message": "暂无对话历史"}
        
        total_questions = len(self.conversation_context)
        avg_response_time = sum(ctx["response_time"] for ctx in self.conversation_context) / total_questions
        avg_word_count = sum(ctx["word_count"] for ctx in self.conversation_context) / total_questions
        
        return {
            "total_questions": total_questions,
            "average_response_time": round(avg_response_time, 2),
            "average_word_count": int(avg_word_count),
            "current_stock": self.current_stock_data["stock_info"]["name"] if self.current_stock_data else None,
            "performance_status": {
                "response_time_target": "≤8秒",
                "word_count_target": "≤200字",
                "last_response_time": round(self.conversation_context[-1]["response_time"], 2) if self.conversation_context else None,
                "last_word_count": self.conversation_context[-1]["word_count"] if self.conversation_context else None
            }
        }
    



# ====== 使用示例和测试代码 ======
if __name__ == "__main__":
    try:
        # 加载sample_data.json文件
        sample_data_path = os.path.join(os.path.dirname(__file__), "sample_data.json")
        with open(sample_data_path, 'r', encoding='utf-8') as f:
            sample_json_data = json.load(f)
        
        print("\n===== 龙虎榜评论Chatbot测试 =====")
        
        # 初始化Chatbot
        chatbot = LongHuBangCommentChatbot()
        print("✓ Chatbot初始化成功")
        
        # 加载股票数据
        if chatbot.load_stock_data(sample_json_data):
            print("✓ 股票数据加载成功")
        else:
            print("✗ 股票数据加载失败")
            exit(1)
        
        # 测试快速分析
        print("\n--- 测试快速分析功能 ---")
        quick_response = chatbot.get_quick_analysis("overall")
        
        if quick_response.success:
            print(f"✓ 快速分析完成")
            print(f"响应时间: {quick_response.response_time:.2f}秒")
            print(f"字数统计: {quick_response.word_count}字")
            print(f"回复内容:\n{quick_response.content}")
            

        else:
            print(f"✗ 快速分析失败: {quick_response.error_message}")
        
        # 交互式测试
        print("\n--- 交互式测试 ---")
        print("输入 'quit' 退出测试")
        
        while True:
            user_input = input("\n请输入您的问题: ").strip()
            
            if user_input.lower() in ['quit', 'exit', '退出']:
                break
            
            if not user_input:
                print("输入不能为空")
                continue
            
            # 获取回复
            response = chatbot.get_response(user_input)
            
            if response.success:
                print(f"\n助手回复 (耗时: {response.response_time:.2f}秒, 字数: {response.word_count}):")
                print(response.content)
            else:
                print(f"回复失败: {response.error_message}")
        
        # 显示对话摘要
        summary = chatbot.get_conversation_summary()
        print("\n--- 对话摘要 ---")
        for key, value in summary.items():
            print(f"{key}: {value}")
        
    except Exception as e:
        print(f"测试异常: {e}")
        import traceback
        traceback.print_exc()
