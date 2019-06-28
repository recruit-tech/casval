import os

from flask import current_app as app
from google.cloud import storage


class LocalFileStorage:

    RESULT_DIR_NAME = "/results"

    def __init__(self):
        self.results_dir = os.path.realpath(
            os.path.dirname(os.path.abspath(__file__)) + "/.." + self.RESULT_DIR_NAME
        )
        os.makedirs(self.results_dir, exist_ok=True)

    def load(self, key):
        try:
            with open(self.results_dir + "/" + key, "r", encoding="utf8") as file:
                body = file.read()
            return body
        except Exception as e:
            app.logger.error(e)
            return None

    def store(self, key, body):
        try:
            filepath = self.results_dir + "/" + key
            with open(filepath, "w", encoding="utf8") as file:
                file.write(body)
        except Exception as e:
            app.logger.error(e)
            return False

        return True


class CloudFileStorage:

    RESULT_DIR_NAME = "results/"

    def __init__(self):
        self.client = storage.Client(project=os.environ["GCP_PROJECT_NAME"])
        self.bucket = self.client.get_bucket(os.environ["GCP_REPORT_STORAGE_NAME"])

    def load(self, key):
        try:
            blob = self.bucket.get_blob(self.RESULT_DIR_NAME + key)
            return blob.download_as_string().decode("utf-8")
        except Exception as e:
            app.logger.error(e)
            return None

    def store(self, key, body):
        try:
            blob = self.bucket.blob(self.RESULT_DIR_NAME + key)
            blob.upload_from_string(body)
        except Exception as e:
            app.logger.error(e)
            return False

        return True
