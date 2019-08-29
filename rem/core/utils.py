import binascii
import hashlib
import ipaddress
import os
import re
import socket
from datetime import datetime
from urllib.parse import urlparse

import validators
from flask import current_app as app

PASSWORD_SALT = os.getenv("PASSWORD_SALT", "password-salt")
PASSWORD_HASH_ALG = "sha256"
PASSWORD_ITERATION = 1000
SLACK_DOMAIN = "slack.com"


class Utils:
    @staticmethod
    def is_source_ip_permitted(source_ip_str):
        if len(app.config["PERMITTED_SOURCE_IP_RANGES"]) == 0:
            return True

        permitted_ip_ranges = app.config["PERMITTED_SOURCE_IP_RANGES"].split(",")
        source_ip = ipaddress.ip_address(source_ip_str)

        for permitted_ip_range in permitted_ip_ranges:
            permitted_ip_network = ipaddress.ip_network(permitted_ip_range)
            if source_ip in permitted_ip_network:
                return True

        return False

    @staticmethod
    def load_env_from_config_file(config_file_path):
        with open(config_file_path, "r") as f:
            content = f.readlines()
            content = [re.split("\s*=\s*", x.strip(), 1) for x in content if "=" in x]
            for k, v in dict(content).items():
                os.environ[k] = v
            return True

    @staticmethod
    def get_password_hash(password):
        return binascii.hexlify(
            hashlib.pbkdf2_hmac(
                PASSWORD_HASH_ALG, password.encode(), PASSWORD_SALT.encode(), PASSWORD_ITERATION
            )
        ).decode("utf-8")

    @staticmethod
    def is_ipv4(value):
        try:
            return validators.ip_address.ipv4(value)
        except Exception:
            return False

    @staticmethod
    def is_public_address(value):
        try:
            return ipaddress.ip_address(value).is_global
        except Exception:
            return False

    @staticmethod
    def is_domain(value):
        try:
            return validators.domain(value)
        except Exception:
            return False

    @staticmethod
    def is_host_resolvable(value):
        try:
            return len(socket.gethostbyname(value)) > 0
        except Exception:
            return False

    @staticmethod
    def is_slack_url(value):
        try:
            url = urlparse(value)
            return url.hostname.endswith(SLACK_DOMAIN)
        except Exception:
            return False

    @staticmethod
    def get_default_datetime():
        return datetime(1, 1, 1)

    @staticmethod
    def format_openvas_description(value):
        desc = re.sub("\n{2,}", "\n", value)
        desc = re.sub(r"^(\w+)=", r"\1\n", desc)
        desc = re.sub(r"\|(\w+)=", r"\n\n\1\n", desc)
        return desc

    @staticmethod
    def is_local():
        return not bool(os.getenv("CONFIG_ENV_FILE_PATH", ""))
