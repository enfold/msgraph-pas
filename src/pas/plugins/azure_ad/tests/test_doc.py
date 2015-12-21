# -*- coding: utf-8 -*-
import doctest
import pprint
import unittest

from interlude import interact
from pas.plugins.azure_ad.testing import PASAzureADLayer
from plone.testing import layered, z2

optionflags = doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS
optionflags = optionflags | doctest.REPORT_ONLY_FIRST_FAILURE

TESTFILES = [
    ('../plugin.rst', PASAzureADLayer),
]


def test_suite():
    suite = unittest.TestSuite()
    suite.addTests([
        layered(
            doctest.DocFileSuite(
                docfile,
                globs={
                    'interact': interact,
                    'pprint': pprint.pprint,
                    'z2': z2,
                },
                optionflags=optionflags,
            ),
            layer=layer(),
        ) for docfile, layer in TESTFILES
    ])
    return suite
