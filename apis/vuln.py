from flask import abort
from flask import request
from flask_restplus import Namespace
from flask_restplus import Resource
from flask_restplus import fields
from flask_restplus import reqparse

from core import Authorizer
from core import ResultTable
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


@api.route("/<string:oid>/")
@api.doc(security="API Token")
@api.response(200, "Success")
@api.response(400, "Bad Request")
@api.response(401, "Invalid Token")
@api.response(404, "Not Found")
class Vulnerability(Resource):

    VulnPatchInputModel = api.model("VulnPatchInput", {"fix_required": fields.String(required=True)})

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
