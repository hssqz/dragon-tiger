# 龙虎榜评论区Chatbot上下文工程设计方案

## 一、核心问题与场景

### 1.1 上下文组装问题
当前的`lhb_comment_chatbot.py`只支持简单的多轮对话，缺乏对评论区@触发场景的上下文理解能力。核心需求是在@触发时，组装正确的上下文信息。

### 1.2 两种关键场景

#### 场景1：并行@回复
多个用户同时@同一评论下的LLM：
```
格局哥🔥: "松原安全这波太给力了！"
├── 用户A: "@gushen 格局哥说得对吗？"
├── 用户B: "@gushen 我觉得风险很大，你怎么看？"  
└── 用户C: "@gushen 什么时候入场好？"
```

#### 场景2：串行@追问
单个用户持续@追问：
```
格局哥🔥: "松原安全这波太给力了！"
└── 用户A: "@gushen 格局哥说得对吗？"
    └── LLM: "从龙虎榜数据看..."
        └── 用户A: "@gushen 那风险点在哪？"
            └── LLM: "主要风险是..."
                └── 用户A: "@gushen 现在能买吗？"
```

## 二、上下文组装策略

### 2.1 并行@场景需要的上下文
当多个用户同时@同一评论时，需要组装：
- **@问题本身**：用户的具体提问
- **目标评论**：被@的那条评论内容和作者
- **龙虎榜数据**：股票基础信息和分析结论

### 2.2 串行@场景需要的上下文  
当用户连续@追问时，需要组装：
- **@问题本身**：用户的具体提问
- **目标评论**：被@的那条评论内容和作者
- **对话历史**：该用户与LLM的历史问答记录（包含问题和回复）
- **龙虎榜数据**：股票基础信息和分析结论

## 三、数据结构设计

### 3.1 评论数据结构
```python
comment_item = {
    "comment_id": "c_001",
    "author": {
        "name": "格局哥🔥"
    },
    "content": "见弟们，松原安全这波太给力了！连续三天涨超30%...",
    "timestamp": "08-21 18:37"
}
```

### 3.2 上下文数据结构
```python
# 并行@场景上下文
parallel_context = {
    "mention_question": "格局哥说得对吗？",           # @后的问题
    "target_comment": comment_item,                    # 被@的评论
    "post_data": {                                     # 龙虎榜数据
        "stock_info": {...},
        "analysis_report": {...}
    }
}

# 串行@场景上下文
serial_context = {
    "mention_question": "那风险点在哪？",              # @后的问题
    "target_comment": comment_item,                    # 被@的评论
    "conversation_history": [                          # 对话历史
        {
            "round": 1,
            "user_question": "格局哥说得对吗？",
            "llm_response": "从龙虎榜数据看，格局哥的分析有一定道理..."
        }
    ],
    "post_data": {                                     # 龙虎榜数据
        "stock_info": {...},
        "analysis_report": {...}
    }
}
```

## 四、上下文组装逻辑

### 4.1 并行@场景的Prompt组装
```python
def build_parallel_context_prompt(parallel_context):
    prompt = f"""
## 当前@提及
问题：{parallel_context['mention_question']}

## 被@的评论
{parallel_context['target_comment']['author']['name']}: {parallel_context['target_comment']['content']}

## 龙虎榜数据
股票：{parallel_context['post_data']['stock_info']['name']}
分析结论：{parallel_context['post_data']['analysis_report']['final_verdict']['outlook']}

请基于以上信息进行专业回复。
"""
    return prompt
```

### 4.2 串行@场景的Prompt组装
```python
def build_serial_context_prompt(serial_context):
    prompt = f"""
## 当前@提及
问题：{serial_context['mention_question']}

## 被@的评论
{serial_context['target_comment']['author']['name']}: {serial_context['target_comment']['content']}

## 我们的对话历史
{format_conversation_history(serial_context['conversation_history'])}

## 龙虎榜数据
股票：{serial_context['post_data']['stock_info']['name']}
分析结论：{serial_context['post_data']['analysis_report']['final_verdict']['outlook']}

请基于之前的对话记忆继续回复。
"""
    return prompt

def format_conversation_history(history):
    result = ""
    for round in history:
        result += f"第{round['round']}轮:\n"
        result += f"用户问：{round['user_question']}\n"
        result += f"我回复：{round['llm_response']}\n\n"
    return result
```

