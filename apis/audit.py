import csv
import secrets
import tempfile
import uuid
from datetime import timedelta

from flask import Response
from flask import abort
from flask import request
from flask_jwt_extended import create_access_token
from flask_restplus import Namespace
from flask_restplus import fields
from flask_restplus import inputs
from flask_restplus import reqparse
from peewee import fn

from core import AuditDownloadInputSchema
from core import AuditInputSchema
from core import AuditListInputSchema
from core import AuditResource
from core import AuditTable
from core import AuditTokenInputSchema
from core import AuditUpdateSchema
from core import Authorizer
from core import ContactSchema
from core import ContactTable
from core import ResultTable
from core import ScanInputSchema
from core import Scanner
from core import ScanResource
from core import ScanTable
from core import Utils
from core import VulnTable
from core import db

from .scan import ScanOutputModel

api = Namespace("audit")

ContactModel = api.model(
    "ContactModel", {"name": fields.String(required=True), "email": fields.String(required=True)}
)

AuditOutputModel = api.model(
    "AuditOutputModel",
    {
        "id": fields.Integer(required=True),
        "uuid": fields.String(required=True, attribute=lambda audit: audit["uuid"].hex),
        "name": fields.String(required=True),
        "description": fields.String(required=True),
        "submitted": fields.Boolean(required=True),
        "approved": fields.Boolean(required=True),
        "rejected_reason": fields.String(required=True),
        "ip_restriction": fields.Boolean(required=True),
        "password_protection": fields.Boolean(required=True),
        "slack_integration": fields.Boolean(required=True),
        "created_at": fields.DateTime(required=True),
        "updated_at": fields.DateTime(required=True),
        "contacts": fields.List(fields.Nested(ContactModel), required=True),
        "scans": fields.List(fields.String()),
    },
)


@api.route("/")
@api.doc(security="API Token")
@api.response(200, "Success")
@api.response(400, "Bad Request")
@api.response(401, "Invalid Token")
class AuditList(AuditResource):

    AuditListGetParser = reqparse.RequestParser()
    AuditListGetParser.add_argument("submitted", type=inputs.boolean, default=False, location="args")
    AuditListGetParser.add_argument("approved", type=inputs.boolean, default=False, location="args")
    AuditListGetParser.add_argument("unsafe_only", type=inputs.boolean, default=False, location="args")
    AuditListGetParser.add_argument("keyword", type=str, location="args")
    AuditListGetParser.add_argument("page", type=int, default=1, location="args")
    AuditListGetParser.add_argument("count", type=int, default=10, location="args")

    AuditListPostInputModel = api.model(
        "AuditListPostInput",
        {
            "name": fields.String(required=True),
            "description": fields.String(required=True),
            "contacts": fields.List(fields.Nested(ContactModel), required=True),
        },
    )

    @api.expect(AuditListGetParser)
    @api.marshal_with(AuditOutputModel, skip_none=True, as_list=True)
    @Authorizer.admin_token_required
    def get(self):
        """Get audit list"""
        schema = AuditListInputSchema()
        params, errors = schema.load(request.args)
        if errors:
            abort(400, errors)

        audit_query = AuditTable.select(
            AuditTable,
            fn.GROUP_CONCAT(
                ContactTable.name.distinct(),
                ContactSchema.SEPARATER_NAME_EMAIL,
                ContactTable.email,
                python_value=(
                    lambda contacts: [
                        dict(zip(["name", "email"], contact.rsplit(ContactSchema.SEPARATER_NAME_EMAIL)))
                        for contact in contacts.split(ContactSchema.SEPARATER_CONTACTS)
                    ]
                ),
            ).alias("contacts"),
        ).join(ContactTable, on=(AuditTable.id == ContactTable.audit_id))

        if "unsafe_only" in params and params["unsafe_only"] == True:
            audit_query = (
                audit_query.join(ScanTable, on=(AuditTable.id == ScanTable.audit_id))
                .join(ResultTable, on=(ScanTable.id == ResultTable.scan_id))
                .join(VulnTable, on=(ResultTable.oid == VulnTable.oid))
                .where(VulnTable.fix_required == "REQUIRED")
                .where(ScanTable.comment == "")
            )

        if "keyword" in params and len(params["keyword"]) > 0:
            audit_query = audit_query.where(
                (AuditTable.name ** "%{}%".format(params["keyword"]))
                | (AuditTable.description ** "%{}%".format(params["keyword"]))
            )
        if "submitted" in params:
            audit_query = audit_query.where(AuditTable.submitted == params["submitted"])
        if "approved" in params:
            audit_query = audit_query.where(AuditTable.approved == params["approved"])
        audit_query = audit_query.group_by(AuditTable.id)
        audit_query = audit_query.order_by(AuditTable.updated_at.desc())
        audit_query = audit_query.paginate(params["page"], params["count"])

        return list(audit_query.dicts())

    @api.expect(AuditListPostInputModel)
    @api.marshal_with(AuditOutputModel)
    @Authorizer.admin_token_required
    def post(self):
        """Register new audit"""
        schema = AuditInputSchema()
        params, errors = schema.load(request.json)
        if errors:
            abort(400, errors)

        # Audit UUID must be 'NNNNNNNN-NNNN-NNNN-NNNN-NNNN00000000'
        # because lower 32 bits are used for UUID of scans/tasks.
        params["uuid"] = uuid.UUID(secrets.token_hex(12) + "0" * 8)

        with db.database.atomic():
            audit = AuditTable(**params)
            audit.save()

            for contact in params["contacts"]:
                contact["audit_id"] = audit.id

            ContactTable.insert_many(params["contacts"]).execute()

        return AuditResource.get_by_uuid(audit.uuid, withContacts=True, withScans=True)


