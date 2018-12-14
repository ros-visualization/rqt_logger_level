# Software License Agreement (BSD License)
#
# Copyright (c) 2012, Willow Garage, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above
#    copyright notice, this list of conditions and the following
#    disclaimer in the documentation and/or other materials provided
#    with the distribution.
#  * Neither the name of Willow Garage, Inc. nor the names of its
#    contributors may be used to endorse or promote products derived
#    from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

# import rosnode
# import rospy
# import rosservice

import time

import rclpy
from rclpy.logging import LoggingSeverity
from rqt_py_common.message_helpers import get_service_class
from rcl_interfaces.msg import LoggerLevelType

from python_qt_binding.QtCore import QObject, qWarning


class LoggerLevelServiceCaller(QObject):

    """
    Handles service calls for getting lists of nodes and loggers
    Also handles sending requests to change logger levels
    """

    def __init__(self, node):
        super(LoggerLevelServiceCaller, self).__init__()
        self._node = node
        self._node_names = []
        self._current_levels = {}

    def get_levels(self):
        return [self.tr('DEBUG'), self.tr('INFO'), self.tr('WARN'), self.tr('ERROR'), self.tr('FATAL')]

    def get_node_names(self):
        """
        Gets a list of available services via a ros service call.
        :returns: a list of all nodes that provide the set_logger_level service, ''list(str)''
        """
        self._node_names = []
        nodes = sorted(self._node.get_node_names())
        service_names_and_types = dict(self._node.get_service_names_and_types())
        for node_name in nodes:
            service_topic = '/{}/set_logger_level'.format(node_name)
            if service_topic in service_names_and_types.keys() and \
                    'rcl_interfaces/SetLoggerLevel' in service_names_and_types[service_topic]:
                self._node_names.append(node_name)

        return self._node_names

    def send_logger_change_message(self, node, level):
        """
        Sends a logger level change request to 'node'.
        :param node: name of the node to chaange, ''str''
        :param logger: name of the logger to change, ''str''
        :param level: name of the level to change, ''str''
        :returns: True if the response is valid, ''bool''
        :returns: False if the request raises an exception or would not change the cached state, ''bool''
        """
        service_name = '/{}/set_logger_level'.format(node)
        if node in self._current_levels and self._current_levels[node].lower() == level.lower():
            return False

        service_class = get_service_class('rcl_interfaces/SetLoggerLevel')

        logger_level = getattr(LoggerLevelType, level.upper())
        request = service_class.Request(name='node', logger_level=logger_level)

        cli = self._node.create_client(service_class, service_name)

        while not cli.wait_for_service(timeout_sec=1.0):
            qWarning(
                'LoggerLevelServiceCaller.send_logger_change_message()'
                'Service ({}, {}) not available'.format(
                    service_name, service_class))

        future = cli.call_async(request)
        timeout = 2
        start_time = time.time()
        time_ellapsed = time.time() - start_time
        while time_ellapsed < timeout and rclpy.ok() and (not future.done()):
            time_ellapsed = time.time() - start_time

        if future.done() and future.result() is not None:
            return True

        qWarning('LoggerLevelServiceCaller.send_logger_change_message(): request:\n%r' % (request))
        qWarning(
            'LoggerLevelServiceCaller.send_logger_change_message(): error calling service "%s".' %
            (service_name))
        return False

    def get_logger_level(self, node_name):
        service_name = '/{}/get_logger_level'.format(node_name)
        service_class = get_service_class('rcl_interfaces/GetLoggerLevel')
        request = service_class.Request(name=node_name)
        # setattr(request, 'name', node_name)
        cli = self._node.create_client(service_class, service_name)
        while not cli.wait_for_service(timeout_sec=3.0):
            qWarning(
                'LoggerLevelServiceCaller.get_logger_level()'
                'Service ({}, {}) not available'.format(
                    service_name, service_class))

        future = cli.call_async(request)
        timeout = 2
        start_time = time.time()
        time_ellapsed = time.time() - start_time
        while time_ellapsed < timeout and rclpy.ok() and (not future.done()):
            time_ellapsed = time.time() - start_time

        if future.done() and future.result() is not None:
            response = future.result()
            self._current_levels[node_name] = LoggingSeverity(response.logger_level).name
            return self._current_levels[node_name]

        qWarning('LoggerLevelServiceCaller.get_logger_level(): request:\n%r' % (request))
        qWarning(
            'LoggerLevelServiceCaller.get_logger_level(): error calling service "%s".' %
            (service_name))
        return ''
