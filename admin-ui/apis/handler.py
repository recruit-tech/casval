from flask import abort
from flask_restplus import Namespace
from flask_restplus import Resource

from core import DeletedTask
from core import FailedTask
from core import PendingTask
from core import RunningTask
from core import StoppedTask

api = Namespace("handler")


@api.route("/<string:task>/")
@api.doc(security="None")
@api.response(200, "Success")
class TaskHandler(Resource):
    def get(self, task):
        """Invoke task handlers"""

        if task == "pending":
            PendingTask().handle()
        elif task == "running":
            RunningTask().handle()
        elif task == "stopped":
            StoppedTask().handle()
        elif task == "failed":
            FailedTask().handle()
        elif task == "deleted":
            DeletedTask().handle()
        else:
            abort(404)

        return True