@api.route("/<string:audit_uuid>/tokens/")
@api.doc(security="None")
@api.response(200, "Success")
class AuditToken(AuditResource):

    AuditTokenInputModel = api.model("AuditTokenInput", {"password": fields.String()})
    AuditTokenModel = api.model("AuditToken", {"token": fields.String(required=True)})

    @api.expect(AuditTokenInputModel)
    @api.marshal_with(AuditTokenModel)
    @api.response(401, "Invalid Password")
    @api.response(403, "Invalid Source IP")
    @api.response(404, "Not Found")
    def post(self, audit_uuid):
        """Publish an API token for the specified audit"""
        audit = AuditResource.get_by_uuid(audit_uuid, withContacts=False, withScans=False)

        if audit["ip_restriction"] == True:
            if Utils.is_source_ip_permitted(request.access_route[0]) == False:
                abort(403, "Not allowed to access from your IP address")

        if audit["password_protection"] == True:
            params, errors = AuditTokenInputSchema().load(request.json)
            if errors:
                abort(400, errors)

            if Utils.get_password_hash(params["password"]) != audit["password"]:
                abort(401, "Invalid password")

        token = create_access_token(identity={"scope": audit_uuid, "restricted": False})
        return {"token": token}, 200


@api.route("/<string:audit_uuid>/tokens/restricted")
@api.doc(security="API Token")
@api.response(200, "Success")
class AuditRestrictedToken(AuditResource):

    AuditTokenModel = api.model("AuditToken", {"token": fields.String(required=True)})

    @api.marshal_with(AuditTokenModel)
    @api.response(404, "Not Found")
    @Authorizer.token_required
    def post(self, audit_uuid):
        """Publish a restricted API token for the specified audit"""

        token = create_access_token(identity={"scope": audit_uuid, "restricted": True}, expires_delta=False)
        return {"token": token}, 200


@api.route("/<string:audit_uuid>/")
@api.doc(security="API Token")
@api.response(200, "Success")
@api.response(401, "Invalid Token")
@api.response(404, "Not Found")
class AuditItem(AuditResource):

    AuditPatchInputModel = api.model(
        "AuditPatchInput",
        {
            "name": fields.String(),
            "description": fields.String(),
            "contacts": fields.List(fields.Nested(ContactModel)),
            "ip_restriction": fields.Boolean(),
            "password_protection": fields.Boolean(),
            "password": fields.String(),
            "slack_default_webhook_url": fields.String(required=False),
        },
    )

    @api.marshal_with(AuditOutputModel)
    @Authorizer.token_required
    def get(self, audit_uuid):
        """Get the specified audit"""
        audit = AuditResource.get_by_uuid(audit_uuid, withContacts=True, withScans=True)
        return audit

    @api.expect(AuditPatchInputModel)
    @api.marshal_with(AuditOutputModel)
    @api.response(400, "Bad Request")
    @Authorizer.token_required
    def patch(self, audit_uuid):
        """Update the specified audit"""
        audit = AuditResource.get_by_uuid(audit_uuid, withContacts=False, withScans=False)

        schema = AuditUpdateSchema(
            only=[
                "name",
                "description",
                "contacts",
                "password",
                "ip_restriction",
                "password_protection",
                "slack_default_webhook_url",
            ]
        )
        params, errors = schema.load(request.json)
        if errors:
            abort(400, errors)

        if params.get("password_protection") == True and "password" not in params:
            abort(400, "Password must be provided when enforcing protection")

        if "password" in params:
            params["password"] = Utils.get_password_hash(params["password"])

        if params.get("password_protection") == False:
            params["password"] = ""

        contacts = []
        if "contacts" in params:
            contacts = params["contacts"]
            params.pop("contacts")

        with db.database.atomic():
            if params != {}:
                AuditTable.update(params).where(AuditTable.id == audit["id"]).execute()

            if len(contacts) > 0:
                for contact in contacts:
                    contact["audit_id"] = audit["id"]
                ContactTable.delete().where(ContactTable.audit_id == audit["id"]).execute()
                ContactTable.insert_many(contacts).execute()

        return AuditResource.get_by_uuid(audit["uuid"], withContacts=True, withScans=True)

    @Authorizer.admin_token_required
    def delete(self, audit_uuid):
        """Delete the specified audit"""
        audit_query = AuditTable.delete().where(AuditTable.uuid == audit_uuid)
        if audit_query.execute() == 0:
            abort(404, "Not Found")
        else:
            return {}


