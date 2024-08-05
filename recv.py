#!/usr/bin/env python3

import asyncio
import json
import logging
from websockets import connect
from telegram import Bot
from typing import Dict, Any

# 配置日志记录
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Telegram 机器人 Token 和聊天 ID（建议使用环境变量或配置文件来存储这些信息）
TELEGRAM_BOT_TOKEN = ''
TELEGRAM_CHAT_ID = ''

# 初始化 Telegram 机器人
bot = Bot(token=TELEGRAM_BOT_TOKEN)

# OneBot WebSocket 服务器列表
ONEBOT_WS_URLS = [
    "ws://",
    "ws://"
]

# 忽略的消息类型列表
IGNORE_TYPES = ["heartbeat"]

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
        if message.get("message_type") == "private":
            return format_private_message(message)
        elif message.get("message_type") == "group":
            return format_group_message(message)
    return f"收到来自 OneBot 的消息: {json.dumps(message, indent=2)}"

def format_private_message(message: Dict[str, Any]) -> str:
    """格式化私聊消息"""
    sender_info = message.get("sender", {})
    sender_id = sender_info.get("user_id", "未知")
    sender_nickname = sender_info.get("nickname", "未知")
    raw_message = message.get("raw_message", "")
    formatted_message = (
        f"**来自 {sender_nickname}（用户 ID: {sender_id}）的私聊消息：**\n"
        f"{format_message_content(raw_message, message.get('message', []))}\n"
    )
    return formatted_message

def format_group_message(message: Dict[str, Any]) -> str:
    """格式化群消息"""
    sender_info = message.get("sender", {})
    sender_id = sender_info.get("user_id", "未知")
    sender_nickname = sender_info.get("nickname", "未知")
    group_id = message.get("group_id", "未知")
    raw_message = message.get("raw_message", "")
    formatted_message = (
        f"**群组 {group_id} 的消息**\n"
        f"来自 {sender_nickname}（用户 ID: {sender_id}）：\n"
        f"{format_message_content(raw_message, message.get('message', []))}\n"
    )
    return formatted_message

def format_message_content(raw_message: str, message_elements: list) -> str:
    """格式化消息内容（处理图片、表情等）"""
    # 替换 CQ 码
    formatted_message = raw_message
    
    # 替换 CQ 码中的图片
    for element in message_elements:
        if element.get("type") == "image":
            file_url = element.get("data", {}).get("url", "")
            formatted_message += f"\n![图片]({file_url})"
        
        # 替换 CQ 码中的表情
        elif element.get("type") == "face":
            face_id = element.get("data", {}).get("id", "")
            formatted_message += f"\n[表情 {face_id}]"
    
    return formatted_message

async def main():
    """主函数，创建任务并启动处理"""
    tasks = [asyncio.create_task(handle_onebot(ws_url)) for ws_url in ONEBOT_WS_URLS]
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
