import json

import requests

USERNAME = "CASVAL"
ICON_EMOJI = ":robot_face:"


class SlackIntegrator:

    COLOR_DANGER = "#ff0000"
    COLOR_WARNING = "warning"
    COLOR_UNRATED = "#000000"
    COLOR_GOOD = "good"

    def __init__(self, webhook_url):
        self.webhook_url = webhook_url

    def send(self, title, attachments):
        payload = {"username": USERNAME, "icon_emoji": ICON_EMOJI, "text": title}
        if attachments:
            payload["attachments"] = attachments

        requests.post(self.webhook_url, data=json.dumps(payload))
