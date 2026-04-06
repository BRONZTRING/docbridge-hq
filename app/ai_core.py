import os
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

# 统帅请注意：此处需填入汝之真实大模型 API 密钥。
# 现暂时使用占位符，待统帅日后获取到如 DeepSeek、GigaChat 或 OpenAI 的密钥后替换。
# 若使用兼容接口，还需配置 base_url，例如：os.environ["OPENAI_API_BASE"] = "https://api.deepseek.com/v1"
os.environ["OPENAI_API_KEY"] = "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

# 实例化大模型 (此处默认以 gpt-3.5-turbo 为例，可随时更换为更强大的模型)
# temperature=0 代表我们不需要模型具有创造力，只需要它极其严谨地提取法律与金融事实。
llm = ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo")

def build_summary_chain() -> LLMChain:
    """
    第一道管线：深度长文档浓缩摘要链
    """
    prompt_template = """
    统帅指令：你现在是 DocBridge AI 的首席多语种商业分析师。
    请阅读以下文档内容，并将其浓缩为一段高度精炼的摘要（不超过 300 字）。
    无论原文是俄文、日文还是英文，摘要必须以【中文】输出，以便统帅快速决策。

    文档内容:
    {text}

    精炼摘要:
    """
    prompt = PromptTemplate(template=prompt_template, input_variables=["text"])
    return LLMChain(llm=llm, prompt=prompt)

def build_risk_chain() -> LLMChain:
    """
    第二道管线：风险拦截雷达与合规排雷链
    """
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
    prompt = PromptTemplate(template=prompt_template, input_variables=["text"])
    return LLMChain(llm=llm, prompt=prompt)