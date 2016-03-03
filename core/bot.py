from core.utils import *
from threading import Thread
from time import time
import re

def start():
    setup()

    bot.bindings.get_me()
    print('Account: [%s] %s (@%s)' % (bot.id, bot.first_name, bot.username))

    Thread(target=bot.bindings.inbox_listener, name='Inbox Listener').start()
    Thread(target=outbox_listener, name='Outbox Listener').start()

    color = Colors()
    while (started):
        message = inbox.get()
        
        # Ignores old messages
        if message.date < time() - 10:
            return

        if message.type == 'text':
            if message.receiver.id > 0:
                print('%s[%s << %s] %s%s' % (color.OKGREEN, message.receiver.first_name, message.sender.first_name, message.content, color.ENDC))
            else:
                print('%s[%s << %s] %s%s' % (color.OKGREEN, message.receiver.title, message.sender.first_name, message.content, color.ENDC))
        else:
            if message.receiver.id > 0:
                print('%s[%s << %s] <%s>%s' % (color.OKGREEN, message.receiver.first_name, message.sender.first_name, message.type, color.ENDC))
            else:
                print('%s[%s << %s] <%s>%s' % (color.OKGREEN, message.receiver.title, message.sender.first_name, message.type, color.ENDC))
        
        for plugin in plugins:
            for command, parameters in plugin.commands:
                trigger = command.replace('/', '^' + config.start)

                if re.compile(trigger).search(message.content.lower()):
                    try:
                        if hasattr(plugin, 'inline') and message.type == 'inline_query':
                            plugin.inline(message)
                        else:
                            plugin.run(message)
                    except:
                        send_exception(message)


def setup():
    print('Loading configuration...')
    config.load(config)
    users.load(users)
    groups.load(groups)

    if not config.keys.bot_api_token and not config.keys.tg_cli_port:
        print('\nBindings not configured!')
        print('\tSelect the bindings to use:\n\t\t0. Telegram Bot API\n\t\t1. Telegram-CLI')
        frontend = input('\tBindings: ')
        if frontend == '1':
            config.keys.tg_cli_port = input('\tTelegram-CLI port: ')
            config.bindings = 'tg'
        else:
            config.keys.bot_api_token = input('\tTelegram Bot API token: ')
            config.bindings = 'api'
        config.plugins = list_plugins()
        config.save(config)
    else:
        if config.bindings == 'api' and config.keys.bot_api_token:
            print('\nUsing Telegram Bot API token: {}'.format(config.keys.bot_api_token))
        elif config.bindings == 'tg' and config.keys.tg_cli_port:
            print('\nUsing Telegram-CLI port: {}'.format(config.keys.tg_cli_port))

    load_plugins()

    bot.set_bindings(config.bindings)


def list_plugins():
    list = []
    for file in os.listdir('plugins'):
        if file.endswith('.py'):
            list.append(file.rstrip('.py'))
    return list


def load_plugins():
    print('\nLoading plugins...')
    for plugin in config.plugins:
        try:
            plugins.append(importlib.import_module('plugins.' + plugin))
            print('\t[OK] ' + plugin)
        except Exception as e:
            print('\t[Failed] ' + plugin + ': ' + str(e))

    print('\tLoaded: ' + str(len(plugins)) + '/' + str(len(config.plugins)))
    return plugins


def outbox_listener():
    color = Colors()
    while (started):
        message = outbox.get()
        if message.type == 'text':
            if message.receiver.id > 0:
                print('{3}>> [{0} << {2}] {1}{4}'.format(message.receiver.first_name, message.content,
                                                   message.sender.first_name, color.OKBLUE, color.ENDC))
            else:
                print('{3}>> [{0} << {2}] {1}{4}'.format(message.receiver.title, message.content,
                                                   message.sender.first_name, color.OKBLUE, color.ENDC))
        else:
            if message.receiver.id > 0:
                print('{3}>> [{0} << {2}] <{1}>{4}'.format(message.receiver.first_name, message.type,
                                                     message.sender.first_name, color.OKBLUE, color.ENDC))
            else:
                print('{3}>> [{0} << {2}] <{1}>{4}'.format(message.receiver.title, message.type, message.sender.first_name, color.OKBLUE, color.ENDC))
        bot.bindings.send_message(message)