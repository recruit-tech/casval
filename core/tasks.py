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
from .resources import AuditResource
from .scanners import OpenVASScanner as Scanner
from .scanners import ScannerException
from .scanners import ScanStatus
from .slack import SlackIntegrator
from .utils import Utils

if Utils.is_local():
    # For local environment
    from .storages import LocalFileStorage as Storage
else:
    # For google cloud platform environment
    from .storages import CloudFileStorage as Storage

SCAN_MAX_PARALLEL_SESSION = os.getenv("SCAN_MAX_PARALLEL_SESSION", 1)
SCAN_REPORT_KEY_NAME = "{audit_id:08}-{scan_id:08}-{task_uuid:.8}.xml"
SCAN_MAX_DURATION_IN_HOUR = 24


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
                app.logger.exception("Exception, task={}, error={}".format(task, error))

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

    def _notify_to_slack(self, task, next_progress):
        message_mode = ""

        if next_progress == TaskProgress.RUNNING.name:
            message_mode = SlackIntegrator.MessageMode.STARTED
        elif next_progress == TaskProgress.FAILED.name:
            message_mode = SlackIntegrator.MessageMode.FAILED
        elif task["progress"] == TaskProgress.STOPPED.name and next_progress == TaskProgress.DELETED.name:
            message_mode = SlackIntegrator.MessageMode.COMPLETED

        if message_mode:
            webhook_url = task["slack_webhook_url"]

            if not webhook_url:
                audit = AuditResource.get_by_id(task["audit_id"])
                webhook_url = audit["slack_default_webhook_url"]
            if webhook_url:
                try:
                    SlackIntegrator(webhook_url).send(message_mode, task)
                except Exception as error:
                    app.logger.warn("Failed to send to Slack. error={}".format(error))

    def _update(self, task, next_progress):
        self._notify_to_slack(task, next_progress)
        task["progress"] = next_progress
        if next_progress == TaskProgress.DELETED.name:
            if task.get("session") is not None:
                try:
                    Scanner(json.loads(task["session"])).delete()
                except Exception as error:
                    app.logger.exception("Exception, task={}, error={}".format(task, error))
        TaskTable.update(task).where(TaskTable.id == task["id"]).execute()

    def _process(self, task):
        app.logger.exception("Error, needs to override `process` method")


class PendingTask(BaseTask):
    def __init__(self):
        super().__init__(TaskProgress.PENDING.name)

    def add(self, entry):
        entry["progress"] = TaskProgress.PENDING.name
        task = TaskTable(**entry)
        task.save()
        return task

    def _set_scan_started_time(self, task):
        now = datetime.now(tz=pytz.utc)
        ScanTable.update({"started_at": now}).where(ScanTable.task_uuid == task["uuid"]).execute()

    def _process(self, task):
        running_task_num = self._get_running_task_count()
        if running_task_num >= SCAN_MAX_PARALLEL_SESSION:
            app.logger.info("Abandoned to launch scan, already running {} task(s).".format(running_task_num))
            return False

        start_at = task["start_at"].replace(tzinfo=pytz.utc)
        end_at = task["end_at"].replace(tzinfo=pytz.utc)
        now = datetime.now(tz=pytz.utc)

        if start_at > now:
            # The scheduled time has not come yet.
            return True

        if end_at < (now + timedelta(hours=1)):
            task["error_reason"] = "The scan has been abandoned since the `end_at` is soon or over."
            app.logger.warn("Abandoned to launch scan, task={task}".format(task=task))
            self._update(task, next_progress=TaskProgress.FAILED.name)
            return True

        if self._is_task_expired(task):
            task["error_reason"] = "The scan has been cancelled by user."
            app.logger.info("Task deleted silently, task={task}".format(task=task))
            self._update(task, next_progress=TaskProgress.DELETED.name)
            return True

        scanner = None
        if task.get("session") == "":
            scanner = Scanner()
        else:
            scanner = Scanner(json.loads(task["session"]))

        session = scanner.create()
        task["session"] = json.dumps(session)

        if session is None:
            self._update(task, next_progress=TaskProgress.PENDING.name)
            return True

        if session["status"] != "CREATED":
            self._update(task, next_progress=TaskProgress.PENDING.name)
            return True

        self._set_scan_started_time(task)
        session = Scanner(json.loads(task["session"])).launch_scan(task["target"])
        task["session"] = json.dumps(session)
        task["started_at"] = now
        app.logger.info("Scan launched successfully, task={task}".format(task=task))
        self._update(task, next_progress=TaskProgress.RUNNING.name)
        return True


