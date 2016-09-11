rtmbot-plugin-wallbot
=====================

Hi, I'm Wallbot.
My job is to post notification messages on the notification board at the entrance to Seaton Court.

You can talk to me in a couple of ways. You can either send me a direct message or use `@wallbot` at the start of your message.
I respond to the following instructions:
 - `help` _displays this information_
 - `post MESSAGE` _posts a message to the notification board at Seaton Court_
 - `authors` _lists Slack users I am allowed to post messages from_
 - `add @USER` _grants me permission to post messages from a user (or list of users)_
 - `remove @USER` _removes my permission to post message from a user (or list of users_

## Installation
Wallbot is a plugin for SlackHQ's [python-rtmbot](https://github.com/slackhq/python-rtmbot) which adds the ability to send messages to a kiosk style notification board.

You'll need to do the following before starting:
  - [Create new Bot on Slack](https://landregistry.slack.com/apps/build/custom-integration).
  - [Generate an oAuth token for Imgur](https://api.imgur.com/oauth2/addclient).
  - [Find your user_id in the Slack API](https://api.slack.com/methods/auth.test/test)
  - Create a channel in Slack for audit events.
  - [Find the channel_id for your audit channel](https://api.slack.com/methods/channels.list/test).

You can now proceed with the installation:

  - Install `python-rtmbot` from GitHub:
```
git clone https://github.com/slackhq/python-rtmbot.git
> Cloning into 'python-rtmbot'...
> remote: Counting objects: 431, done.
> remote: Total 431 (delta 0), reused 0 (delta 0), pack-reused 431
> Receiving objects: 100% (431/431), 166.62 KiB | 90.00 KiB/s, done.
> Resolving deltas: 100% (213/213), done.
> Checking connectivity... done.
```

  - And the same again with `rtmbot-plugin-wallbot`:
```
git clone https://github.com/benfairless/rtmbot-plugin-wallbot.git
> Cloning into 'rtmbot-plugin-wallbot'...
> remote: Counting objects: 5, done.
> remote: Compressing objects: 100% (4/4), done.
> remote: Total 5 (delta 0), reused 5 (delta 0), pack-reused 0
> Unpacking objects: 100% (5/5), done.
> Checking connectivity... done.
```

  - Copy the wallbot plugin into the rtmbot plugin directory:
```
cp rtmbot-plugin-wallbot/wallbot.py python-rtmbot/plugins/wallbot.py
```

  - Copy the example configuration file into the rtmbot directory:
```
cp rtmbot-plugin-wallbot/rtmbot.conf.example
```

  - Edit the configuration file found at `python-rtmbot/rtmbot.conf`:
```yaml
DEBUG: False
SLACK_TOKEN: "xoxb-11111111111-222222222222222222222222"
WALLBOT:
        INITIAL_USER:  your user_id
        AUDIT_CHANNEL: audit channel_id
        AUDIT_FILE: 'audit.log'
        TRUST_FILE: 'trust.json'
        POST_FILE: 'post.json'
        IMGUR_ID: Imgur oAuth Token
        IMGUR_SECRET: Imgur oAuth Secret Token
```

  - *Optional* Create Python virtualenv:
```
pyvenv ./virtualenv
source ./virtualenv/bin/activate
> (virtualenv) $
```

  - Install dependencies for both `python-rtmbot` and `rtmbot-plugin-wallbot`:
```
pip install -r python-rtmbot/requirements.txt
> Successfully installed docutils-0.12 lockfile-0.12.2 python-daemon-2.1.1 pyyaml-3.12 requests-2.11.1 six-1.10.0 slackclient-1.0.1 websocket-client-0.37.0
pip install -r rtmbot-plugin-wallbot/requirements.txt
> Successfully installed imgurpython-1.1.7
```

  - Run `rtmbot`
```
export WALLBOT_CONFIG='./python-rtmbot.conf'
./python-rtmbot/rtmbot.py -c $WALLBOT_CONFIG
```
