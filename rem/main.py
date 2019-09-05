import json
import logging
import os
import traceback

from flask import Flask
from flask_cors import CORS
from peewee import MySQLDatabase

from apis import api
from core import AuditTable
from core import ContactTable
from core import ResultTable
from core import ScanTable
from core import TaskTable
from core import Utils
from core import VulnTable
from core import db
from core import jwt
from core import marshmallow


class FormatterJSON(logging.Formatter):
    def format(self, record):
        record.message = record.getMessage()
        if self.usesTime():
            record.asctime = self.formatTime(record, self.datefmt)
        log = {
            "severity": record.levelname,
            "message": record.message,
            "module": record.module,
            "filename": record.filename,
            "funcName": record.funcName,
            "levelno": record.levelno,
            "lineno": record.lineno,
            "traceback": {},
        }
        if record.exc_info:
            exception_data = traceback.format_exc().splitlines()
            log["traceback"] = exception_data

        return json.dumps(log, ensure_ascii=False)


formatter = FormatterJSON(
    "[%(levelname)s]\t%(asctime)s.%(msecs)dZ\t%(levelno)s\t%(message)s\n", "%Y-%m-%dT%H:%M:%S"
)

logging.basicConfig(level=logging.INFO)
logging.getLogger().handlers[0].setFormatter(formatter)

app = Flask(__name__)

if Utils.is_gcp():
    # Use Cloud SQL for Google Cloud Platform
    Utils.load_env_from_config_file(os.environ["CONFIG_ENV_FILE_PATH"])
    app.config["DATABASE"] = MySQLDatabase(
        os.environ["DB_NAME"],
        unix_socket=os.path.join("/cloudsql", os.environ["DB_INSTANCE_NAME"]),
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
    )
else:
    # Use MySQL official docker image for local environment
    app.config["DATABASE"] = MySQLDatabase(
        os.getenv("DB_NAME", "casval"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", "Passw0rd!"),
        host=os.getenv("DB_ENDPOINT", "127.0.0.1"),
        port=int(os.getenv("DB_PORT", "3306")),
    )

app.config["ADMIN_PASSWORD"] = os.getenv("ADMIN_PASSWORD", "admin-password")
app.config["PERMITTED_SOURCE_IP_RANGES"] = os.getenv("PERMITTED_SOURCE_IP_RANGES", "")
app.config["PERMITTED_ORIGINS"] = os.getenv("PERMITTED_ORIGINS", "*")
app.config["JWT_SECRET_KEY"] = os.getenv("SECRET_KEY", "super-secret")
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = 3 * 3600  # 3 hours
app.config["JWT_IDENTITY_CLAIM"] = "sub"
app.config["RESTPLUS_MASK_SWAGGER"] = False
app.config["SWAGGER_UI_REQUEST_DURATION"] = True
app.config["SWAGGER_UI_DOC_EXPANSION"] = "list"
app.config["SWAGGER_UI_JSONEDITOR"] = True

api.init_app(app)
db.init_app(app)
jwt.init_app(app)
jwt._set_error_handler_callbacks(api)
marshmallow.init_app(app)
CORS(app, origins=app.config["PERMITTED_ORIGINS"])

with db.database:
    db.database.create_tables([AuditTable, ContactTable, ScanTable, TaskTable, VulnTable, ResultTable])


@app.after_request
def add_header(response):
    response.headers["Cache-Control"] = "private, no-store, no-cache, must-revalidate"
    return response
