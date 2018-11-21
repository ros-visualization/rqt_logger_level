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

import rclpy

from python_qt_binding.QtCore import QObject, qWarning
from rqt_py_common.message_helpers import get_service_class


class LoggerLevelServiceCaller(QObject):

    """
    Handles service calls for getting lists of nodes and loggers
    Also handles sending requests to change logger levels
    """

    def __init__(self, context):
        super(LoggerLevelServiceCaller, self).__init__()
        self._context = context

    def get_levels(self):
        return [self.tr('Debug'), self.tr('Info'), self.tr('Warn'), self.tr('Error'), self.tr('Fatal')]

    def get_loggers(self, node):
        if self._refresh_loggers(node):
            return self._current_loggers
        else:
            return []

    def get_node_names(self):
        """
        Gets a list of available services via a ros service call.
        :returns: a list of all nodes that provide the set_logger_level service, ''list(str)''
        """
        service_name = '/set_logger_level'

        # Get available nodes and services
        nodes = set(self._context.get_node_names())
        services = self._context.get_service_names_and_types()

        # Filter and sort nodes by whether they offer the set_logger_level service
        applicable_nodes = (service.replace(service_name, '') for service, _ in services if service_name in service)
        set_logger_level_nodes = sorted((node for node in applicable_nodes if node in nodes))

        return set_logger_level_nodes

    def _refresh_loggers(self, node):
        """
        Stores a list of loggers available for passed in node
        :param node: name of the node to query, ''str''
        """
        self._current_loggers = []
        self._current_levels = {}
        servicename = node + '/get_loggers'
        services = dict(self._context.get_service_names_and_types())
        if servicename not in services:
            qWarning('Service "{}" is not currently available'.format(servicename))
            return False

        service_type_name = services[servicename]
        service_class = get_service_class(service_type_name)
        request = service_class.Request()

        cli = node.create_client(service_class, servicename)
        future = cli.call_async(request)
        rclpy.spin_until_future_complete(node, future)

        if future.result() is None:
            qWarning('Exception while calling service: %r' % future.exception())
            return False

        response = future.result()


        if response._slot_types[0] == 'roscpp/Logger[]':
            for logger in getattr(response, response.__slots__[0]):
                self._current_loggers.append(getattr(logger, 'name'))
                self._current_levels[getattr(logger, 'name')] = getattr(logger, 'level')
        else:
            qWarning(repr(response))
            return False
        return True

    def send_logger_change_message(self, node, logger, level):
        """
        Sends a logger level change request to 'node'.
        :param node: name of the node to chaange, ''str''
        :param logger: name of the logger to change, ''str''
        :param level: name of the level to change, ''str''
        :returns: True if the response is valid, ''bool''
        :returns: False if the request raises an exception or would not change the cached state, ''bool''
        """
        servicename = node + '/set_logger_level'
        if self._current_levels[logger].lower() == level.lower():
            return False

        services = dict(self._context.get_service_names_and_types())
        if servicename not in services:
            qWarning('Service "{}" is not currently available'.format(servicename))
            return False

        service_type_name = services[servicename]
        service_class = get_service_class(service_type_name)
        request = service_class.Request()

        setattr(request, 'logger', logger)
        setattr(request, 'level', level)

        cli = node.create_client(service_class, servicename)
        future = cli.call_async(request)
        rclpy.spin_until_future_complete(node, future)

        if future.result() is None:
            qWarning('Exception while calling service: %r' % future.exception())
            return False

        response = future.result()
        self._current_levels[logger] = response.level
        return True
