# -*- coding: utf-8 -*-
import pas.plugins.azure_ad
from plone.app.robotframework.testing import REMOTE_LIBRARY_BUNDLE_FIXTURE
from plone.app.testing import (PLONE_FIXTURE, FunctionalTesting,
                               IntegrationTesting, PloneSandboxLayer,
                               applyProfile)
from plone.testing import Layer, z2
from Products.CMFCore.interfaces import ISiteRoot
from zope.component import provideUtility

try:
    # plone 5.x with PlonePAS >=5.0
    from Products.PlonePAS.setuphandlers import migrate_root_uf
except ImportError:
    # plone 4.x with PlonePAS <5.0
    from Products.PlonePAS.Extensions.Install import migrate_root_uf

SITE_OWNER_NAME = SITE_OWNER_PASSWORD = 'admin'


class PASAzureADLayer(Layer):

    defaultBases = (
        z2.INTEGRATION_TESTING,
    )

    # Products that will be installed, plus options
    products = (
        ('Products.GenericSetup',           {'loadZCML': True}, ),  # noqa
        ('Products.CMFCore',                {'loadZCML': True}, ),  # noqa
        ('Products.PluggableAuthService',   {'loadZCML': True}, ),  # noqa
        ('Products.PluginRegistry',         {'loadZCML': True}, ),  # noqa
        ('Products.PlonePAS',               {'loadZCML': True}, ),  # noqa
    )

    def setUp(self):
        self.setUpZCML()

    def testSetUp(self):
        self.setUpProducts()
        provideUtility(self['app'], provides=ISiteRoot)
        migrate_root_uf(self['app'])

    def setUpZCML(self):
        """Stack a new global registry and load ZCML configuration of Plone
        and the core set of add-on products into it.
        """

        # Load dependent products's ZCML
        from zope.configuration import xmlconfig
        from zope.dottedname.resolve import resolve

        def loadAll(filename):
            for p, config in self.products:
                if not config['loadZCML']:
                    continue
                try:
                    package = resolve(p)
                except ImportError:
                    continue
                try:
                    xmlconfig.file(
                        filename,
                        package,
                        context=self['configurationContext']
                    )
                except IOError:
                    pass

        loadAll('meta.zcml')
        loadAll('configure.zcml')
        loadAll('overrides.zcml')

    def setUpProducts(self):
        """Install all old-style products listed in the the ``products`` tuple
        of this class.
        """
        for prd, config in self.products:
            z2.installProduct(self['app'], prd)


class PASAzureADPloneLayer(PloneSandboxLayer):

    defaultBases = (PLONE_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        # auto.CSRF_DISABLED = True
        self.loadZCML(package=pas.plugins.azure_ad)
        z2.installProduct(app, 'pas.plugins.azure_ad')

    def tearDownZope(self, app):
        # auto.CSRF_DISABLED = ORIGINAL_CSRF_DISABLED
        pass

    def setUpPloneSite(self, portal):
        applyProfile(portal, 'pas.plugins.azure_ad.plone_integration:default')


PAS_PLUGINS_AzureAD_PLONE_FIXTURE = PASAzureADPloneLayer()


PAS_PLUGINS_AzureAD_PLONE_INTEGRATION_TESTING = IntegrationTesting(
    bases=(PAS_PLUGINS_AzureAD_PLONE_FIXTURE,),
    name='PasPluginsAzureADPloneLayer:IntegrationTesting'
)


PAS_PLUGINS_AzureAD_PLONE_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(PAS_PLUGINS_AzureAD_PLONE_FIXTURE,),
    name='PasPluginsAzureADPloneLayer:FunctionalTesting'
)


PAS_PLUGINS_AzureAD_PLONE_ACCEPTANCE_TESTING = FunctionalTesting(
    bases=(
        PAS_PLUGINS_AzureAD_PLONE_FIXTURE,
        REMOTE_LIBRARY_BUNDLE_FIXTURE,
        z2.ZSERVER_FIXTURE
    ),
    name='PasPluginsAzureADPloneLayer:AcceptanceTesting'
)
