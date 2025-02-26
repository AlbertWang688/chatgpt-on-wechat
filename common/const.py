# bot_type
OPEN_AI = "openAI"
CHATGPT = "chatGPT"
BAIDU = "baidu"
XUNFEI = "xunfei"
CHATGPTONAZURE = "chatGPTOnAzure"
LINKAI = "linkai"
RAG4AI = "rag4AI"
CLAUDEAI = "claude"
QWEN = "qwen"
GEMINI = "gemini"
ZHIPU_AI = "glm-4"


# model
GPT35 = "gpt-3.5-turbo"
GPT4 = "gpt-4"
GPT4_TURBO_PREVIEW = "gpt-4-0125-preview"
GPT4_VISION_PREVIEW = "gpt-4-vision-preview"
WHISPER_1 = "whisper-1"
TTS_1 = "tts-1"
TTS_1_HD = "tts-1-hd"

MODEL_LIST = ["gpt-3.5-turbo", "gpt-3.5-turbo-16k", "gpt-4", "wenxin", "wenxin-4", "xunfei", "claude", "gpt-4-turbo",
              "gpt-4-turbo-preview", "gpt-4-1106-preview", GPT4_TURBO_PREVIEW, QWEN, GEMINI, ZHIPU_AI]

# 其他模型与机器人对应关系 model_to_bot_type
MODEL_TO_BOT_TYPE =  {
    "text-davinci-003": OPEN_AI,
    "wenxin": BAIDU,
    "wenxin-4": BAIDU,
    "xunfei": XUNFEI,
    "qwen": QWEN,
    "gemini": GEMINI,
    "claude": CLAUDEAI,
}

# channel
FEISHU = "feishu"
DINGTALK = "dingtalk"   
