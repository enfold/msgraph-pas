# -*- coding: utf-8 -*-
import httplib
import json
import logging
import os
import re
import urllib
from datetime import datetime
from time import time

from AccessControl import ClassSecurityInfo
from App.class_init import InitializeClass
from pas.plugins.azure_ad.interfaces import IAzureADPlugin
from plone.memoize import ram
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from Products.PlonePAS import interfaces as plonepas_interfaces
from Products.PlonePAS.plugins.group import PloneGroup
from Products.PluggableAuthService.interfaces import plugins as pas_interfaces
from Products.PluggableAuthService.permissions import ManageGroups
from Products.PluggableAuthService.plugins.BasePlugin import BasePlugin
from zope.annotation.interfaces import IAnnotations
from zope.globalrequest import getRequest
from zope.interface import implementer

logger = logging.getLogger('pas.plugins.azure_ad')
zmidir = os.path.join(os.path.dirname(__file__), 'zmi')


def manage_addAzureADPlugin(dispatcher, id, title='', RESPONSE=None, **kw):
    """Create an instance of a Azure AD Plugin.
    """
    azure_ad_plugin = AzureADPlugin(id, title, **kw)
    dispatcher._setObject(azure_ad_plugin.getId(), azure_ad_plugin)
    if RESPONSE is not None:
        RESPONSE.redirect('manage_workspace')


manage_addAzureADPluginForm = PageTemplateFile(
    os.path.join(zmidir, 'add_plugin.pt'),
    globals(),
    __name__='addAzureADPlugin'
)


def _azure_ad_cachekey(method, self, exact_match=False, **kw):
    return(time() // int(os.environ.get('AZURE_CACHE_TIMEOUT', 60)),
           method, exact_match, kw)


@implementer(
    IAzureADPlugin,
    pas_interfaces.IGroupsPlugin,
    pas_interfaces.IGroupEnumerationPlugin,
    pas_interfaces.IPropertiesPlugin,
    pas_interfaces.IUserEnumerationPlugin,
    plonepas_interfaces.capabilities.IGroupCapability,
    plonepas_interfaces.group.IGroupIntrospection)
