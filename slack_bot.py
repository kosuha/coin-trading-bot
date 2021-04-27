import requests
import config.slack_token as slack

def post_message(text):
    response = requests.post("https://slack.com/api/chat.postMessage",
        headers={"Authorization": "Bearer "+ slack.token},
        data={"channel": "#coin", "text": text}
    )
    # print(response)