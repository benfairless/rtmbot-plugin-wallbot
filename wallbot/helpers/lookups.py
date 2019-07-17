import logging

def lookup_user(client, user_id, pretty=False, mention=True):
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
        logging.debug("Found user '%s' (%s)" % (user['profile']['real_name'], user['id']))
        return name
    else:
        logging.debug("Could not find user '%s'" % user_id)
        return None

def whoami(client):
    """ Lookup bot details """
    response = client.api_call('auth.test')
    if response['ok'] == True:
        logging.info("Running as user '%s' (%s) in team '%s' (%s)" % (response['user'], response['user_id'], response['team'], response['team_id']))
        return response['user'], response['user_id']
    else:
        logging.error('Invalid response whilst performing auth.test API call')
        return None

def validate_users(client, potential_users):
    """ Validate an array of potential user_ids """
    valid_users   = []
    invalid_users = []
    for user in potential_users:
        user = user.lstrip('<@').rstrip('>')
        if lookup_user(client, user): valid_users.append(user)
        else: invalid_users.append(user)
    return (valid_users, invalid_users)
