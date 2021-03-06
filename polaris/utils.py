from polaris.types import json2obj
from html.parser import HTMLParser
from DictObject import DictObject
from polaris.types import AutosaveDict
from re import compile
import logging, requests, json, magic, mimetypes, tempfile, os, subprocess, re


def get_input(message, ignore_reply=True):
    if message.type == 'text' or message.type == 'inline_query':
        text = message.content
    else:
        return None

    if not ignore_reply and message.reply and message.reply.type == 'text':
        text += ' ' + message.reply.content

    if not ' ' in text:
        return None

    return text[text.find(" ") + 1:]


def get_command(message):
    if message.content.startswith(config.start):
        command = first_word(message.content).lstrip(config.start)
        return command.replace('@' + bot.username, '')
    elif message.type == 'inline_query':
        return first_word(message.content)
    else:
        return None


def is_command(self, number, text):
    if 'command' in self.commands[number - 1]:
        trigger = self.commands[number - 1]['command'].replace('/', self.bot.config.prefix).lower()
        if compile(trigger).search(text.lower()):
            return True

    if 'friendly' in self.commands[number - 1]:
        trigger = self.commands[number - 1]['friendly'].replace('/', self.bot.config.prefix).lower()
        if compile(trigger).search(text.lower()):
            return True

    if 'shortcut' in self.commands[number - 1]:
        trigger = self.commands[number - 1]['shortcut'].replace('/', self.bot.config.prefix).lower()
        if len(self.commands[number - 1]['shortcut']) < 3:
            trigger += ' '
        if compile(trigger).search(text.lower()):
            return True

    return False


def set_setting(bot, uid, key, value):
    settings = AutosaveDict('polaris/data/%s.settings.json' % bot.name)

    if not isinstance(uid, str):
        uid = str(uid)

    if not uid in settings:
        settings[uid] = {}
    settings[uid][key] = value
    settings.store_database()


def get_setting(bot, uid, key):
    settings = AutosaveDict('polaris/data/%s.settings.json' % bot.name)

    if not isinstance(uid, str):
        uid = str(uid)

    try:
        return settings[uid][key]
    except:
        return None


def del_setting(bot, uid, key):
    settings = AutosaveDict('polaris/data/%s.settings.json' % bot.name)

    if not isinstance(uid, str):
        uid = str(uid)

    del(settings[uid][key])
    settings.store_database()


def has_tag(bot, target, tag, return_match = False):
    tags = AutosaveDict('polaris/data/%s.tags.json' % bot.name)

    if not isinstance(target, str):
        target = str(target)

    if target in tags and '?' in tag:
        for target_tag in tags[target]:
            if target_tag.startswith(tag.split('?')[0]):
                if return_match:
                    return target_tag

                else:
                    return True

        return False

    elif target in tags and tag in tags[target]:
        return True

    else:
        return False


def set_tag(bot, target, tag):
    tags = AutosaveDict('polaris/data/%s.tags.json' % bot.name)

    if not isinstance(target, str):
        target = str(target)

    if not target in tags:
        tags[target] = []

    if not tag in tags[target]:
        tags[target].append(tag)
        tags.store_database()


def del_tag(bot, target, tag):
    tags = AutosaveDict('polaris/data/%s.tags.json' % bot.name)

    if not isinstance(target, str):
        target = str(target)

    tags[target].remove(tag)
    tags.store_database()


def is_admin(bot, uid):
    if not isinstance(uid, str):
        uid = str(uid)

    if str(bot.config.owner) == uid:
        return True

    elif has_tag(bot, uid, 'admin') or has_tag(bot, uid, 'owner'):
        return True

    else:
        return False


def is_trusted(bot, uid):
    if not isinstance(uid, str):
        uid = str(uid)

    if is_admin(bot, uid) or has_tag(bot, uid, 'trusted'):
        return True

    else:
        return False


def is_mod(bot, uid, gid):
    if not isinstance(uid, str):
        uid = str(uid)

    if is_trusted(bot, uid) or has_tag(bot, uid, 'globalmod') or has_tag(bot, uid, 'mod:%s' % gid):
        return True

    else:
        return False


def set_step(bot, target, plugin, step):
    steps = AutosaveDict('polaris/data/%s.steps.json' % bot.name)

    if not isinstance(target, str):
        target = str(target)

    steps[target] = {
        'plugin': plugin,
        'step': step
    }
    steps.store_database()


def get_step(bot, target):
    steps = AutosaveDict('polaris/data/%s.steps.json' % bot.name)

    if not isinstance(target, str):
        target = str(target)

    if not target in steps:
        return None
    else:
        return steps[target]


def cancel_steps(bot, target):
    steps = AutosaveDict('polaris/data/%s.steps.json' % bot.name)

    if not isinstance(target, str):
        target = str(target)

    if target in steps:
        del steps[target]
        steps.store_database()


def first_word(text, i=1):
    try:
        return text.split()[i - 1]
    except:
        return False


def all_but_first_word(text):
    if ' ' not in text:
        return False
    return text.split(' ', 1)[1]


def last_word(text):
    if ' ' not in text:
        return False
    return text.split()[-1]


def is_int(number):
    try:
        number = int(number)
        return True
    except:
        return False


def get_plugin_name(obj):
    return str(type(obj)).split('.')[2]


