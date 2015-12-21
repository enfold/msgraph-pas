import os
from setuptools import (
    setup,
    find_packages,
)

version = '1.0.0.dev0'
shortdesc = "Azure AD Plugin for Zope2 PluggableAuthService (users and groups)"
longdesc = open(os.path.join(os.path.dirname(__file__), 'README.rst')).read()
longdesc += open(os.path.join(os.path.dirname(__file__), 'TODO.rst')).read()
longdesc += open(os.path.join(os.path.dirname(__file__), 'CHANGES.rst')).read()
longdesc += open(os.path.join(os.path.dirname(__file__), 'LICENSE.rst')).read()


setup(
    name='pas.plugins.azure_ad',
    version=version,
    description=shortdesc,
    long_description=longdesc,
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Zope2',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ],
    keywords='zope2 pas plone azure ad',
    author='Enfold Systems',
    author_email='jpg@rosario.com',
    url='https://pypi.python.org/pypi/pas.plugins.azure_ad',
    license='BSD like',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    namespace_packages=['pas', 'pas.plugins'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'AccessControl',
        'Acquisition',
        'Plone',
        'plone.api',
        'setuptools',
    ],
    extras_require={
        'test': [
            'interlude[ipython]>=1.3.1',
            'plone.app.robotframework[debug]',
            'plone.app.testing',
            'plone.testing',
            'zope.configuration',
        ]
    },
    entry_points="""
    [z3c.autoinclude.plugin]
    target = plone
    """,
)
