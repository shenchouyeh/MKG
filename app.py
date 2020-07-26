# encoding: utf-8
import json
import os
import random
import requests

from opencc import OpenCC
from question_classifier import *
from question_parser import *
from answer_search import *

cc1 = OpenCC('tw2sp') #繁體中文 (台灣) -> 簡體中文 (包含慣用詞轉換 )
cc2 = OpenCC('s2twp') #簡體中文 -> 繁體中文 (台灣, 包含慣用詞轉換)

handler = ChatBotGraph()

#================== ChatBot 區段
class ChatBotGraph:
    def __init__(self):
        self.classifier = QuestionClassifier()
        self.parser = QuestionPaser()
        self.searcher = AnswerSearcher()

    def chat_main(self, sent):
        answer = '您好，我是居家護理智慧小助理。'
        res_classify = self.classifier.classify(sent)
        if not res_classify:
            return answer
        res_sql = self.parser.parser_main(res_classify)
        final_answers = self.searcher.search_main(res_sql)
        if not final_answers:
            return answer
        else:
            return '\n'.join(final_answers)

#================== LineBot 區段

from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    LocationMessage,
    TemplateSendMessage, ButtonsTemplate, URITemplateAction,
)


app = Flask(__name__)

# 使用環境變數，才不會外洩秘密
handler = WebhookHandler(os.environ['CHANNEL_SECRET'])
line_bot_api = LineBotApi(os.environ['CHANNEL_ACCESS_TOKEN'])

@app.route('/')
def index():
    return "<p>Hello World!</p>"

@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

# ================= 機器人區塊 Start =================
@handler.add(MessageEvent, message=TextMessage)  # default
def handle_text_message(event):                  # default
    msg = event.message.text # message from user
    uid = event.source.user_id # user id

    #============== 處理回覆
    question = cc1.convert(msg)
    answer = handler.chat_main(question)
    answer = cc2.convert(answer)
 
    msg = answer
    line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=msg))

# ================= 機器人區塊 End =================

if __name__ == "__main__":
     app.run(host='0.0.0.0',port=int(os.environ['PORT']))
