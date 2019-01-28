from setuptools import setup, find_packages


setup(
    name='zeit.content.modules',
    version='1.2.0',
    author='Zeit Online',
    author_email='zon-backend@zeit.de',
    url='http://www.zeit.de/',
    description="vivi Content Modules",
    packages=find_packages('src'),
    package_dir={'': 'src'},
    include_package_data=True,
    zip_safe=False,
    license='BSD',
    namespace_packages=['zeit', 'zeit.content'],
    install_requires=[
        'grokcore.component',
        'lxml',
        'mock',
        'plone.testing',
        'setuptools',
        'zeit.cms',
        'zeit.edit',
        'zeit.content.text >= 2.3.0.dev0',
        'zope.component',
        'zope.interface',
        'zope.schema',
    ],
    entry_points={
    },
)
