# groupme-slack-connect

The code connects a GroupMe group to Slack channel.

This was useful when going from GroupMe to Slack but still support legacy users (e.g., on SMS, etc.)

I tried using sameroom.io but it was too limited as a free trial version (only 5 messages in 24 hrs)

## Environment Variables
It expects the following environment variables:
- APP_ID: Slack bot APP_ID (e.g., `Axxxxxxx`)
- TEAM_ID: Slack bot TEAM_ID (e.g, `Txxxxxxx`)
- VERIFICATION_TOKEN: Slac bot Verification Token
- SLACK_BOT_TOKEN: (Slack bot token `xoxb-XXXX...` Get it in OAuth setting of Slack Bot)
- SLACK_INVITE_LINK: (if you want people to join Slack in the forwarded message in GroupMe: e.g., `https://join.slack.com...`)
- GROUPME_GROUP_TO_BOT_ID: JSON string mapping GroupMe group to Bot ID (e.g., `'{"12345678":"abcdef1234567890", ...}'`)
- GROUPME_GROUP_TO_SLACK_CHANNEL: JSON string mapping GroupMe group to Slack channel (e.g., `'{"12345678":"Cxxxxxx", ...}'`)

## GroupMe Setup
Create a bot in GroupMe and get the Access Token for the app.

https://dev.groupme.com/applications/

The following command will return all the group information in JSON. Find the `group_id` of the group you're trying to connect to.
```
curl "https://api.groupme.com/v3/groups?token=<ACCESS_TOKEN>"
```

Then the following command will add the app to the group. Note the `bot_id` that gets returned. (You will need to run this for each group you want to connect to Slack.)
```
curl -X POST -d '{"bot": { "name": "slack-groupme-connect", "group_id": "<GROUP_ID>", "callback_url": "<CALLBACK/groupme-callback>"}}' -H 'Content-Type: application/json' "https://api.groupme.com/v3/bots?token=<ACCESS_TOKEN>"
```
Note that the callback will be on your server (e.g., Heroku) and URI `/groupme-callback`.

Create a JSON string of `group_id`:`bot_id` for each group you want connected.
```
GROUPME_GROUP_TO_BOT_ID='{"GROUP_ID1":"BOT_ID1", "GROUP_ID2","BOT_ID2"}'
```

## Slack Setup
Create a bot. In Settings->Basic Information->App Credentials, you will note the following variables:
- APP_ID: Slack bot APP_ID (e.g., `Axxxxxxx`)
- TEAM_ID: Slack bot TEAM_ID (e.g, `Txxxxxxx`)
- VERIFICATION_TOKEN: Slac bot Verification Token

OAuth and Permissions->Scopes, add the following:
- channels:history
- groups:history
- chat:write
- users:read
Install and note the Bot User OAuth Token (`xoxb-XXXXX...`)

Then in Event Subscriptions (once you deployed the app...), set the callback URL and subscribe to the bot events:
- message:channels
- message:groups

Create an Invite Link on Slack and set `SLACK_INVITE_LINK`