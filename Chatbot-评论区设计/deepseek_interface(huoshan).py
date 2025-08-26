"""
用于与火山引擎提供的DeepSeek API进行交互，使用OpenAI兼容格式调用
"""

import os
import logging
from dotenv import load_dotenv
from openai import OpenAI

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('huoshan_deepseek_interface')

# 加载环境变量
load_dotenv()
 
class HuoshanDeepSeekInterface:
    """
    火山引擎DeepSeek API接口类
    使用OpenAI兼容格式调用火山引擎提供的DeepSeek API生成内容
    """
    
    def __init__(self, api_key=None, model_version=None):
        """
        初始化火山引擎DeepSeek接口
        
        参数:
            api_key(str): 火山引擎API密钥，默认从环境变量获取
        """
        # 如果未提供API密钥，从环境变量中获取
        self.api_key = api_key or os.getenv("HUOSHAN_API_KEY", "43a030ac-8ea1-4fd9-b05a-49a11bfe4f72")
        if not self.api_key:
            raise ValueError("未提供API密钥，请通过参数传入或设置HUOSHAN_API_KEY环境变量")
        
        # 如果未提供模型版本，使用默认值deepseek-v3-1-250821
        self.model_version = model_version or os.getenv("HUOSHAN_MODEL_VERSION", "deepseek-v3-1-250821")
        logger.info(f"初始化火山引擎DeepSeek接口，使用模型: {self.model_version}")
        
        # 初始化OpenAI客户端，配置火山引擎API
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://ark.cn-beijing.volces.com/api/v3",
        )
        
        # 初始化多轮对话历史
        self.conversation_history = []
    
    def generate_text_with_thinking(self, prompt, max_tokens=32768, temperature=1.3, timeout=180):
        """
        
        参数:
            prompt(str): 提示词
            max_tokens(int): 最大生成token数量
            temperature(float): 生成文本的随机性，越高越随机
            timeout(int): API请求超时时间(秒)，默认180秒
            
        返回:
            tuple: (生成的文本, 思考过程)
        """
        try:
            # 记录提示词长度
            prompt_length = len(prompt)
            logger.info(f"发送流式请求到火山引擎API，启用推理过程，提示词长度: {prompt_length}字符")
            
            # 构建提示词，指示模型进行详细思考
            messages = [
                {"role": "system", "content": "请在回答前详细思考分析问题，提供你的推理过程。"},
                {"role": "user", "content": prompt}
            ]
            
            # 使用流式输出获取推理过程
            response_stream = self.client.chat.completions.create(
                model=self.model_version,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                timeout=timeout,
                stream=True
            )
            
            reasoning_content = ""  # 推理过程
            answer_content = ""     # 最终回答
            is_answering = False    # 标记是否已开始回答
            
            logger.info("开始处理流式响应...")
            
            for chunk in response_stream:
                # 跳过不包含choices的chunk
                if not hasattr(chunk, "choices") or not chunk.choices:
                    continue
                
                delta = chunk.choices[0].delta
                
                # 收集推理内容（DeepSeek-R1的推理过程）
                if hasattr(delta, "reasoning_content") and delta.reasoning_content is not None:
                    reasoning_content += delta.reasoning_content
                
                # 收集回答内容
                if hasattr(delta, "content") and delta.content is not None:
                    if not is_answering:
                        is_answering = True
                        logger.info("开始收集回答内容")
                    answer_content += delta.content
            
            logger.info(f"成功获取响应，生成文本长度: {len(answer_content)}，推理过程长度: {len(reasoning_content)}")
            
            if not reasoning_content:
                logger.warning("未获取到推理过程，当前模型可能不支持推理模式")
            
            return answer_content, reasoning_content
                
        except Exception as e:
            error_message = str(e)
            logger.error(f"API请求异常: {error_message}")
            
            if "timeout" in error_message.lower():
                return f"生成失败: API请求超时，请尝试减小输入数据量或增加超时设置", ""
            return f"生成失败: API请求异常 - {error_message}", ""
    
    def stream_output_with_thinking(self, prompt, callback_thinking=None, callback_answer=None, max_tokens=32768, temperature=0.7, timeout=180):
        """
        流式输出推理过程和回答，通过回调函数实时处理
        
        参数:
            prompt(str): 提示词
            callback_thinking(callable): 处理推理内容的回调函数
            callback_answer(callable): 处理回答内容的回调函数
            max_tokens(int): 最大生成token数量
            temperature(float): 生成文本的随机性
            timeout(int): 请求超时时间(秒)
            
        返回:
            tuple: (生成的文本, 推理过程)
        """
        try:
            logger.info(f"发送流式请求到火山引擎API，启用实时输出...")
            
            messages = [
                {"role": "system", "content": "请在回答前详细思考分析问题，提供你的推理过程。"},
                {"role": "user", "content": prompt}
            ]
            
            # 流式响应
            response_stream = self.client.chat.completions.create(
                model=self.model_version,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                timeout=timeout,
                stream=True
            )
            
            reasoning_content = ""  # 完整推理过程
            answer_content = ""     # 完整回答内容
            is_answering = False    # 标记是否进入回答阶段
            
            for chunk in response_stream:
                if not hasattr(chunk, "choices") or not chunk.choices:
                    continue
                    
                delta = chunk.choices[0].delta
                
                # 处理推理内容
                if hasattr(delta, "reasoning_content") and delta.reasoning_content is not None:
                    reasoning_content += delta.reasoning_content
                    # 如果有回调函数，调用它
                    if callback_thinking:
                        callback_thinking(delta.reasoning_content)
                
                # 处理回答内容
                if hasattr(delta, "content") and delta.content is not None:
                    if not is_answering:
                        is_answering = True
                        logger.info("开始进行回复")
                    answer_content += delta.content
                    # 如果有回调函数，调用它
                    if callback_answer:
                        callback_answer(delta.content)
            
            logger.info(f"流式输出完成，生成文本长度: {len(answer_content)}，推理过程长度: {len(reasoning_content)}")
            return answer_content, reasoning_content
            
        except Exception as e:
            error_message = str(e)
            logger.error(f"流式API请求异常: {error_message}")
            if callback_answer:
                callback_answer(f"\n生成失败: {error_message}")
            return f"生成失败: API请求异常 - {error_message}", ""

    # ====== 多轮对话功能 ======
    
    def start_conversation(self, system_message=None):
        """
        开始新的多轮对话会话
        
        参数:
            system_message(str): 可选的系统消息，用于设置助手的角色和行为
        """
        self.conversation_history = []
        if system_message:
            self.conversation_history.append({
                "role": "system",
                "content": system_message
            })
        logger.info(f"开始新的多轮对话会话，系统消息: {'已设置' if system_message else '未设置'}")
    
    def add_user_message(self, message):
        """
        添加用户消息到对话历史
        
        参数:
            message(str): 用户消息内容
        """
        if not isinstance(message, str) or not message.strip():
            raise ValueError("用户消息不能为空")
            
        self.conversation_history.append({
            "role": "user", 
            "content": message.strip()
        })
        logger.info(f"添加用户消息，当前对话轮数: {len([m for m in self.conversation_history if m['role'] == 'user'])}")
    
    def get_assistant_response_stream(self, callback_thinking=None, callback_answer=None, max_tokens=32768, temperature=0.7, timeout=180):
        """
        获取助手的流式响应并自动添加到对话历史
        
        参数:
            callback_thinking(callable): 处理推理内容的回调函数
            callback_answer(callable): 处理回答内容的回调函数
            max_tokens(int): 最大生成token数量
            temperature(float): 生成文本的随机性
            timeout(int): 请求超时时间(秒)
            
        返回:
            tuple: (生成的文本, 推理过程)
        """
        if not self.conversation_history:
            raise ValueError("对话历史为空，请先使用start_conversation()开始新对话或add_user_message()添加用户消息")
        
        # 检查最后一条消息是否为用户消息
        if self.conversation_history[-1]["role"] != "user":
            raise ValueError("最后一条消息必须是用户消息，请使用add_user_message()添加用户消息")
        
        try:
            logger.info(f"获取助手响应，对话历史长度: {len(self.conversation_history)}")
            
            # 使用完整的对话历史发送流式请求
            response_stream = self.client.chat.completions.create(
                model=self.model_version,
                messages=self.conversation_history,
                max_tokens=max_tokens,
                temperature=temperature,
                timeout=timeout,
                stream=True
            )
            
            reasoning_content = ""  # 完整推理过程
            answer_content = ""     # 完整回答内容
            is_answering = False    # 标记是否进入回答阶段
            
            for chunk in response_stream:
                if not hasattr(chunk, "choices") or not chunk.choices:
                    continue
                    
                delta = chunk.choices[0].delta
                
                # 处理推理内容
                if hasattr(delta, "reasoning_content") and delta.reasoning_content is not None:
                    reasoning_content += delta.reasoning_content
                    # 如果有回调函数，调用它
                    if callback_thinking:
                        callback_thinking(delta.reasoning_content)
                
                # 处理回答内容
                if hasattr(delta, "content") and delta.content is not None:
                    if not is_answering:
                        is_answering = True
                        logger.info("开始接收助手回复")
                    answer_content += delta.content
                    # 如果有回调函数，调用它
                    if callback_answer:
                        callback_answer(delta.content)
            
            # 将助手回复添加到对话历史
            if answer_content:
                self.conversation_history.append({
                    "role": "assistant",
                    "content": answer_content
                })
                logger.info(f"助手响应完成，回答长度: {len(answer_content)}，推理过程长度: {len(reasoning_content)}")
            else:
                logger.warning("未获取到助手回答内容")
            
            return answer_content, reasoning_content
            
        except Exception as e:
            error_message = str(e)
            logger.error(f"多轮对话API请求异常: {error_message}")
            if callback_answer:
                callback_answer(f"\n生成失败: {error_message}")
            return f"生成失败: API请求异常 - {error_message}", ""
    
    def clear_conversation(self):
        """
        清空对话历史
        """
        self.conversation_history = []
        logger.info("对话历史已清空")
    
    def get_conversation_history(self):
        """
        获取当前对话历史
        
        返回:
            list: 对话历史消息列表
        """
        return self.conversation_history.copy()
    
    def set_system_message(self, system_message):
        """
        设置或更新系统消息
        
        参数:
            system_message(str): 系统消息内容
        """
        if not isinstance(system_message, str) or not system_message.strip():
            raise ValueError("系统消息不能为空")
        
        # 如果已有系统消息，更新它
        if self.conversation_history and self.conversation_history[0]["role"] == "system":
            self.conversation_history[0]["content"] = system_message.strip()
            logger.info("系统消息已更新")
        else:
            # 在对话历史开头插入系统消息
            self.conversation_history.insert(0, {
                "role": "system",
                "content": system_message.strip()
            })
            logger.info("系统消息已添加")
    
    def get_conversation_summary(self):
        """
        获取对话摘要信息
        
        返回:
            dict: 包含对话统计信息的字典
        """
        user_messages = [m for m in self.conversation_history if m["role"] == "user"]
        assistant_messages = [m for m in self.conversation_history if m["role"] == "assistant"]
        system_messages = [m for m in self.conversation_history if m["role"] == "system"]
        
        total_chars = sum(len(m["content"]) for m in self.conversation_history)
        
        return {
            "total_messages": len(self.conversation_history),
            "user_messages": len(user_messages),
            "assistant_messages": len(assistant_messages),
            "system_messages": len(system_messages),
            "total_characters": total_chars,
            "conversation_rounds": len(user_messages)
        }