class AzureADPlugin(BasePlugin):
    """
    """
    security = ClassSecurityInfo()
    meta_type = 'Azure AD Plugin'
    manage_options = ({
        'label': 'Azure AD Settings',
        'action': 'manage_azure_ad_plugin',
    }, ) + BasePlugin.manage_options

    # Tell PAS to swallow our exceptions
    _dont_swallow_my_exceptions = False
    # OAuth2 is required to access this API.
    # Constant strings for OAuth2 flow
    # The OAuth authority
    _authority = 'login.microsoftonline.com'
    _graph = 'graph.windows.net'
    # The token endpoint, where the app sends the auth code
    # to get an access token
    _access_token_url = '/{0}/oauth2/token'
    _api_version = '1.6'
    _tenant_id = os.environ.get('AZURE_TENANT_ID', 'common')
    _client_id = os.environ.get('AZURE_CLIENT_ID')
    _client_secret = os.environ.get('AZURE_CLIENT_SECRET')
    _map_attrs = json.loads(os.environ.get('AZURE_MAP_ATTRS', '{}'))
    _format_attrs = json.loads(os.environ.get('AZURE_FORMAT_ATTRS', '{}'))
    _map_group_attrs = \
        json.loads(os.environ.get('AZURE_MAP_GROUP_ATTRS', '{}'))
    _format_group_attrs = \
        json.loads(os.environ.get('AZURE_FORMAT_GROUP_ATTRS', '{}'))
    plugin_caching = True

    def __init__(self, id, title=None, **kw):
        self._setId(id)
        self.title = title

    def map_attrs(self, reverse=False, map_attrs=None, **kw):
        new_attrs = {}
        if not map_attrs:
            map_attrs = self._map_attrs
        attrs = reverse and {v: k for k, v in map_attrs.items()} \
            or map_attrs
        for k, v in kw.items():
            new_attr = attrs.get(k, k)
            new_attrs[new_attr] = v
        return new_attrs

    def format_attrs(self, format_attrs=None, **kw):
        kw = {k: v and v or '' for k, v in kw.items()}
        if not format_attrs:
            format_attrs = self._format_attrs
        attrs = {}
        for k, v in format_attrs.items():
            try:
                attrs[k] = v.format(**kw)
            except KeyError:
                pass
        return attrs

    @property
    @security.private
    def _token_data(self):
        params = {
            'api-version': self._api_version,
            'grant_type': 'client_credentials',
            'client_id': self._client_id,
            'client_secret': self._client_secret,
            'resource': 'https://{0}'.format(self._graph),
        }
        conn = httplib.HTTPSConnection(self._authority)
        conn.request('POST', self._access_token_url.format(self._tenant_id),
                     urllib.urlencode(params))
        response = conn.getresponse()
        data = response.read()
        logger.debug(data)
        token_data = json.loads(data)
        conn.close()
        return token_data

    @property
    @security.private
    def token(self):
        request = getRequest()
        key = "pas.plugins.azure_ad-token_data"
        if self.plugin_caching:
            cache = IAnnotations(request)
            data = cache.get(key, None)
        else:
            # we can disable caching for testing purposes
            data = None
            cache = {}
        if not data or \
           datetime.now() > datetime.fromtimestamp(int(data['expires_on'])):
            data = self._token_data
            cache[key] = data

        if 'access_token' in data:
            return data['access_token']
        return None

    @security.private
    @ram.cache(_azure_ad_cachekey)
    def _azure_ad_request(self, url, method='GET', params={}, headers={}):
        params['api-version'] = self._api_version
        headers['Authorization'] = 'Bearer {0}'.format(self.token)
        conn = httplib.HTTPSConnection(self._graph)
        logger.debug('/{0}/{1}?{2}'.format(self._tenant_id,
                                           urllib.quote(url),
                                           urllib.urlencode(params)))
        conn.request(method, '/{0}/{1}?{2}'.format(self._tenant_id,
                                                   urllib.quote(url),
                                                   urllib.urlencode(params)),
                     '', headers)
        response = conn.getresponse()
        data = response.read()
        logger.debug(data)
        conn.close()
        return json.loads(data)

    @property
    @security.private
    def groups_enabled(self):
        return self.groups() is not None

    @property
    @security.private
    def users_enabled(self):
        return self.users() is not None

    @security.private
    @ram.cache(_azure_ad_cachekey)
    def groups(self, exact_match=False, **kw):
        params = {}
        if kw:
            params['$filter'] = ''
            for k, v in kw.items():
                if not v:
                    continue
                if isinstance(v, unicode):
                    v = v.encode('utf-8')
                if exact_match:
                    params['$filter'] += "{0} eq '{1}' or ".format(k, v)
                else:
                    params['$filter'] += \
                        "startswith({0}, '{1}') or ".format(k, v)
            params['$filter'] = params['$filter'][:-4]
        groups_data = self._azure_ad_request('/groups', params=params)
        return groups_data.get('value', ())

    @security.private
    @ram.cache(_azure_ad_cachekey)
    def users(self, exact_match=False, **kw):
        params = {}
        if kw:
            params['$filter'] = ''
            for k, v in kw.items():
                if not v:
                    continue
                if isinstance(v, unicode):
                    v = v.encode('utf-8')
                if exact_match:
                    params['$filter'] += "{0} eq '{1}' or ".format(k, v)
                else:
                    params['$filter'] += \
                        "startswith({0}, '{1}') or ".format(k, v)
            params['$filter'] = params['$filter'][:-4]

        users_data = self._azure_ad_request('/users', params=params)
        return users_data.get('value')

    @security.public
    def reset(self):
        # XXX flush caches
        pass

    # ##
    # pas_interfaces.IGroupEnumerationPlugin
    #
    #  Allow querying groups by ID, and searching for groups.
    #
    @security.private
    def enumerateGroups(self, id=None, exact_match=False, sort_by=None,
                        max_results=None, **kw):
        """ -> ( group_info_1, ... group_info_N )

        o Return mappings for groups matching the given criteria.

        o 'id' in combination with 'exact_match' true, will
          return at most one mapping per supplied ID ('id' and 'login'
          may be sequences).

        o If 'exact_match' is False, then 'id' may be treated by
          the plugin as "contains" searches (more complicated searches
          may be supported by some plugins using other keyword arguments).

        o If 'sort_by' is passed, the results will be sorted accordingly.
          known valid values are 'id' (some plugins may support others).

        o If 'max_results' is specified, it must be a positive integer,
          limiting the number of returned mappings.  If unspecified, the
          plugin should return mappings for all groups satisfying the
          criteria.

        o Minimal keys in the returned mappings:

          'id' -- (required) the group ID

          'pluginid' -- (required) the plugin ID (as returned by getId())

          'properties_url' -- (optional) the URL to a page for updating the
                              group's properties.

          'members_url' -- (optional) the URL to a page for updating the
                           principals who belong to the group.

        o Plugin *must* ignore unknown criteria.

        o Plugin may raise ValueError for invalid critera.

        o Insufficiently-specified criteria may have catastrophic
          scaling issues for some implementations.
        """
        if id:
            if not isinstance(id, basestring):
                # XXX TODO
                raise NotImplementedError('sequence is not supported yet.')
            kw['id'] = id
        if 'title' in kw:
            kw['fullname'] = kw.pop('title')
        kw = self.map_attrs(map_attrs=self._map_group_attrs, **kw)
        groups = self.groups(exact_match, **kw)
        if not groups:
            return ()
        pluginid = self.getId()
        ret = list()
        for group in groups:
            group = self.map_attrs(reverse=True,
                                   map_attrs=self._map_group_attrs,
                                   **group)
            group['pluginid'] = pluginid
            ret.append(group)
        if max_results and len(ret) > max_results:
            ret = ret[:max_results]
        return ret

    # ##
    # pas_interfaces.IGroupsPlugin
    #
    #  Determine the groups to which a user belongs.
    @security.private
    def getGroupsForPrincipal(self, principal, request=None):
        """principal -> ( group_1, ... group_N )

        o Return a sequence of group names to which the principal
          (either a user or another group) belongs.

        o May assign groups based on values in the REQUEST object, if present
        """
        url = '/users/{0}/$links/memberOf'.format(principal)
        data = self._azure_ad_request(url)
        if not data or 'odata.error' in data:
            return ()
        groups = data.get('value', ())
        ids = []
        for group in groups:
            url = re.sub('https://{0}/{1}'.format(self._graph,
                                                  self._tenant_id),
                         '', group.get('url'))
            data = self._azure_ad_request(url)
            id = self.map_attrs(reverse=True,
                                map_attrs=self._map_group_attrs,
                                **data).get('id')
            ids.append(id)
        return ids

    # ##
    # pas_interfaces.IUserEnumerationPlugin
    #
    #   Allow querying users by ID, and searching for users.
    #
    @security.private
    def enumerateUsers(self, id=None, login=None, exact_match=False,
                       sort_by=None, max_results=None, **kw):
        """-> ( user_info_1, ... user_info_N )

        o Return mappings for users matching the given criteria.

        o 'id' or 'login', in combination with 'exact_match' true, will
          return at most one mapping per supplied ID ('id' and 'login'
          may be sequences).

        o If 'exact_match' is False, then 'id' and / or login may be
          treated by the plugin as "contains" searches (more complicated
          searches may be supported by some plugins using other keyword
          arguments).

        o If 'sort_by' is passed, the results will be sorted accordingly.
          known valid values are 'id' and 'login' (some plugins may support
          others).

        o If 'max_results' is specified, it must be a positive integer,
          limiting the number of returned mappings.  If unspecified, the
          plugin should return mappings for all users satisfying the criteria.

        o Minimal keys in the returned mappings:

          'id' -- (required) the user ID, which may be different than
                  the login name

          'login' -- (required) the login name

          'pluginid' -- (required) the plugin ID (as returned by getId())

          'editurl' -- (optional) the URL to a page for updating the
                       mapping's user

        o Plugin *must* ignore unknown criteria.

        o Plugin may raise ValueError for invalid criteria.

        o Insufficiently-specified criteria may have catastrophic
          scaling issues for some implementations.
        """
        if login:
            if not isinstance(login, basestring):
                # XXX TODO
                raise NotImplementedError('sequence is not supported yet.')
            kw['login'] = login

        # pas search users gives both login and name if login is meant
        if "login" in kw and "name" in kw:
            del kw["name"]

        if id:
            if not isinstance(id, basestring):
                # XXX TODO
                raise NotImplementedError('sequence is not supported yet.')
            kw['id'] = id
        kw = self.map_attrs(**kw)
        users = self.users(exact_match, **kw)
        if not users:
            return tuple()
        pluginid = self.getId()
        ret = list()
        for usr in users:
            usr = self.map_attrs(reverse=True, **usr)
            usr['pluginid'] = pluginid
            ret.append(usr)
        if max_results and len(ret) > max_results:
            ret = ret[:max_results]
        return ret

    # ##
    # plonepas_interfaces.group.IGroupManagement
    #
    @security.private
    def addGroup(self, id, **kw):
        """
        Create a group with the supplied id, roles, and groups.
        return True if the operation suceeded
        """
        # XXX
        return False

    @security.protected(ManageGroups)
    def addPrincipalToGroup(self, principal_id, group_id):
        """
        Add a given principal to the group.
        return True on success
        """
        # XXX
        return False

    @security.private
    def updateGroup(self, id, **kw):
        """
        Edit the given group. plugin specific
        return True on success
        """
        # XXX
        return False

    @security.private
    def setRolesForGroup(self, group_id, roles=()):
        """
        set roles for group
        return True on success
        """
        # even Products.PlonePAS.plugins.GroupAwareRoleManager does not
        # implement this. We're save to ignore it too for now. But at least
        # we do implement it.
        return False

    @security.private
    def removeGroup(self, group_id):
        """
        Remove the given group
        return True on success
        """
        # XXX
        return False

    @security.protected(ManageGroups)
    def removePrincipalFromGroup(self, principal_id, group_id):
        """
        remove the given principal from the group
        return True on success
        """
        # XXX
        return False

    # ##
    # plonepas_interfaces.plugins.IMutablePropertiesPlugin
    # (including signature of pas_interfaces.IPropertiesPlugin)
    #
    #  Return a property set for a user. Property set can either an object
    #  conforming to the IMutable property sheet interface or a dictionary (in
    #  which case the properties are not persistently mutable).
    #
    @security.private
    def getPropertiesForUser(self, user_or_group, request=None):
        """User -> IMutablePropertySheet || {}

        o User will implement IPropertiedUser. ???

        o Plugin may scribble on the user, if needed (but must still
          return a mapping, even if empty).

        o May assign properties based on values in the REQUEST object, if
          present
        """
        if not user_or_group:
            return {}
        ugid = user_or_group.getId()
        try:
            uprops = self.enumerateUsers(id=ugid, exact_match=True)
            if uprops:
                return self.format_attrs(**uprops[0])
            gprops = self.enumerateGroups(id=ugid, exact_match=True)
            if gprops:
                return self.format_attrs(format_attrs=self._format_group_attrs,
                                         **gprops[0])
        except KeyError:
            pass
        return {}

    @security.private
    def setPropertiesForUser(self, user, propertysheet):
        """Set modified properties on the user persistently.

        Does nothing, it is called by MutablePropertySheet in
        setProperty and setProperties.
        """
        pass

    @security.private
    def deleteUser(self, user_id):
        """Remove properties stored for a user.

        Does nothing, if a user is deleted by ``doDeleteUser``, all it's
        properties are away as well.
        """
        pass

    # ##
    # plonepas_interfaces.plugins.IUserManagement
    # (including signature of pas_interfaces.IUserAdderPlugin)
    #
    @security.private
    def doAddUser(self, login, password):
        """ Add a user record to a User Manager, with the given login
            and password

        o Return a Boolean indicating whether a user was added or not
        """
        # XXX
        return False

    @security.private
    def doChangeUser(self, user_id, password, **kw):
        """Change a user's password (differs from role) roles are set in
        the pas engine api for the same but are set via a role
        manager)
        """
        # XXX
        return False

    @security.private
    def doDeleteUser(self, login):
        """Remove a user record from a User Manager, with the given login
        and password

        o Return a Boolean indicating whether a user was removed or
          not
        """
        # XXX
        return False

    # ##
    # plonepas_interfaces.capabilities.IDeleteCapability
    # (plone ui specific)
    #
    @security.public
    def allowDeletePrincipal(self, id):
        """True if this plugin can delete a certain user/group.
        """
        # XXX
        return False

    # ##
    # plonepas_interfaces.capabilities.IGroupCapability
    # (plone ui specific)
    #
    @security.public
    def allowGroupAdd(self, principal_id, group_id):
        """
        True if this plugin will allow adding a certain principal to
        a certain group.
        """
        # XXX
        return False

    @security.public
    def allowGroupRemove(self, principal_id, group_id):
        """
        True if this plugin will allow removing a certain principal
        from a certain group.
        """
        # XXX
        return False

    # ##
    # plonepas_interfaces.capabilities.IGroupIntrospection
    # (plone ui specific)

    # XXX: why dont we have security declarations here?
    def getGroupById(self, group_id):
        """
        Returns the portal_groupdata-ish object for a group
        corresponding to this id. None if group does not exist here!
        """
        url = '/groups/{0}'.format(group_id)
        group = self._azure_ad_request(url)
        if not group or 'odata.error' in group:
            return None
        title = group.get('displayName', None)
        pgroup = PloneGroup(group_id, title).__of__(self)
        pas = self._getPAS()
        plugins = pas.plugins
        # add properties
        for propfinder_id, propfinder in \
                plugins.listPlugins(pas_interfaces.IPropertiesPlugin):
            data = self.format_attrs(format_attrs=self._format_group_attrs,
                                     **group)
            if not data:
                continue
            pgroup.addPropertysheet(propfinder_id, data)
        # add roles
        for rolemaker_id, rolemaker in \
                plugins.listPlugins(pas_interfaces.IRolesPlugin):

            roles = rolemaker.getRolesForPrincipal(pgroup, None)
            if not roles:
                continue
            pgroup._addRoles(roles)
        return pgroup

    def getGroups(self):
        """
        Returns an iteration of the available groups
        """
        return map(self.getGroupById, self.getGroupIds())

    def getGroupIds(self):
        """
        Returns a list of the available groups (ids)
        """
        ids = []
        for group in self.groups():
            id = self.map_attrs(reverse=True,
                                map_attrs=self._map_group_attrs,
                                **group).get('id')
            ids.append(id)
        return ids

    def getGroupMembers(self, group_id):
        """
        return the members of the given group
        """
        url = '/groups/{0}/$links/members'.format(group_id)
        data = self._azure_ad_request(url)
        if not data:
            return ()
        members = data.get('value', ())
        member_ids = []
        for member in members:
            url = re.sub('https://{0}/{1}'.format(self._graph,
                                                  self._tenant_id),
                         '', member.get('url'))
            data = self._azure_ad_request(url)
            id = self.map_attrs(reverse=True, **data).get('id')
            member_ids.append(id)
        return member_ids

    # ##
    # plonepas_interfaces.capabilities.IPasswordSetCapability
    # (plone ui specific)
    #
    @security.public
    def allowPasswordSet(self, id):
        """True if this plugin can set the password of a certain user.
        """
        # XXX
        return False


InitializeClass(AzureADPlugin)
