import json
import os
from datetime import datetime
from datetime import timedelta
from enum import Enum
from enum import auto

import pytz
from flask import current_app as app
from peewee import fn

from .models import ResultTable
from .models import ScanTable
from .models import TaskTable
from .models import VulnTable
from .models import db
from .scanners import OpenVASScanner as Scanner
from .scanners import ScanStatus
from .utils import Utils

if len(os.getenv("CONFIG_ENV_FILE_PATH", "")) > 0:
    # for production environment
    from .storages import CloudFileStorage as Storage
else:
    # for development environment
    from .storages import LocalFileStorage as Storage

SCAN_MAX_PARALLEL_SESSION = 1
SCAN_REPORT_KEY_NAME = "{audit_id:08}-{scan_id:08}-{task_uuid:.8}.xml"


class TaskProgress(Enum):
    PENDING = auto()
    RUNNING = auto()
    STOPPED = auto()
    FAILED = auto()
    DELETED = auto()


class BaseTask:
    def __init__(self, progress):
        self.progress = progress

    def handle(self):
        for task in self._get_tasks():
            try:
                result = self._process(task)
                if result == False:
                    # Skip subsequent tasks and return
                    return False
            except Exception as error:
                app.logger.error("[Task] Exception, task={}, error={}".format(task, error))

        return True

    def _get_tasks(self):
        task_query = (
            TaskTable.select().where(TaskTable.progress == self.progress).order_by(TaskTable.updated_at.asc())
        )
        return list(task_query.dicts())

    def _get_running_task_count(self):
        task_query = TaskTable.select(fn.Count(TaskTable.id).alias("count")).where(
            TaskTable.progress == TaskProgress.RUNNING.name
        )
        return task_query.dicts().get()["count"]

    def _is_task_expired(self, task):
        scan_query = (
            ScanTable()
            .select(fn.Count(ScanTable.id).alias("count"))
            .where((ScanTable.task_uuid == task["uuid"]))
        )
        return scan_query.dicts().get()["count"] == 0

    def _update(self, task, next_progress):
        task["progress"] = next_progress
        TaskTable.update(task).where(TaskTable.id == task["id"]).execute()

    def _process(self, task):
        app.logger.error("[Task] Error, needs to override `process` method")


class PendingTask(BaseTask):
    def __init__(self):
        super().__init__(TaskProgress.PENDING.name)

    def add(self, entry):
        entry["progress"] = TaskProgress.PENDING.name
        task = TaskTable(**entry)
        task.save()
        return task

    def _process(self, task):
        running_task_num = self._get_running_task_count()
        if running_task_num >= SCAN_MAX_PARALLEL_SESSION:
            app.logger.info("[Pending Task] Abandoned, already running {} task(s).".format(running_task_num))
            return False

        start_at = task["start_at"].replace(tzinfo=pytz.utc)
        end_at = task["end_at"].replace(tzinfo=pytz.utc)
        now = datetime.now(tz=pytz.utc).astimezone(pytz.timezone("Asia/Tokyo"))

        if start_at > now:
            # The scheduled time has not come yet.
            return True

        if end_at < (now + timedelta(hours=1)):
            task["error_reason"] = "The scan has been abandoned since the `end_at` is soon or over."
            app.logger.info("[Pending Task] Abandoned, task={task}".format(task=task))
            self._update(task, next_progress=TaskProgress.FAILED.name)
            return True

        if self._is_task_expired(task):
            task["error_reason"] = "The scan has been cancelled by user."
            app.logger.info("[Pending Task] Removed silently, task={task}".format(task=task))
            self._update(task, next_progress=TaskProgress.DELETED.name)
            return True

        session = Scanner().launch_scan(task["target"])
        task["session"] = json.dumps(session)
        app.logger.info("[Pending task] Launched successfully, task={task}".format(task=task))
        self._update(task, next_progress=TaskProgress.RUNNING.name)
        return True


