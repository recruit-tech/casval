from flask import abort
from flask import request
from flask_restplus import Namespace
from flask_restplus import Resource
from flask_restplus import fields

from core import Authorizer
from core import PendingTask
from core import ScanResource
from core import ScanTable
from core import ScanUpdateSchema
from core import Utils
from core import db

api = Namespace("scan")


ScanResultModel = api.model(
    "ScanResultModel",
    {
        "oid": fields.String(required=True),
        "name": fields.String(required=True),
        "host": fields.String(required=True),
        "port": fields.String(required=True),
        "description": fields.String(required=True),
        "qod": fields.String(required=True),
        "severity": fields.String(required=True),
        "severity_rank": fields.String(required=True),
        "scanner": fields.String(required=True),
        "fix_required": fields.String(required=True),
    },
)

ScanOutputModel = api.model(
    "ScanOutputModel",
    {
        "target": fields.String(required=True),
        "uuid": fields.String(required=True, attribute=lambda scan: scan["uuid"].hex),
        "error_reason": fields.String(required=True),
        "comment": fields.String(required=True),
        "created_at": fields.DateTime(required=True),
        "updated_at": fields.DateTime(required=True),
        "scheduled": fields.Boolean(required=True),
        "processed": fields.Boolean(required=True),
        "start_at": fields.DateTime(required=True),
        "end_at": fields.DateTime(required=True),
        "results": fields.List(fields.Nested(ScanResultModel), required=True),
    },
)


@api.route("/<string:scan_uuid>/")
@api.doc(security="API Token")
@api.response(200, "Success")
@api.response(401, "Invalid Token")
@api.response(404, "Not Found")
class ScanItem(Resource):

    ScanPatchInputModel = api.model("ScanPatchInput", {"comment": fields.String(required=True)})

    @api.marshal_with(ScanOutputModel)
    @Authorizer.token_required
    def get(self, scan_uuid):
        """Retrieve the specified scan"""
        return ScanResource.get_by_uuid(scan_uuid, withResults=True)

    @api.expect(ScanPatchInputModel)
    @api.marshal_with(ScanOutputModel)
    @api.response(400, "Bad Request")
    @Authorizer.token_required
    @ScanResource.reject_if_submitted_or_approved
    def patch(self, scan_uuid):
        """Update the specified scan"""
        scan = ScanResource.get_by_uuid(scan_uuid, withResults=False)
        schema = ScanUpdateSchema(only=["comment"])
        params, errors = schema.load(request.json)
        if errors:
            abort(400, errors)

        ScanTable.update(params).where(ScanTable.id == scan["id"]).execute()
        return ScanResource.get_by_uuid(scan_uuid, withResults=False)

    @Authorizer.token_required
    @ScanResource.reject_if_submitted_or_approved
    def delete(self, scan_uuid):
        """Delete the specified scan"""
        scan_query = ScanTable.delete().where(ScanTable.uuid == scan_uuid)
        if scan_query.execute() == 0:
            abort(404, "Not Found")
        else:
            return {}


@api.route("/<string:scan_uuid>/schedule/")
@api.doc(security="API Token")
@api.response(200, "Success")
@api.response(401, "Invalid Token")
@api.response(404, "Not Found")
class ScanSchedule(Resource):

    ScanSchedulePatchInputModel = api.model(
        "ScanSchedulePatchInput",
        {"start_at": fields.DateTime(required=True), "end_at": fields.DateTime(required=True)},
    )

    @api.expect(ScanSchedulePatchInputModel)
    @api.marshal_with(ScanOutputModel)
    @api.response(400, "Bad Request")
    @Authorizer.token_required
    @ScanResource.reject_if_submitted_or_approved
    def patch(self, scan_uuid):
        """Schedule the specified scan"""
        scan = ScanResource.get_by_uuid(scan_uuid, withResults=False)

        if scan["scheduled"] == True:
            abort(400, "Already scheduled")

        schema = ScanUpdateSchema(only=["start_at", "end_at"])
        params, errors = schema.load(request.json)
        if errors:
            abort(400, errors)

        with db.database.atomic():

            task = PendingTask().add(
                {
                    "audit_id": scan["audit_id"],
                    "scan_id": scan["id"],
                    "target": scan["target"],
                    "start_at": params["start_at"],
                    "end_at": params["end_at"],
                }
            )

            params["task_uuid"] = task.uuid
            params["scheduled"] = True
            ScanTable.update(params).where(ScanTable.id == scan["id"]).execute()

        return ScanResource.get_by_uuid(scan_uuid, withResults=False)

    @api.marshal_with(ScanOutputModel)
    @api.response(400, "Bad Request")
    @Authorizer.token_required
    @ScanResource.reject_if_submitted_or_approved
    def delete(self, scan_uuid):
        """Cancel the specified scan schedule"""
        scan = ScanResource.get_by_uuid(scan_uuid, withResults=False)

        if scan["scheduled"] == False:
            abort(400, "Already canceled")

        data = {
            "start_at": Utils.get_default_datetime(),
            "end_at": Utils.get_default_datetime(),
            "scheduled": False,
            "task_uuid": None,
        }

        ScanTable.update(data).where(ScanTable.id == scan["id"]).execute()
        return ScanResource.get_by_uuid(scan_uuid, withResults=False)
