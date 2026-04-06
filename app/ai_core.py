import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

# 【法术激活】：读取根目录的 .env 文件，将其中的机密注入系统环境变量
load_dotenv()

# 实例化大模型（它会自动去环境变量里寻找 OPENAI_API_KEY，无需明文写出）
llm = ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo")

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