Installation
============


Zope2
-----

Add to the instance section of your buildout::

    eggs =
        ...
        pas.plugins.azure_ad

    zcml =
        ...
        pas.plugins.azure_ad

Run buildout. Restart Zope.

Then got to your acl_users folder and add an AzureAD-Plugin.
Configure it using the settings form and activate its features with the ``activate`` tab.


Plone
-----

Add to the instance section of your buildout::

    eggs =
        ...
        pas.plugins.azure_ad

Run buildout. Restart Plone.

Then go to the Plone control-panel, select ``extensions`` and install the Azure AD Plugin.
A new Azure AD Settings icon appear on the left. Click it and configure the plugin there.

To use an own integration-profile, just add to the profiles
``metadata.xml`` file::

    ...
    <dependencies>
        ...
        <dependency>profile-pas.plugins.azure_ad.plonecontrolpanel:default</dependency>
    </dependencies>
    ...


Contributors
============

- Juan Pablo Giménez <jpg@rosario.com>
