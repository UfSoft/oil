#!/usr/bin/env python
try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

setup(
    name='OilDB',
    version='0.1',
    description='OIL Database Layout',
    author='Pedro Algarvio',
    author_email='ufs@ufsoft.org',
    url='http://oil.ufsoft.org',
    install_requires=["Pylons>=0.9.5"],
    packages=find_packages(exclude=['ez_setup']),
    include_package_data=True,
    namespace_packages=['oil'],
    test_suite='nose.collector',
    package_data={'oil': ['i18n/*/LC_MESSAGES/*.mo']},
#    entry_points="""
#    [paste.app_factory]
#    main = boil.wsgiapp:make_app
#
#    [paste.app_install]
#    main = pylons.util:PylonsInstaller
#    """,
)
