# -*- encoding: utf-8 -*-

import sadf
import sadf.fieldgroups as fg


def test_sadf():
    """Just make sure that the modules can be imported and that the
    SadfCommand can be instantiated.
    """
    sadf.SadfCommand(start_time='11:00:00', end_time='13:00:00')
    assert 1 is 1
