import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

# 揭开隐身斗篷，自动吸入 .env 中的变量
load_dotenv()

# 从环境变量中提取密钥，实现兵符分离
SILICONFLOW_API_KEY = os.getenv("SILICONFLOW_API_KEY")
if not SILICONFLOW_API_KEY:
    raise ValueError("未在 .env 中寻获 SILICONFLOW_API_KEY！")

# 1. 文本主炮：硅基流动 Qwen2.5-7B (免费，极速，多语种巅峰)
llm = ChatOpenAI(
    model="Qwen/Qwen2.5-7B-Instruct",
    api_key=SILICONFLOW_API_KEY,
    base_url="https://api.siliconflow.cn/v1",
    temperature=0
)

# 2. 高维折叠枪：本地 768 维神兵 (强制 CPU 运行，防止克隆崩溃)
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
    model_kwargs={'device': 'cpu'}
)

def get_embeddings():
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