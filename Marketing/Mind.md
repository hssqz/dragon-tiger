#龙虎榜设计思考

能上LLM就上LLM，绝对不用Code
可控性配上一个json output也够了
做好上下文压缩，智能是最大的杠杆


2.垂直agent？
Top down的设计逻辑是错的
Botton up的设计逻辑才work
前者的设计架构在当前context management才刚刚兴起的背景下远远不成熟

3.塞什么给到LLM，上下文非常关键-聚焦广度
以及把塞之后到内容是否再次喂给LLM，让LLM再次加深-聚焦深度