@api.route("/<string:audit_uuid>/submit/")
@api.doc(security="API Token")
@api.response(200, "Success")
@api.response(401, "Invalid Token")
@api.response(404, "Not Found")
class AuditSubmission(AuditResource):

    AuditWithdrawalInputModel = api.model("AuditWithdrawalInput", {"rejected_reason": fields.String()})

    @api.marshal_with(AuditOutputModel)
    @Authorizer.token_required
    def post(self, audit_uuid):
        """Submit the specified audit result"""
        audit = AuditResource.get_by_uuid(audit_uuid, withContacts=False, withScans=False)

        if audit["submitted"] == True:
            abort(400, "Already submitted")

        if audit["approved"] == True:
            abort(400, "Already approved by administrator(s)")

        schema = AuditUpdateSchema(only=["submitted", "rejected_reason"])
        params, _errors = schema.load({"submitted": True, "rejected_reason": ""})

        with db.database.atomic():
            AuditTable.update(params).where(AuditTable.id == audit["id"]).execute()

        return AuditResource.get_by_uuid(audit["uuid"], withContacts=True, withScans=True)

    @api.expect(AuditWithdrawalInputModel)
    @api.marshal_with(AuditOutputModel)
    @Authorizer.token_required
    def delete(self, audit_uuid):
        """Withdraw the submission of the specified audit result"""
        audit = AuditResource.get_by_uuid(audit_uuid, withContacts=False, withScans=False)

        if audit["submitted"] == False:
            abort(400, "Not submitted yet")

        if audit["approved"] == True:
            abort(400, "Already approved by administrator(s)")

        schema = AuditUpdateSchema(only=["submitted", "rejected_reason"])
        params, errors = schema.load(
            {"submitted": False, "rejected_reason": ""}  # TODO: Get rejected reason from UI
        )
        if errors:
            abort(400, errors)

        with db.database.atomic():
            AuditTable.update(params).where(AuditTable.id == audit["id"]).execute()

        return AuditResource.get_by_uuid(audit["uuid"], withContacts=True, withScans=True)


@api.route("/<string:audit_uuid>/approve/")
@api.doc(security="API Token")
@api.response(200, "Success")
@api.response(401, "Invalid Token")
@api.response(404, "Not Found")
class AuditApproval(AuditResource):
    @api.marshal_with(AuditOutputModel)
    @Authorizer.admin_token_required
    def post(self, audit_uuid):
        """Approve the specified audit submission"""
        audit = AuditResource.get_by_uuid(audit_uuid, withContacts=False, withScans=False)

        if audit["approved"] == True:
            abort(400, "Already approved")

        schema = AuditUpdateSchema(only=["approved", "submitted"])
        params, _errors = schema.load({"approved": True, "submitted": True})

        with db.database.atomic():
            AuditTable.update(params).where(AuditTable.id == audit["id"]).execute()

        return AuditResource.get_by_uuid(audit["uuid"], withContacts=True, withScans=True)

    @api.marshal_with(AuditOutputModel)
    @Authorizer.admin_token_required
    def delete(self, audit_uuid):
        """Withdraw the approval of the specified audit submission"""
        audit = AuditResource.get_by_uuid(audit_uuid, withContacts=False, withScans=False)

        if audit["approved"] == False:
            abort(400, "Not approved yet")

        schema = AuditUpdateSchema(only=["approved"])
        params, _errors = schema.load({"approved": False})

        with db.database.atomic():
            AuditTable.update(params).where(AuditTable.id == audit["id"]).execute()

        return AuditResource.get_by_uuid(audit["uuid"], withContacts=True, withScans=True)


