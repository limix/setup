from __future__ import unicode_literals

import pprint
import re
import sys
from ast import literal_eval
from os import chdir, getcwd
from os.path import abspath, dirname, join
from importlib import import_module

from setuptools import find_packages, setup

PY2 = sys.version_info[0] == 2

if PY2:
    string_types = unicode, str
else:
    string_types = bytes, str

DESCRIPTION_FILE = "README.md"


def get_config_parser():
    if PY2:
        from ConfigParser import ConfigParser
    else:
        from configparser import ConfigParser
        return ConfigParser()


def unicode_airlock(v):
    r"""Convert string to unicode representation."""
    if isinstance(v, bytes):
        v = v.decode()
        return v


class setup_folder(object):
    r"""Temporarily change to setup.py's folder."""

    def __init__(self):
        self._old_path = None

    def __enter__(self):
        src_path = dirname(abspath(sys.argv[0]))
        self._old_path = getcwd()
        chdir(src_path)
        sys.path.insert(0, src_path)

    def __exit__(self, *_):
        del sys.path[0]
        chdir(self._old_path)


def get_init_metadata(metadata, name):
    expr = re.compile(r"__%s__ *=[^\"]*\"([^\"]*)\"" % name)
    prjname = metadata['packages'][0]
    data = open(join(prjname, "__init__.py")).read()
    return re.search(expr, data).group(1)


def extract_package_metadata(name):
    pass


def make_list(metadata):
    return metadata.strip().split()


def if_set_list(metadata, name):
    if name in metadata:
        metadata[name] = make_list(metadata[name])


def literal_else_apply(metadata, key, func):
    if key in metadata:
        metadata[key] = literal_eval(metadata[key])
    else:
        metadata[key] = func()


def if_literal(metadata, key):
    if key in metadata:
        metadata[key] = literal_eval(metadata[key])


def convert_types(metadata):
    bools = ['True', 'False']
    for k in metadata.keys():
        v = unicode_airlock(metadata[k])
        if isinstance(metadata[k], string_types) and v in bools:
            metadata[k] = v == 'True'


def extract_about_info(pkg_folder):
    exec(open(join(pkg_folder, "__about__.py")).read())
    d = dict(locals())
    relevant_keys = [
        'maintainer', 'maintainer_email', 'description', 'version', 'author',
        'author_email'
    ]
    d = {k.strip('__'): v for (k, v) in d.items()}
    return {k: v for (k, v) in d.items() if k in relevant_keys}


def parse_requirements(metadata, filename, metaname):
    if metaname not in metadata:
        return
    with open(filename) as f:
        metadata[metaname] = f.read().splitlines()


def parse_cffi(metadata, data):
    metadata['cffi_modules'] = make_list(data['modules'])


def parse_entry_points(metadata, data):
    if 'console_scripts' in data:
        metadata['entry_points'] = {
            'console_scripts': make_list(data['console_scripts'])
        }
    return metadata


def setup_package():
    config = get_config_parser()
    config.read('setup.cfg')

    metadata = dict(config.items('metadata'))

    # Mandatory settings
    metadata['include_package_data'] = True
    metadata['zip_safe'] = True
    metadata['description_file'] = DESCRIPTION_FILE
    metadata['long_description'] = open(DESCRIPTION_FILE).read()

    literal_else_apply(metadata, 'packages', find_packages)

    pkg_folder = metadata['packages'][0]
    metadata.update(extract_about_info(pkg_folder))

    parse_requirements(metadata, 'setup-requirements.txt', 'setup_requires')
    parse_requirements(metadata, 'test-requirements.txt', 'test_require')
    parse_requirements(metadata, 'requirements.txt', 'install_requires')

    if_set_list(metadata, 'keywords')

    if 'metadata:cffi' in config:
        parse_cffi(metadata, dict(config.items('metadata:cffi')))

    if 'metadata:entry_points' in config:
        data = dict(config.items('metadata:entry_points'))
        parse_entry_points(metadata, data)

    # setup(**metadata)
    pp = pprint.PrettyPrinter()
    pp.pprint(metadata)


if __name__ == '__main__':
    with setup_folder():
        setup_package()
