from functools import wraps

from flask import abort
from flask_restplus import Resource

from core import AuditTable
from core import ResultTable
from core import ScanTable
from core import VulnTable


class AuditResource(Resource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @staticmethod
    def get_by_uuid(audit_uuid, withContacts=False, withScans=False):
        audit_query = AuditTable.select().where(AuditTable.uuid == audit_uuid)

        try:
            audit = audit_query.dicts()[0]
        except:
            abort(404, "Not Found")

        if withContacts:
            audit["contacts"] = []
            for contact in audit_query[0].contacts.dicts():
                audit["contacts"].append(contact)

        if withScans:
            audit["scans"] = []
            for scan in audit_query[0].scans.dicts():
                audit["scans"].append(scan["uuid"].hex)

        return audit

    @staticmethod
    def get_audit_id_by_uuid(audit_uuid):
        audit = AuditResource.get_by_uuid(audit_uuid)
        return audit["id"]


class ScanResource(Resource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def reject_if_submitted_or_approved(f):
        @wraps(f)
        def decorate(self, *args, **kwargs):

            if "audit_uuid" in kwargs:
                audit_uuid = kwargs["audit_uuid"]
            elif "scan_uuid" in kwargs:
                audit_uuid = kwargs["scan_uuid"][0:24] + "0" * 8
            else:
                abort(400, "Requested endpoint has no `audit_uuid` or `scan_uuid`")

            audit = AuditResource.get_by_uuid(audit_uuid)
            if audit["submitted"] or audit["approved"]:
                abort(400, "Audit has been submitted or approved")
            else:
                return f(self, *args, **kwargs)

        return decorate

    @staticmethod
    def get_by_uuid(scan_uuid, withResults=False):
        scan_query = ScanTable.select().where(ScanTable.uuid == scan_uuid)
        scan = scan_query.dicts()[0]

        try:
            scan = scan_query.dicts()[0]
        except:
            abort(404, "Not Found")

        if withResults:
            scan["results"] = []

            results = (
                ResultTable.select(ResultTable, VulnTable.fix_required)
                .join(VulnTable, on=(ResultTable.oid == VulnTable.oid))
                .where(ResultTable.scan_id == scan["id"])
            )
            for result in results.dicts():
                scan["results"].append(result)

        return scan
