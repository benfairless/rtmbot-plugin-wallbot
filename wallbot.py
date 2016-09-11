import json
import yaml
import os
from re import sub as substitute
from datetime import datetime
from random import choice
from client import slack_client as client
from imgurpython import ImgurClient

# Global outputs array used to stream messages to Slack
outputs = []

# Gather information about the bot
bot = client.api_call('auth.test')

# Settings
conf = yaml.load(open(os.getenv('WALLBOT_CONFIG','rtmbot.conf'), 'r'))
config = conf['WALLBOT']
audit_channel = config['AUDIT_CHANNEL']
initial_user  = config['INITIAL_USER']
trust_file    = config['TRUST_FILE']
audit_file    = config['AUDIT_FILE']
post_file     = config['POST_FILE']
imgur_id      = config['IMGUR_ID']
imgur_secret  = config['IMGUR_SECRET']

# TODO:
#   - parameterise variables so they can be loaded from config file or environment vars.
#   - put onto github


################################################################################
################################ MAIN FUNCTIONS ################################
################################################################################


class Trusted(list):
    """ Persistent trust store """

    def __init__(self, filepath):
        self.filepath = filepath
        self.users = []

        if len(self.users) >= 0:
            self.load()

    def add(self, user):
        """ Add user to Trusted """
        self.users.append(user)
        self.update()

    def remove(self, user):
        """ Remove user from Trusted """
        self.users.remove(user)
        self.update()

    def load(self):
        """ Load data from on-disk store """
        try:
            with open(self.filepath, 'r') as f:
                self.users = json.load(f)
        except:
            self.users = [initial_user]
            self.update()

    def update(self):
        """ Update on-disk store """
        parsed = json.dumps(self.users)
        with open(self.filepath, 'w') as f: f.write(parsed)


def process_message(slack):
    """ Main function called by rtmbot which decides if wallbot should process messages """
    # There are two circumstances in which the bot should respond; either you
    # message it directly (in a direct channel), or you include a mention (@bot)
    # at the start of your message. It should not respond to it's own messages.
    if (slack['type'] == 'message' and not 'subtype' in slack.keys()):
        if slack['user'] != bot['user_id'] and (slack['channel'].startswith('D') or slack['text'].startswith('<@%s>' % bot['user_id'])):
            wallbot(slack)


