import json
import logging

class TrustStore(object):
    """ Persistent trust store """

    def __init__(self, filepath):
        self.filepath = filepath
        self.users    = []

        if len(self.users) >= 0:
            self.load()
        logging.info('Trust Store loaded')

    def add(self, user):
        """ Add user to TrustStore """
        if not user in self.users:
            self.users.append(user)
        logging.info("Added user '%s' to Trust Store" % user)
        self.update()

    def remove(self, user):
        """ Remove user from TrustStore """
        self.users.remove(user)
        logging.info("Removed user '%s' from Trust Store" % user)
        self.update()

    def exists(self, user):
        """ Check if user is in users list """
        return True if user in self.users else False

    def load(self):
        """ Load data from on-disk store """
        try:
            with open(self.filepath, 'r') as f:
                self.users = json.load(f)
            logging.debug("Loaded Trust Store from '%s'" % self.filepath)
        except:
            self.users = []
            self.update()

    def update(self):
        """ Update on-disk store """
        parsed = json.dumps(self.users)
        with open(self.filepath, 'w') as f: f.write(parsed)
        logging.debug("Updated on-disk Trust Store at '%s'" % self.filepath)
