import json
from datetime import datetime
from .lookups import lookup_user

def save_post(post_file, client, message, user_id):
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
        'author': lookup_user(client, user_id, pretty=True, mention=False)
    }
    # Render JSON from data dictionary
    formatted = json.dumps(posting, sort_keys=True, indent=4, separators=(',', ': '))
    # Write JSON data to disk
    with open(post_file, 'w') as f: f.write(formatted)
    return posting
