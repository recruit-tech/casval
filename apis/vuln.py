import csv
import tempfile
from datetime import timedelta

from flask import Response
from flask import abort
from flask import request
from flask_restplus import Namespace
from flask_restplus import Resource
from flask_restplus import fields
from flask_restplus import reqparse

from core import Authorizer
from core import ResultTable
from core import Utils
from core import VulnListInputSchema
from core import VulnTable
from core import VulnUpdateSchema

api = Namespace("vuln")


VulnOutputModel = api.model(
    "VulnOutput",
    {
        "oid": fields.String(required=True),
        "fix_required": fields.String(required=True),
        "name": fields.String(required=True),
        "cvss_base": fields.String(required=True),
        "cve": fields.String(required=True),
        "description": fields.String(required=True),
        "advice": fields.String(required=True),
    },
)


@api.route("/")
@api.doc(security="API Token")
@api.response(200, "Success")
@api.response(400, "Bad Request")
@api.response(401, "Invalid Token")
class VulneravilityList(Resource):

    VulnListGetParser = reqparse.RequestParser()
    VulnListGetParser.add_argument("fix_required", type=str, location="args")
    VulnListGetParser.add_argument("keyword", type=str, location="args")
    VulnListGetParser.add_argument("page", type=int, location="args")
    VulnListGetParser.add_argument("count", type=int, location="args")

    @api.expect(VulnListGetParser)
    @api.marshal_with(VulnOutputModel, as_list=True)
    @Authorizer.admin_token_required
    def get(self):
        """Get vulnerability list"""
        schema = VulnListInputSchema()
        params, errors = schema.load(request.args)
        if errors:
            abort(400, errors)

        vuln_query = VulnTable.select(
            VulnTable.oid,
            VulnTable.fix_required,
            VulnTable.advice,
            ResultTable.name,
            ResultTable.cvss_base,
            ResultTable.cve,
            ResultTable.description,
        ).join(ResultTable, on=(VulnTable.oid == ResultTable.oid))

        if "fix_required" in params and len(params["fix_required"]) > 0:
            vuln_query = vuln_query.where(VulnTable.fix_required == params["fix_required"])

        if "keyword" in params and len(params["keyword"]) > 0:
            vuln_query = vuln_query.where(
                (VulnTable.oid ** "%{}%".format(params["keyword"]))
                | (ResultTable.name ** "%{}%".format(params["keyword"]))
            )
        vuln_query = vuln_query.group_by(
            VulnTable.oid,
            VulnTable.fix_required,
            VulnTable.advice,
            ResultTable.name,
            ResultTable.cvss_base,
            ResultTable.cve,
            ResultTable.description,
        )
        vuln_query = vuln_query.order_by(VulnTable.oid.desc())
        vuln_query = vuln_query.paginate(params["page"], params["count"])

        response = []
        for vulnerability in vuln_query.dicts():
            response.append(vulnerability)

        return response


@api.route("/download/")
@api.doc(security="API Token")
@api.response(200, "Success")
@api.response(400, "Bad Request")
@api.response(401, "Invalid Token")
class VulneravilityListDownload(Resource):

    VULNERABILITY_CSV_COLUMNS = [
        "oid",
        "name",
        "fix_required",
        "cve",
        "cvss_base",
        "description",
        "advice",
        "created_at",
        "updated_at",
    ]

    VulnListDownloadParser = reqparse.RequestParser()
    VulnListDownloadParser.add_argument("fix_required", type=str, location="args")
    VulnListDownloadParser.add_argument("keyword", type=str, location="args")

    @api.expect(VulnListDownloadParser)
    @Authorizer.admin_token_required
    def get(self):
        """Download all vulnerability list"""
        schema = VulnListInputSchema(only=["tz_offset", "fix_required", "keyword"])
        params, errors = schema.load(request.args)
        if errors:
            abort(400, errors)

        vuln_query = VulnTable.select(
            VulnTable.oid,
            VulnTable.fix_required,
            VulnTable.advice,
            VulnTable.created_at,
            VulnTable.updated_at,
            ResultTable.name,
            ResultTable.cvss_base,
            ResultTable.cve,
            ResultTable.description,
        ).join(ResultTable, on=(VulnTable.oid == ResultTable.oid))

        if "fix_required" in params and len(params["fix_required"]) > 0:
            vuln_query = vuln_query.where(VulnTable.fix_required == params["fix_required"])

        if "keyword" in params and len(params["keyword"]) > 0:
            vuln_query = vuln_query.where(
                (VulnTable.oid ** "%{}%".format(params["keyword"]))
                | (ResultTable.name ** "%{}%".format(params["keyword"]))
            )
        vuln_query = vuln_query.group_by(
            VulnTable.oid,
            VulnTable.fix_required,
            VulnTable.advice,
            VulnTable.created_at,
            VulnTable.updated_at,
            ResultTable.name,
            ResultTable.cvss_base,
            ResultTable.cve,
            ResultTable.description,
        )
        vuln_query = vuln_query.order_by(VulnTable.oid.desc())
        output = ""

        with tempfile.TemporaryFile("r+") as f:
            writer = csv.DictWriter(
                f, VulneravilityListDownload.VULNERABILITY_CSV_COLUMNS, extrasaction="ignore"
            )
            writer.writeheader()
            for vuln in vuln_query.dicts():
                vuln["description"] = Utils.format_openvas_description(vuln["description"])
                vuln["created_at"] = vuln["created_at"] + timedelta(minutes=params["tz_offset"])
                vuln["updated_at"] = vuln["updated_at"] + timedelta(minutes=params["tz_offset"])
                writer.writerow(vuln)
            f.flush()
            f.seek(0)
            output += f.read()

        headers = {"Content-Type": "text/csv", "Content-Disposition": "attachment"}
        return Response(response=output, status=200, headers=headers)


@api.route("/<string:oid>/")
@api.doc(security="API Token")
@api.response(200, "Success")
@api.response(400, "Bad Request")
@api.response(401, "Invalid Token")
@api.response(404, "Not Found")
class Vulnerability(Resource):

    VulnPatchInputModel = api.model(
        "VulnPatchInput",
        {"fix_required": fields.String(required=False), "advice": fields.String(required=False)},
    )

    @api.expect(VulnPatchInputModel, validate=True)
    @Authorizer.admin_token_required
    def patch(self, oid):
        """Decide whether the specified vulnerability requires to be fixed"""
        schema = VulnUpdateSchema()
        params, errors = schema.load(request.json)
        if errors:
            abort(400, errors)

        VulnTable.update(params).where(VulnTable.oid == oid).execute()

        return {}