@api.route("/<string:audit_uuid>/download/")
@api.doc(security="API Token")
@api.response(200, "Success", headers={"Content-Type": "text/csv", "Content-Disposition": "attachment"})
@api.response(401, "Invalid Token")
@api.response(404, "Not Found")
class AuditDownload(AuditResource):

    AUDIT_CSV_COLUMNS = [
        "target",
        "host",
        "port",
        "name",
        "cve",
        "cvss_base",
        "severity_rank",
        "fix_required",
        "description",
        "oid",
        "started_at",
        "ended_at",
        "comment",
        "advice",
    ]

    @Authorizer.token_required
    def get(self, audit_uuid):
        """Download the specified audit result"""

        schema = AuditDownloadInputSchema()
        params, errors = schema.load(request.args)
        if errors:
            abort(400, errors)

        audit_query = AuditTable.select().where(AuditTable.uuid == audit_uuid)

        audit = audit_query.dicts()[0]
        output = audit["name"] + "\n" + audit["description"] + "\n\n"

        scan_ids = []
        for scan in audit_query[0].scans.dicts():
            if scan["processed"] is True:
                scan_ids.append(scan["id"])

        results = (
            ResultTable.select(ResultTable, ScanTable, VulnTable)
            .join(ScanTable)
            .join(VulnTable, on=(ResultTable.oid == VulnTable.oid))
            .where(ResultTable.scan_id.in_(scan_ids))
            .order_by(ResultTable.scan_id)
        )

        with tempfile.TemporaryFile("r+") as f:
            writer = csv.DictWriter(f, AuditDownload.AUDIT_CSV_COLUMNS, extrasaction="ignore")
            writer.writeheader()
            for result in results.dicts():
                result["started_at"] = result["started_at"] + timedelta(minutes=params["tz_offset"])
                result["ended_at"] = result["ended_at"] + timedelta(minutes=params["tz_offset"])
                result["description"] = Utils.format_openvas_description(result["description"])
                writer.writerow(result)
            f.flush()
            f.seek(0)
            output += f.read()

        headers = {"Content-Type": "text/csv", "Content-Disposition": "attachment"}
        return Response(response=output, status=200, headers=headers)


@api.route("/<string:audit_uuid>/scan/")
@api.doc(security="API Token")
@api.response(200, "Success")
@api.response(401, "Invalid Token")
@api.response(404, "Not Found")
class AuditScan(AuditResource):

    ScanListPostInputModel = api.model("ScanListPostInput", {"target": fields.String(required=True)})
    ScanListPostErrorResponseModel = api.model(
        "ScanListPostErrorResponse",
        {
            "error_reason": fields.String(
                enum=[
                    "audit-id-not-found",
                    "audit-submitted",
                    "audit-approved",
                    "target-is-private-ip",
                    "could-not-resolve-target-fqdn",
                    "target-is-not-fqdn-or-ipv4",
                ],
                required=True,
            )
        },
    )

    @api.expect(ScanListPostInputModel)
    @api.marshal_with(ScanOutputModel)
    @api.response(400, "Bad Request", ScanListPostErrorResponseModel)
    @Authorizer.token_required
    @ScanResource.reject_if_submitted_or_approved
    def post(self, audit_uuid):
        """Register new scan"""
        schema = ScanInputSchema()
        params, errors = schema.load(request.json)
        if errors:
            abort(400, errors)

        # Scan UUID consists of upper 96 bits of audit UUID (=A) and 32 bits random number (=B),
        # i.e., 'AAAAAAAA-AAAA-AAAA-AAAA-AAAABBBBBBBB'.
        params["uuid"] = uuid.UUID(audit_uuid[0:24] + secrets.token_hex(4))
        params["audit_id"] = AuditResource.get_audit_id_by_uuid(audit_uuid)

        scanner_info = Scanner.get_info()
        params["source_ip"] = scanner_info["source_ip"]

        scan_insert_query = ScanTable(**params)
        scan_insert_query.save()
        return ScanResource.get_by_uuid(scan_insert_query.uuid)
