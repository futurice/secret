#!/usr/bin/env python
from __future__ import absolute_import
from __future__ import print_function
import sys, six
from tabulate import tabulate

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

class Capturing(list):
    def __enter__(self):
        self._stdout = sys.stdout
        sys.stdout = self._stringio = StringIO()
        return self

    def __exit__(self, *args):
        self.extend(self._stringio.getvalue().splitlines())
        sys.stdout = self._stdout

def fmt_console(result):
    def is_str(result):
        try:
            return isinstance(result, basestring)
        except NameError:
            return isinstance(result, str)
    if any(isinstance(result, k) for k in [list]):
        print("Keys:")
        for k in result:
            print(k)
    elif isinstance(result, bytes):
        print(result)
    elif is_str(result):
        print(result)
    else:
        table = [["Key", "Value"]]
        for k,v in six.iteritems(result):
            table.append([k,v])
        print(tabulate(table, numalign='left', tablefmt='plain'))

def fmt_docker(result):
    c = []
    for k,v in six.iteritems(result):
        c.append('-e '+k+'="'+v+'"')
    print(" ".join(c), end='')

def has_error(result):
    try:
        if result.startswith('Error'):
            return True
    except Exception:
        return False

def prettyprint(result, args):
    with Capturing() as output:
        if args.fmt == 'docker':
            fmt_docker(result)
        else:
            fmt_console(result)

    pretty = "\n".join(output)
    if args.output == '':
        print(pretty)
    else:
        if not has_error(result):
            with open(args.output, 'w') as f:
                f.write(pretty)

    if has_error(result):
        sys.exit(1)