class RunningTask(BaseTask):
    def __init__(self):
        super().__init__(TaskProgress.RUNNING.name)

    def _process(self, task):
        end_at = task["end_at"].replace(tzinfo=pytz.utc)
        now = datetime.now(tz=pytz.utc).astimezone(pytz.timezone("Asia/Tokyo"))

        if end_at <= now:
            Scanner(json.loads(task["session"])).terminate_scan()
            task["error_reason"] = "The scan has been terminated since the `end_at` is over."
            app.logger.info("[Running Task] Scan terminated by timeout, task_uuid={task}".format(task=task))
            self._update(task, next_progress=TaskProgress.FAILED.name)
            return True

        if self._is_task_expired(task):
            Scanner(json.loads(task["session"])).terminate_scan()
            task["error_reason"] = "The scan has been cancelled by user."
            app.logger.info("[Running Task] Scan terminated forcibly, task={task}".format(task=task))
            self._update(task, next_progress=TaskProgress.DELETED.name)
            return True

        status = Scanner(json.loads(task["session"])).check_status()

        if status == ScanStatus.STOPPED:
            app.logger.info("[Running Task] Scan stopped successfully, task={task}".format(task=task))
            self._update(task, next_progress=TaskProgress.STOPPED.name)
        elif status == ScanStatus.FAILED:
            task["error_reason"] = "The scan has failed."
            app.logger.info("[Running Task] Scan failed, task={task}".format(task=task))
            self._update(task, next_progress=TaskProgress.FAILED.name)
        else:
            app.logger.info("[Running Task] Scan ongoing, status={}, task={}".format(status, task))

        return True


class StoppedTask(BaseTask):
    def __init__(self):
        super().__init__(TaskProgress.STOPPED.name)

    def _process(self, task):
        storage = Storage()
        key = SCAN_REPORT_KEY_NAME.format(
            audit_id=task["audit_id"], scan_id=task["scan_id"], task_uuid=task["uuid"].hex
        )

        report = storage.load(key)
        if report is None:
            report = Scanner(json.loads(task["session"])).get_report()
            storage.store(key, report)

        report = Scanner.parse_report(report)

        with db.database.atomic():

            if self._is_task_expired(task) == False:

                data = {
                    "error_reason": "",
                    "task_uuid": None,
                    "scheduled": False,
                    "processed": True,
                    "start_at": Utils.get_default_datetime(),
                    "end_at": Utils.get_default_datetime(),
                }

                scan_query = ScanTable.update(data).where(ScanTable.task_uuid == task["uuid"])
                scan_query.execute()

                for vuln in report["vulns"]:
                    vuln_query = VulnTable.insert(vuln).on_conflict(
                        preserve=[VulnTable.fix_required], update=vuln
                    )
                    vuln_query.execute()

                ResultTable.delete().where(ResultTable.scan_id == task["scan_id"]).execute()

                for result in report["results"]:
                    result["scan_id"] = task["scan_id"]
                    result_query = ResultTable.insert(result)
                    result_query.execute()

            task["error_reason"] = "None!"
            app.logger.info("[Stopped Task] Deleted, task={}".format(task))
            self._update(task, next_progress=TaskProgress.DELETED.name)

        return True


class FailedTask(BaseTask):
    def __init__(self):
        super().__init__(TaskProgress.FAILED.name)

    def _process(self, task):
        try:
            result = {
                "error_reason": task["error_reason"],
                "task_uuid": None,
                "scheduled": False,
                "processed": True,
                "start_at": Utils.get_default_datetime(),
                "end_at": Utils.get_default_datetime(),
            }
            scan_query = ScanTable.update(result).where(ScanTable.task_uuid == task["uuid"])
            scan_query.execute()
        except Exception as error:
            app.logger.error("[Failed Task] Exception, task={}, error={}".format(task, error))

        task["error_reason"] += " (from Failed Task)"
        app.logger.info("[Failed Task] Deleted, task={task}".format(task=task))
        self._update(task, next_progress=TaskProgress.DELETED.name)
        return


class DeletedTask:
    @staticmethod
    def handle():
        # TODO
        print("handle!")
        return {}
