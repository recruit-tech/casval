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
from .scanners import ScanServerException
from .scanners import ScanStatus
from .slack import SlackIntegrator
from .utils import Utils

if Utils.is_gcp():
    from .storages import CloudFileStorage as Storage
else:
    from .storages import LocalFileStorage as Storage

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
                if self._is_task_expired(task) and self.progress != TaskProgress.DELETED.name:
                    task["error_reason"] = "Scan was cancelled by user."
                    app.logger.info("Delete task due to cancellation, task={task}".format(task=task))
                    self._update(task, next_progress=TaskProgress.DELETED.name)
                    continue
                is_continuable = self._process(task)
                if not is_continuable:
                    break
            except Exception as error:
                app.logger.exception("Exception, task={}, error={}".format(task, error))
        return True

    def _get_tasks(self):
        task_query = (
            TaskTable.select().where(TaskTable.progress == self.progress).order_by(TaskTable.updated_at.asc())
        )
        return list(task_query.dicts())

    def _is_task_expired(self, task):
        scan_query = (
            ScanTable()
            .select(fn.Count(ScanTable.id).alias("count"))
            .where((ScanTable.task_uuid == task["uuid"]))
        )
        return scan_query.dicts().get()["count"] == 0

    def _get_slack_message(self, task, next_progress):
        title = ""
        attachments = []

        if next_progress == TaskProgress.RUNNING.name:
            title = "Now scanning *{target}*.".format(target=task["target"])
        elif next_progress == TaskProgress.FAILED.name:
            title = ":rotating_light: *Scan error at {target}*.".format(target=task["target"])

        elif task["progress"] == TaskProgress.STOPPED.name and next_progress == TaskProgress.DELETED.name:
            elapsed_time = task["ended_at"] - task["started_at"]
            elapsed_minutes = (elapsed_time.days * 24 * 60) + (elapsed_time.seconds / 60)
            title = "Scan for *{target}* completed ({elapsed} min).".format(
                target=task["target"], elapsed=int(elapsed_minutes)
            )

            fix_required = {"REQUIRED": 0, "RECOMMENDED": 0, "OPTIONAL": 0, "UNDEFINED": 0}
            for result in task["results"]:
                fix_required[result["fix_required"]] += 1

            if fix_required["REQUIRED"] > 0:
                heading = "Urgent Response Required ({count})".format(count=fix_required["REQUIRED"])
                item = {"color": SlackIntegrator.COLOR_DANGER, "fields": [{"title": heading}]}
                attachments.append(item)
            if fix_required["RECOMMENDED"] > 0:
                heading = "Fix Recommended ({count})".format(count=fix_required["RECOMMENDED"])
                item = {"color": SlackIntegrator.COLOR_WARNING, "fields": [{"title": heading}]}
                attachments.append(item)
            if fix_required["UNDEFINED"] > 0:
                heading = "Severity Unrated ({count})".format(count=fix_required["UNDEFINED"])
                item = {"color": SlackIntegrator.COLOR_UNRATED, "fields": [{"title": heading}]}
                attachments.append(item)
            if len(attachments) == 0:
                heading = "No Response Required :tada:"
                item = {"color": SlackIntegrator.COLOR_GOOD, "fields": [{"title": heading}]}
                attachments.append(item)

        return title, attachments

    def _notify_to_slack(self, task, next_progress):
        title, attachments = self._get_slack_message(task, next_progress)
        if title:
            app.logger.info(
                "New message, payload={}".format(
                    {
                        "title": title,
                        "attachments": attachments,
                        "audit_id": task["audit_id"],
                        "scan_id": task["scan_id"],
                        "target": task["target"],
                    }
                )
            )
            webhook_url = task["slack_webhook_url"]
            if not webhook_url:
                audit = AuditResource.get_by_id(task["audit_id"])
                webhook_url = audit["slack_default_webhook_url"]
            if webhook_url:
                try:
                    SlackIntegrator(webhook_url).send(title, attachments)
                except Exception as error:
                    app.logger.warn("Failed to send a message to Slack, error={}".format(error))

    def _reset_scan_schedule(self, task):
        scan = {
            "error_reason": task["error_reason"],
            "task_uuid": None,
            "scheduled": False,
            "processed": True,
            "start_at": Utils.get_default_datetime(),
            "end_at": Utils.get_default_datetime(),
        }
        ScanTable.update(scan).where(ScanTable.task_uuid == task["uuid"]).execute()

    def _update(self, task, next_progress):
        self._notify_to_slack(task, next_progress)
        task["progress"] = next_progress
        if next_progress == TaskProgress.DELETED.name:
            if task.get("session"):
                Scanner(json.loads(task["session"])).delete()
                app.logger.info("Scan deleted successfully, task={}".format(task))
        TaskTable.update(task).where(TaskTable.id == task["id"]).execute()

    def _process(self, task):
        app.logger.exception("Error, needs to override `_process` method")


