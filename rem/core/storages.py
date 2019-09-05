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

    def store(self, key, body):
        try:
            filepath = self.results_dir + "/" + key
            with open(filepath, "w", encoding="utf8") as file:
                file.write(body)
        except Exception as e:
            app.logger.warn(e)
            return False

        return True


class CloudFileStorage:

    RESULT_DIR_NAME = "results/"

    def __init__(self):
        self.client = storage.Client(project=os.environ["GCP_PROJECT_NAME"])
        self.bucket = self.client.get_bucket(os.environ["GCP_REPORT_STORAGE_NAME"])

    def store(self, key, body):
        try:
            blob = self.bucket.blob(self.RESULT_DIR_NAME + key)
            blob.upload_from_string(body)
        except Exception as e:
            app.logger.warn(e)
            return False

        return True
