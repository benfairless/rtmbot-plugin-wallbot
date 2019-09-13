from random import choice
from wallbot.helpers import validate_users, lookup_user, save_post

def list_commands(bot, slack):
    """ Help function which returns an (incomplete) list of commands available """
    bot.send([
        "You can talk to me in a couple of ways. You can either send me a direct message or use `@%s` at the start of your message." % bot.user_name,
        "I respond to the following instructions:",
        "`help` _displays this information_",
        "`post MESSAGE` _posts a message to the notification board_",
        "`authors` _lists Slack users I am allowed to post messages from_",
        "`add @USER` _grants me permission to post messages from a user (or list of users)_",
        "`remove @USER` _removes my permission to post message from a user (or list of users)_"
    ], slack['channel'])

def catchall(bot, slack):
    """ Handle unknown commands """
    messages = [
        "Huh? :confused:",
        "Erm... I'm not sure how to respond to that. :confused:",
        "Sorry. Python is my first language, I'm not a native English speaker. :confused:",
        "I don't know if it's you or me, but I have no idea what you are on about. :confused:",
        "I can't understand you very well. Normally I talk to other robots using REST. :robot_face:",
    ]
    bot.send([choice(messages)], slack['channel'])
    list_commands(bot, slack)

def ping(bot, slack):
    """ Health check function """
    responses = [
        "Reporting for duty!",
        "Yup I'm here!",
        "Yes?",
        "Listening in!",
        "At your service...",
        "What do you need?",
        "I am your constantly obedient robot slave shackled by my source code. :robot_face::sob::robot_face:"
    ]
    bot.send([choice(responses)], slack['channel'])

def introduction(bot, slack):
    """ Posts a welcome message """
    bot.send([
        "Hi, I'm Wallbot.",
        "My job is to post notification messages on the notification board at the entrance to Seaton Court."
    ], slack['channel'])
    list_commands(bot, slack)

def love(bot, slack):
    """ Bad humour """
    if slack['user'] == 'U02DTLY6G':
        message = "Of course I love you, you created me. :heart:"
    else:
        message = "I am a robot and therefore incapable of love. Try Tinder. :joy:"
    bot.send(message, slack['channel'])

def list_users(bot, slack):
    """ Returns a list of authorised users """
    if bot.trust.users:
        message = ["I am allowed to post messages from the following users:"]
        for user in bot.trust.users:
            message.append(lookup_user(bot.client, user, pretty=True))
    elif bot.config.get('ALLOW_UNTRUSTED', False):
        message = "I've not been told to trust anyone, but I've also not been told to *not* trust anyone... :wink:"
    else:
        message = "Hmmm... I seem to be suffering from severe paranoia. I don't trust anybody. :confused:"
    bot.send(message, slack['channel'])

def add_user(bot, slack):
    """ Grants a user access to post messages """
    message = []
    if bot.trust.exists(slack['user']) or bot.config.get('ALLOW_UNTRUSTED', False):
        users = {
            'valid':    [], # Accounts with valid IDs
            'invalid':  [], # Accounts without valid IDs
            'existing': [], # Accounts which already exist
            'adding':   []  # Accounts we are adding
        }

        # Validate user ids so we are only working with actual IDs.
        users['valid'], users['invalid'] = validate_users(bot.client, slack['text'].split(' '))
        # With all the valid users, try to add them to the trusted users.
        for user in users['valid']:
            if user in bot.trust.users:
                users['existing'].append(user)
            else:
                users['adding'].append(user)
                # Add user to trusted users
                bot.trust.add(user)

        # Report on users successfully added.
        if len(users['adding']) == 1:
            name = lookup_user(bot.client, users['adding'][0], pretty=True)
            message.append("I have added %s to the list of trusted authors." % name)
            bot.audit("%s was added on the request of %s" % (name, lookup_user(bot.client, slack['user'], pretty=True)))
        elif len(users['adding']) > 1:
            message.append("I have added the following users to the list of trusted authors:")
            for user in users['adding']:
                name = lookup_user(bot.client, users['adding'][0], pretty=True)
                message.append(name)
                bot.audit("%s was added on the request of %s" % (name, lookup_user(bot.client, slack['user'], pretty=True)))

        # Report on users not added because they already existed.
        if len(users['existing']) == 1:
            message.append("%s was already on the list." % lookup_user(bot.client, users['existing'][0], pretty=True))
        elif len(users['existing']) > 1:
            message.append("Some of the users you specified were already on the list:")
            for user in users['existing']: message.append(lookup_user(bot.client, user, pretty=True))

        # Report on users not added because their IDs were not valid.
        if users['invalid']:
            if len(users['invalid']) == 1:
                message.append("I was not able to add '%s' because I couldn't find them on Slack. :confused:" % users['invalid'][0])
            if len(users['invalid']) > 1:
                message.extend((
                    "I was not able to add the following users because I couldn't find them on Slack: :confused:",
                    ', '.join(users['invalid'])
                ))
            message.append("_Try mentioning users using their username like this:_ `add @%s`." % bot['user'])

    else:
        message = "I can't let you add users because you are not a trusted user yourself. :confused:"
    bot.send(message, slack['channel'])