# Returns all plugin names from /polaris/plugins/ #
def load_plugin_list():
    plugin_list = []
    for plugin_name in os.listdir('polaris/plugins'):
        if plugin_name.endswith('.py'):
            plugin_list.append(plugin_name[:-3])
    return sorted(plugin_list)


def send_request(url, params=None, headers=None, files=None, data=None, post=False, parse=True, get_text=False):
    try:
        if post:
            r = requests.post(url, params=params, headers=headers, files=files, data=data, timeout=100)
        else:
            r = requests.get(url, params=params, headers=headers, files=files, data=data, timeout=100)
    except:
        logging.error('Error making request to: %s' % url)
        return None

    if r.status_code != 200:
        logging.error(r.text)
        while r.status_code == 429:
            r = r.get(url, params=params, headers=headers, files=files, data=data)
    try:
        if parse:
            return DictObject(json.loads(r.text))
        elif get_text:
            return r.text
        else:
            return r.url
    except:
        return None


def get_coords(input):
    url = 'http://maps.googleapis.com/maps/api/geocode/json'
    params = {'address': input}

    data = send_request(url, params=params)

    if not data or data['status'] == 'ZERO_RESULTS':
        return False, False, False, False

    locality = data.results[0].address_components[0].long_name
    for address in data.results[0].address_components:
        if 'country' in address['types']:
            country = address['long_name']

    return (data['results'][0]['geometry']['location']['lat'],
            data['results'][0]['geometry']['location']['lng'],
            locality, country)


def get_streetview(latitude, longitude, key, size='640x320', fov=90, heading=235, pitch=10):
    url = 'http://maps.googleapis.com/maps/api/streetview'
    params = {
        'size': size,
        'location': '%s,%s' % (latitude, longitude),
        'fov': fov,
        'heading': heading,
        'pitch': pitch,
        'key': key
    }

    return download(url, params=params)


def download(url, params=None, headers=None, method='get', extension=None):
    try:
        if method == 'post':
            res = requests.post(url, params=params, headers=headers, stream=True)
        else:
            res = requests.get(url, params=params, headers=headers, stream=True)
        if not extension:
            extension = os.path.splitext(url)[1].split('?')[0]
        f = tempfile.NamedTemporaryFile(delete=False, suffix=extension)
        for chunk in res.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)
    except Exception as e:
        logging.error(e)
        return None
    f.seek(0)
    if not extension:
        f.name = fix_extension(f.name)
    return f.name


def save_to_file(res):
    ext = os.path.splitext(res.url)[1].split('?')[0]
    f = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
    for chunk in res.iter_content(chunk_size=1024):
        if chunk:
            f.write(chunk)
    f.seek(0)
    if not ext:
        f.name = fix_extension(f.name)
    return open(f.name, 'rb')


def fix_extension(file_path):
    type = magic.from_file(file_path, mime=True)
    extension = str(mimetypes.guess_extension(type, strict=False))
    if extension is not None:
        # I hate to have to use this s***
        if extension.endswith('jpe'):
            extension = extension.replace('jpe', 'jpg')
        os.rename(file_path, file_path + extension)
        return file_path + extension
    else:
        return file_path


def get_short_url(long_url, api_key):
    url = 'https://www.googleapis.com/urlshortener/v1/url'
    params = {'longUrl': long_url, 'key': api_key}
    headers = {'content-type': 'application/json'}

    res = send_request(url, params=params, headers=headers, data=json.dumps(params), post=True)

    return res.id


def mp3_to_ogg(input):
    output = tempfile.NamedTemporaryFile(delete=False, suffix='.ogg').name

    with open(os.devnull, "w") as DEVNULL:
        converter = subprocess.check_call(
            ['ffmpeg', '-i', input, '-ac', '1', '-c:a', 'libopus', '-b:a', '16k', '-y', output],
            stdout=DEVNULL)

    return output


def remove_markdown(text):
    characters = ['_', '*', '[', '`', '(', '\\']
    aux = list()
    for x in range(len(text)):
        if x >= 0 and text[x] in characters and text[x - 1] != '\\':
            pass
        else:
            aux.append(text[x])
    return ''.join(aux)


def remove_html(text):
    text = re.sub('<[^<]+?>', '', text)
    text = text.replace('&lt;', '<');
    text = text.replace('&gt;', '>');
    return text
    s = HTMLParser()
    s.reset()
    s.reset()
    s.strict = False
    s.convert_charrefs = True
    s.fed = []
    s.feed(text)
    return ''.join(s.fed)


def set_logger(debug=False):
    logFormatterConsole = logging.Formatter("[%(processName)-11.11s]  %(message)s")
    logFormatterFile = logging.Formatter("%(asctime)s [%(processName)-11.11s] [%(levelname)-5.5s]  %(message)s")
    rootLogger = logging.getLogger()
    if debug:
        rootLogger.setLevel(logging.DEBUG)
    else:
        rootLogger.setLevel(logging.INFO)

    fileHandler = logging.FileHandler("bot.log", mode='w')
    fileHandler.setFormatter(logFormatterFile)
    rootLogger.addHandler(fileHandler)

    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(logFormatterConsole)
    rootLogger.addHandler(consoleHandler)

    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("polaris.types").getChild('AutosaveDict').setLevel(logging.ERROR)
