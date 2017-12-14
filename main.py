import os
import time
import slackclient

SLACK_TOKEN = os.environ.get('SLACK_BOT_TOKEN')
CHANNEL = 'outage'

# initialize slack client
sc = slackclient.SlackClient(SLACK_TOKEN)

# check if everything is alright
is_ok = sc.api_call("users.list").get('ok')
print(is_ok)

def get_channel_name(channel_id):
    channel_info = sc.api_call("channels.info", channel=channel_id)
    return channel_info["channel"]["name"]

def write_to_chan(msg):
    sc.api_call(
            "chat.postMessage",
            channel="#"+CHANNEL,
            text=msg)

def handle_event(event):
    #print(event)
    if event.get('type') == 'message' and get_channel_name(event.get('channel')) == CHANNEL:
        msg = event.get('text')
        print(msg)

def listen_to_chan():
    if sc.rtm_connect():
        print('Slack client connected...')
        while True:
            events = sc.rtm_read()
            for event in events:
                handle_event(event)
            time.sleep(0.1)
    else:
        print('Connection to Slack failed.')

if __name__=='__main__':
    write_to_chan("Ready to call an outage :red_circle:")
    listen_to_chan()
