import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
# 引入本地开源折叠枪
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

# 读取隐身斗篷中的机密
load_dotenv()

# 1. 文本主炮：继续白嫖谷歌的 2.5 世代极速旗舰
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)

# 2. 高维折叠枪：彻底换装本地 1GB 大小的多语种开源神器！
# (首次运行时，它会在后台自动下载大约 1.1GB 的模型文件，请耐心等待)
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-multilingual-mpnet-base-v2")

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

def build_qa_chain():
    """
    第三道管线：基于向量检索的 RAG 审讯链
    """
    prompt_template = """
    统帅指令：你现在是 DocBridge AI 的首席情报官。
    请根据以下提取的【文档参考片段】，回答统帅的【提问】。
    如果片段中没有相关信息，请如实回答“根据当前文档片段，未能找到相关情报”，绝不能胡编乱造。
    无论提问或片段是什么语言，请一律用【中文】进行专业、严谨的回答。

    文档参考片段:
    {context}

    统帅提问:
    {question}

    情报回复:
    """
    prompt = PromptTemplate.from_template(prompt_template)
    return prompt | llm | StrOutputParser()