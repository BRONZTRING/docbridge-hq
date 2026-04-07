import os
import re
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

# ==========================================
# 🛡️ 战术乙：本地合规隐私护盾 (Privacy Shield)
# ==========================================
class PrivacyShield:
    def __init__(self):
        self.mapping = {}
        self.counter = 0

    def mask(self, text: str) -> str:
        if not text: return text
        # 拦截规则1：邮箱地址
        def repl_email(m):
            self.counter += 1
            key = f"[绝密邮箱_{self.counter}]"
            self.mapping[key] = m.group(0)
            return key
        text = re.sub(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', repl_email, text)
        
        # 拦截规则2：大额资金与涉外货币 (演示级)
        def repl_money(m):
            self.counter += 1
            key = f"[绝密金额_{self.counter}]"
            self.mapping[key] = m.group(0)
            return key
        text = re.sub(r'\d+(?:\.\d+)?(?:万|亿)?(?:人民币|美元|卢布)', repl_money, text)
        return text

    def unmask(self, text: str) -> str:
        if not text: return text
        for key, real_val in self.mapping.items():
            text = text.replace(key, real_val)
        return text

# ==========================================
# 认知管线 Prompt 构建
# ==========================================
def build_summary_chain():
    prompt = PromptTemplate.from_template("""统帅指令：你现在是 DocBridge AI 的首席多语种商业分析师。请阅读以下文档内容，浓缩为不超过 300 字的摘要。必须以【中文】输出。\n文档内容:\n{text}\n精炼摘要:""")
    return prompt | llm | StrOutputParser()

def build_risk_chain():
    prompt = PromptTemplate.from_template("""统帅指令：你现在是 DocBridge AI 的首席国际法务风控官。请提取以下三维度风险：1.【违约责任】2.【管辖地与争议解决】3.【潜在陷阱】。必须以【结构化的中文】输出。\n文档内容:\n{text}\n风险排雷报告:""")
    return prompt | llm | StrOutputParser()

def build_qa_chain():
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