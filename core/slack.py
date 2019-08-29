import json
from enum import Enum
from enum import auto

import requests

USERNAME = "CASVAL"
ICON_EMOJI = ":robot_face:"
COLOR_DANGER = "#ff0000"
COLOR_WARNING = "warning"
COLOR_UNRATED = "#000000"
COLOR_GOOD = "good"


class SlackIntegrator:
    class MessageMode(Enum):
        STARTED = auto()
        FAILED = auto()
        COMPLETED = auto()

    def __init__(self, webhook_url):
        self.webhook_url = webhook_url

    def send(self, message_mode, task):
        payload = {"username": USERNAME, "icon_emoji": ICON_EMOJI}

        if message_mode == SlackIntegrator.MessageMode.STARTED:
            payload["text"] = "Now scanning *{target}*.".format(target=task["target"])
        elif message_mode == SlackIntegrator.MessageMode.FAILED:
            payload["text"] = ":rotating_light: *Scan error at {target}*.".format(target=task["target"])
        elif message_mode == SlackIntegrator.MessageMode.COMPLETED:
            fix_required = {"REQUIRED": 0, "RECOMMENDED": 0, "OPTIONAL": 0, "UNDEFINED": 0}

            for result in task["results"]:
                fix_required[result["fix_required"]] += 1

            elapsed_time = task["ended_at"] - task["started_at"]
            elapsed_minutes = (elapsed_time.days * 24 * 60) + (elapsed_time.seconds / 60)
            payload["text"] = "Scan for *{target}* completed ({elapsed} min).".format(
                target=task["target"], elapsed=int(elapsed_minutes)
            )

            attachments = []
            if fix_required["REQUIRED"] > 0:
                title = "Urgent Response Required ({count})".format(count=fix_required["REQUIRED"])
                item = {"color": COLOR_DANGER, "fields": [{"title": title}]}
                attachments.append(item)
            if fix_required["RECOMMENDED"] > 0:
                title = "Fix Recommended ({count})".format(count=fix_required["RECOMMENDED"])
                item = {"color": COLOR_WARNING, "fields": [{"title": title}]}
                attachments.append(item)
            if fix_required["UNDEFINED"] > 0:
                title = "Severity Unrated ({count})".format(count=fix_required["UNDEFINED"])
                item = {"color": COLOR_UNRATED, "fields": [{"title": title}]}
                attachments.append(item)
            if len(attachments) == 0:
                title = "No Response Required :tada:"
                item = {"color": COLOR_GOOD, "fields": [{"title": title}]}
                attachments.append(item)
            payload["attachments"] = attachments

        requests.post(self.webhook_url, data=json.dumps(payload))