# ====== 简单测试示例 ======
if __name__ == "__main__":
    try:
        # 加载环境变量并初始化接口
        load_dotenv()
        huoshan_interface = HuoshanDeepSeekInterface()
        
        # 测试提示词
        test_prompt = "请简述龙虎榜席位分析的意义"
        
        # # 测试方法1: generate_text_with_thinking (不实时显示)
        # print("\n===== 测试 generate_text_with_thinking =====")
        # print("正在生成，请稍候...")
        # answer1, thinking1 = huoshan_interface.generate_text_with_thinking(test_prompt, temperature=0.7)
        # 
        # print("\n=== 推理过程 ===")
        # print(thinking1)
        # print("\n=== 最终回答 ===")
        # print(answer1)
        # print("\n=== 测试1完成 ===\n")

        # # 测试方法2: stream_output_with_thinking (实时显示)
        # print("\n===== 测试 stream_output_with_thinking =====")
        # print("正在测试火山引擎API，流式输出推理过程和回答...")
        # 
        # # 定义回调函数
        # def print_thinking(content):
        #     print(content, end="", flush=True)
        #     
        # def print_answer(content):
        #     print(content, end="", flush=True)
        # 
        # # 执行流式生成
        # print("\n=== 推理过程 ===\n")
        # answer2, thinking2 = huoshan_interface.stream_output_with_thinking(
        #     test_prompt, 
        #     callback_thinking=print_thinking,
        #     callback_answer=print_answer,
        #     temperature=0.7
        # )
        # print("\n\n=== 测试2完成 ===\n")

        # 测试方法1: 多轮对话功能
        print("\n===== 测试多轮对话功能 =====")
        print("开始测试多轮对话...")
        
        # 定义多轮对话的回调函数
        def multi_chat_thinking(content):
            print(content, end="", flush=True)
            
        def multi_chat_answer(content):
            print(content, end="", flush=True)
        
        # 开始新对话
        huoshan_interface.start_conversation("你是一个专业的金融分析师，擅长龙虎榜数据分析。")
        print("✓ 对话会话已启动")
        
        # 开始交互式多轮对话
        round_count = 1
        print("\n提示: 输入 'quit' 或 'exit' 退出对话")
        
        while True:
            print(f"\n--- 第{round_count}轮对话 ---")
            user_input = input("请输入您的问题: ").strip()
            
            # 检查退出命令
            if user_input.lower() in ['quit', 'exit', '退出', 'q']:
                print("对话结束")
                break
            
            # 检查空输入
            if not user_input:
                print("输入不能为空，请重新输入")
                continue
            
            # 添加用户消息
            huoshan_interface.add_user_message(user_input)
            print(f"用户: {user_input}")
            print("\n助手回复:")
            
            # 获取助手响应
            try:
                answer, thinking = huoshan_interface.get_assistant_response_stream(
                    callback_thinking=multi_chat_thinking,
                    callback_answer=multi_chat_answer,
                    temperature=0.7
                )
                print("\n")
                round_count += 1
            except Exception as e:
                print(f"\n生成响应时出错: {e}")
                break
        
        # 显示对话摘要
        summary = huoshan_interface.get_conversation_summary()
        print("\n=== 对话摘要 ===")
        print(f"总消息数: {summary['total_messages']}")
        print(f"对话轮数: {summary['conversation_rounds']}")
        print(f"用户消息: {summary['user_messages']}")
        print(f"助手消息: {summary['assistant_messages']}")
        print(f"系统消息: {summary['system_messages']}")
        print(f"总字符数: {summary['total_characters']}")
        
        # 显示完整对话历史
        print("\n=== 完整对话历史 ===")
        history = huoshan_interface.get_conversation_history()
        for i, msg in enumerate(history):
            role_name = {"system": "系统", "user": "用户", "assistant": "助手"}[msg["role"]]
            content_preview = msg["content"][:100] + "..." if len(msg["content"]) > 100 else msg["content"]
            print(f"{i+1}. [{role_name}] {content_preview}")
        
        print("\n=== 测试1完成 ===\n")
            
    except Exception as e:
        print(f"测试异常: {str(e)}")
        import traceback
        traceback.print_exc() 