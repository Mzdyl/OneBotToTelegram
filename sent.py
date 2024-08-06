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
    message_content = ' '.join(args[2:]).strip()

    ws_url = ONEBOT_WS_URLS.get(backend)
    if not ws_url:
        await update.message.reply_text("无效的后端选择。请使用 `backend1` 或 `backend2`。")
        return

    # 检查是否有媒体文件
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

async def get_login_info(update: Update, context: CallbackContext):
    """获取登录号信息"""
    backend = context.args[0].strip()
    ws_url = ONEBOT_WS_URLS.get(backend)
    if not ws_url:
        await update.message.reply_text("无效的后端选择。")
        return

    await get_info("get_login_info", {}, ws_url, update)

async def get_stranger_info(update: Update, context: CallbackContext):
    """获取陌生人信息"""
    user_id = context.args[0].strip()
    backend = context.args[1].strip()
    ws_url = ONEBOT_WS_URLS.get(backend)
    if not ws_url:
        await update.message.reply_text("无效的后端选择。")
        return

    await get_info("get_stranger_info", {"user_id": user_id}, ws_url, update)

async def get_friend_list(update: Update, context: CallbackContext):
    """获取好友列表"""
    backend = context.args[0].strip()
    ws_url = ONEBOT_WS_URLS.get(backend)
    if not ws_url:
        await update.message.reply_text("无效的后端选择。")
        return

    await get_info("get_friend_list", {}, ws_url, update)

async def get_group_info(update: Update, context: CallbackContext):
    """获取群信息"""
    group_id = context.args[0].strip()
    backend = context.args[1].strip()
    ws_url = ONEBOT_WS_URLS.get(backend)
    if not ws_url:
        await update.message.reply_text("无效的后端选择。")
        return

    await get_info("get_group_info", {"group_id": group_id}, ws_url, update)

async def get_group_list(update: Update, context: CallbackContext):
    """获取群列表"""
    backend = context.args[0].strip()
    ws_url = ONEBOT_WS_URLS.get(backend)
    if not ws_url:
        await update.message.reply_text("无效的后端选择。")
        return

    await get_info("get_group_list", {}, ws_url, update)

async def get_group_member_info(update: Update, context: CallbackContext):
    """获取群成员信息"""
    group_id = context.args[0].strip()
    user_id = context.args[1].strip()
    backend = context.args[2].strip()
    ws_url = ONEBOT_WS_URLS.get(backend)
    if not ws_url:
        await update.message.reply_text("无效的后端选择。")
        return

    await get_info("get_group_member_info", {"group_id": group_id, "user_id": user_id}, ws_url, update)

async def get_group_member_list(update: Update, context: CallbackContext):
    """获取群成员列表"""
    group_id = context.args[0].strip()
    backend = context.args[1].strip()
    ws_url = ONEBOT_WS_URLS.get(backend)
    if not ws_url:
        await update.message.reply_text("无效的后端选择。")
        return

    await get_info("get_group_member_list", {"group_id": group_id}, ws_url, update)

async def get_record(update: Update, context: CallbackContext):
    """获取语音"""
    record_id = context.args[0].strip()
    backend = context.args[1].strip()
    ws_url = ONEBOT_WS_URLS.get(backend)
    if not ws_url:
        await update.message.reply_text("无效的后端选择。")
        return

    await get_info("get_record", {"record_id": record_id}, ws_url, update)

async def get_image(update: Update, context: CallbackContext):
    """获取图片"""
    image_id = context.args[0].strip()
    backend = context.args[1].strip()
    ws_url = ONEBOT_WS_URLS.get(backend)
    if not ws_url:
        await update.message.reply_text("无效的后端选择。")
        return

    await get_info("get_image", {"image_id": image_id}, ws_url, update)

async def can_send_image(update: Update, context: CallbackContext):
    """检查是否可以发送图片"""
    backend = context.args[0].strip()
    ws_url = ONEBOT_WS_URLS.get(backend)
    if not ws_url:
        await update.message.reply_text("无效的后端选择。")
        return

    await get_info("can_send_image", {}, ws_url, update)

async def can_send_record(update: Update, context: CallbackContext):
    """检查是否可以发送语音"""
    backend = context.args[0].strip()
    ws_url = ONEBOT_WS_URLS.get(backend)
    if not ws_url:
        await update.message.reply_text("无效的后端选择。")
        return

    await get_info("can_send_record", {}, ws_url, update)

async def get_status(update: Update, context: CallbackContext):
    """获取运行状态"""
    backend = context.args[0].strip()
    ws_url = ONEBOT_WS_URLS.get(backend)
    if not ws_url:
        await update.message.reply_text("无效的后端选择。")
        return

    await get_info("get_status", {}, ws_url, update)

