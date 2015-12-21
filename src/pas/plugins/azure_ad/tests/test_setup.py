# -*- coding: utf-8 -*-
"""Setup tests for this package."""
import unittest

from pas.plugins.azure_ad.testing import \
    PAS_PLUGINS_AzureAD_PLONE_INTEGRATION_TESTING  # noqa
from Products.CMFCore.utils import getToolByName


class TestSetup(unittest.TestCase):
    """Test that pas.plugins.authomatic is properly installed."""

    layer = PAS_PLUGINS_AzureAD_PLONE_INTEGRATION_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer['portal']
        self.installer = getToolByName(self.portal, 'portal_quickinstaller')

    def test_product_installed(self):
        """Test if pas.plugins.authomatic is installed with
           portal_quickinstaller.
        """
        self.assertTrue(
            self.installer.isProductInstalled(
                'pas.plugins.azure_ad.plone_integration'
            )
        )
        self.assertIn('azure_ad', self.portal.acl_users)

    def test_uninstall(self):
        """Test if pas.plugins.authomatic is cleanly uninstalled."""
        self.installer.uninstallProducts(
            ['pas.plugins.azure_ad.plone_integration']
        )
        self.assertFalse(
            self.installer.isProductInstalled(
                'pas.plugins.azure_ad'
            )
        )
        self.assertNotIn('azure_ad', self.portal.acl_users)
