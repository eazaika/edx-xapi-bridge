#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function

import os
import re
import sys

from setuptools import setup


def get_version(*file_paths):
    """Extract version string from the given file."""
    filename = os.path.join(os.path.dirname(__file__), *file_paths)
    with open(filename, 'r', encoding='utf-8') as version_file:
        version_file_content = version_file.read()
    version_match = re.search(
        r"^__version__ = ['\"]([^'\"]*)['\"]",
        version_file_content, re.M
    )
    if version_match:
        return version_match.group(1)
    raise RuntimeError('Unable to find version string.')


VERSION = get_version('xapi_bridge', '__init__.py')

if sys.argv[-1] == 'tag':
    print("Tagging the version on GitHub:")
    os.system(f"git tag -a {VERSION} -m 'version {VERSION}'")
    os.system("git push --tags")
    sys.exit()

# Чтение README и CHANGELOG
def read_file(filename):
    with open(os.path.join(os.path.dirname(__file__), filename), 'r', encoding='utf-8') as file:
        return file.read()

README = read_file('README.md')
# CHANGELOG = read_file('CHANGELOG.rst')  # Раскомментировать, если файл существует

setup(
    name='edx-xapi-bridge',
    version=VERSION,
    description="Process to watch edX tracking logs and convert/publish them as xAPI statements to an external LRS.",
    long_description=README,
    long_description_content_type='text/markdown',  # Указание типа контента для README.md
    author='ADLNet/Appsembler',
    author_email='bryan@appsembler.com',
    url='https://github.com/appsembler/edx-xapi-bridge',
    packages=['xapi_bridge'],
    include_package_data=True,
    install_requires=[  # Добавьте зависимости, например:
        'requests>=2.25',
        'python-dateutil>=2.8',
        'tincan>=0.6',  # или другая xAPI-библиотека
    ],
    license="Apache Software License 2.0",
    zip_safe=False,
    keywords='xAPI TinCan edx',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12'
    ],
    python_requires='>=3.10',  # Указание минимальной версии Python
    # entry_points={  # Раскомментировать, если есть консольные скрипты
    #     'console_scripts': [
    #         'xapi-bridge = xapi_bridge.cli:main',
    #     ],
    # },
)
