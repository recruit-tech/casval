from flask import abort
from flask import current_app as app
from flask import request
from flask_jwt_extended import create_access_token
from flask_restplus import Namespace
from flask_restplus import Resource
from flask_restplus import fields

from core import AuthInputSchema
from core import Utils

api = Namespace("auth")


@api.route("/")
class Authenticate(Resource):

    AuthInputModel = api.model("AuthInputModel", {"password": fields.String(required=True)})
    AdminTokenModel = api.model("AdminTokenModel", {"token": fields.String(required=True)})

    @api.doc(security=None)
    @api.expect(AuthInputModel)
    @api.marshal_with(AdminTokenModel, description="API Token for Administrators")
    @api.response(200, "Success")
    @api.response(400, "Bad Request")
    @api.response(401, "Invalid Password")
    @api.response(403, "Invalid Source IP")
    def post(self):
        """Publish an API token for administrators"""

        if Utils.is_source_ip_permitted(request.access_route[0]) == False:
            abort(403, "Not allowed to access from your IP address")

        params, errors = AuthInputSchema().load(request.json)
        if errors:
            abort(400, errors)

        if params["password"] != app.config["ADMIN_PASSWORD"]:
            abort(401, "Invalid password")

        token = create_access_token(identity={"scope": "*", "restricted": False})
        return {"token": token}, 200
