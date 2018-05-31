from setuptools import setup

setup(
    name='cfdns',
    version='0.2',
    description='dynamic DNS with cloudflare',
    url='http://github.com/rupa/cfdns',
    author='rupa',
    author_email='rupa@lrrr.us',
    license='MIT',
    packages=['cfdns'],
    entry_points={
        'console_scripts': ['cfdns=cfdns:main'],
    },
    zip_safe=False
)
