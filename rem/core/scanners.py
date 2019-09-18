import os
from enum import Enum
from enum import auto
from xml.etree import ElementTree

from flask import current_app as app

from openvas_lib import VulnscanManager
from openvas_lib import VulnscanServerError
from openvas_lib import report_parser_from_text

from .utils import Utils

if Utils.is_gcp():
    from core.deployers import KubernetesDeployer as Deployer
else:
    from core.deployers import LocalDeployer as Deployer


class ScanStatus(Enum):
    RUNNING = auto()
    STOPPED = auto()
    FAILED = auto()


class OpenVASScanner:

    SCANNER_NAME = "OpenVAS Default"
    DEFAULT_TIMEOUT = 60

    def __init__(self, session=None):
        self.ov_deployment_id = None
        self.ov_host = None
        self.ov_port = None
        self.user = os.getenv("OPENVAS_OMP_USERNAME", "admin")
        self.password = os.getenv("OPENVAS_OMP_PASSWORD", "admin")
        self.profile = os.getenv("OPENVAS_PROFILE", "Full and very deep")
        self.alive_test = os.getenv("OPENVAS_ALIVE_TEST", "Consider Alive")
        self.session = session

        if session:
            # Restore previous scanner session
            self.ov_deployment_id = session.get("ov_deployment_id")
            self.ov_host = session.get("ov_host")
            self.ov_port = session.get("ov_port")
            if self.ov_host and self.ov_port and Deployer(session["ov_deployment_id"]).is_ready():
                self.conn = self._connect()

    def create(self):
        ov_server = Deployer(self.ov_deployment_id).create()
        self.session = {
            "ov_deployment_id": ov_server["uid"],
            "ov_host": ov_server["host"],
            "ov_port": ov_server["port"],
            "ov_scan_id": None,
            "ov_target_id": None,
            "target": None,
        }
        return self.session

    def delete(self):
        app.logger.info("Trying to delete scanner...")
        Deployer(self.ov_deployment_id).delete()

        if self.session["ov_scan_id"] and self.session["ov_target_id"] and not Utils.is_gcp():
            # Cleanup OpenVAS scan/target manually if local environment
            self.conn.delete_scan(self.session["ov_scan_id"])
            self.conn.delete_target(self.session["ov_target_id"])

        app.logger.info("Completed to delete scanner.")

    def is_ready(self):
        return Deployer(self.session["ov_deployment_id"]).is_ready()

    def launch_scan(self, target):
        app.logger.info("Trying to launch new scan...")
        ov_scan_id, ov_target_id = self.conn.launch_scan(
            target=target, profile=self.profile, alive_test=self.alive_test, max_hosts=1, max_checks=3
        )
        self.session["target"] = target
        self.session["ov_scan_id"] = ov_scan_id
        self.session["ov_target_id"] = ov_target_id
        app.logger.info("Completed to launch scan, session={}".format(self.session))
        return self.session

    def check_status(self):
        try:
            status = self.conn.get_scan_status(self.session["ov_scan_id"])
            app.logger.info("Current scan progress={}, session={}".format(status, self.session))
            # See https://github.com/greenbone/gvmd/blob/577f1b463f5861794bb97066dd0c9c4ab6c223df/src/manage.c#L1482
            if status in ["New", "Running", "Requested"]:
                return ScanStatus.RUNNING
            elif status in ["Done"]:
                return ScanStatus.STOPPED
            else:
                return ScanStatus.FAILED
        except Exception as error:
            app.logger.exception("Scan status check error, reason={}".format(error))
            return ScanStatus.RUNNING

    def get_report(self):
        app.logger.info("Trying to get scan report...")
        ov_report_id = self.conn.get_report_id(self.session["ov_scan_id"])

        app.logger.info("Found report_id={}".format(ov_report_id))
        report_xml = self.conn.get_report_xml(ov_report_id)
        report_txt = ElementTree.tostring(report_xml, encoding="unicode", method="xml")

        app.logger.info("Completed to downloaded report, {} characters.".format(len(report_txt)))
        self.conn.delete_report(ov_report_id)
        return report_txt

    def _connect(self):
        try:
            app.logger.info("Trying to connect to scanner {}:{} ...".format(self.ov_host, self.ov_port))
            return VulnscanManager(self.ov_host, self.user, self.password, self.ov_port, self.DEFAULT_TIMEOUT)
        except VulnscanServerError:
            raise ScanServerException("Scan server connection error.")

    @classmethod
    def get_info(cls):
        return {"source_ip": os.getenv("OPENVAS_SCAN_ENDPOINT", "127.0.0.1")}

    @classmethod
    def parse_report(cls, report_txt):
        app.logger.info("Trying to parse report...")
        parse_records = report_parser_from_text(report_txt, ignore_log_info=False)

        vulns = []
        results = []

        for record in parse_records:
            vuln = {"oid": record.nvt.oid}
            vulns.append(vuln)

            result = {
                "name": record.nvt.name,
                "host": record.host,
                "port": record.port.port_name,
                "cvss_base": record.nvt.cvss_base,
                "cve": ",".join(record.nvt.cve),
                "oid": record.nvt.oid,
                "description": record.nvt.tags[0],
                "qod": "",  # FIXME: not supported by openvas_lib
                "severity": record.severity,
                "severity_rank": record.threat,
                "scanner": OpenVASScanner.SCANNER_NAME,
            }
            results.append(result)

        return {"results": results, "vulns": vulns}


class ScanServerException(Exception):
    pass
