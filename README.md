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

  - Clone `rtmbot-plugin-wallbot` from GitHub:
```shell
git clone https://github.com/benfairless/rtmbot-plugin-wallbot.git
> Cloning into 'rtmbot-plugin-wallbot'...
> remote: Counting objects: 5, done.
> remote: Compressing objects: 100% (4/4), done.
> remote: Total 5 (delta 0), reused 5 (delta 0), pack-reused 0
> Unpacking objects: 100% (5/5), done.
> Checking connectivity... done.
```

  - Create a Python virtualenv *optional*:
```shell
python3 -m venv ./.virtualenv && source ./.virtualenv/bin/activate
```

- Install dependencies:
```shell
pip install -r requirements.txt
```

  - Copy the example configuration file:
```shell
cp rtmbot.conf.example rtmbot.conf
```

  - Edit the configuration file found at `rtmbot.conf`:
```yaml
DEBUG: False
SLACK_TOKEN: "xoxb-XXXXXXXXXXX-XXXXXXXXXXXXXXXXXXXXXXXX"
ACTIVE_PLUGINS:
 - wallbot.plugin.Wallbot

Wallbot:
  ALLOW_UNTRUSTED: True # Disable once users are added to trust list
  AUDIT_CHANNEL: 'GXXXXXXXX'
  AUDIT_FILE: 'audit.log'
  TRUST_FILE: 'trust.json'
  POST_FILE: 'html/post.json'
```

  - Run `rtmbot`
```
rtmbot
```
