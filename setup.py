#!/usr/bin/env python
try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

setup(
    name='OIL',
    version='0.1',
    description="Online IRC Logger",
    author="Pedro Algarvio",
    author_email="ufs@ufsoft.org",
    url="http://oil.ufsoft.org/",
    install_requires=["Pylons", "Genshi", "python-openid>=2.0.1"],
    packages=find_packages(exclude=['ez_setup']),
    include_package_data=True,
    test_suite='nose.collector',
    package_data={'oil': ['i18n/*/LC_MESSAGES/*.mo']},
    message_extractors = {'oil': [
        ('**.py', 'python', None),
        ('**/templates/**.html', 'genshi', None),
        ('public/**', 'ignore', None)]
    },
    entry_points="""
    [paste.app_factory]
    main = oil.config.middleware:make_app

    [paste.app_install]
    main = pylons.util:PylonsInstaller

    [distutils.commands]
    extract = babel.messages.frontend:extract_messages
    init = babel.messages.frontend:init_catalog
    compile = babel.messages.frontend:compile_catalog
    update = babel.messages.frontend:update_catalog
    """,
)
