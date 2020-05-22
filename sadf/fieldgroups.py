#!/usr/bin/env python
# coding: utf-8

import six
import pandas as pd


class FieldGroup(object):

    _point_labels = None

    def __init__(self, *args, **kwds):
        self.columns = None
        self.datapoints = []
        self._report = None
        self.sadf_cmd = []
        self.sar_cmd = []

        self.parse_args(*args, **kwds)

    def parse_args(self, *args, **kwds):
        pass

    def parse_datapoint(self, datapoint):
        if not self.columns:
            self.columns = sorted(datapoint)

        self.datapoints.append([datapoint[k] for k in self.columns])

    def to_report(self, index):
        return pd.DataFrame(self.datapoints, columns=self.columns, index=index)


class CPULoad(FieldGroup):

    _label = 'cpu-load'

    def parse_args(self, all_fields=False, cores=None):
        self.datapoints = {}
        self.sar_cmd = ['-u']
        if all_fields:
            self._label = 'cpu-load-all'
            self.sar_cmd.append('ALL')

        if cores is not None:
            self.sar_cmd += ['-P', cores]

    def parse_datapoint(self, datapoint):
        for core in datapoint:
            cpu_num = core.pop('cpu')
            if not self.columns:
                self.columns = sorted(core)

            if cpu_num not in self.datapoints:
                self.datapoints[cpu_num] = []

            self.datapoints[cpu_num].append([core[k] for k in self.columns])

    def to_report(self, index):
        return {
            cpu: pd.DataFrame(data, columns=self.columns, index=index)
            for (cpu, data) in six.iteritems(self.datapoints)
        }


class HugePages(FieldGroup):

    _label = 'hugepages'

    def parse_args(self):
        self.sar_cmd = ['-H']

    def parse_datapoint(self, datapoint):
        if not self.columns:
            self.columns = sorted(datapoint)

        self.datapoints.append([datapoint[k] for k in self.columns])

    def to_report(self, index):
        return pd.DataFrame(self.datapoints, columns=self.columns, index=index)


class IO(FieldGroup):

    _label = 'io'

    def parse_args(self):
        self.sar_cmd = ['-b']

    def parse_datapoint(self, datapoint):
        datapoint = {
            'bread': datapoint['io-reads']['bread'],
            'rtps': datapoint['io-reads']['rtps'],
            'bwrtn': datapoint['io-writes']['bwrtn'],
            'wtps': datapoint['io-writes']['wtps'],
            'tps': datapoint['tps'],
        }

        super(IO, self).parse_datapoint(datapoint)


class Kernel(FieldGroup):

    _label = 'kernel'

    def parse_args(self):
        self.sar_cmd = ['-v']


class Memory(FieldGroup):

    _label = 'memory'

    def parse_args(self, all_fields=False):
        self.sar_cmd = ['-r']
        if all_fields:
            self.sar_cmd.append('ALL')


class Network(FieldGroup):

    _label = 'network'

    class Dev(FieldGroup):

        _label = 'net-dev'

        def parse_args(self):
            self.datapoints = {}

        def parse_datapoint(self, datapoint):
            for iface in datapoint:
                iface_name = iface.pop('iface')
                if iface_name not in self.datapoints:
                    self.datapoints[iface_name] = []

                if not self.columns:
                    self.columns = sorted(iface)

                self.datapoints[iface_name].append([
                    iface[k] for k in self.columns
                ])

        def to_report(self, index):
            return {
                iface: pd.DataFrame(data, columns=self.columns, index=index)
                for (iface, data) in six.iteritems(self.datapoints)
            }

    class EDev(Dev):
        _label = 'net-edev'

    class NFS(FieldGroup):
        _label = 'net-nfs'

    class NFSD(FieldGroup):
        _label = 'net-nfsd'

    class Sock(FieldGroup):
        _label = 'net-sock'

    def parse_args(self, dev=False, edev=False, nfs=False, nfsd=False,
                   sock=False):

        self.sub_groups = []
        self.sar_cmd = ['-n']
        self.keywords = []
        self.datapoints = {}

        if dev:
            self.sub_groups.append(self.Dev())
            self.keywords.append('DEV')

        if edev:
            self.sub_groups.append(self.EDev())
            self.keywords.append('EDEV')

        if nfs:
            self.sub_groups.append(self.NFS())
            self.keywords.append('NFS')

        if nfsd:
            self.sub_groups.append(self.NFSD())
            self.keywords.append('NFSD')

        if sock:
            self.sub_groups.append(self.Sock())
            self.keywords.append('SOCK')

        if len(self.keywords) == 0:
            self.keywords.append('ALL')
            self.sub_groups.append(self.Dev())
            self.sub_groups.append(self.EDev())
            self.sub_groups.append(self.NFS())
            self.sub_groups.append(self.NFSD())
            self.sub_groups.append(self.Sock())

        self.sar_cmd.append(','.join(self.keywords))

    def parse_datapoint(self, datapoint):
        for group in self.sub_groups:
            if group._label in datapoint:
                group.parse_datapoint(datapoint[group._label])

    def to_report(self, index):
        return {
            g._label: g.to_report(index)
            for g in self.sub_groups
        }


class Paging(FieldGroup):

    _label = 'paging'

    def parse_args(self):
        self.sar_cmd = ['-B']


class ProcessAndContextSwitch(FieldGroup):

    _label = 'process-and-context-switch'

    def parse_args(self):
        self.sar_cmd = ['-w']


class Queue(FieldGroup):

    _label = 'queue'

    def parse_args(self):
        self.sar_cmd = ['-q']


class SwapPages(FieldGroup):

    _label = 'swap-pages'

    def parse_args(self):
        self.sar_cmd = ['-W']