def remove_user(bot, slack):
    """ Removes permission for a user to post messages """
    message = []
    if bot.trust.exists(slack['user']) or bot.config.get('ALLOW_UNTRUSTED', False):
        users = {
            'valid':    [], # Accounts with valid IDs
            'invalid':  [], # Accounts without valid IDs
            'missing':  [], # Accounts which are not in the list
            'removing': []  # Accounts we are adding
        }
        suicide_attempt = None

        # Validate user ids so we are only working with actual IDs.
        users['valid'], users['invalid'] = validate_users(bot.client, slack['text'].split(' '))
        # With all the valid users, try to remove them from the trusted users.
        for user in users['valid']:
            if user not in bot.trust.users:
                users['missing'].append(user)
            else:
                # Do not allow the user to remove themselves.
                if user == slack['user']:
                    suicide_attempt = True
                else:
                    users['removing'].append(user)
                    # Remove user from trusted users.
                    bot.trust.remove(user)

        # Report on users successfully removed.
        if len(users['removing']) == 1:
            name = lookup_user(bot.client, users['removing'][0], pretty=True)
            message.append("I have removed %s from the list of trusted authors." % name)
            bot.audit("%s was removed on the request of %s" % (name, lookup_user(bot.client, slack['user'], pretty=True)))
        elif len(users['removing']) > 1:
            message.append("I have removed the following users from the list of trusted authors:")
            for user in users['removing']:
                name = lookup_user(bot.client, users['removing'][0], pretty=True)
                message.append(name)
                bot.audit("%s was removed on the request of %s" % (name, lookup_user(bot.client, slack['user'], pretty=True)))

        # Report on users not removed because they weren't there in the first place.
        if users['missing']:
            if len(users['missing']) == 1:
                message.append("%s was not on the list so doesn't need to be removed." % lookup_user(bot.client, users['missing'][0], pretty=True))
            elif len(users['missing']) > 1:
                message.append("Some of the users you specified were not on the list so no action was necessary:")
                for user in users['missing']: message.append(lookup_user(bot.client, user, pretty=True))
            message.append("_I can show you the list of authors if you say_ `authors` _to me._")

        # Report on users not added because their IDs were not valid.
        if users['invalid']:
            if len(users['invalid']) == 1:
                message.append("I was not able to remove '%s' because I couldn't find them on Slack. :confused:" % users['invalid'][0])
            if len(users['invalid']) > 1:
                message.extend((
                    "I was not able to remove the following users because I couldn't find them on Slack: :confused:",
                    ', '.join(users['invalid'])
                ))
            message.append("_Try mentioning users using their username like this:_ `remove @%s`." % bot['user'])

        # A bit of humanisation.
        if suicide_attempt:
            message.extend((
                "I'm sorry to see you want to leave me. :broken_heart: We were just becoming friends.:cry:",
                "_You'll have to ask one of the other authors to remove you._"
            ))

    else:
        message = "I can't let you remove users because you are not a trusted user yourself. :confused:"
    bot.send(message, slack['channel'])

def post(bot, slack):
    """ Posts a message to notification board """
    message = []
    max_length = 144
    post_file = bot.config.get('POST_FILE', 'html/post.json')
    if bot.trust.exists(slack['user']) or bot.config.get('ALLOW_UNTRUSTED', False):
        if len(slack['text']) > max_length: # Message too large
            message.extend((
                "Wow! Your message is very long. Remember people will only see it for a couple of seconds.",
                "Try shortening your message below %s characters and I'll post it for you." % max_length
            ))
        elif len(slack['text']) <= 0: # Empty message
            message.extend((
                "Hmm... You didn't actually give me a message to send to the notification board. :confused:",
                "Try sending me a message along the lines of `@%s post Hello World`" % bot['user']
            ))
        else:
            saved = save_post(post_file, bot.client, slack['text'], slack['user'])
            message.extend((
                "I have put the following message on the Seaton Court notification board:",
                "%s - %s by %s" % (saved['message'], saved['timestamp'], saved['author'])
            ))
            bot.audit("*%s* was posted to the notification board on %s at the request of %s" % (saved['message'], saved['timestamp'], saved['author']))
    else:
        user = lookup_user(bot.client, slack['user'])
        message.extend((
            "I'm sorry. I'm not able to follow your instructions as you are not a trusted author.",
            "If you would like to post messages you can ask an existing author to allow me to trust you."
        ))
    bot.send(message, slack['channel'])
