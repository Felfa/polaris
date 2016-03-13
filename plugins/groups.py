from core.utils import *

commands = [
    ('/groups', []),
    ('/join', ['alias | chat id']),
    ('/mods', []),
    ('/info', []),
    ('/invite', ['user']),
    ('/kill', ['user']),
    ('/ban', ['user']),
    ('/addgroup', []),
    ('/remgroup', []),
    ('/addmod', ['user']),
    ('/demod', ['user'])
]
description = 'Group management features. Currently very experimental and unstable.'
hidden = True


def run(m):
    input = get_input(m)
    if m.reply:
        id = m.reply.sender.id
    else:
        id = m.sender.id
    uid = m.sender.id
    gid = m.receiver.id

    if get_command(m) == 'groups':
        message = lang.errors.unsupported

    elif get_command(m) == 'join':
        message = lang.errors.unsupported
    
    elif get_command(m) == 'mods':
        mods = ''
        globalmods = ''
        admins = ''
        for uid in tags.list:
            if 'mod:' + str(m.receiver.id)[1:] in tags.list[uid]:
                mods += '\t-\t%s\n' % user_info(int(uid))
            if 'globalmod' in tags.list[uid]:
                globalmods += '\t-\t%s\n' % user_info(int(uid))
            if 'admin' in tags.list[uid]:
                admins += '\t-\t%s\n' % user_info(int(uid))
        
        message = 'Mods: \n%s\nGlobalmods: \n%s\nAdmins:\n%s\n' % (mods, globalmods, admins)
        
    elif get_command(m) == 'info':
        message = lang.errors.unsupported

    elif get_command(m) == 'invite' and (is_admin(uid) or is_mod(uid, gid)):
        if m.receiver.id > 0:
            return send_message(m, lang.errors.unsupported)

        if m.reply:
            if not invite_user(m, id):
                return send_message(m, lang.errors.peerflood)
        elif input:
            if not invite_user(m, input):
                return send_message(m, lang.errors.peerflood)
        
        message = 'User added.'

    elif get_command(m) == 'kill' and (is_admin(uid) or is_mod(uid, gid)):
        if m.receiver.id > 0:
            return send_message(m, lang.errors.unsupported)

        if m.reply:
            if not kick_user(m, id):
                return send_message(m, lang.errors.notchatadmin)
        elif input:
            if not kick_user(m, input):
                return send_message(m, lang.errors.notchatadmin)
        else:
            if not kick_user(m, uid):
                return send_message(m, lang.errors.notchatadmin)
        
        message = 'User kicked.'

    elif get_command(m) == 'ban':
        message = lang.errors.unsupported

    elif get_command(m) == 'addgroup':
        message = lang.errors.unsupported

    elif get_command(m) == 'remgroup':
        message = lang.errors.unsupported

    elif get_command(m) == 'addmod' and (is_admin(uid) or is_mod(uid, str(gid)[1:])):
        if m.receiver.id > 0:
            return send_message(m, lang.errors.unsupported)

        set_tag(id, 'mod:%s' % str(gid)[1:])
        if m.reply:
            name = m.reply.sender.first_name
        else:
            name = m.sender.first_name
        message = '%s has been promoted to moderator for chat %s.' % (name, m.receiver.title)

    elif get_command(m) == 'demod' and (is_admin(uid) or is_mod(uid, str(gid)[1:])):
        if m.receiver.id > 0:
            return send_message(m, lang.errors.unsupported)

        rem_tag(id, 'mod:%s' % str(gid)[1:])
        if m.reply:
            name = m.reply.sender.first_name
        else:
            name = m.sender.first_name

        message = '%s has been demoted to member for chat %s.' % (name, m.receiver.title)

    else:
        message = lang.errors.permission

    send_message(m, message)
