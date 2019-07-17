from re import sub as substitute
from rtmbot.core import Plugin

import logging
import wallbot.helpers
import wallbot.actions

class Wallbot(Plugin):

    def __init__(self, slack_client, plugin_config):
        """ Initialise using provided arguments """
        self.name    = type(self).__name__
        self.client  = slack_client
        self.config  = plugin_config
        self.jobs    = []
        self.debug   = self.config.get('DEBUG', False)
        self.outputs = []
        self.actions = wallbot.actions
        self.trust   = wallbot.helpers.TrustStore(self.config.get('TRUST_FILE', 'trust.json'))
        # Lookup bot user info from token
        self.user_name, self.user_id = wallbot.helpers.whoami(self.client)
        logging.info(self.name + ' started')
        self.audit('We starting')

    def process_message(self, slack):
        """ Main function called by rtmbot which decides if wallbot should process messages """
        # There are two circumstances in which the bot should respond; either you
        # message it directly (in a direct channel), or you include a mention (@bot)
        # at the start of your message. It should not respond to it's own messages.
        if (slack['type'] == 'message' and not 'subtype' in slack.keys()):
            if slack['user'] != self.user_id and (slack['channel'].startswith('D') or slack['text'].startswith('<@%s>' % self.user_id)):
                self.filter_message(slack)

    def filter_message(self, slack):
        """ Checks the start of messages to figure out which command to run """
        # Dictionary of strings to match to functions
        filters = {
            'hello':              'ping',
            'ping':               'ping',
            'you there':          'ping',
            'post':               'post',
            'add':                'add_user',
            'remove':             'remove_user',
            'authors':            'list_users',
            'help':               'list_commands',
            'commands':           'list_commands',
            'say hello':          'introduction',
            'hey':                'introduction',
            'introduce yourself': 'introduction',
            'do you love me':     'love'
        }
        # Strip the mention off the start of the message if necessary.
        mention = '<@%s>' % self.user_id
        if slack['text'].startswith(mention):
            slack['text'] = substitute(r'^%s ' % mention, '', slack['text'])
        # Process keyword filters
        for keyword, filter in filters.items():
            if slack['text'].lower().startswith(keyword):
                slack['text'] = substitute(r'^' + keyword, '', slack['text']).lstrip()
                action = getattr(self.actions, filter)
                logging.info("Action '%s' triggered by message matching keyword '%s'" % (filter, keyword))
                action(self, slack)
                return
        # Catchall for when no keyword can be matched
        self.actions.catchall(self, slack)
        logging.debug("Action 'catchall' triggered by unrecognised message '%s'" % slack['text'])

    def send(self, messages, channel):
        """ Send messages to output stream """
        # Process strings as well as iterables
        if isinstance(messages, str):
            message = messages
        else:
            message = '\n'.join(messages)
        # Post message to output stream
        self.outputs.append([channel, message])

    def audit(self, message):
        """ Send messages to audit channel, logfile, and logger """
        channel  = self.config.get('AUDIT_CHANNEL', False)
        log_file = self.config.get('AUDIT_FILE', False)
        if channel: outputs.append([channel, message])
        if log_file:
            with open(log_file, 'a') as f: f.write(message)
        logging.warning('AUDIT: ' + message)
