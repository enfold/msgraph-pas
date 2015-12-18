# -*- coding: utf-8 -*-
from pas.plugins.azure_ad.plugin import AzureADPlugin


TITLE = 'Azure AD plugin (pas.plugins.azure_ad)'


def isNotSetupProfile(context):
    marker_file = 'pas.plugins.azure_ad_marker.txt'
    return context.readDataFile(marker_file) is None


def isNotUninstallProfile(context):
    marker_file = 'pas.plugins.azure_ad_uninstall_marker.txt'
    return context.readDataFile(marker_file) is None


def _addPlugin(pas, pluginid='azure_ad'):
    installed = pas.objectIds()
    if pluginid in installed:
        return TITLE + ' already installed.'
    plugin = AzureADPlugin(pluginid, title=TITLE)
    pas._setObject(pluginid, plugin)
    plugin = pas[plugin.getId()]  # get plugin acquisition wrapped!
    for info in pas.plugins.listPluginTypeInfo():
        interface = info['interface']
        if not interface.providedBy(plugin):
            continue
        pas.plugins.activatePlugin(interface, plugin.getId())
        pas.plugins.movePluginsDown(
            interface,
            [x[0] for x in pas.plugins.listPlugins(interface)[:-1]],
        )


def _removePlugin(pas, pluginid='azure_ad'):
    installed = pas.objectIds()
    if pluginid not in installed:
        return TITLE + ' not installed.'
    pas.manage_delObjects(pluginid)


def setupPlugin(context):
    if isNotSetupProfile(context):
        return
    site = context.getSite()
    pas = site.acl_users
    _addPlugin(pas)


def uninstallPlugin(context):
    if isNotUninstallProfile(context):
        return
    site = context.getSite()
    pas = site.acl_users
    _removePlugin(pas)
