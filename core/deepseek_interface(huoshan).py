"""
用于与火山引擎提供的DeepSeek API进行交互，使用OpenAI兼容格式调用
"""

import os
import json
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
            model_version(str): 模型版本，默认使用deepseek-r1-250528
        """
        # 如果未提供API密钥，从环境变量中获取
        self.api_key = api_key or os.getenv("HUOSHAN_API_KEY", "43a030ac-8ea1-4fd9-b05a-49a11bfe4f72")
        if not self.api_key:
            raise ValueError("未提供API密钥，请通过参数传入或设置HUOSHAN_API_KEY环境变量")
        
        # 如果未提供模型版本，使用默认值deepseek-r1-250528
        self.model_version = model_version or os.getenv("HUOSHAN_MODEL_VERSION", "deepseek-r1-250528")
        logger.info(f"初始化火山引擎DeepSeek接口，使用模型: {self.model_version}")
        
        # 初始化OpenAI客户端，配置火山引擎API
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://ark.cn-beijing.volces.com/api/v3",
        )
    
    def generate_text_with_thinking(self, prompt, max_tokens=65536, temperature=1.3, timeout=180):
        """
        使用火山引擎DeepSeek生成文本并展示思考过程
        注意：对于deepseek-r1模型，推理过程在流式输出中体现
        
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
    
    def generate_text_simple(self, prompt, max_tokens=65536, temperature=0.7, timeout=180):
        """
        简单的非流式文本生成（不获取推理过程）
        
        参数:
            prompt(str): 提示词
            max_tokens(int): 最大生成token数量
            temperature(float): 生成文本的随机性
            timeout(int): 请求超时时间(秒)
            
        返回:
            str: 生成的文本
        """
        try:
            logger.info(f"发送非流式请求到火山引擎API")
            
            messages = [
                {"role": "system", "content": "你是一个专业的金融分析助手。"},
                {"role": "user", "content": prompt}
            ]
            
            response = self.client.chat.completions.create(
                model=self.model_version,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                timeout=timeout,
                stream=False
            )
            
            content = response.choices[0].message.content
            logger.info(f"成功获取响应，生成文本长度: {len(content)}")
            return content
                
        except Exception as e:
            error_message = str(e)
            logger.error(f"API请求异常: {error_message}")
            return f"生成失败: API请求异常 - {error_message}"
    
    def stream_output_with_thinking(self, prompt, callback_thinking=None, callback_answer=None, max_tokens=65536, temperature=0.7, timeout=180):
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

    def generate_json_output(self, prompt, json_schema_example, max_tokens=65536, temperature=1.0, timeout=180, max_retries=3):
        """
        使用火山引擎DeepSeek生成结构化JSON输出
        
        参数:
            prompt(str): 用户提示词
            json_schema_example(str): JSON格式示例，用于指导模型输出格式
            max_tokens(int): 最大生成token数量
            temperature(float): 生成文本的随机性
            timeout(int): 请求超时时间(秒)
            max_retries(int): 最大重试次数，用于处理空content问题
            
        返回:
            dict: 解析后的JSON对象，如果失败返回None
        """
        # 构建包含JSON格式要求的system prompt
        system_prompt = f"""
请根据用户的要求，严格按照JSON格式输出结果。你必须输出有效的JSON格式。

JSON格式示例：
{json_schema_example}

请确保：
1. 输出的内容必须是有效的JSON格式
2. 所有字符串值都用双引号包围
3. 不要添加任何JSON之外的说明文字
4. 严格按照示例的结构组织数据
"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
        
        # 重试机制，处理可能的空content问题
        for attempt in range(max_retries):
            try:
                logger.info(f"发送JSON格式请求到火山引擎API (尝试 {attempt + 1}/{max_retries})")
                
                # 注意：火山引擎API可能不支持response_format参数，需要通过prompt引导
                response = self.client.chat.completions.create(
                    model=self.model_version,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    timeout=timeout,
                    stream=False
                )
                
                content = response.choices[0].message.content
                
                # 处理空content问题
                if not content or content.strip() == "":
                    logger.warning(f"API返回空content (尝试 {attempt + 1}/{max_retries})")
                    if attempt < max_retries - 1:
                        continue
                    else:
                        logger.error("多次尝试后仍返回空content")
                        return None
                
                # 尝试解析JSON
                try:
                    # 清理可能的markdown代码块标记
                    if content.startswith("```json"):
                        content = content[7:]
                    if content.endswith("```"):
                        content = content[:-3]
                    content = content.strip()
                    
                    json_result = json.loads(content)
                    logger.info(f"成功获取JSON响应，解析成功")
                    return json_result
                except json.JSONDecodeError as json_error:
                    logger.error(f"JSON解析失败: {json_error}")
                    logger.error(f"原始响应内容: {content}")
                    if attempt < max_retries - 1:
                        logger.info("重试中...")
                        continue
                    else:
                        return None
                        
            except Exception as e:
                error_message = str(e)
                logger.error(f"JSON格式API请求异常 (尝试 {attempt + 1}/{max_retries}): {error_message}")
                if attempt < max_retries - 1:
                    continue
                else:
                    return None
        
        logger.error("所有尝试均失败")
        return None

    def generate_json_output_with_validation(self, prompt, json_schema_example, required_fields=None, max_tokens=16384, temperature=0.7, timeout=180):
        """
        生成JSON输出并验证必需字段
        
        参数:
            prompt(str): 用户提示词
            json_schema_example(str): JSON格式示例
            required_fields(list): 必需字段列表，用于验证输出
            max_tokens(int): 最大生成token数量
            temperature(float): 生成文本的随机性
            timeout(int): 请求超时时间(秒)
            
        返回:
            dict: 验证通过的JSON对象，如果失败返回None
        """
        result = self.generate_json_output(prompt, json_schema_example, max_tokens, temperature, timeout)
        
        if result is None:
            return None
            
        # 如果指定了必需字段，进行验证
        if required_fields:
            missing_fields = []
            for field in required_fields:
                if field not in result:
                    missing_fields.append(field)
            
            if missing_fields:
                logger.error(f"JSON输出缺少必需字段: {missing_fields}")
                return None
            else:
                logger.info("JSON输出验证通过")
        
        return result


# ====== 简单测试示例 ======
if __name__ == "__main__":
    try:
        # 加载环境变量并初始化接口
        load_dotenv()
        huoshan_interface = HuoshanDeepSeekInterface()
        
        # 测试提示词
        test_prompt = "请简述龙虎榜席位分析的意义"
        
        # 测试方法1: generate_text_simple (简单非流式)
        print("\n===== 测试 generate_text_simple =====")
        print("正在生成，请稍候...")
        answer_simple = huoshan_interface.generate_text_simple(test_prompt, temperature=0.7)
        print("\n=== 简单回答 ===")
        print(answer_simple)
        print("\n=== 测试1完成 ===\n")

        # 测试方法2: generate_text_with_thinking (不实时显示)
        print("\n===== 测试 generate_text_with_thinking =====")
        print("正在生成，请稍候...")
        answer1, thinking1 = huoshan_interface.generate_text_with_thinking(test_prompt, temperature=0.7)
        
        print("\n=== 推理过程 ===")
        print(thinking1)
        print("\n=== 最终回答 ===")
        print(answer1)
        print("\n=== 测试2完成 ===\n")

        # 测试方法3: stream_output_with_thinking (实时显示)
        print("\n===== 测试 stream_output_with_thinking =====")
        print("正在测试火山引擎API，流式输出推理过程和回答...")
        
        # 定义回调函数
        def print_thinking(content):
            print(content, end="", flush=True)
            
        def print_answer(content):
            print(content, end="", flush=True)
        
        # 执行流式生成
        print("\n=== 推理过程 ===\n")
        answer2, thinking2 = huoshan_interface.stream_output_with_thinking(
            test_prompt, 
            callback_thinking=print_thinking,
            callback_answer=print_answer,
            temperature=0.7
        )
        print("\n\n=== 测试3完成 ===\n")

        # 测试方法4: generate_json_output (JSON格式输出)
        print("\n===== 测试 generate_json_output =====")
        json_prompt = "请分析股票300033同花顺的基本情况"
        json_example = """{
    "stock_code": "300033",
    "stock_name": "同花顺",
    "analysis": {
        "basic_info": "公司基本信息",
        "financial_status": "财务状况分析",
        "market_position": "市场地位",
        "risk_factors": ["风险因素1", "风险因素2"],
        "investment_advice": "投资建议"
    },
    "rating": "买入/持有/卖出",
    "confidence": 0.85
}"""
        
        print("正在生成JSON格式分析...")
        json_result = huoshan_interface.generate_json_output(
            json_prompt,
            json_example,
            max_tokens=65536,
            temperature=1.0
        )
        
        if json_result:
            print("\n=== JSON分析结果 ===")
            print(json.dumps(json_result, ensure_ascii=False, indent=2))
        else:
            print("JSON生成失败")
        print("\n=== 测试4完成 ===\n")

        # 测试方法5: generate_json_output_with_validation (带验证的JSON输出)
        print("\n===== 测试 generate_json_output_with_validation =====")
        required_fields = ["stock_code", "stock_name", "rating"]
        print("正在生成带验证的JSON格式分析...")
        validated_result = huoshan_interface.generate_json_output_with_validation(
            json_prompt,
            json_example,
            required_fields=required_fields,
            temperature=0.7
        )
        
        if validated_result:
            print("\n=== 验证通过的JSON结果 ===")
            print(json.dumps(validated_result, ensure_ascii=False, indent=2))
        else:
            print("JSON生成或验证失败")
        print("\n=== 测试5完成 ===")
            
    except Exception as e:
        print(f"测试异常: {str(e)}")
        import traceback
        traceback.print_exc() 