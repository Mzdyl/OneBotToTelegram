#!/usr/bin/env python3

import asyncio
import json
import logging
import configparser
from websockets import connect
from telegram import Bot
from typing import Dict, Any

# 配置日志记录
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 读取配置文件
config = configparser.ConfigParser()
config.read('.config')

# Telegram 机器人 Token 和聊天 ID（建议使用环境变量或配置文件来存储这些信息）
TELEGRAM_BOT_TOKEN = config['telegram']['bot_token']
TELEGRAM_CHAT_ID = config['telegram']['chat_id']

# 初始化 Telegram 机器人
bot = Bot(token=TELEGRAM_BOT_TOKEN)

# OneBot WebSocket 服务器列表
ONEBOT_WS_URLS = config['onebot']['ws_urls'].split(',')

# OneBot 机器人名称列表
BOT_NAME = {int(key): value for key, value in config['bot_names'].items()}

# 忽略的消息类型列表
IGNORE_TYPES = ["heartbeat", "lifecycle"]

# 表情ID到表情名称的映射字典
FACE_ID_TO_NAME = {int(key): value for key, value in config['face_ids'].items()}

async def handle_onebot(ws_url: str):
    """处理 OneBot WebSocket 连接并接收消息"""
    while True:
        try:
            async with connect(ws_url) as websocket:
                async for message in websocket:
                    data = json.loads(message)
                    await process_onebot_message(data)
        except Exception as e:
            logger.error(f"连接到 {ws_url} 失败: {e}")
            await asyncio.sleep(5)  # 等待 5 秒后重试

async def process_onebot_message(message: Dict[str, Any]):
    """处理收到的 OneBot 消息并转发到 Telegram"""
    if should_ignore_message(message):
        return

    text = format_message(message)
    try:
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=text, parse_mode='Markdown')
        logger.info(f"消息已发送到 Telegram 聊天 ID {TELEGRAM_CHAT_ID}")
    except Exception as e:
        logger.error(f"发送消息到 Telegram 失败: {e}")

def should_ignore_message(message: Dict[str, Any]) -> bool:
    """检查消息是否应被忽略（如心跳消息）"""
    return (
        message.get("post_type") == "meta_event" and
        message.get("meta_event_type") in IGNORE_TYPES
    )

def format_message(message: Dict[str, Any]) -> str:
    """格式化 OneBot 消息以便发送到 Telegram"""
    if message.get("post_type") == "message":
#       return message 
        if message.get("message_type") == "private":
            return format_private_message(message)
        elif message.get("message_type") == "group":
            return format_group_message(message)
    return f"收到来自 OneBot 的消息: {json.dumps(message, indent=2)}"

def format_private_message(message: Dict[str, Any]) -> str:
    """格式化私聊消息"""
    self_id = message.get("self_id")
    self_name = BOT_NAME[self_id]
    sender_info = message.get("sender", {})
    sender_id = sender_info.get("user_id", "未知")
    sender_nickname = sender_info.get("nickname", "未知")
    raw_message = message.get("raw_message", "")
    formatted_message = (
        f"**{self_name} 收到来自 {sender_nickname}（用户 ID: {sender_id}）的私聊消息：**\n"
        f"{format_message_content(raw_message, message.get('message', []))}\n"
    )
    return formatted_message

def format_group_message(message: Dict[str, Any]) -> str:
    """格式化群消息"""
    self_id = message.get("self_id")
    self_name = BOT_NAME[self_id]
    sender_info = message.get("sender", {})
    sender_id = sender_info.get("user_id", "未知")
    sender_nickname = sender_info.get("nickname", "未知")
    group_id = message.get("group_id", "未知")
    raw_message = message.get("raw_message", "")
    formatted_message = (
        f"**{self_name} 收到群组 {group_id} 的消息**\n"
        f"来自 {sender_nickname}（用户 ID: {sender_id}）：\n"
        f"{format_message_content(raw_message, message.get('message', []))}\n"
    )
    return formatted_message

def format_message_content(raw_message: str, message_elements: list) -> str:
    """格式化消息内容（处理图片、表情等）"""
    # 初始化消息内容
