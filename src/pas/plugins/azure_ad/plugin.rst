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
    ['chooser', 'credentials_basic_auth', 'credentials_cookie_auth', 'pasazure_ad',
    'plugins', 'roles', 'sniffer', 'users']

    >>> azure_ad = pas['pasazure_ad']
    >>> azure_ad
    <AzureADPlugin at /acl_users/pasazure_ad>

turn off plugin_caching for testing, because test request has strange
behaviour::

    >>> azure_ad.plugin_caching = False

PAS Plugins
===========

IAuthenticationPlugin
---------------------

::

    >>> azure_ad.authenticateCredentials({'login':'cn0', 'password': 'secret0'})
    (u'uid0', 'cn0')

    >>> azure_ad.authenticateCredentials({'login':'admin', 'password': 'admin'})

    >>> azure_ad.authenticateCredentials({'login':'nonexist', 'password': 'dummy'})


IGroupEnumerationPlugin
-----------------------

Signature is ``enumerateGroups(self, id=None, exact_match=False, sort_by=None,
max_results=None, **kw)``

::

    >>> azure_ad.enumerateGroups(id='group2')
    [{'pluginid': 'pasazure_ad', 'id': 'group2'}]

    >>> print sorted([_['id'] for _ in azure_ad.enumerateGroups(id='group*')])
    ['group0', 'group1', 'group2', 'group3', 'group4', 'group5', 'group6',
    'group7', 'group8', 'group9']

    >>> [_['id'] for _ in azure_ad.enumerateGroups(id='group*', sort_by='id')]
    ['group0', 'group1', 'group2', 'group3', 'group4', 'group5', 'group6',
    'group7', 'group8', 'group9']

    >>> azure_ad.enumerateGroups(id='group*', exact_match=True)
    ()

    >>> azure_ad.enumerateGroups(id='group5', exact_match=True)
    [{'pluginid': 'pasazure_ad', 'id': 'group5'}]

    >>> len(azure_ad.enumerateGroups(id='group*', max_results=3))
    3


IGroupsPlugin
-------------

::

    >>> user = pas.getUserById('uid9')
    >>> azure_ad.getGroupsForPrincipal(user)
    [u'group9']

    >>> user = pas.getUserById('uid1')
    >>> azure_ad.getGroupsForPrincipal(user)
    [u'group1', u'group2', u'group3', u'group4', u'group5',
    u'group6', u'group7', u'group8', u'group9']

    >>> user = pas.getUserById('uid0')
    >>> azure_ad.getGroupsForPrincipal(user)
    []

IPropertiesPlugin
-----------------

see PlonePAS, IMutablePropertiesPlugin

IUserEnumerationPlugin
----------------------

Signature is ``enumerateUsers( id=None, login=None, exact_match=False,
sort_by=None, max_results=None, **kw)``

::

    >>> azure_ad.enumerateUsers(id='uid1')
    [{'login': u'cn1', 'pluginid': 'pasazure_ad', 'id': 'uid1'}]

    >>> azure_ad.enumerateUsers(id='uid*')
    [{'login': u'cn0', 'pluginid': 'pasazure_ad', 'id': 'uid0'},
    {'login': u'cn1', 'pluginid': 'pasazure_ad', 'id': 'uid1'},
    {'login': u'cn2', 'pluginid': 'pasazure_ad', 'id': 'uid2'},
    {'login': u'cn3', 'pluginid': 'pasazure_ad', 'id': 'uid3'},
    {'login': u'cn4', 'pluginid': 'pasazure_ad', 'id': 'uid4'},
    {'login': u'cn5', 'pluginid': 'pasazure_ad', 'id': 'uid5'},
    {'login': u'cn6', 'pluginid': 'pasazure_ad', 'id': 'uid6'},
    {'login': u'cn7', 'pluginid': 'pasazure_ad', 'id': 'uid7'},
    {'login': u'cn8', 'pluginid': 'pasazure_ad', 'id': 'uid8'},
    {'login': u'cn9', 'pluginid': 'pasazure_ad', 'id': 'uid9'}]

    >>> [_['id'] for _ in azure_ad.enumerateUsers(id='uid*', sort_by='id')]
    ['uid0', 'uid1', 'uid2', 'uid3', 'uid4', 'uid5', 'uid6', 'uid7', 'uid8',
    'uid9']

    >>> azure_ad.enumerateUsers(id='uid*', exact_match=True)
    ()

    >>> azure_ad.enumerateUsers(id='uid4', exact_match=True)
    [{'login': u'cn4', 'pluginid': 'pasazure_ad', 'id': 'uid4'}]

    >>> len(azure_ad.enumerateUsers(id='uid*', max_results=3))
    3

    >>> azure_ad.enumerateUsers(login='cn1')
    [{'login': u'cn1', 'pluginid': 'pasazure_ad', 'id': 'uid1'}]


