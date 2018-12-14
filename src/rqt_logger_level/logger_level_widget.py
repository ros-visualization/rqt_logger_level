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

import os
import rclpy
from rclpy.logging import LoggingSeverity

from ament_index_python.resources import get_resource

from python_qt_binding import loadUi
from python_qt_binding.QtCore import qWarning
from python_qt_binding.QtWidgets import QWidget


class LoggerLevelWidget(QWidget):

    """
    Widget for use with LoggerLevelServiceCaller class to alter the ROS logger levels
    """

    def __init__(self, service_caller, node):
        """
        :param node: shared rqt node
        """
        super(LoggerLevelWidget, self).__init__()

        pkg_name = 'rqt_logger_level'
        _, package_path = get_resource('packages', pkg_name)
        ui_file = os.path.join(
            package_path, 'share', pkg_name, 'resource', 'logger_level.ui')

        loadUi(ui_file, self)
        self.setObjectName('LoggerLevelWidget')
        self._service_caller = service_caller
        self._node = node

        self.node_list.currentRowChanged[int].connect(self.node_changed)
        self.level_list.currentRowChanged[int].connect(self.level_changed)
        self.refresh_button.clicked[bool].connect(self.refresh_nodes)

        self.refresh_nodes()
        if self.node_list.count() > 0:
            self.node_list.setCurrentRow(0)

    def refresh_nodes(self):
        """
        Refreshes the top level node list and repoulates the node_list widget.
        As a side effect the level and logger lists are cleared
        """
        self.level_list.clear()
        self.node_list.clear()
        for name in self._node.get_node_names():
            self.node_list.addItem(name)

    def node_changed(self, row):
        """
        Handles the rowchanged event for the node_list widget
        Populates logger_list with the loggers for the node selected
        :param row: the selected row in node_list, ''int''
        """
        if row == -1:
            return
        if row < 0 or row >= self.node_list.count():
            qWarning('Node row %s out of bounds. Current count: %s' % (row, self.node_list.count()))
            return
        self.level_list.clear()

        for level in self._service_caller.get_levels():
            self.level_list.addItem(level)

    def level_changed(self, row):
        """
        Handles the rowchanged event for the level_list widget
        Makes a service call to change the logger level for the indicated node/logger to the
        selected value
        :param row: the selected row in level_list, ''int''
        """
        if row == -1:
            return
        if row < 0 or row >= self.level_list.count():
            qWarning('Level row %s out of bounds. Current count: %s' %
                     (row, self.level_list.count()))
            return
        logging_level_text = self.level_list.item(row).text()
        logging_level = getattr(LoggingSeverity, logging_level_text.upper())

        # TODO implement services and service caller
        rclpy.logging.set_logger_level(
            self.node_list.currentItem().text(),
            logging_level)
