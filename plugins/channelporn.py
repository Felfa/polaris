from __main__ import *
from utilies import *

triggers = {
	''
}

def action(msg):
		if (msg.chat.id == -27616291
		and not msg.text
		and not hasattr(msg, 'new_chat_participant')
		and not hasattr(msg, 'left_chat_participant')):
			core.forward_message('@porndb',  msg.chat.id, msg.message_id)