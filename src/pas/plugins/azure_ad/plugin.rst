==================
Test of the plugin
==================

Setup
=====

Basics
------

::
    >>> app = layer['app']
    >>> pas = app.acl_users
    >>> pas
    <PluggableAuthService at /acl_users>

Create
------

::
    >>> from pas.plugins.azure_ad.setuphandlers import _addPlugin
    >>> _addPlugin(app.acl_users)
    >>> sorted(pas.objectIds())
    ['azure_ad', 'chooser', 'credentials_basic_auth', 'credentials_cookie_auth', 'plugins', 'roles', 'sniffer', 'users']

    >>> azure_ad = pas['azure_ad']
    >>> azure_ad
    <AzureADPlugin at /acl_users/azure_ad>

turn off plugin_caching for testing, because test request has strange
behaviour::

    >>> azure_ad.plugin_caching = False

PAS Plugins
===========

IGroupEnumerationPlugin
-----------------------

Signature is ``enumerateGroups(self, id=None, exact_match=False, sort_by=None,
max_results=None, **kw)``

::

    >>> azure_ad.enumerateGroups(id='group2')
    ()


IGroupsPlugin
-------------

::

    >>> user = pas.getUserById('uid9')
    >>> azure_ad.getGroupsForPrincipal(user)
    ()


IPropertiesPlugin
-----------------

see PlonePAS, IMutablePropertiesPlugin

IUserEnumerationPlugin
----------------------

Signature is ``enumerateUsers( id=None, login=None, exact_match=False,
sort_by=None, max_results=None, **kw)``

::

    >>> azure_ad.enumerateUsers(id='uid1')
    ()


IDeleteCapability
-----------------

It's not allowed to delete a principal using this plugin. We may change this
later and make it configurable::

    >>> azure_ad.allowDeletePrincipal('uid0')
    False

    >>> azure_ad.allowDeletePrincipal('unknownuser')
    False


PlonePAS
========

IGroupCapability
----------------

By now adding groups is not allowed.  We may change this later and make it
configurable::

    >>> azure_ad.allowGroupAdd('uid0', 'group0')
    False

Same for deletion of groups::

    >>> azure_ad.allowGroupRemove('uid0', 'group0')
    False

IGroupIntrospection
-------------------

getGroupById returns the portal_groupdata-ish object for a group corresponding
to this id::

    >>> print azure_ad.getGroupById('non-existent')
    None

list all groups ids::

    >>> azure_ad.getGroupIds()
    []

list all groups::

    >>> azure_ad.getGroups()
    []

list all members of a group::

    >>> azure_ad.getGroupMembers('group3')
    []

IPasswordSetCapability
----------------------

User are able to set the password::

    >>> azure_ad.allowPasswordSet('uid0')
    False

Not so for groups::

    >>> azure_ad.allowPasswordSet('group0')
    False

Also not for non existent::

    >>> azure_ad.allowPasswordSet('ghost')
    False

IGroupManagement
----------------

See also ``IGroupCapability`` - for now we dont support this::

    >>> azure_ad.addGroup(id)
    False

    >>> azure_ad.addPrincipalToGroup('uid0', 'group0')
    False

    >>> azure_ad.updateGroup('group9', **{})
    False

    >>> azure_ad.setRolesForGroup('uid0', roles=('Manager'))
    False

    >>> azure_ad.removeGroup('group0')
    False

    >>> azure_ad.removePrincipalFromGroup('uid1', 'group1')
    False
