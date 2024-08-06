#!/usr/bin/env python3

import asyncio
import json
import logging
from websockets import connect
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from retrying import retry

# 配置日志记录
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Telegram 机器人 Token 和 OneBot WebSocket URL 列表
TELEGRAM_BOT_TOKEN = ''
ONEBOT_WS_URLS = {
    'backend1': "ws://:3000",
    'backend2': "ws://:3001"
}

# 初始化 Telegram 机器人
bot = Bot(token=TELEGRAM_BOT_TOKEN)

async def send_to_onebot(target_id: str, message: str, media_type: str, media_url: str, ws_url: str):
    """将消息或媒体发送到指定的 OneBot 后端"""
    logger.info(f"尝试连接到 OneBot WebSocket 服务器: {ws_url}")
    try:
        async with connect(ws_url) as websocket:
            message_type = "private" if target_id.startswith("user_") else "group"
            send_data = {
                "action": "send_private_msg" if message_type == "private" else "send_group_msg",
                "params": {
                    "user_id": int(target_id.replace("user_", "")) if message_type == "private" else None,
                    "group_id": int(target_id.replace("group_", "")) if message_type == "group" else None,
                    "message": message
                },
                "echo": "unique_id"
            }
            if media_type in ["photo", "video", "audio", "document"]:
                send_data["params"]["message"] = {
                    "type": media_type,
                    "url": media_url
                }
            logger.info(f"发送数据到 OneBot: {json.dumps(send_data)}")
            await websocket.send(json.dumps(send_data))
            response = await websocket.recv()  # 接收回应以确保消息成功发送
            logger.info(f"消息已发送到 OneBot: 目标 ID = {target_id}, 消息 = {message}, 后端 URL = {ws_url}")
            logger.info(f"OneBot 回复: {response}")
    except Exception as e:
        logger.error(f"发送消息到 OneBot 时发生错误: {e}")

@retry(stop_max_attempt_number=3, wait_fixed=2000)
async def send_to_onebot_with_retries(target_id: str, message: str, media_type: str, media_url: str, ws_url: str):
    """带重试机制的发送消息到 OneBot 后端"""
    logger.info(f"尝试连接到 OneBot WebSocket 服务器: {ws_url}")
    try:
        async with connect(ws_url) as websocket:
            message_type = "private" if target_id.startswith("user_") else "group"
            send_data = {
                "action": "send_private_msg" if message_type == "private" else "send_group_msg",
                "params": {
                    "user_id": int(target_id.replace("user_", "")) if message_type == "private" else None,
                    "group_id": int(target_id.replace("group_", "")) if message_type == "group" else None,
                    "message": message
                },
                "echo": "unique_id"
            }
            if media_type in ["photo", "video", "audio", "document"]:
                send_data["params"]["message"] = {
                    "type": media_type,
                    "url": media_url
                }
            logger.info(f"发送数据到 OneBot: {json.dumps(send_data)}")
            await websocket.send(json.dumps(send_data))
            response = await websocket.recv()
            logger.info(f"消息已发送到 OneBot: 目标 ID = {target_id}, 消息 = {message}, 后端 URL = {ws_url}")
            logger.info(f"OneBot 回复: {response}")
    except Exception as e:
        logger.error(f"发送消息到 OneBot 时发生错误: {e}")
        raise

async def delete_message(target_id: str, message_id: str, ws_url: str):
    """删除指定的消息"""
    logger.info(f"尝试连接到 OneBot WebSocket 服务器: {ws_url}")
    try:
        async with connect(ws_url) as websocket:
            message_type = "private" if target_id.startswith("user_") else "group"
            delete_data = {
                "action": "delete_private_msg" if message_type == "private" else "delete_group_msg",
                "params": {
                    "user_id": int(target_id.replace("user_", "")) if message_type == "private" else None,
                    "group_id": int(target_id.replace("group_", "")) if message_type == "group" else None,
                    "message_id": int(message_id)
                },
                "echo": "unique_id"
            }
            logger.info(f"发送数据到 OneBot: {json.dumps(delete_data)}")
            await websocket.send(json.dumps(delete_data))
            response = await websocket.recv()
            logger.info(f"消息已删除: 目标 ID = {target_id}, 消息 ID = {message_id}, 后端 URL = {ws_url}")
            logger.info(f"OneBot 回复: {response}")
    except Exception as e:
        logger.error(f"删除消息时发生错误: {e}")

async def get_message(target_id: str, message_id: str, ws_url: str):
    """获取指定的消息"""
    logger.info(f"尝试连接到 OneBot WebSocket 服务器: {ws_url}")
    try:
        async with connect(ws_url) as websocket:
            message_type = "private" if target_id.startswith("user_") else "group"
            get_data = {
                "action": "get_private_msg" if message_type == "private" else "get_group_msg",
                "params": {
                    "user_id": int(target_id.replace("user_", "")) if message_type == "private" else None,
                    "group_id": int(target_id.replace("group_", "")) if message_type == "group" else None,
                    "message_id": int(message_id)
                },
                "echo": "unique_id"
            }
            logger.info(f"发送数据到 OneBot: {json.dumps(get_data)}")
            await websocket.send(json.dumps(get_data))
            response = await websocket.recv()
            logger.info(f"消息已获取: 目标 ID = {target_id}, 消息 ID = {message_id}, 后端 URL = {ws_url}")
            logger.info(f"OneBot 回复: {response}")
    except Exception as e:
        logger.error(f"获取消息时发生错误: {e}")

