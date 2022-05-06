import os
import sys
import json
import requests

from flask import Flask, request, Response

app = Flask(__name__)

@app.route('/slack-callback/', methods=['POST'])
def slack_event_hook():
  params = request.get_json(force=True)
  log('Recieved from Slack: {}'.format(params))
  if 'challenge' in params:
    data = {
      'challenge': params.get('challenge'),
    }
    resp = Response(
      response=json.dumps(data),
      status=200,
      mimetype='application/json'
    )
    resp.headers['Content-type'] = 'application/json'
    return resp
  if validate(params):
    if params["event"]["type"] == "message" and "subtype" not in params["event"] and "app_id" not in params["event"]:
      text = params["event"]["text"]
      slack_user_id = params["event"]["user"]
      slack_channel = params["event"]["channel"]

      groupme_group = get_groupme_group_by_slack_channel(slack_channel)
      if (groupme_group is None):
        return "ok", 200
      groupme_bot_id = get_bot_id_by_groupme_group(groupme_group)
      if (groupme_bot_id is None):
        return "ok", 200
      name = get_name_from_slack_user_id(slack_user_id)
      if (name is None):
        return "ok", 200
      msg = '(Message was received in Slack)\n{}:\n{}\n\n(Join Slack: {})'.format(name,text,os.environ['SLACK_INVITE_LINK'])
      groupme_send_message(groupme_bot_id,msg)
  return "ok", 200


@app.route('/groupme-callback/', methods=['POST'])
def groupme_event_hook():
  data = request.get_json()
  log('Recieved from groupme: {}'.format(data))

  if data['sender_type'] == 'user':
    slack_channel = get_slack_channel_by_groupme_group(data['group_id'])
    if (slack_channel is None):
      log('Slack channel not found for the groupme group {}'.format(data['group_id']))
      return "ok", 200

    msg = '(Message was received in GroupMe)\n{}:\n{}'.format(data['name'], data['text'])
    slack_send_message(slack_channel, msg)

  return "ok", 200


def validate(params):
  if params["event"]["type"] != "message":
    log("Event type is ", params["event"]["type"], "but not `message`")

  app_id = params["api_app_id"] == os.environ["APP_ID"]
  token = params["token"] == os.environ["VERIFICATION_TOKEN"]
  team = params["team_id"] == os.environ["TEAM_ID"]

  if app_id and token and team:
    log("slack request validation completed successfully")
    return True
  else:
    if not app_id:
      log("env: APP_ID is not right!")
    if not token:
      log("env: TOKEN is not right!")
    if not team:
      log("env: TEAM_ID is not right!")
  log("slack request validation completed successfully")
  return False


def get_name_from_slack_user_id(slack_user_id):
  log("getting the name of the slack user from id {}".format(slack_user_id))
  headers = {
    "content-type": "application/x-www-form-urlencoded",
    "Authorization": "Bearer " + os.getenv('SLACK_BOT_TOKEN'),
  }
  r = requests.get("https://slack.com/api/users.info?user="+slack_user_id, headers=headers)
  if (r.status_code == 200):
    r_json = json.loads(r.text)
    if r_json["ok"]:
      log("found the slack user (real) name {}".format(r_json["user"]["real_name"]))
      return r_json["user"]["real_name"]
  log("could not find the slack user information for ID {}, status: {}, resp: {}".format(slack_user_id, r.status_code, r.text))
  return None


def get_slack_channel_by_groupme_group(groupme_group):
  map_groupme_group_to_slack_channel = json.loads(os.getenv('GROUPME_GROUP_TO_SLACK_CHANNEL'))
  if groupme_group in map_groupme_group_to_slack_channel:
    log("found the slack channel {} from groupme_group {}".format(map_groupme_group_to_slack_channel[groupme_group],groupme_group))
    return map_groupme_group_to_slack_channel[groupme_group]
  log("Could not find slack channel for groupme_group {}".format(groupme_group))
  return None


def get_groupme_group_by_slack_channel(slack_channel):
  map_groupme_group_to_slack_channel = json.loads(os.getenv('GROUPME_GROUP_TO_SLACK_CHANNEL'))
  for g in map_groupme_group_to_slack_channel:
    if map_groupme_group_to_slack_channel[g] == slack_channel:
      log("found the groupme group {} from slack channel {}".format(slack_channel,g))
      return g
  log("Could not find groupme_group for slack channel {}".format(slack_channel))
  return None


def get_bot_id_by_groupme_group(groupme_group):
  map_groupme_group_to_bot_id = json.loads(os.getenv('GROUPME_GROUP_TO_BOT_ID'))

  if groupme_group in map_groupme_group_to_bot_id:
    log("found the groupme bot_id {} from groupme_group {}".format(map_groupme_group_to_bot_id[groupme_group],groupme_group))
    return map_groupme_group_to_bot_id[groupme_group]
  return None


def slack_send_message(channel, msg):
  log("sending message to slack channel {}:{}".format(channel, msg))
  data = {
    "channel": channel,
    "text": msg,
  }
  headers = {
    "content-type": "application/json;charset=UTF-8",
    "Authorization": "Bearer " + os.getenv('SLACK_BOT_TOKEN'),
  }
  r = requests.post("https://slack.com/api/chat.postMessage", headers=headers, json=data)
  log("chat.postMessage Exit with status code {}".format(r.status_code))


def groupme_send_message(bot_id, msg):
  log("sending message to groupme:{}".format(msg))
  data = {
    'bot_id' : bot_id,
    'text'   : msg,
  }
  headers = {
    "content-type": "application/json;charset=UTF-8",
  }
  r = requests.post('https://api.groupme.com/v3/bots/post', headers=headers, json=data)
  log("bots/post Exit with status code {}".format(r.status_code))

def log(msg):
  print(str(msg))
  sys.stdout.flush()