import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

load_dotenv()
SILICONFLOW_API_KEY = os.getenv("SILICONFLOW_API_KEY")
if not SILICONFLOW_API_KEY:
    raise ValueError("未在 .env 中寻获 SILICONFLOW_API_KEY！")

llm = ChatOpenAI(
    model="Qwen/Qwen2.5-7B-Instruct",
    api_key=SILICONFLOW_API_KEY,
    base_url="https://api.siliconflow.cn/v1",
    temperature=0
)

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
    model_kwargs={'device': 'cpu'}
)

def get_embeddings(): return embeddings

def build_summary_chain():
    prompt = PromptTemplate.from_template("""统帅指令：你现在是 DocBridge AI 的首席多语种商业分析师。请阅读以下文档内容，浓缩为不超过 300 字的摘要。必须以【中文】输出。\n文档内容:\n{text}\n精炼摘要:""")
    return prompt | llm | StrOutputParser()

def build_risk_chain():
    prompt = PromptTemplate.from_template("""统帅指令：你现在是 DocBridge AI 的首席国际法务风控官。请提取以下三维度风险：1.【违约责任】2.【管辖地与争议解决】3.【潜在陷阱】。必须以【结构化的中文】输出。\n文档内容:\n{text}\n风险排雷报告:""")
    return prompt | llm | StrOutputParser()

def build_qa_chain():
    # 【战术升级】：注入历史对话记录，打破失忆症！
    prompt = PromptTemplate.from_template("""统帅指令：你现在是 DocBridge AI 的首席情报官。
    请根据以下提取的【文档参考片段】以及【历史对话记录】，回答统帅的【最新提问】。
    如果片段中没有相关信息，请结合上下文推理，或如实回答“未能找到相关情报”。
    一律用【中文】进行专业、严谨的回答。
    
    文档参考片段:
    {context}
    
    历史对话记录:
    {chat_history}
    
    统帅最新提问:
    {question}
    
    情报回复:""")
    return prompt | llm | StrOutputParser()