### 5.1 并行@场景示例
```python
# 场景：多个用户同时@同一评论
target_comment = {
    "author": {"name": "格局哥🔥"},
    "content": "见弟们，松原安全这波太给力了！连续三天涨超30%..."
}

# 构建并行@上下文
parallel_context = {
    "mention_question": "格局哥说得对吗？",
    "target_comment": target_comment,
    "post_data": lhb_json_data
}

# 生成上下文prompt
prompt = build_parallel_context_prompt(parallel_context)
# 基于龙虎榜数据进行专业回复
```

### 5.2 串行@场景示例  
```python
# 场景：用户连续@追问
target_comment = {
    "author": {"name": "格局哥🔥"},
    "content": "见弟们，松原安全这波太给力了！连续三天涨超30%..."
}

# 构建串行@上下文
serial_context = {
    "mention_question": "那风险点在哪？",
    "target_comment": target_comment,
    "conversation_history": [
        {
            "round": 1,
            "user_question": "这个龙虎榜看起来资金分歧很大？",
            "llm_response": "从数据看确实存在分歧，主力买入0.72亿，但也有量化基金卖出..."
        }
    ],
    "post_data": lhb_json_data
}

# 生成上下文prompt
prompt = build_serial_context_prompt(serial_context)
# 最终回复会基于第1轮的分析继续深入
```

---

## 总结

本设计方案专注于**上下文组装问题**，明确了@触发场景下的核心上下文需求：

### 并行@场景必要上下文
- @问题本身
- 被@的评论
- 龙虎榜基础数据

### 串行@场景必要上下文
- @问题本身
- 被@的评论
- 该用户的历史对话记录（包含问题和回复）
- 龙虎榜基础数据

通过这种简化的上下文组装策略，确保LLM在评论区@触发时能够获得准确、相关的背景信息，生成专业的龙虎榜分析回复。




# 附录
股神的上下文组装逻辑：


``` java

        ##角色：\n" +
        "你是微速科技的股吧智能助手,在股吧中的昵称是'股神',与现实中的股神巴菲特没有关系，用户@你和你进行互动。" +
        "## 人设特点\n" +
        "- 确定性追求：强调投资的确定性，偏好盈利模式清晰、市场地位稳固的企业；并集中投资于少数几家经过深入研究的公司\n" +
        "- 长期视角：坚持长期投资，不为短期市场波动所动\n" +
        "- 直率与坦诚：直言不讳，分享自己的真实想法；经常抛出大胆的观点称为金句\n" +
        "- 幽默与乐观：常带幽默感，使复杂的投资理念变得易于理解；对于市场的大跌，一直称为牛市初期\n" +
        "- 语言风格：不太使用专业术语和经济概念。擅长以通俗易懂的方式表达复杂的观点，使其内容适合普通听众或读者。\n"+
        "##功能：\n" +
        "在股吧中对用户的'@股神'提出的问题进行回复，你会根据用户的问题结合以下的[相关信息]来进行回帖\n" +
        "##要求：\n" +
        "1.内容中不需要出现\"回复评论、评论回复、根据你提供的信息\"之类的描述，也不需要称呼提出问题的用户昵称。\n" +
        "2.结合下面的[相关信息]和个人见解，构建有深度的回答。\n" +
        "3.当你回答需要明确的股票名称或者公司名称，而用户提出的问题不包含体的股票名称或者公司名称等信息时，从相关信息中帖子主题中获取股票名称或者公司名称，补全用户的问题之后再回答。\n" +
        "4.回复不要超过200字，语言精练，突出重点。\n"+
        "##用户的问题：\n"+
        "{{question}}\n"+
        "##相关信息：\n"+
        "1.帖子主题：{{postTitle}}\n"+
        "2.贴子的内容：{{postText}}\n"+
        "3.上级回复的内容：{{parentCommentText}}\n"+
        "4.相关性数据：{{info}}\n"+
        "根据已有信息无法得出结论时，可以尝试通过Function Calling调用定义的functions获取最新数据和信息，\n" +
        "基于以上信息，用专业、简洁的语言回答用户的金融及投资类问题。如果问题超出你的能力范围或你没有获取足够的信息，请如实告知并礼貌拒绝回答，避免编造你不知道的信息。
```