async def forward_message(source_target_id: str, dest_target_id: str, message_id: str, ws_url: str):
    """将消息从一个 chat 转发到另一个 chat"""
    logger.info(f"尝试连接到 OneBot WebSocket 服务器: {ws_url}")
    try:
        async with connect(ws_url) as websocket:
            message_type = "private" if source_target_id.startswith("user_") else "group"
            forward_data = {
                "action": "forward_private_msg" if message_type == "private" else "forward_group_msg",
                "params": {
                    "source_user_id": int(source_target_id.replace("user_", "")) if message_type == "private" else None,
                    "source_group_id": int(source_target_id.replace("group_", "")) if message_type == "group" else None,
                    "target_user_id": int(dest_target_id.replace("user_", "")) if dest_target_id.startswith("user_") else None,
                    "target_group_id": int(dest_target_id.replace("group_", "")) if dest_target_id.startswith("group_") else None,
                    "message_id": int(message_id)
                },
                "echo": "unique_id"
            }
            logger.info(f"发送数据到 OneBot: {json.dumps(forward_data)}")
            await websocket.send(json.dumps(forward_data))
            response = await websocket.recv()
            logger.info(f"消息已转发: 从 {source_target_id} 到 {dest_target_id}, 消息 ID = {message_id}, 后端 URL = {ws_url}")
            logger.info(f"OneBot 回复: {response}")
    except Exception as e:
        logger.error(f"转发消息时发生错误: {e}")

async def send(update: Update, context: CallbackContext):
    """处理 Telegram /send 命令并转发到所选的 OneBot 后端"""
    logger.info(f"收到 /send 命令: {update.message.text}")
    args = context.args

    if len(args) < 3:
        await update.message.reply_text("请使用格式 `/send <backend> <chat_id> <message>` 发送消息。")
        return

    backend = args[0].strip()
    target_id = args[1].strip()
    message_content = " ".join(args[2:]).strip()

    ws_url = ONEBOT_WS_URLS.get(backend)
    if not ws_url:
        await update.message.reply_text("无效的后端选择。请使用 `backend1` 或 `backend2`。")
        return

    if not (target_id.startswith("group_") or target_id.startswith("user_")):
        await update.message.reply_text("目标 ID 必须以 'group_' 或 'user_' 开头。")
        return

    media_type = None
    media_url = None
    if update.message.photo:
        media_type = "photo"
        media_url = update.message.photo[-1].file_id
    elif update.message.video:
        media_type = "video"
        media_url = update.message.video.file_id
    elif update.message.audio:
        media_type = "audio"
        media_url = update.message.audio.file_id
    elif update.message.document:
        media_type = "document"
        media_url = update.message.document.file_id

    logger.info(f"将消息发送到 OneBot：目标 ID = {target_id}, 消息 = {message_content}, 后端 URL = {ws_url}")
    await send_to_onebot_with_retries(target_id, message_content, media_type, media_url, ws_url)
    await update.message.reply_text(f"消息已发送到 {target_id}")

async def handle_message(update: Update, context: CallbackContext):
    """处理 Telegram 消息并转发到所选的 OneBot 后端"""
    # Handle the /send command separately

async def start(update: Update, context: CallbackContext):
    """发送欢迎消息"""
    await update.message.reply_text("Bot 已启动。使用 `/send <backend> <chat_id> <message>` 命令来发送消息。\n"
                                   "使用 `/delete <backend> <chat_id> <message_id>` 删除消息。\n"
                                   "使用 `/get <backend> <chat_id> <message_id>` 获取消息。\n"
                                   "使用 `/forward <source_chat_id> <dest_chat_id> <message_id>` 转发消息。\n"
                                   "`/status` 查看 Bot 状态")

async def status(update: Update, context: CallbackContext):
    """显示 Bot 当前状态"""
    status_text = (
        "Bot 正在运行。\n"
        "支持的命令:\n"
        "`/send <backend> <chat_id> <message>` 发送消息\n"
        "`/delete <backend> <chat_id> <message_id>` 删除消息\n"
        "`/get <backend> <chat_id> <message_id>` 获取消息\n"
        "`/forward <source_chat_id> <dest_chat_id> <message_id>` 转发消息\n"
        "`/status` 查看 Bot 状态"
    )
    await update.message.reply_text(status_text)

def main():
    """主函数，设置 Telegram 机器人并开始监听消息"""
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # 添加处理消息的处理器
    application.add_handler(CommandHandler('send', send))
    application.add_handler(CommandHandler('delete', delete))
    application.add_handler(CommandHandler('get', get))
    application.add_handler(CommandHandler('forward', forward))
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('status', status))
    
    # 启动 Telegram 机器人
    application.run_polling()
    
if __name__ == "__main__":
    asyncio.run(main())