class PendingTask(BaseTask):
    def __init__(self):
        super().__init__(TaskProgress.PENDING.name)

    def add(self, entry):
        entry["progress"] = TaskProgress.PENDING.name
        task = TaskTable(**entry)
        task.save()
        return task

    def _get_running_task_count(self):
        task_query = TaskTable.select(fn.Count(TaskTable.id).alias("count")).where(
            TaskTable.progress == TaskProgress.RUNNING.name
        )
        return task_query.dicts().get()["count"]

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
            task["error_reason"] = "Scan was abandoned since `end_at` is soon or over."
            app.logger.warn("Abandoned to launch scan, task={task}".format(task=task))
            self._update(task, next_progress=TaskProgress.FAILED.name)
            return True

        scanner = None
        if task.get("session"):
            scanner = Scanner(json.loads(task["session"]))
        else:
            scanner = Scanner()

        session = scanner.create()
        task["session"] = json.dumps(session)

        if not scanner.is_ready():
            # Skip the task if scanner is not ready
            self._update(task, next_progress=TaskProgress.PENDING.name)
            return True

        try:
            session = Scanner(session).launch_scan(task["target"])
            task["session"] = json.dumps(session)
            task["started_at"] = now
            ScanTable.update({"started_at": now}).where(ScanTable.task_uuid == task["uuid"]).execute()
            app.logger.info("Scan launched successfully, task={task}".format(task=task))
            self._update(task, next_progress=TaskProgress.RUNNING.name)
        except ScanServerException:
            # FIXME: Need to handle persistent server exception here
            app.logger.warn(
                "Scan server error during launch. We consider the error is due to OpenVAS server update for the time being."
            )

        return True


class RunningTask(BaseTask):
    def __init__(self):
        super().__init__(TaskProgress.RUNNING.name)

    def _update(self, task, next_progress):

        if next_progress in [TaskProgress.STOPPED.name, TaskProgress.FAILED.name]:
            now = datetime.now(tz=pytz.utc)
            task["ended_at"] = now
            ScanTable.update({"ended_at": now}).where(ScanTable.task_uuid == task["uuid"]).execute()

        super()._update(task, next_progress)

    def _process(self, task):
        end_at = task["end_at"].replace(tzinfo=pytz.utc)
        started_at = task["started_at"].replace(tzinfo=pytz.utc)
        now = datetime.now(tz=pytz.utc)

        if now > (started_at + timedelta(hours=SCAN_MAX_DURATION_IN_HOUR)):
            task["error_reason"] = "Scan was terminated since it took more than {} hours.".format(
                SCAN_MAX_DURATION_IN_HOUR
            )
            app.logger.warn("Scan deleted by timeout, task_uuid={task}".format(task=task))
            self._update(task, next_progress=TaskProgress.FAILED.name)
            return True

        if end_at <= now:
            task["error_reason"] = "Scan was terminated since `end_at` is over."
            app.logger.warn("Scan was deleted since it exceeded end_at, task_uuid={task}".format(task=task))
            self._update(task, next_progress=TaskProgress.FAILED.name)
            return True

        try:
            status = Scanner(json.loads(task["session"])).check_status()
        except ScanServerException as error:
            app.logger.exception("Exception, task={}, error={}".format(task, error))
            task["error_reason"] = "Scan was terminated due to server down."
            self._update(task, next_progress=TaskProgress.FAILED.name)
            return True

        if status == ScanStatus.STOPPED:
            app.logger.info("Scan stopped successfully, task={task}".format(task=task))
            self._update(task, next_progress=TaskProgress.STOPPED.name)
        elif status == ScanStatus.FAILED:
            app.logger.exception("Scan failed, task={task}".format(task=task))
            task["error_reason"] = "Scan was terminated due to scanner error."
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

        try:
            raw_report = Scanner(json.loads(task["session"])).get_report()
            storage.store(key, raw_report)
            report = Scanner.parse_report(raw_report)
        except ScanServerException as error:
            app.logger.exception("Exception, task={}, error={}".format(task, error))
            task["error_reason"] = "Report download failed due to server down."
            self._update(task, next_progress=TaskProgress.FAILED.name)
            return True

        with db.database.atomic():
            self._reset_scan_schedule(task)
            for vuln in report["vulns"]:
                VulnTable.insert(vuln).on_conflict_ignore().execute()
            ResultTable.update(scan_id=None).where(ResultTable.scan_id == task["scan_id"]).execute()
            results = report["results"]
            for result in results:
                result["scan_id"] = task["scan_id"]
            ResultTable.insert_many(results).execute()

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
        task["error_reason"] = ""
        self._update(task, next_progress=TaskProgress.DELETED.name)
        return True


class FailedTask(BaseTask):
    def __init__(self):
        super().__init__(TaskProgress.FAILED.name)

    def _process(self, task):
        self._reset_scan_schedule(task)
        self._update(task, next_progress=TaskProgress.DELETED.name)
        return True


class DeletedTask:
    @staticmethod
    def handle():
        return {}
