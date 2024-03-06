from bot.bot_factory import create_bot
from bridge.context import Context
from bridge.reply import Reply
from common import const
from common.log import logger
from common.singleton import singleton
from config import conf
from translate.factory import create_translator
from voice.factory import create_voice


@singleton
class Bridge(object):
    def __init__(self):
        self.btype = {
            "chat": const.CHATGPT,
            "voice_to_text": conf().get("voice_to_text", "openai"),
            "text_to_voice": conf().get("text_to_voice", "google"),
            "translate": conf().get("translate", "baidu"),
        }
        model_type = conf().get("model") or const.GPT35
        # if model_type in ["text-davinci-003"]:
        #     self.btype["chat"] = const.OPEN_AI
        # if conf().get("use_azure_chatgpt", False):
        #     self.btype["chat"] = const.CHATGPTONAZURE
        # if model_type in ["wenxin", "wenxin-4"]:
        #     self.btype["chat"] = const.BAIDU
        # if model_type in ["xunfei"]:
        #     self.btype["chat"] = const.XUNFEI
        # if model_type in [const.QWEN]:
        #     self.btype["chat"] = const.QWEN
        # if model_type in [const.GEMINI]:
        #     self.btype["chat"] = const.GEMINI
        # if model_type in ["claude"]:
        #     self.btype["chat"] = const.CLAUDEAI
        
        # 检查model_type是否在映射中，如果是，则更新self.btype["chat"]
        if model_type in const.MODEL_TO_BOT_TYPE:
            self.btype["chat"] = const.MODEL_TO_BOT_TYPE[model_type]
        
        # 单独处理基于主机器人衍生出的bot(如use_azure_chatgpt，use_RAG,use_linkai的逻辑，考虑到可能的异常
        try:
            if conf().get("use_azure_chatgpt", False):
                self.btype["chat"] = const.CHATGPTONAZURE
            if conf().get("use_RAG",False):
                self.btype["chat"] = const.RAG4AI
            if conf().get("use_linkai",False) and conf().get("linkai_api_key"):
                self.btype["chat"] = const.LINKAI
                if not conf().get("voice_to_text") or conf().get("voice_to_text") in ["openai"]:
                    self.btype["voice_to_text"] = const.LINKAI
                if not conf().get("text_to_voice") or conf().get("text_to_voice") in ["openai", const.TTS_1, const.TTS_1_HD]:
                    self.btype["text_to_voice"] = const.LINKAI
        except Exception as e:
                # 假设这里我们简单打印异常，实际应用中可能需要更复杂的错误处理逻辑
                print(f"Error retrieving use_azure_chatgpt flag: {e}")


        # if conf().get("use_linkai") and conf().get("linkai_api_key"):
        #     self.btype["chat"] = const.LINKAI
        #     if not conf().get("voice_to_text") or conf().get("voice_to_text") in ["openai"]:
        #         self.btype["voice_to_text"] = const.LINKAI
        #     if not conf().get("text_to_voice") or conf().get("text_to_voice") in ["openai", const.TTS_1, const.TTS_1_HD]:
        #         self.btype["text_to_voice"] = const.LINKAI


        
        self.bots = {}
        self.chat_bots = {}
    
    def get_bot(self, typename):
        """
        根据给定的类型名称获取对应的机器人实例
        :param typename: 机器人类型名称
        :return: 机器人实例
        """
        if self.bots.get(typename) is None:
            logger.info("create bot {} for {}".format(self.btype[typename], typename))
            if typename == "text_to_voice":
                self.bots[typename] = create_voice(self.btype[typename])
            elif typename == "voice_to_text":
                self.bots[typename] = create_voice(self.btype[typename])
            elif typename == "chat":
                self.bots[typename] = create_bot(self.btype[typename])
            elif typename == "translate":
                self.bots[typename] = create_translator(self.btype[typename])
        return self.bots[typename]

    def get_bot_type(self, typename):
        return self.btype[typename]

    def fetch_reply_content(self, query, context: Context) -> Reply:
        return self.get_bot("chat").reply(query, context)

    def fetch_voice_to_text(self, voiceFile) -> Reply:
        return self.get_bot("voice_to_text").voiceToText(voiceFile)

    def fetch_text_to_voice(self, text) -> Reply:
        return self.get_bot("text_to_voice").textToVoice(text)

    def fetch_translate(self, text, from_lang="", to_lang="en") -> Reply:
        return self.get_bot("translate").translate(text, from_lang, to_lang)

    def find_chat_bot(self, bot_type: str):
        if self.chat_bots.get(bot_type) is None:
            self.chat_bots[bot_type] = create_bot(bot_type)
        return self.chat_bots.get(bot_type)

    def reset_bot(self):
        """
        重置bot路由
        """
        self.__init__()