class RunningTask(BaseTask):
    def __init__(self):
        super().__init__(TaskProgress.RUNNING.name)

    def _update(self, task, next_progress):
        now = datetime.now(tz=pytz.utc)
        ScanTable.update({"ended_at": now}).where(ScanTable.task_uuid == task["uuid"]).execute()
        task["ended_at"] = now
        super()._update(task, next_progress)

    def _process(self, task):
        end_at = task["end_at"].replace(tzinfo=pytz.utc)
        started_at = task["started_at"].replace(tzinfo=pytz.utc)
        now = datetime.now(tz=pytz.utc)

        if now > (started_at + timedelta(hours=SCAN_MAX_DURATION_IN_HOUR)):
            task[
                "error_reason"
            ] = "The scan has been terminated since the scan took more than {} hours.".format(
                SCAN_MAX_DURATION_IN_HOUR
            )
            app.logger.warn("Scan deleted by timeout, task_uuid={task}".format(task=task))
            self._update(task, next_progress=TaskProgress.FAILED.name)
            return True

        if end_at <= now:
            task["error_reason"] = "The scan has been terminated since the `end_at` is over."
            app.logger.warn("Scan deleted since it exceeded end_at, task_uuid={task}".format(task=task))
            self._update(task, next_progress=TaskProgress.FAILED.name)
            return True

        if self._is_task_expired(task):
            task["error_reason"] = "The scan has been cancelled by user."
            app.logger.warn("Scan deleted forcibly, task={task}".format(task=task))
            self._update(task, next_progress=TaskProgress.DELETED.name)
            return True

        try:
            status = Scanner(json.loads(task["session"])).check_status()
        except ScannerException as error:
            task["error_reason"] = "Scan server error"
            app.logger.exception("Exception, task={}, error={}".format(task, error))
            self._update(task, next_progress=TaskProgress.FAILED.name)
            return True

        if status == ScanStatus.STOPPED:
            app.logger.info("Scan stopped successfully, task={task}".format(task=task))
            self._update(task, next_progress=TaskProgress.STOPPED.name)
        elif status == ScanStatus.FAILED:
            task["error_reason"] = "The scan has failed."
            app.logger.exception("Scan failed, task={task}".format(task=task))
            self._update(task, next_progress=TaskProgress.FAILED.name)
        else:
            app.logger.info("Scan ongoing, status={}, task={}".format(status, task))

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
                    vuln_query = VulnTable.insert(vuln).on_conflict_ignore()
                    vuln_query.execute()

                ResultTable.delete().where(ResultTable.scan_id == task["scan_id"]).execute()

                for result in report["results"]:
                    result["scan_id"] = task["scan_id"]
                    result_query = ResultTable.insert(result)
                    result_query.execute()

        show_result_query = (
            ResultTable.select(
                ResultTable.oid, ResultTable.name, ResultTable.host, ResultTable.port, VulnTable.fix_required
            )
            .join(VulnTable, on=(VulnTable.oid == ResultTable.oid))
            .where(ResultTable.scan_id == task["scan_id"])
            .order_by(ResultTable.oid.desc())
        )

        results = []
        for result in show_result_query.dicts():
            results.append(result)

        task["results"] = results
        task["error_reason"] = "None!"
        app.logger.info("Scan deleted successfully, task={}".format(task))
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
            app.logger.exception("Exception, task={}, error={}".format(task, error))

        task["error_reason"] += " (from Failed Task)"
        app.logger.info("Scan delete, task={task}".format(task=task))
        self._update(task, next_progress=TaskProgress.DELETED.name)
        return


class DeletedTask:
    @staticmethod
    def handle():
        # TODO
        return {}
