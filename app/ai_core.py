import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

# 读取隐身斗篷中的机密 (自动加载 GOOGLE_API_KEY)
load_dotenv()

# 1. 文本分析主炮：全面换装 2026 年最新 3.1 世代！
# 这里使用的是极速轻骑兵，适合日常秒级排雷
llm = ChatGoogleGenerativeAI(model="gemini-3.1-flash-live-preview", temperature=0)

# 若统帅处理几十页以上的艰深俄文文献，可注释掉上面那行，改用下面这把巅峰重剑：
# llm = ChatGoogleGenerativeAI(model="gemini-3.1-pro-preview", temperature=0)

# 2. 高维空间折叠枪：谷歌原生 768 维向量模型
embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")

def get_embeddings():
    """向外界提供折叠枪"""
    return embeddings

def build_summary_chain():
    prompt_template = """
    统帅指令：你现在是 DocBridge AI 的首席多语种商业分析师。
    请阅读以下文档内容，并将其浓缩为一段高度精炼的摘要（不超过 300 字）。
    无论原文是俄文、日文还是英文，摘要必须以【中文】输出，以便统帅快速决策。

    文档内容:
    {text}

    精炼摘要:
    """
    prompt = PromptTemplate.from_template(prompt_template)
    return prompt | llm | StrOutputParser()

def build_risk_chain():
    prompt_template = """
    统帅指令：你现在是 DocBridge AI 的首席国际法务风控官。
    请审查以下跨国合同或商业文档的内容，并运用你的专业知识，极其敏锐地提取出以下三个维度的风险点：
    1. 【违约责任】：若发生违约，具体的赔偿条款或惩罚机制是什么？
    2. 【管辖地与争议解决】：若发生商业纠纷，适用哪个国家的法律？在何地进行仲裁或诉讼？
    3. 【潜在陷阱】：条款中是否存在对己方明显不利的隐蔽条件或模糊表述？

    请务必保持客观严谨。无论原文语种为何，请以【结构化的中文】输出你的风险排雷报告。

    文档内容:
    {text}

    风险排雷报告:
    """
    prompt = PromptTemplate.from_template(prompt_template)
    return prompt | llm | StrOutputParser()