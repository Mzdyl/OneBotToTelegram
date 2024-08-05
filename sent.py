#!/usr/bin/env python3

import asyncio
import json
import logging
from websockets import connect
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# 配置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Telegram 机器人 Token 和 OneBot WebSocket URL 列表
TELEGRAM_BOT_TOKEN = ''
ONEBOT_WS_URLS = {
	'backend1': "ws://:3000",
	'backend2': "ws://:3001"
}

# 初始化 Telegram 机器人
bot = Bot(token=TELEGRAM_BOT_TOKEN)

async def send_to_onebot(target_id: str, message: str, ws_url: str):
	"""将消息发送到指定的 OneBot 后端"""
	logger.info(f"尝试连接到 OneBot WebSocket 服务器: {ws_url}")
	try:
		async with connect(ws_url) as websocket:
			# 根据目标 ID 确定消息类型
			message_type = "private" if target_id.startswith("user_") else "group"
			send_data = {
				"action": "send_private_msg" if message_type == "private" else "send_group_msg",
				"params": {
					"user_id": int(target_id.replace("user_", "")) if message_type == "private" else None,
					"group_id": int(target_id.replace("group_", "")) if message_type == "group" else None,
					"message": message
				},
				"echo": "unique_id"  # 可以替换为唯一的标识符
			}
			logger.info(f"发送数据到 OneBot: {json.dumps(send_data)}")
			await websocket.send(json.dumps(send_data))
			response = await websocket.recv()  # 接收回应以确保消息成功发送
			logger.info(f"消息已发送到 OneBot: 目标 ID = {target_id}, 消息 = {message}, 后端 URL = {ws_url}")
			logger.info(f"OneBot 回复: {response}")
	except Exception as e:
		logger.error(f"发送消息到 OneBot 时发生错误: {e}")
		
async def handle_message(update: Update, context: CallbackContext):
	"""处理 Telegram 消息并转发到所选的 OneBot 后端"""
	logger.info(f"收到消息: {update.message.text}")
	logger.info(f"消息详情: {update.message}")
	
	text = update.message.text
	
	# 提取后端标识符、目标 chat_id 和消息内容
	parts = text.split(maxsplit=2)
	if len(parts) < 3:
		await update.message.reply_text("请使用格式 `send <backend> <chat_id> <message>` 发送消息。")
		return
	
	backend = parts[1].strip()
	target_id = parts[2].split(maxsplit=1)[0].strip()
	message = parts[2].split(maxsplit=1)[1].strip()
	
	# 确认后端标识符是否有效
	ws_url = ONEBOT_WS_URLS.get(backend)
	if not ws_url:
		await update.message.reply_text("无效的后端选择。请使用 `backend1` 或 `backend2`。")
		return
	
	# 确认目标 ID 格式正确
	if not (target_id.startswith("group_") or target_id.startswith("user_")):
		await update.message.reply_text("目标 ID 必须以 'group_' 或 'user_' 开头。")
		return
	
	logger.info(f"将消息发送到 OneBot：目标 ID = {target_id}, 消息 = {message}, 后端 URL = {ws_url}")
	
	# 将消息发送到 OneBot
	await send_to_onebot(target_id, message, ws_url)
	await update.message.reply_text(f"消息已发送到 {target_id}")
	
async def start(update: Update, context: CallbackContext):
	"""发送欢迎消息"""
	await update.message.reply_text("Bot 已启动。使用 `send <backend> <chat_id> <message>` 命令来发送消息。")
	
def main():
	"""主函数，设置 Telegram 机器人并开始监听消息"""
	application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
	
	# 添加处理消息的处理器
	application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
	application.add_handler(CommandHandler('start', start))
	
	# 启动 Telegram 机器人
	application.run_polling()
	
if __name__ == "__main__":
	asyncio.run(main())
	