def wallbot(slack):
    """ Bot interface. Checks the start of messages to figure out which command to run """

    ############################################################################
    ######################## WALLBOT RUNTIME FUNCTIONS #########################
    ############################################################################

    # Set up persistent storage of trusted users
    trusted = Trusted(trust_file)
    print('Trusted users: ' + str(trusted.users))

    def run():
        """ Checks the start of messages to figure out which command to run """
        # Strip the mention off the start of the message if necessary.
        mention = '<@%s>' % bot['user_id']
        if slack['text'].startswith(mention):
            slack['text'] = substitute(r'^%s ' % mention, '', slack['text'])

        # hello / you there / ping
        if slack['text'].lower().startswith('hello') or slack['text'].lower().startswith('you there') or slack['text'].lower().startswith('ping'):
            ping()

        # post
        elif slack['text'].startswith('post'):
            slack['text'] = substitute(r'^post', '', slack['text']).lstrip()
            post()

        # add
        elif slack['text'].startswith('add'):
            slack['text'] = substitute(r'^add', '', slack['text']).lstrip()
            add()

        # remove
        elif slack['text'].startswith('remove'):
            slack['text'] = substitute(r'^remove', '', slack['text']).lstrip()
            remove()

        # authors
        elif slack['text'].lower().startswith('authors'):
            authors()

        # help / commands
        elif slack['text'].lower().startswith('help') or slack['text'].startswith('commands'):
            commands()

        # say hello / introduce yourself
        elif slack['text'].lower().startswith('say hello') or slack['text'].lower().startswith('introduce yourself'):
            introduction()

        # do you love me
        elif slack['text'].lower().startswith('do you love me'):
            love()

        # kitten USER
        elif slack['text'].startswith('kitten'):
            slack['text'] = substitute(r'^kitten', '', slack['text']).lstrip()
            kitten()

        # catchall
        else:
            confused()
            print('UNRECOGNISED: ' + str(slack))


    ############################################################################
    ######################## WALLBOT COMMAND FUNCTIONS #########################
    ############################################################################

    def post():
        """ Posts a message to notification board """
        message = []
        max_length = 144
        if authorised(slack['user']):
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
                saved = save(slack['text'], slack['user'])
                message.extend((
                    "I have put the following message on the Seaton Court notification board:",
                    "%s - %s by %s" % (saved['message'], saved['timestamp'], saved['author'])
                ))
                audit("*%s* was posted to the notification board on %s at the request of %s" % (saved['message'], saved['timestamp'], saved['author']))
        else:
            user = lookupUser(slack['user'])
            message.extend((
                "I'm sorry. I'm not able to follow your instructions as you are not a trusted author.",
                "If you would like to post messages you can ask an existing author to allow me to trust you."
            ))
        send(message)


    def add():
        """ Grants a user access to post messages """
        message = []
        if authorised(slack['user']):
            users = {
                'valid':    [], # Accounts with valid IDs
                'invalid':  [], # Accounts without valid IDs
                'existing': [], # Accounts which already exist
                'adding':   []  # Accounts we are adding
            }

            # Validate user ids so we are only working with actual IDs.
            users['valid'], users['invalid'] = validateUsers(slack['text'].split(' '))
            # With all the valid users, try to add them to the trusted users.
            for user in users['valid']:
                if user in trusted.users:
                    users['existing'].append(user)
                else:
                    users['adding'].append(user)
                    # Add user to trusted users
                    trusted.add(user)

            # Report on users successfully added.
            if len(users['adding']) == 1:
                name = lookupUser(users['adding'][0], pretty=True)
                message.append("I have added %s to the list of trusted authors." % name)
                audit("%s was added on the request of %s" % (name, lookupUser(slack['user'], pretty=True)))
            elif len(users['adding']) > 1:
                message.append("I have added the following users to the list of trusted authors:")
                for user in users['adding']:
                    name = lookupUser(users['adding'][0], pretty=True)
                    message.append(name)
                    audit("%s was added on the request of %s" % (name, lookupUser(slack['user'], pretty=True)))

            # Report on users not added because they already existed.
            if len(users['existing']) == 1:
                message.append("%s was already on the list." % lookupUser(users['existing'][0], pretty=True))
            elif len(users['existing']) > 1:
                message.append("Some of the users you specified were already on the list:")
                for user in users['existing']: message.append(lookupUser(user, pretty=True))

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
        send(message)


    def remove():
        """ Removes permission for a user to post messages """
        message = []
        if authorised(slack['user']):
            users = {
                'valid':    [], # Accounts with valid IDs
                'invalid':  [], # Accounts without valid IDs
                'missing':  [], # Accounts which are not in the list
                'removing': []  # Accounts we are adding
            }
            suicide_attempt = None

            # Validate user ids so we are only working with actual IDs.
            users['valid'], users['invalid'] = validateUsers(slack['text'].split(' '))
            # With all the valid users, try to remove them from the trusted users.
            for user in users['valid']:
                if user not in trusted.users:
                    users['missing'].append(user)
                else:
                    # Do not allow the user to remove themselves.
                    if user == slack['user']:
                        suicide_attempt = True
                    else:
                        users['removing'].append(user)
                        # Remove user from trusted users.
                        trusted.remove(user)

            # Report on users successfully removed.
            if len(users['removing']) == 1:
                name = lookupUser(users['removing'][0], pretty=True)
                message.append("I have removed %s from the list of trusted authors." % name)
                audit("%s was removed on the request of %s" % (name, lookupUser(slack['user'], pretty=True)))
            elif len(users['removing']) > 1:
                message.append("I have removed the following users from the list of trusted authors:")
                for user in users['removing']:
                    name = lookupUser(users['removing'][0], pretty=True)
                    message.append(name)
                    audit("%s was removed on the request of %s" % (name, lookupUser(slack['user'], pretty=True)))

            # Report on users not removed because they weren't there in the first place.
            if users['missing']:
                if len(users['missing']) == 1:
                    message.append("%s was not on the list so doesn't need to be removed." % lookupUser(users['missing'][0], pretty=True))
                elif len(users['missing']) > 1:
                    message.append("Some of the users you specified were not on the list so no action was necessary:")
                    for user in users['missing']: message.append(lookupUser(user, pretty=True))
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
        send(message)


    def authors():
        """ Returns a list of authorised users """
        if trusted.users:
            message = ["I am allowed to post messages from the following users:"]
            for user in trusted.users:
                message.append(lookupUser(user, pretty=True))
        else:
            message = "Hmmm... I seem to be suffering from severe paranoia. I don't trust anybody. :confused:"
        send(message)


    def commands():
        """ Help function which returns an (incomplete) list of commands available """
        send([
            "You can talk to me in a couple of ways. You can either send me a direct message or use `@%s` at the start of your message." % bot['user'],
            "I respond to the following instructions:",
            "`help` _displays this information_",
            "`post MESSAGE` _posts a message to the notification board at Seaton Court_",
            "`authors` _lists Slack users I am allowed to post messages from_",
            "`add @USER` _grants me permission to post messages from a user (or list of users)_",
            "`remove @USER` _removes my permission to post message from a user (or list of users)_"
        ])


    def ping():
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
        send([choice(responses)])


    def introduction():
        """ Posts a welcome message """
        send([
            "Hi, I'm Wallbot.",
            "My job is to post notification messages on the notification board at the entrance to Seaton Court."
        ])
        commands()


    def confused():
        """ Handle unknown commands """
        messages = [
            "Huh? :confused:",
            "Erm... I'm not sure how to respond to that. :confused:",
            "Sorry. Python is my first language, I'm not a native english speaker. :confused:",
            "I can't understand you very well. Normally I talk to other robots using REST. :robot_face:",
        ]
        send([choice(messages)])
        commands()

    def love():
        """ Bad humour """
        if slack['user'] == 'U02DTLY6G':
            send("Of course I love you, you created me. :heart:")
        else:
            send("I am a robot and therefore incapable of love. Try Tinder. :joy:")

    def kitten():
        """ Send kittens to your colleagues """

        # Identify who sent the kittens.
        blame = lookupUser(slack['user'])

        # Pick an emoji
        emojis = [
            ':smiley_cat:',
            ':smile_cat:',
            ':heart_eyes_cat:',
            ':smirk_cat:',
            ':kissing_cat:',
            ':cat:',
            ':cat2:'
        ]

        # Setup imgur client.
        imgur = ImgurClient(imgur_id, imgur_secret)

        # Get one loveable floof.
        def chooseKitty():
            kittens = []
            for i in range(0,4):
                more_kittens = imgur.subreddit_gallery('kittens', sort='top', page=i)
                kittens = kittens + more_kittens
            return choice(kittens)

        # Send a user a direct message
        def directMessage(user, message):
            dm = client.api_call('im.open', user=user)
            channel_id = dm['channel']['id']
            send(message, channel=channel_id)

        # If we are sending kittens to other people
        if len(slack['text']) > 0:
            # Validate kitty targets
            users = {}
            users['valid'], users['invalid'] = validateUsers(slack['text'].split(' '))

            # With all the valid users, try to send them kittens.
            for user in users['valid']:
                payload = [
                    "Courtesy of %s %s\n" % (blame, choice(emojis)),
                    chooseKitty().link
                ]
                directMessage(user, payload)

            message = []
            if users['invalid']:
                if len(users['invalid']) == 1:
                    message.append("I was not able to send a kitten to '%s' because I couldn't find them on Slack. :crying_cat_face:" % users['invalid'][0])
                if len(users['invalid']) > 1:
                    message.extend((
                        "I was not able to send a kitten to the following users because I couldn't find them on Slack: :crying_cat_face:",
                        ', '.join(users['invalid'])
                    ))
                message.append("_Try mentioning users using their username like this:_ `kitten @%s`." % bot['user'])

            # Report on successfully delivered kittens
            kitten_count = 'Sent '
            for i in range(len(users['valid'])):
                kitten_count = kitten_count + ':smiley_cat:'
            message.append(kitten_count)

        # Send kitty to source chat if no users were specified.
        else:
            message = [
                "Courtesy of %s %s\n" % (blame, choice(emojis)),
                chooseKitty().link
            ]

        send(message)


    ############################################################################
    ######################## WALLBOT INTERNAL FUNCTIONS ########################
    ############################################################################


    def send(messages, channel=None):
        """ Send messages to output stream """
        # Default to the source channel
        if channel == None: channel = slack['channel']
        # Process strings as well as iterables
        if isinstance(messages, str): message = messages
        else: message = '\n'.join(messages)
        # Post message to output stream
        outputs.append([channel, message])


    def audit(message):
        """ Send messages to audit channel """
        channel = audit_channel
        with open(audit_file, 'a') as f: f.write(message)
        outputs.append([channel, message])


    def authorised(user_id):
        """ Check if user is in authorised_users list """
        return True if user_id in trusted.users else False


    def validateUsers(potential_users):
        """ Validate an array of potential user_ids """
        valid_users = []
        invalid_users = []
        for user in potential_users:
            user = user.lstrip('<@').rstrip('>')
            if lookupUser(user): valid_users.append(user)
            else: invalid_users.append(user)
        return (valid_users, invalid_users)


    def lookupUser(user_id, pretty=False, mention=True):
        """ Lookup user details """
        response = client.api_call('users.info', user=user_id)
        if response['ok'] == True:
            user = response['user']
            name = user['name']
            # If mention is set use @user instead of user in the name.
            if mention == True:
                name = '<@%s>' % user['id']
            # If pretty is set include full name if we know it.
            if pretty == True and len(user['profile']['real_name']) > 0:
                name = '%s (%s)' % (name, user['profile']['real_name'])
            return name
        else:
            return None


    def save(message,user_id):
        """ Save message and metadata to file """
        def suffix(day):
            """ Identifies which suffix to add to a day of the month """
            return 'th' if 11 <= day <=13 else {1:'st' ,2:'nd' ,3:'rd'}.get(day%10, 'th')

        def datefmt(date):
            """ Formats date into a human friendly format """
            return date.strftime('%B {S} %Y @ %H:%M').replace('{S}', str(date.day) + suffix(date.day))

        # Build dictionary containing message and metadata
        posting = {
            'message': message,
            'timestamp': datefmt(datetime.now()),
            'author': lookupUser(user_id, pretty=True, mention=False)
        }
        # Render JSON from data dictionary
        formatted = json.dumps(posting, sort_keys=True, indent=4, separators=(',', ': '))
        # Write JSON data to disk
        with open(post_file, 'w') as f: f.write(formatted)
        return posting

    ############################################################################
    ############################# WALLBOT RUNTIME ##############################
    ############################################################################

    run()
