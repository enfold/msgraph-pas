# -*- coding: utf-8 -*-
from AccessControl.Permissions import add_user_folders
from Products.PluggableAuthService import registerMultiPlugin
from pas.plugins.azure_ad.plugin import AzureADPlugin
from pas.plugins.azure_ad.plugin import manage_addAzureADPlugin
from pas.plugins.azure_ad.plugin import manage_addAzureADPluginForm
from pas.plugins.azure_ad.plugin import zmidir

import os


PROJECTNAME = 'pas.plugins.azure_ad'


def initialize(context):
    """Initializer called when used as a Zope 2 product."""
    registerMultiPlugin(AzureADPlugin.meta_type)  # Add to PAS menu
    context.registerClass(
        AzureADPlugin,
        permission=add_user_folders,
        icon=os.path.join(zmidir, 'azure_ad.png'),
        constructors=(manage_addAzureADPluginForm,
                      manage_addAzureADPlugin),
        visibility=None
    )