async def get_version_info(update: Update, context: CallbackContext):
    """获取版本信息"""
    backend = context.args[0].strip()
    ws_url = ONEBOT_WS_URLS.get(backend)
    if not ws_url:
        await update.message.reply_text("无效的后端选择。")
        return

    await get_info("get_version_info", {}, ws_url, update)


async def get_info(action: str, params: dict, ws_url: str, update: Update):
    """获取信息"""
    logger.info(f"尝试连接到 OneBot WebSocket 服务器: {ws_url}")
    try:
        async with connect(ws_url) as websocket:
            # 确保连接成功
#           await asyncio.sleep(1)  # 等待连接建立
            
            get_data = {
                "action": action,
                "params": params,
                "echo": "unique_id"
            }
            logger.info(f"发送数据到 OneBot: {json.dumps(get_data)}")
            await websocket.send(json.dumps(get_data))
            
            # 收到连接确认
            while True:
                response = await websocket.recv()
                response_data = json.loads(response)
                
                # 处理生命周期事件
                if response_data.get("post_type") == "meta_event" and response_data.get("meta_event_type") == "lifecycle":
                    logger.info(f"连接生命周期事件: {response_data}")
                    if response_data.get("sub_type") == "connect":
                        logger.info("连接已建立，等待实际响应...")
                    continue  # 继续接收下一个消息
                
                # 处理实际响应
                logger.info(f"OneBot 回复: {response_data}")
                await update.message.reply_text(f"OneBot 回复: {response_data}")
                break
            
    except asyncio.TimeoutError:
        logger.error("请求超时")
    except Exception as e:
        logger.error(f"获取信息时发生错误: {e}")
        

async def start(update: Update, context: CallbackContext):
    """发送欢迎消息"""
    await update.message.reply_text("Bot 已启动。使用以下命令：\n"
                                   "`/send <backend> <chat_id> <message>` 发送消息\n"
                                   "`/delete <backend> <chat_id> <message_id>` 删除消息\n"
                                   "`/get <backend> <chat_id> <message_id>` 获取消息\n"
                                   "`/forward <source_chat_id> <dest_chat_id> <message_id>` 转发消息\n"
                                   "`/get_login_info <backend>` 获取登录号信息\n"
                                   "`/get_stranger_info <user_id> <backend>` 获取陌生人信息\n"
                                   "`/get_friend_list <backend>` 获取好友列表\n"
                                   "`/get_group_info <group_id> <backend>` 获取群信息\n"
                                   "`/get_group_list <backend>` 获取群列表\n"
                                   "`/get_group_member_info <group_id> <user_id> <backend>` 获取群成员信息\n"
                                   "`/get_group_member_list <group_id> <backend>` 获取群成员列表\n"
                                   "`/get_record <record_id> <backend>` 获取语音\n"
                                   "`/get_image <image_id> <backend>` 获取图片\n"
                                   "`/can_send_image <backend>` 检查是否可以发送图片\n"
                                   "`/can_send_record <backend>` 检查是否可以发送语音\n"
                                   "`/get_status <backend>` 获取运行状态\n"
                                   "`/get_version_info <backend>` 获取版本信息")

def main():
    """主函数，设置 Telegram 机器人并开始监听消息"""
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # 添加处理消息的处理器
    application.add_handler(CommandHandler('send', send))
    application.add_handler(CommandHandler('delete', delete_message))
    application.add_handler(CommandHandler('get', get_message))
    application.add_handler(CommandHandler('forward', forward_message))
    application.add_handler(CommandHandler('get_login_info', get_login_info))
    application.add_handler(CommandHandler('get_stranger_info', get_stranger_info))
    application.add_handler(CommandHandler('get_friend_list', get_friend_list))
    application.add_handler(CommandHandler('get_group_info', get_group_info))
    application.add_handler(CommandHandler('get_group_list', get_group_list))
    application.add_handler(CommandHandler('get_group_member_info', get_group_member_info))
    application.add_handler(CommandHandler('get_group_member_list', get_group_member_list))
    application.add_handler(CommandHandler('get_record', get_record))
    application.add_handler(CommandHandler('get_image', get_image))
    application.add_handler(CommandHandler('can_send_image', can_send_image))
    application.add_handler(CommandHandler('can_send_record', can_send_record))
    application.add_handler(CommandHandler('get_status', get_status))
    application.add_handler(CommandHandler('get_version_info', get_version_info))
    application.add_handler(CommandHandler('start', start))
    
    # 启动 Telegram 机器人
    application.run_polling()
    
if __name__ == "__main__":
    asyncio.run(main())
    