IDeleteCapability
-----------------

It's not allowed to delete a principal using this plugin. We may change this
later and make it configurable::

    >>> azure_ad.allowDeletePrincipal('uid0')
    False

    >>> azure_ad.allowDeletePrincipal('unknownuser')
    False


Picklable
---------

In order to cache propertysheets it must be picklable::

    >>> from Acquisition import aq_base
    >>> import pickle
    >>> len(pickle.dumps(aq_base(azure_ad))) > 200
    True


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

    >>> azure_ad.getGroupById('group0')
    <PloneGroup u'group0'>

    >>> print azure_ad.getGroupById('non-existent')
    None

list all groups ids::

    >>> azure_ad.getGroupIds()
    [u'group0', u'group1', u'group2', u'group3', u'group4', u'group5',
    u'group6', u'group7', u'group8', u'group9']

list all groups::

    >>> azure_ad.getGroups()
    [<PloneGroup u'group0'>, <PloneGroup u'group1'>, <PloneGroup u'group2'>,
    <PloneGroup u'group3'>, <PloneGroup u'group4'>, <PloneGroup u'group5'>,
    <PloneGroup u'group6'>, <PloneGroup u'group7'>, <PloneGroup u'group8'>,
    <PloneGroup u'group9'>]

list all members of a group::

    >>> azure_ad.getGroupMembers('group3')
    (u'uid1', u'uid2', u'uid3')

IPasswordSetCapability
----------------------

User are able to set the password::

    >>> azure_ad.allowPasswordSet('uid0')
    True

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

IMutablePropertiesPlugin
------------------------

Get works::

    >>> user = pas.getUserById('uid0')
    >>> sheet = azure_ad.getPropertiesForUser(user, request=None)
    >>> sheet
    <pas.plugins.azure_ad.sheet.AzureADUserPropertySheet instance at ...>

    >>> sheet.getProperty('mail')
    u'uid0@groupOfNames_10_10.com'

Set does nothing, but the sheet itselfs set immediatly::

    >>> from pas.plugins.azure_ad.sheet import AzureADUserPropertySheet
    >>> sheet = AzureADUserPropertySheet(user, azure_ad)
    >>> sheet.getProperty('mail')
    u'uid0@groupOfNames_10_10.com'

    >>> sheet.setProperty(None, 'mail', u'foobar@example.com')
    >>> sheet.getProperty('mail')
    u'foobar@example.com'

    >>> sheet2 = AzureADUserPropertySheet(user, azure_ad)
    >>> sheet2.getProperty('mail')
    u'foobar@example.com'

    >>> azure_ad.deleteUser('cn9')


In order to cache propertysheets it must be picklable::

    >>> len(pickle.dumps(sheet2)) > 600
    True


IUserManagement
---------------

Password change and attributes at once with ``doChangeUser``::

    >>> azure_ad.doChangeUser('uid9', 'geheim') is None
    True

    >>> azure_ad.authenticateCredentials({'login':'cn9', 'password': 'geheim'})
    (u'uid9', 'cn9')


We dont support user deletion for now. We may change this later and make it
configurable::

    >>> azure_ad.doDeleteUser('uid0')
    False
