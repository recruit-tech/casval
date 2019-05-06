#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
This file contains OMPv4 implementation
"""

from openvas_lib import *
from openvas_lib.common import *

__license__ = """
Copyright 2018 - Golismero project

Redistribution and use in source and binary forms, with or without modification
, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
this list of conditions and the following disclaimer in the documentation
and/or other materials provided with the distribution.

3. Neither the name of the copyright holder nor the names of its contributors
may be used to endorse or promote products derived from this software without
specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF
THE POSSIBILITY OF SUCH DAMAGE.
"""

__all__ = ["OMPv4"]


# ------------------------------------------------------------------------------
#
# OMPv4 implementation
#
# ------------------------------------------------------------------------------
class OMPv4(OMP):
    """
    Internal manager for OpenVAS low level operations.

    ..note:
        This class is based in code from the original OpenVAS plugin:

        https://pypi.python.org/pypi/OpenVAS.omplib

    ..warning:
        This code is only compatible with OMP 4.0.
    """

    # ----------------------------------------------------------------------
    def __init__(self, omp_manager):
        """
        Constructor.

        :param omp_manager: _OMPManager object.
        :type omp_manager: ConnectionManager
        """
        # Call to super
        super(OMPv4, self).__init__(omp_manager)

    # ----------------------------------------------------------------------
    #
    # PUBLIC METHODS
    #
    # ----------------------------------------------------------------------
    def delete_task(self, task_id):
        """
        Delete a task in OpenVAS server.

        :param task_id: task id
        :type task_id: str

        :raises: AuditNotFoundError, ServerError
        """
        request = """<delete_task task_id="%s" />""" % task_id

        try:
            self._manager.make_xml_request(request, xml_result=True)
        except ClientError:
            raise AuditNotFoundError()

    # ----------------------------------------------------------------------
    def stop_task(self, task_id):
        """
        Stops a task in OpenVAS server.

        :param task_id: task id
        :type task_id: str

        :raises: ServerError, AuditNotFoundError
        """

        request = """<stop_task task_id="%s" />""" % task_id
        try:
            self._manager.make_xml_request(request, xml_result=True)
        except ClientError:
            raise AuditNotFoundError()

    # ----------------------------------------------------------------------
    def create_task(self, name, target, config=None, schedule=None, comment=""):
        """
        Creates a task in OpenVAS.

        :param name: name to the task
        :type name: str

        :param target: target to scan
        :type target: str

        :param config: config (profile) name
        :type config: str

        :param schedule: schedule ID to use.
        :type schedule: str

        :param comment: comment to add to task
        :type comment: str

        :return: the ID of the task created.
        :rtype: str

        :raises: ClientError, ServerError
        """

        if not config:
            config = "Full and fast"

        request = """<create_task>
            <name>%s</name>
            <comment>%s</comment>
            <config id="%s"/>
            <target id="%s"/>""" % (
            name,
            comment,
            config,
            target,
        )
        if schedule:
            request += """<schedule>%s</schedule>""" % (schedule)
        request += """</create_task>"""

        return self._manager.make_xml_request(request, xml_result=True).get("id")

    # ----------------------------------------------------------------------
    def create_port_list(self, name, port_range, comment=""):
        """
        Creates a port list in OpenVAS.

        :param name: name to the port list
        :type name: str

        :param port_range: Port ranges. Should be a string of the form "T:22-80,U:53,88,1337"
        :type port_range: str

        :param comment: comment to add to the port list
        :type comment: str

        :return: the ID of the created target.
        :rtype: str

        :raises: ClientError, ServerError TODO
        """
        request = """<create_port_list>
	            <name>%s</name>
	            <port_range>%s</port_range>
	            <comment>%s</comment>
    </create_port_list>""" % (
            name,
            port_range,
            comment,
        )

        return self._manager.make_xml_request(request, xml_result=True).get("id")

    # ----------------------------------------------------------------------
    def create_schedule(
        self, name, hour, minute, month, day, year, period=None, duration=None, timezone="UTC"
    ):
        """
		Creates a schedule in the OpenVAS server.

		:param name: name to the schedule
		:type name: str

		:param hour: hour at which to start the schedule, 0 to 23
		:type hour: str

		:param minute: minute at which to start the schedule, 0 to 59
		:type minute: str

		:param month: month at which to start the schedule, 1-12
		:type month: str

		:param year: year at which to start the schedule
		:type year: str

		:param timezone: The timezone the schedule will follow. The format of a timezone is the same as that of the TZ environment variable on GNU/Linux systems
		:type timezone: str

		:param period:How often the Manager will repeat the scheduled task. Assumed unit of days
		:type period: str

		:param duration: How long the Manager will run the scheduled task for. Assumed unit of hours
		:type period: str

		:return: the ID of the created schedule.
		:rtype: str

		:raises: ClientError, ServerError
		"""
        request = """<create_schedule>
	            <name>%s</name>
	            <first_time>
	            <hour>%s</hour>
	            <minute>%s</minute>
	            <month>%s</month>
	            <day_of_month>%s</day_of_month>
	            <year>%s</year>
	            </first_time>
	            <timezone>%s</timezone>
	            <comment>%s</comment>""" % (
            name,
            hour,
            minute,
            month,
            day,
            year,
            timezone,
            "",
        )
        if duration:
            request += """<duration>%s<unit>hour</unit></duration>""" % (duration)
        else:
            request += """<duration>0<unit>hour</unit></duration>"""
        if period:
            request += """<period>
	            %s
	            <unit>day</unit>
	            </period>""" % (
                period
            )
        else:
            request += """<period>0<unit>day</unit></period>"""
        request += """
    </create_schedule>"""

        return self._manager.make_xml_request(request, xml_result=True).get("id")

    # ----------------------------------------------------------------------
    def create_target(self, name, hosts, comment="", port_list="Default"):
        """
        Creates a target in OpenVAS.

        :param name: name to the target
        :type name: str

        :param hosts: target list. Can be only one target or a list of targets
        :type hosts: str | list(str)

        :param comment: comment to add to task
        :type comment: str

        :param port_list: Port List ID in the server to use for the target
        :type comment: str

        :return: the ID of the created target.
        :rtype: str

        :raises: ClientError, ServerError
        """
        from collections import Iterable

        if isinstance(hosts, str):
            m_targets = hosts
        elif isinstance(hosts, Iterable):
            m_targets = str(",".join(hosts))

        request = """<create_target>
	            <name>%s</name>
	            <hosts>%s</hosts>
	            <port_list>%s</port_list>
	            <comment>%s</comment>
    </create_target>""" % (
            name,
            m_targets,
            port_list,
            comment,
        )

        return self._manager.make_xml_request(request, xml_result=True).get("id")

    # ----------------------------------------------------------------------
    def delete_target(self, target_id):
        """
		Delete a target in OpenVAS server.

		:param target_id: target id
		:type target_id: str

		:raises: ClientError, ServerError
		"""

        request = """<delete_target target_id="%s" />""" % target_id

        self._manager.make_xml_request(request, xml_result=True)

    # ----------------------------------------------------------------------
    def get_configs(self, config_id=None):
        """
		Get information about the configs in the server.

		If name param is provided, only get the config associated to this name.

		:param config_id: config id to get
		:type config_id: str

		:return: `ElementTree`

		:raises: ClientError, ServerError
		"""
        # Recover all config from OpenVAS
        if config_id:
            return self._manager.make_xml_request(
                '<get_configs config_id="%s"/>' % config_id, xml_result=True
            )
        else:
            return self._manager.make_xml_request("<get_configs />", xml_result=True)

    # ----------------------------------------------------------------------
    def get_configs_ids(self, name=None):
        """
		Get information about the configured profiles (configs)in the server.

		If name param is provided, only get the ID associated to this name.

		:param name: config name to get
		:type name: str

		:return: a dict with the format: {config_name: config_ID}

		:raises: ClientError, ServerError
		"""
        m_return = {}

        for x in self.get_configs().findall("config"):
            m_return[x.find("name").text] = x.get("id")

        if name:
            return {name: m_return[name]}
        else:
            return m_return

    # ----------------------------------------------------------------------
    def get_targets(self, target_id=None):
        """
		Get information about the targets in the server.

		If name param is provided, only get the target associated to this name.

		:param target_id: target id to get
		:type target_id: str

		:return: `ElementTree` | None

		:raises: ClientError, ServerError
		"""
        # Recover all config from OpenVAS
        if target_id:
            return self._manager.make_xml_request('<get_targets id="%s"/>' % target_id, xml_result=True).find(
                './/target[@id="%s"]' % target_id
            )
        else:
            return self._manager.make_xml_request("<get_targets />", xml_result=True)

    def get_targets_ids(self, name=None):
        """
		Get IDs of targets of the server.

		If name param is provided, only get the ID associated to this name.

		:param name: target name to get
		:type name: str

		:return: a dict with the format: {target_name: target_ID}

		:raises: ClientError, ServerError
		"""
        m_return = {}

        for x in self.get_targets().findall("target"):
            m_return[x.find("name").text] = x.get("id")

            if name:
                return {name: m_return[name]}
            else:
                return m_return

    # ----------------------------------------------------------------------
    def get_tasks(self, task_id=None):
        """
		Get information about the configured profiles in the server.

		If name param is provided, only get the task associated to this name.

		:param task_id: task id to get
		:type task_id: str

		:return: `ElementTree` | None

		:raises: ClientError, ServerError
		"""
        # Recover all config from OpenVAS
        if task_id:
            return self._manager.make_xml_request('<get_tasks id="%s"/>' % task_id, xml_result=True).find(
                './/task[@id="%s"]' % task_id
            )
        else:
            return self._manager.make_xml_request("<get_tasks />", xml_result=True)

    # ----------------------------------------------------------------------
    def is_task_running(self, task_id):
        """
		Return true if task is running

		:param task_id: ID of task to start.
		:type task_id: str

		:return: bool
		:rtype: bool

		:raises: ClientError, ServerError
		"""
        # Get status with xpath
        status = self.get_tasks().find('.//task[@id="%s"]/status' % task_id)

        if status is None:
            raise ServerError("Task not found")

        return status.text in ("Running", "Requested")

    # ----------------------------------------------------------------------
    def get_tasks_ids(self, name=None):
        """
		Get IDs of tasks of the server.

		If name param is provided, only get the ID associated to this name.

		:param name: task name to get
		:type name: str

		:return: a dict with the format: {task_name: task_ID}

		:raises: ClientError, ServerError
		"""

        m_return = {}

        for x in self.get_tasks().findall("task"):
            m_return[x.find("name").text] = x.get("id")

        if name:
            return {name: m_return[name]}
        else:
            return m_return

    # ----------------------------------------------------------------------
    def get_task_status(self, task_id):
        """
		Get task status

		:param task_id: ID of task to start.
		:type task_id: str

		:raises: ClientError, ServerError
		"""
        if not isinstance(task_id, str):
            raise TypeError("Expected string, got %r instead" % type(task_id))

        status = self.get_tasks().find('.//task[@id="%s"]/status' % task_id)

        if status is None:
            raise ServerError("Task not found")

        return status.text

    # ----------------------------------------------------------------------
    def get_tasks_progress(self, task_id):
        """
		Get the progress of the task.

		:param task_id: ID of the task
		:type task_id: str

		:return: a float number between 0-100
		:rtype: float

		:raises: ClientError, ServerError
		"""
        if not isinstance(task_id, str):
            raise TypeError("Expected string, got %r instead" % type(task_id))

        m_sum_progress = 0.0  # Partial progress
        m_progress_len = 0.0  # All of tasks

        # Get status with xpath
        tasks = self.get_tasks()
        status = tasks.find('.//task[@id="%s"]/status' % task_id)

        if status is None:
            raise ServerError("Task not found")

        if status.text in ("Running", "Pause Requested", "Paused"):
            h = tasks.findall('.//task[@id="%s"]/progress/host_progress/host' % task_id)

            if h is not None:
                m_progress_len += float(len(h))
                m_sum_progress += sum([float(x.tail) for x in h])

        elif status.text in ("Delete Requested", "Done", "Stop Requested", "Stopped", "Internal Error"):
            return 100.0  # Task finished

        try:
            return m_sum_progress / m_progress_len
        except ZeroDivisionError:
            return 0.0

    # ----------------------------------------------------------------------
    def get_tasks_ids_by_status(self, status="Done"):
        """
		Get IDs of tasks of the server depending of their status.

		Allowed status are: "Done", "Paused", "Running", "Stopped".

		If name param is provided, only get the ID associated to this name.

		:param status: get task with this status
		:type status: str - ("Done" |"Paused" | "Running" | "Stopped".)

		:return: a dict with the format: {task_name: task_ID}

		:raises: ClientError, ServerError
		"""
        if status not in ("Done", "Paused", "Running", "Stopped"):
            raise ValueError("Requested status are not allowed")

        m_task_ids = {}

        for x in self.get_tasks().findall("task"):
            if x.find("status").text == status:
                m_task_ids[x.find("name").text] = x.attrib["id"]

        return m_task_ids

    # ----------------------------------------------------------------------
    def get_results(self, task_id=None):
        """
		Get the results associated to the scan ID.

		:param task_id: ID of scan to get. All if not provided
		:type task_id: str

		:return: xml object
		:rtype: `ElementTree`

		:raises: ClientError, ServerError
		"""

        if task_id:
            m_query = '<get_results task_id="%s"/>' % task_id
        else:
            m_query = "<get_results/>"

        return self._manager.make_xml_request(m_query, xml_result=True)

    # ----------------------------------------------------------------------
    def get_tasks_detail(self, scan_id):
        if not isinstance(scan_id, str):
            raise TypeError("Expected string, got %r instead" % type(scan_id))

        try:
            m_response = self._manager.make_xml_request(
                '<get_tasks task_id="%s" details="1"/>' % scan_id, xml_result=True
            )
        except ServerError as e:
            raise VulnscanServerError(
                "Can't get the detail for the task %s. Error: %s" % (scan_id, e.message)
            )
        return m_response

    # ----------------------------------------------------------------------
    def get_report_id(self, scan_id):
        m_response = self.get_tasks_detail(scan_id)
        return m_response.find("task").find("last_report")[0].get("id")

    # ----------------------------------------------------------------------
    def get_report_pdf(self, report_id):
        if not isinstance(report_id, str):
            raise TypeError("Expected string, got %r instead" % type(report_id))

        try:
            m_response = self._manager.make_xml_request(
                '<get_reports report_id="%s" format_id="c402cc3e-b531-11e1-9163-406186ea4fc5"/>' % report_id,
                xml_result=True,
            )
        except ServerError as e:
            raise VulnscanServerError(
                "Can't get the pdf for the report %s. Error: %s" % (report_id, e.message)
            )
        return m_response

    # ----------------------------------------------------------------------
    def get_report_html(self, report_id):
        if not isinstance(report_id, str):
            raise TypeError("Expected string, got %r instead" % type(report_id))

        try:
            m_response = self._manager.make_xml_request(
                '<get_reports report_id="%s" format_id="6c248850-1f62-11e1-b082-406186ea4fc5"/>' % report_id,
                xml_result=True,
            )
        except ServerError as e:
            raise VulnscanServerError(
                "Can't get the HTML for the report %s. Error: %s" % (report_id, e.message)
            )
        return m_response

    # ----------------------------------------------------------------------
    def get_report_xml(self, report_id):
        if not isinstance(report_id, str):
            raise TypeError("Expected string, got %r instead" % type(report_id))

        try:
            m_response = self._manager.make_xml_request(
                '<get_reports report_id="%s" />' % report_id, xml_result=True
            )
        except ServerError as e:
            raise VulnscanServerError(
                "Can't get the xml for the report %s. Error: %s" % (report_id, e.message)
            )

        return m_response

    # ----------------------------------------------------------------------
    def start_task(self, task_id):
        """
		Start a task.

		:param task_id: ID of task to start.
		:type task_id: str

		:raises: ClientError, ServerError
		"""
        if not isinstance(task_id, str):
            raise TypeError("Expected string, got %r instead" % type(task_id))

        m_query = '<start_task task_id="%s"/>' % task_id

        m_response = self._manager.make_xml_request(m_query, xml_result=True)

        return m_response
