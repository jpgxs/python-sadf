#!/usr/bin/env python
# coding: utf-8

import datetime
import subprocess

import dateparser
import pandas as pd
import pytz
import simplejson as json
import six
import tzlocal

from sadf import fieldgroups


__version__ = '0.1.2'


class SadfCommandException(Exception):
    pass


class SadfReportException(Exception):
    pass


class SadfReport(object):

    def __init__(self, sadf_output, field_groups):
        """
        :param sadf_output: output from sadf command inside sysstat->hosts->n
        :type sadf_output: dict
        """
        try:
            self.raw_statistics = \
                self._stats_to_timeseries(sadf_output['statistics'])
        except KeyError:
            raise SadfReportException("'statistics' missing from sadf output")

        self.field_groups = field_groups

        self.file_date = sadf_output.get('file-date')
        self.file_time = sadf_output.get('file-utc-time')
        self.machine_arch = sadf_output.get('machine')
        self.machine_name = sadf_output.get('nodename')
        self.num_cpus = sadf_output.get('number-of-cpus')
        self.system_release = sadf_output.get('release')
        self.restarts = sadf_output.get('restarts')

        self.datetimes = sorted(self.raw_statistics)
        self.reports = self._make_reports()

    def _make_reports(self):
        for time in self.datetimes:
            datapoint = self.raw_statistics[time]

            for group in self.field_groups:
                if group._label in datapoint:
                    group.parse_datapoint(datapoint[group._label])

        index = pd.DatetimeIndex(self.datetimes, tz=pytz.utc, name='time')

        return {
            group._label: group.to_report(index)
            for group in self.field_groups
        }

    @staticmethod
    def _stats_to_timeseries(statistics):
        """Converts list of dictionaries with a timestamp key to a large
        dictionary with the timestamp as the key.
        [{"timestamp": ...  "data": ...}] -> {<time>: {"data": ...}}
        """
        stats = {}

        for time_dot in statistics:
            # Often, one comes across {}
            if not time_dot:
                continue

            ts = time_dot.pop('timestamp')
            timestamp = datetime.datetime.strptime(
                '{}T{}'.format(ts['date'], ts['time']),
                '%Y-%m-%dT%H:%M:%S'
            ).replace(tzinfo=None)

            stats[timestamp] = time_dot

        return stats


class SadfCommand(object):

    # Command/binary name for sadf
    _sadf = 'sadf'

    # Local timezone; sadf likes times to be given in the local timezone so we
    # need to convert from UTC
    _local_tz = tzlocal.get_localzone()

    # The format + precision for times we are using. sadf likes them in this
    # format so we'll use this precision for anything
    _time_fmt = '%H:%M:%S'

    # sar/sadf use these to specify the output formats for data. Without these,
    # the output will be localised
    _command_env = {
        'S_TIME_FORMAT': 'ISO',
        'S_TIME_DEF_TIME': 'UTC',
    }

    def __init__(self, start_time=None, end_time=None, interval=None,
                 data_file=None, field_groups=[]):
        """
        :param start_time: UTC time for the start of the report
        :param end_time: UTC time for the end of the report
        :param interval: return statistics at intervals of this many seconds
        :param data_file: path to sa datafile to use. Otherwise, use today's
        :param field_groups: list of FieldGroups to report on
        :type start_time: str, datetime, time
        :type end_time: str, datetime, time
        :type interval: int
        :type data_file: str
        :type field_groups: list:FieldGroup
        """
        self.start_time = start_time
        self.end_time = end_time
        self.interval = interval
        self.field_groups = field_groups
        self.data_file = data_file

    def run(self):
        """Execute the SadfCommand and create an SadfReport
        :returns: SadfReport -- the output of the command"""
        if not self.field_groups:
            self.field_groups = [
                fieldgroups.CPULoad()
            ]

        results = self._exec()

        try:
            host = results['sysstat']['hosts'][0]
        except KeyError as e:
            raise SadfCommandException('Malformed output from sadf: {}'
                                       .format(e.message))

        return SadfReport(host, self.field_groups)

    def _cvt_to_time(self, time):
        if isinstance(time, datetime.time):
            # Convert to a datetime in UTC
            return datetime.datetime.strptime(
                time.strftime(self._time_fmt),
                self._time_fmt
            ).replace(tzinfo=pytz.utc)
        elif isinstance(time, datetime.datetime):
            return time.replace(tzinfo=pytz.utc)
        elif isinstance(time, six.string_types):
            return dateparser.parse(time).replace(tzinfo=pytz.utc)
        else:
            return None

    @property
    def start_time(self):
        return self._start_time

    @start_time.setter
    def start_time(self, start_time):
        if start_time is None:
            self._start_time = None
            return

        self._start_time = self._cvt_to_time(start_time)
        if not self._start_time:
            raise ValueError('start_time must be time or str, not {}'
                             .format(type(start_time)))

    @property
    def start_time_string(self):
        localtime = self.start_time.astimezone(self._local_tz)
        return localtime.strftime(self._time_fmt)

    @property
    def end_time(self):
        return self._end_time

    @end_time.setter
    def end_time(self, end_time):
        if end_time is None:
            self._end_time = None
            return

        self._end_time = self._cvt_to_time(end_time)
        if not self._end_time:
            raise ValueError('end_time must be time or str, not {}'
                             .format(type(end_time)))

    @property
    def end_time_string(self):
        localtime = self.end_time.astimezone(self._local_tz)
        return localtime.strftime(self._time_fmt)

    def _build_command(self):
        command = [self._sadf, '-j']

        if self.start_time:
            command += ['-s', self.start_time_string]

        if self.end_time:
            command += ['-e', self.end_time_string]

        if self.interval:
            command.append('{}'.format(self.interval))

        if self.data_file:
            command.append(self.data_file)

        # End of sadf args. Start sar args
        command.append('--')

        for group in self.field_groups:
            command += group.sar_cmd

        return command

    def _exec(self):
        command = self._build_command()

        proc = subprocess.Popen(command,
                                env=self._command_env,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)

        stdout, stderr = proc.communicate()
        if stderr:
            raise SadfCommandException('Failed to execute sadf command: {}'
                                       .format(stderr.decode('utf-8')))
        try:
            cmd_output = json.loads(stdout.decode())
        except ValueError:
            raise SadfCommandException('Invalid JSON returned by sadf: {}'
                                       .format(stdout.decode('utf-8')))

        return cmd_output
