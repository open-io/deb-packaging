#!/usr/bin/python3

import re


def target_version():
    with open('cffi/recompiler.py', encoding='UTF-8') as f:
        for line in f:
            m = re.match(r'^VERSION = "(0x[0-9A-F]+)"$', line)
            if m:
                return int(m.group(1), 16)
    raise Exception('Version not found')


def backend_supported_versions():
    versions = {}
    with open('c/cffi1_module.c', encoding='UTF-8') as f:
        for line in f:
            m = re.match(r'^#define CFFI_VERSION_(MIN|MAX) *(0x[0-9A-F]+)$',
                         line)
            if m:
                versions[m.group(1)] = int(m.group(2), 16)
                if len(versions) == 2:
                    return versions['MIN'], versions['MAX']
    raise Exception('Versions not found')


versions = backend_supported_versions()
target = target_version()
for pkg in ('python-cffi', 'python3-cffi'):
    subst = {
        'pkg': pkg,
        'min': versions[0],
        'max': versions[1],
        'target': target,
    }
    with open('debian/{0}-backend.substvars'.format(pkg), 'a',
              encoding='UTF-8') as f:
        f.write('cffi:Provides={pkg}-backend-api-min (= {min}), '
                '{pkg}-backend-api-max (= {max}), '
                '{pkg}-backend-api-{target}\n'.format(**subst))
    with open('debian/{0}.pydist'.format(pkg), 'w', encoding='UTF-8') as f:
        f.write('cffi {pkg}-backend-api-{target}\n'.format(**subst))

    # Disabled until we can use versioned provides (blocked by #786803)
    # with open('debian/{0}.pydist'.format(pkg), 'w', encoding='UTF-8') as f:
    #     f.write('cffi {pkg}-backend-api-min (<= {target}), '
    #             '{pkg}-backend-api-max (>= {target})\n'
    #             .format(**subst))
