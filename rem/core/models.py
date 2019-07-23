import uuid

from peewee import SQL
from peewee import BooleanField
from peewee import CharField
from peewee import DateTimeField
from peewee import ForeignKeyField
from peewee import TextField
from peewee import UUIDField
from playhouse.flask_utils import FlaskDB

from .utils import Utils

db = FlaskDB()


class AuditTable(db.Model):
    class Meta:
        db_table = "audit"

    uuid = UUIDField(unique=True)
    name = CharField()
    description = CharField(default="")
    submitted = BooleanField(default=False)
    approved = BooleanField(default=False)
    ip_restriction = BooleanField(default=True)
    password_protection = BooleanField(default=False)
    password = CharField(default="")
    rejected_reason = CharField(default="")
    created_at = DateTimeField(constraints=[SQL("DEFAULT CURRENT_TIMESTAMP")])
    updated_at = DateTimeField(constraints=[SQL("DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")])


class ContactTable(db.Model):
    class Meta:
        db_table = "contact"

    audit_id = ForeignKeyField(AuditTable, backref="contacts", on_delete="CASCADE", on_update="CASCADE")
    name = CharField()
    email = CharField()


class ScanTable(db.Model):
    class Meta:
        db_table = "scan"

    uuid = UUIDField(unique=True)
    audit_id = ForeignKeyField(AuditTable, backref="scans", on_delete="CASCADE", on_update="CASCADE")
    target = CharField()
    start_at = DateTimeField(default=Utils.get_default_datetime)
    end_at = DateTimeField(default=Utils.get_default_datetime)
    started_at = DateTimeField(default=Utils.get_default_datetime)
    ended_at = DateTimeField(default=Utils.get_default_datetime)
    error_reason = CharField(default="")
    scheduled = BooleanField(default=False)
    task_uuid = UUIDField(unique=True, null=True, default=None)
    processed = BooleanField(default=False)
    comment = TextField(default="")
    source_ip = CharField(default="")
    created_at = DateTimeField(constraints=[SQL("DEFAULT CURRENT_TIMESTAMP")])
    updated_at = DateTimeField(constraints=[SQL("DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")])


class TaskTable(db.Model):
    class Meta:
        db_table = "task"

    uuid = UUIDField(unique=True, default=uuid.uuid4)
    audit_id = ForeignKeyField(AuditTable, null=True, on_delete="SET NULL", on_update="CASCADE")
    scan_id = ForeignKeyField(ScanTable, null=True, on_delete="SET NULL", on_update="CASCADE")
    target = CharField()
    start_at = DateTimeField(default=Utils.get_default_datetime)
    end_at = DateTimeField(default=Utils.get_default_datetime)
    error_reason = CharField(default="")
    session = TextField(default="")
    progress = CharField()
    created_at = DateTimeField(constraints=[SQL("DEFAULT CURRENT_TIMESTAMP")])
    updated_at = DateTimeField(constraints=[SQL("DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")])


class VulnTable(db.Model):
    class Meta:
        db_table = "vuln"

    oid = CharField(unique=True, max_length=191, null=True, default=None)
    fix_required = CharField(default="UNDEFINED")
    advice = TextField(default="")
    created_at = DateTimeField(constraints=[SQL("DEFAULT CURRENT_TIMESTAMP")])
    updated_at = DateTimeField(constraints=[SQL("DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")])


class ResultTable(db.Model):
    class Meta:
        db_table = "result"

    scan_id = ForeignKeyField(ScanTable, backref="results", on_delete="CASCADE", on_update="CASCADE")
    name = CharField(null=True)
    host = CharField(null=True)
    port = CharField(null=True)
    cvss_base = CharField(null=True)
    cve = CharField(null=True)
    oid = CharField(null=True)
    description = TextField(null=True)
    qod = CharField(null=True)
    severity = CharField(null=True)
    severity_rank = CharField(null=True)
    scanner = CharField(null=True)
    created_at = DateTimeField(constraints=[SQL("DEFAULT CURRENT_TIMESTAMP")])
    updated_at = DateTimeField(constraints=[SQL("DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")])
