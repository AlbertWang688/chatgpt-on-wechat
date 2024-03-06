# access 自有知識庫平臺

import time
import requests

from bot.bot import Bot
from bot.chatgpt.chat_gpt_session import ChatGPTSession
from bot.session_manager import SessionManager
from bridge.context import Context, ContextType
from bridge.reply import Reply, ReplyType
from common.log import logger
from common.token_bucket import TokenBucket
from config import conf, load_config

import os.path
from llama_index.core import(
    VectorStoreIndex,
    SimpleDirectoryReader,
    StorageContext,
    Settings,
    load_index_from_storage,
)
from llama_index.core.callbacks import(
    CallbackManager,
    TokenCountingHandler,
)
import tiktoken
from llama_index.llms.openai import OpenAI
import threading
from common import memory, utils
import base64
import os

llm = OpenAI()
class rag4AI(Bot):
    def __init__(self):
        super().__init__()
        llm.api_key = conf().get("open_ai_api_key")
        if conf().get("rate_limit_chatgpt"):
            self.tb4chatgpt = TokenBucket(conf().get("rate_limit_chatgpt", 20))
        
        self.sessions = SessionManager(ChatGPTSession, model=conf().get("model") or "gpt-3.5-turbo")
        self.args = {
            "model": conf().get("model") or "gpt-3.5-turbo",  # 对话模型的名称
            "temperature": conf().get("temperature", 0.9),  # 值在[0,1]之间，越大表示回复越具有不确定性
            "time_out": conf().get("request_timeout", None),  # 请求超时时间，openai接口默认设置为600，对于难问题一般需要较长时间
        }
    def reply(self, query, context: Context = None) -> Reply:
        # acquire reply content
        if context.type == ContextType.TEXT:
            logger.info("[rag4AI] query={}",format(query))
        
            session_id = context["session_id"]
            reply = None
            # #chat_gpt_bot.py中以下代码无法运行，#前缀符已被godCMD使用并在进入此模块前拦截
            # clear_memory_commands = conf().get("clear_memory_commands", ["#清除记忆"])
            # if query in clear_memory_commands:
            #     self.sessions.clear_session(session_id)
            #     reply = Reply(ReplyType.INFO, "记忆已清除")
            # elif query == "#清除所有":
            #     self.sessions.clear_all_session()
            #     reply = Reply(ReplyType.INFO, "所有人记忆已清除")
            # elif query == "#更新配置":
            #     load_config()
            #     reply = Reply(ReplyType.INFO, "配置已更新")
            # if reply:
            #     return reply
            session = self.sessions.session_query(query, session_id)
            logger.debug("[RAG4AI] session query={}".format(session.messages))

            api_key = context.get("openai_api_key")
            model = context.get("gpt_model")
            new_args = None
            if model:
                new_args = self.args.copy()
                new_args["model"] = model
            # if context.get('stream'):
            #     # reply in stream
            #     return self.reply_text_stream(query, new_query, session_id)

            reply_content = self.reply_text(session, api_key, args=new_args,query=query)
            logger.debug(
                "[RAG4AI] new_query={}, session_id={}, reply_cont={}, completion_tokens={}".format(
                    session.messages,
                    session_id,
                    reply_content["content"],
                    reply_content["completion_tokens"],
                )
            )
            if reply_content["completion_tokens"] == 0 and len(reply_content["content"]) > 0:
                reply = Reply(ReplyType.ERROR, reply_content["content"])
            elif reply_content["completion_tokens"] > 0:
                self.sessions.session_reply(reply_content["content"], session_id, reply_content["total_tokens"])
                reply = Reply(ReplyType.TEXT, reply_content["content"])
            else:
                reply = Reply(ReplyType.ERROR, reply_content["content"])
                logger.debug("[RAG4AI] reply {} used 0 tokens.".format(reply_content))
            return reply
        # elif context.type == ContextType.IMAGE_CREATE:
        #     ok, retstring = self.create_img(query, 0)
        #     reply = None
        #     if ok:
        #         reply = Reply(ReplyType.IMAGE_URL, retstring)
        #     else:
        #         reply = Reply(ReplyType.ERROR, retstring)
        #     return reply
        else:
            reply = Reply(ReplyType.ERROR, "Bot不支持处理{}类型的消息".format(context.type))
            return reply

    def reply_text(self, session: ChatGPTSession, api_key=None, args=None, retry_count=0,query="") -> dict:

        try:
            if conf().get("rate_limit_chatgpt") and not self.tb4chatgpt.get_token():
                raise SystemError("RateLimitError: rate limit exceeded")
        
            if args is None:
                args = self.args

            # you can set a tokenizer directly, or optionally let it default
            # to the same tokenizer that was used previously for token counting
            # NOTE: The tokenizer should be a function that takes in text and returns a list of tokens
            token_counter = TokenCountingHandler(
                tokenizer=tiktoken.encoding_for_model(self.args["model"]).encode,
                verbose=False, # set to true to see usage printed to the console
            )
            Settings.callback_manager = CallbackManager([token_counter])

            #以下临时测试代码
            # check if storage already exists
            PERSIST_DIR = "./data/persist/"
            if not os.path.exists(PERSIST_DIR):
                # load the documents and create the index
                documents = SimpleDirectoryReader("./data/originalDoc").load_data()
                index = VectorStoreIndex.from_documents(documents)
                # store it for later
                index.storage_context.persist(persist_dir=PERSIST_DIR)
            else:
                # load the existing index
                storage_context = StorageContext.from_defaults(persist_dir=PERSIST_DIR)
                index = load_index_from_storage(storage_context)

            # reset the counts at your discretion!
            token_counter.reset_counts()
            # Either way we can now query the index
            query_engine = index.as_query_engine(llm=llm)
            #此处尚未弄清llama-index中如何实际的模型替换及通用的message组成方式，故此处临时暴力传入query
            Response = query_engine.query("请用中文进行回复：{}".format(query))
            # Response = query_engine.query("中电数通的全称是什么？")
            if Response:
                return {
                    "completion_tokens": token_counter.completion_llm_token_count,
                    "total_tokens": token_counter.total_llm_token_count,
                    "content": Response.response,
                }
            else:
                return {
                    "completion_tokens": 0,
                    "total_tokens": 0,
                    "content": "对不起，我有点懵，啥也没问，不知道怎么回答你",
                }
        except Exception as e:
            need_retry = retry_count < 2
            result = {"completion_tokens": 0, "content": "我现在有点累了，等会再来吧"}
            # if isinstance(e, openai.RateLimitError):
            #     logger.warn("[CHATGPT] RateLimitError: {}".format(e))
            #     result["content"] = "提问太快啦，请休息一下再问我吧"
            #     if need_retry:
            #         time.sleep(20)
            # elif isinstance(e, openai.Timeout):
            #     logger.warn("[CHATGPT] Timeout: {}".format(e))
            #     result["content"] = "我没有收到你的消息"
            #     if need_retry:
            #         time.sleep(5)
            # elif isinstance(e, openai.APIError):
            #     logger.warn("[CHATGPT] Bad Gateway: {}".format(e))
            #     result["content"] = "请再问我一次"
            #     if need_retry:
            #         time.sleep(10)
            # elif isinstance(e, openai.APIConnectionError):
            #     logger.warn("[CHATGPT] APIConnectionError: {}".format(e))
            #     result["content"] = "我连接不到你的网络"
            #     if need_retry:
            #         time.sleep(5)
            # else:
            logger.exception("[RAG4AI] Exception: {}".format(e))
            need_retry = False
            self.sessions.clear_session(session.session_id)

            if need_retry:
                logger.warn("[RAG4AI] 第{}次重试".format(retry_count + 1))
                return self.reply_text(session, api_key, args, retry_count + 1)
            else:
                return result
