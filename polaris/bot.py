from polaris.types import AutosaveDict, Message, Conversation
from polaris.utils import set_logger, is_int, load_plugin_list, get_step, cancel_steps, get_plugin_name
from multiprocessing import Process, Queue
from threading import Thread
from time import sleep
import importlib, logging, time, re, traceback, sys, os, json


class Bot(object):
    def __init__(self, name):
        self.name = name
        self.config = AutosaveDict('bots/%s.json' % self.name)
        self.trans = AutosaveDict('polaris/translations/%s.json' % self.config.translation)
        self.bindings = importlib.import_module('polaris.bindings.%s' % self.config.bindings).bindings(self)
        self.inbox = Queue()
        self.outbox = Queue()
        self.started = False
        self.plugins = None
        self.info = self.bindings.get_me()
        
        if self.info is None:
            raise Exception


    def sender_worker(self):
        try:
            logging.debug('Starting sender worker...')
            while self.started:
                msg = self.outbox.get()
                logging.info(' \x1b[1;32m%s\x1b[1;37m@\x1b[1;33m%s \x1b[1;37msent [%s]: \x1b[0;34m%s\x1b[0;0m' % (msg.sender.first_name, msg.conversation.title, msg.type, msg.content))
                self.bindings.send_message(msg)
        except KeyboardInterrupt:
            pass


    def messages_handler(self):
        try:
            logging.debug('Starting message handler...')
            while self.started:
                msg = self.inbox.get()
                try:
                    logging.info(' \x1b[1;32m%s\x1b[1;37m@\x1b[1;33m%s \x1b[1;37msent [%s]: \x1b[0;34m%s\x1b[0;0m' % (msg.sender.first_name, msg.conversation.title, msg.type, msg.content))
                except AttributeError:
                    logging.info(' \x1b[1;32m%s\x1b[1;37m@\x1b[1;33m%s \x1b[1;37msent [%s]: \x1b[0;34m%s\x1b[0;0m' % (msg.sender.title, msg.conversation.title, msg.type, msg.content))

                self.on_message_receive(msg)

        except KeyboardInterrupt:
            pass


    def start(self):
        self.started = True
        self.plugins = self.init_plugins()

        logging.info('Connected as %s (@%s)' % (self.info.first_name, self.info.username))

        jobs = []
        jobs.append(Process(target=self.bindings.receiver_worker, name='%s R.' % self.name))
        jobs.append(Process(target=self.sender_worker, name='%s S.' % self.name))
        jobs.append(Process(target=self.cron_jobs, name='%s' % self.name))

        for job in jobs:
            job.daemon = True
            job.start()

        Process(target=self.messages_handler, name='%s' % self.name).start()


    def stop(self):
        self.started = False


    def init_plugins(self):
        plugins = []

        logging.debug('Importing plugins...')

        if type(self.config.plugins) is list:
            plugins_to_load = self.config.plugins
        elif self.config.plugins == 'all':
            plugins_to_load = load_plugin_list()
        else:
            plugins_to_load = load_plugin_list()

        for plugin in plugins_to_load:
            try:
                plugins.append(importlib.import_module('polaris.plugins.' + plugin).plugin(self))
                logging.debug('  [OK] %s ' % (plugin))
            except Exception as e:
                logging.error('  [Failed] %s - %s ' % (plugin, str(e)))

        logging.debug('  Loaded: ' + str(len(plugins)) + '/' + str(len(plugins_to_load)))

        return plugins


    def on_message_receive(self, msg):
        try:
            triggered = False

            if msg.content == None:
                return

            step = get_step(self, msg.conversation.id)

            if step:
                for plugin in self.plugins:
                    if get_plugin_name(plugin) == step['plugin'] and hasattr(plugin, 'steps'):
                        if msg.content.startswith('/next'):
                            plugin.steps(msg, -1)
                            cancel_steps(self, msg.conversation.id)

                        if msg.content.startswith('/done'):
                            plugin.steps(msg, 0)
                            cancel_steps(self, msg.conversation.id)

                        else:
                            plugin.steps(msg, step['step'])

            else:
                for plugin in self.plugins:
                    # Always do this action for every message. #
                    if hasattr(plugin, 'always'):
                        plugin.always(msg)

                    # If no query show help #
                    if msg.type == 'inline_query':
                        if msg.content == '':
                            msg.content = '/help'

                    # Check if any command of a plugin matches. #
                    for command in plugin.commands:
                        if 'command' in command:
                            if self.check_trigger(command['command'], msg, plugin):
                                break

                        if 'friendly' in command:
                            if self.check_trigger(command['friendly'], msg, plugin):
                                break

                        if 'shortcut' in command:
                            if len(command['shortcut']) < 3:
                                shortcut = command['shortcut'] + ' '
                            else:
                                shortcut = command['shortcut']

                            if self.check_trigger(shortcut, msg, plugin):
                                break

        except Exception as e:
            logging.exception(traceback.format_exc())
            self.send_alert(traceback.format_exc())


    def check_trigger(self, command, message, plugin):
        if isinstance(command, str):
            command = command.lower()

            # If the commands are not /start or /help, set the correct command start symbol. #
            if ((command == '/start' and '/start' in message.content) or
               (command == '/ayuda' and '/ayuda' in message.content)):
                trigger = command.replace('/', '^/')
            else:
                trigger = command.replace('/', '^' + self.config.prefix)

            if message.content and isinstance(message.content, str) and re.compile(trigger).search(message.content.lower()):
                if message.type == 'inline_query':
                    if hasattr(plugin, 'inline'):
                        plugin.inline(message)

                else:
                    plugin.run(message)

                return True


    def cron_jobs(self):
        try:
            while(self.started):
                for plugin in self.plugins:
                    if hasattr(plugin, 'cron'):
                        plugin.cron()

                sleep(5)
        except KeyboardInterrupt:
            pass


    # METHODS TO MANAGE MESSAGES #
    def send_message(self, msg, content, type='text', reply=None, extra=None):
        message = Message(None, msg.conversation, self.info, content, type, reply=reply, extra=extra)
        self.outbox.put(message)


    def forward_message(self, msg, id):
        self.outbox.put(Message(None, msg.conversation, self.info, msg.content, 'forward',
                                extra={"message": msg.id, "conversation": id}))

    def answer_inline_query(self, msg, results, extra):
        self.outbox.put(Message(msg.id, msg.conversation, self.info, json.dumps(results), 'inline_results', extra))


    # THESE METHODS DO DIRECT ACTIONS #
    def get_file(self, file_id):
        return self.bindings.get_file(file_id)


    def invite_user(self, msg, user_id):
        return self.bindings.invite_conversation_member(msg.conversation.id, user_id)


    def kick_user(self, msg, user_id):
        return self.bindings.kick_conversation_member(msg.conversation.id, user_id)


    def unban_user(self, msg, user_id):
        return self.bindings.unban_conversation_member(msg.conversation.id, user_id)


    def conversation_info(self, conversation_id):
        return self.bindings.conversation_info(conversation_id)


    def send_alert(self, text):
        message = Message(None, Conversation(self.config.alerts_conversation_id, 'Alerts'), self.info, '<pre>%s</pre>' % text, extra={'format': 'HTML', 'preview': False})
        self.outbox.put(message)
