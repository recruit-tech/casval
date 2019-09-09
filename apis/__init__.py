from flask_restplus import Api

from .audit import api as audit
from .auth import api as auth
from .handler import api as handler
from .scan import api as scan
from .vuln import api as vuln

authorizations = {"API Token": {"type": "apiKey", "in": "header", "name": "Authorization"}}

api = Api(
    title="CASVAL REM",
    version="1.0",
    description="CASVAL Remote Execution Module",
    license="Apache License 2.0",
    license_url="http://www.apache.org/licenses/LICENSE-2.0",
    authorizations=authorizations,
)

api.add_namespace(audit, path="/audit")
api.add_namespace(scan, path="/scan")
api.add_namespace(auth, path="/auth")
api.add_namespace(vuln, path="/vuln")
api.add_namespace(handler, path="/handler")

try:
    from .monitor import api as monitor

    api.add_namespace(monitor, path="/monitor")
except ModuleNotFoundError:
    pass