#   formatted_message = f"原始信息:\n{raw_message}\n"
    formatted_message = f"转换前信息:\n{message_elements}\n转换后后信息:\n"
    # 处理消息段
    for element in message_elements:
        element_type = element.get("type")
        data = element.get("data", {})
        
        if element_type == "text":
            text_content = data.get("text", "")
            formatted_message += text_content
            
        elif element_type == "face":
            face_id = data.get("id", "")
            face_name = FACE_ID_TO_NAME.get(face_id, "未知表情")
            formatted_message += f"[表情 {face_id}: {face_name}]"
            
        elif element_type == "image":
            file_name = data.get("file", "图片")
            parts = file_name.split('_')
            if len(parts) >= 4:
                file_name = '_'.join(parts[3:])
            else:
                file_name = file_name
            file_url = data.get("url", data.get("file", ""))
            formatted_message += f"\n[图片:{file_name}]({file_url})"
            
        elif element_type == "record":
            file_url = data.get("url", data.get("file", ""))
            formatted_message += f"\n[语音: {file_url}]"
            
        elif element_type == "video":
            file_url = data.get("url", data.get("file", ""))
            formatted_message += f"\n[视频: {file_url}]"
            
        elif element_type == "at":
            qq = data.get("qq", "")
            if qq == "all":
                formatted_message += "@全体成员 "
            else:
                formatted_message += f"@{qq} "
                
        elif element_type == "rps":
            formatted_message += "\n[猜拳表情]"
            
        elif element_type == "dice":
            formatted_message += "\n[掷骰子表情]"
            
        elif element_type == "shake":
            formatted_message += "\n[窗口抖动]"
            
        elif element_type == "poke":
            poke_type = data.get("type", "")
            poke_id = data.get("id", "")
            formatted_message += f"\n[戳一戳: type={poke_type}, id={poke_id}]"
            
        elif element_type == "anonymous":
            formatted_message += "\n[匿名消息]"
            
        elif element_type == "share":
            url = data.get("url", "")
            title = data.get("title", "")
            content = data.get("content", "")
            image = data.get("image", "")
            formatted_message += f"\n[分享: {title}]({url})"
            if content:
                formatted_message += f" - {content}"
            if image:
                formatted_message += f"\n![分享图片]({image})"
                
        elif element_type == "contact":
            contact_type = data.get("type", "")
            contact_id = data.get("id", "")
            formatted_message += f"\n[推荐{contact_type}: {contact_id}]"
            
        elif element_type == "location":
            lat = data.get("lat", "")
            lon = data.get("lon", "")
            title = data.get("title", "")
            content = data.get("content", "")
            formatted_message += f"\n[位置: {title} ({lat}, {lon})]"
            if content:
                formatted_message += f" - {content}"
                
        elif element_type == "music":
            music_type = data.get("type", "")
            url = data.get("url", "")
            audio = data.get("audio", "")
            title = data.get("title", "")
            content = data.get("content", "")
            image = data.get("image", "")
            if music_type == "custom":
                formatted_message += f"\n[自定义音乐: {title}]({url})"
                if audio:
                    formatted_message += f" - [播放]({audio})"
                if content:
                    formatted_message += f" - {content}"
                if image:
                    formatted_message += f"\n![音乐图片]({image})"
            else:
                formatted_message += f"\n[音乐: {title} ({music_type})]"
                
        elif element_type == "reply":
            reply_id = data.get("id", "")
            formatted_message += f"\n[回复消息{reply_id}: ]"
            
        elif element_type == "forward":
            forward_id = data.get("id", "")
            formatted_message += f"\n[合并转发: {forward_id}]"
            
        elif element_type == "node":
            user_id = data.get("user_id", "")
            nickname = data.get("nickname", "")
            content = data.get("content", "")
            formatted_message += f"\n[合并转发节点: {nickname} ({user_id})]"
            if isinstance(content, list):
                for sub_element in content:
                    sub_element_type = sub_element.get("type")
                    sub_data = sub_element.get("data", {})
                    if sub_element_type == "text":
                        sub_text_content = sub_data.get("text", "")
                        formatted_message += sub_text_content
                    elif sub_element_type == "face":
                        sub_face_id = sub_data.get("id", "")
                        formatted_message += f"[表情 {sub_face_id}]"
                    # 可以继续添加更多子消息段处理
                        
        elif element_type == "xml":
            xml_data = data.get("data", "")
            formatted_message += f"\n[XML消息: {xml_data}]"
            
        elif element_type == "json":
            json_data = data.get("data", "")
            formatted_message += f"\n[JSON消息: {json_data}]"
            
    return formatted_message
    

async def main():
    """主函数，创建任务并启动处理"""
    tasks = [asyncio.create_task(handle_onebot(ws_url)) for ws_url in ONEBOT_WS_URLS]
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
    