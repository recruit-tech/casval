import os
from enum import Enum
from enum import auto
from xml.etree import ElementTree

from flask import current_app as app

from openvas_lib import VulnscanManager
from openvas_lib import report_parser_from_text


class ScanStatus(Enum):
    RUNNING = auto()
    STOPPED = auto()
    FAILED = auto()


class OpenVASScanner:

    SCANNER_NAME = "OpenVAS Default"
    DEFAULT_TIMEOUT = 60

    def __init__(self, session=None):

        self.host = os.getenv("OPENVAS_ENDPOINT", "127.0.0.1")
        self.port = int(os.getenv("OPENVAS_PORT", "9390"))
        self.user = os.getenv("OPENVAS_USERNAME", "admin")
        self.password = os.getenv("OPENVAS_PASSWORD", "admin")
        self.profile = os.getenv("OPENVAS_PROFILE", "Full and fast")

        if session != None:
            self.session = session
            self.host = session["openvas_host"]
            self.port = session["openvas_port"]
            self.profile = session["openvas_profile"]

        self.conn = self._connect()

        return

    def launch_scan(self, target):
        try:
            app.logger.info("[Scanner] Trying to launch new scan session...")
            ov_scan_id, ov_target_id = self.conn.launch_scan(target=target, profile=self.profile)
            session = {
                "target": target,
                "openvas_host": self.host,
                "openvas_port": self.port,
                "openvas_profile": self.profile,
                "openvas_scan_id": ov_scan_id,
                "openvas_target_id": ov_target_id,
            }

            app.logger.info("[Scanner] Launched, session={}".format(session))
            return session

        except Exception as error:
            app.logger.error(error)
            return None

    def check_status(self):
        try:
            status = self.conn.get_scan_status(self.session["openvas_scan_id"])

            app.logger.info("[Scanner] current status={}, session={}".format(status, self.session))

            # https://github.com/greenbone/gvmd/blob/577f1b463f5861794bb97066dd0c9c4ab6c223df/src/manage.c#L1482
            # const char*
            # run_status_name (task_status_t status)
            # {
            #   switch (status)
            #     {
            #       case TASK_STATUS_DELETE_REQUESTED:
            #       case TASK_STATUS_DELETE_WAITING:
            #         return "Delete Requested";
            #       case TASK_STATUS_DELETE_ULTIMATE_REQUESTED:
            #       case TASK_STATUS_DELETE_ULTIMATE_WAITING:
            #         return "Ultimate Delete Requested";
            #       case TASK_STATUS_DONE:             return "Done";
            #       case TASK_STATUS_NEW:              return "New";
            #
            #       case TASK_STATUS_REQUESTED:        return "Requested";
            #
            #       case TASK_STATUS_RUNNING:          return "Running";
            #
            #       case TASK_STATUS_STOP_REQUESTED_GIVEUP:
            #       case TASK_STATUS_STOP_REQUESTED:
            #       case TASK_STATUS_STOP_WAITING:
            #         return "Stop Requested";
            #
            #       case TASK_STATUS_STOPPED:          return "Stopped";
            #       default:                           return "Interrupted";
            #     }
            # }

            if status in ["New", "Running", "Requested"]:
                return ScanStatus.RUNNING
            elif status in ["Done"]:
                return ScanStatus.STOPPED
            else:
                return ScanStatus.FAILED
        except Exception as error:
            app.logger.error(error)
            return ScanStatus.RUNNING

    def terminate_scan(self):
        try:
            app.logger.info("[Scanner] Trying to terminate scan session...")

            self.conn.delete_scan(self.session["openvas_scan_id"])
            self.conn.delete_target(self.session["openvas_target_id"])

            app.logger.info("[Scanner] Terminated.")
            return True
        except Exception as error:
            app.logger.error(error)
            return False

    def get_report(self):
        try:
            app.logger.info("[Scanner] Trying to get report...")

            ov_report_id = self.conn.get_report_id(self.session["openvas_scan_id"])

            app.logger.info("[Scanner] Found report_id={}".format(ov_report_id))

            report_xml = self.conn.get_report_xml(ov_report_id)
            report_txt = ElementTree.tostring(report_xml, encoding="unicode", method="xml")
            app.logger.info("[Scanner] Report downloaded, {} characters.".format(len(report_txt)))
            self.conn.delete_report(ov_report_id)
            self.conn.delete_scan(self.session["openvas_scan_id"])
            self.conn.delete_target(self.session["openvas_target_id"])
            return report_txt
        except Exception as error:
            app.logger.error(error)
            return None

    def _connect(self):
        app.logger.info("[Scanner] Trying to connect to {}:{} ...".format(self.host, self.port))

        return VulnscanManager(self.host, self.user, self.password, self.port, self.DEFAULT_TIMEOUT)

    @classmethod
    def parse_report(cls, report_txt):
        try:
            app.logger.info("[Scanner] Trying to parse report...")
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
        except Exception as error:
            app.logger.error(error)
            return None
