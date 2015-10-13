from __main__ import *
from utilies import *

triggers = {
	''
}

def action(msg):
	if msg.chat.id != config.admin_group:
		if msg.text != '':
			if msg.chat.id != msg.from_user.id and msg.chat.type=='private':
				msg.chat.title = msg.chat.first_name
			
			message = msg.text.replace(bot.first_name + ' ', '')
			message += '\n------------------------\n'

			if msg.from_user.username:
				message += '*Name*: [' + msg.from_user.first_name.replace("_", "\_") + '](http://telegram.me/' + msg.from_user.username.replace("_", "\_") + ')\n'
			else:
				message += '*Name*: ' + msg.from_user.first_name.replace("_", "\_") + '\n'
				
			message += '*User ID*: ' + str(msg.from_user.id) + '\n'
			
			if msg.chat.type == 'group':
				message += '*Group*: ' + msg.chat.title.replace("_", "\_") + '\n'
				message += '*Group ID*: ' + str(msg.chat.id) + '\n'
			message += '*Message ID*: ' + str(msg.message_id)
			
			core.send_message(config.admin_group, message, parse_mode="Markdown")
		else:
			core.forward_message(config.admin_group, msg.chat.id, msg.message_id)
		
	else:
		if hasattr(msg, 'reply_to_message') and msg.reply_to_message.from_user.id == bot.id:
			message_id = last_word(msg.reply_to_message.text.split('\n')[-1])
			chat_id = last_word(msg.reply_to_message.text.split('\n')[-2])
			core.send_message(chat_id, msg.text, reply_to_message_id=message_id, parse_mode="Markdown")