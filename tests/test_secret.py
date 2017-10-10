# encoding=utf8
import unittest
import os, sys

import trollius as asyncio
from trollius import From, Return

try:# PY2
    from cStringIO import StringIO
except:
    from io import StringIO
from contextlib import contextmanager

from secret.secret import runner, prepare, main
from secret.project import get_project

@contextmanager
def capture(command, *args, **kwargs):
    out, sys.stdout = sys.stdout, StringIO()
    command(*args, **kwargs)
    sys.stdout.seek(0)
    yield sys.stdout.read()
    sys.stdout = out

def run_runner(*args, **kwargs):
    # to avoid event loop open/closed -issues while testing
    args = prepare()
    future = main(args, **kwargs)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(future)

def datadir():
    return os.path.dirname(os.path.realpath(__file__))

class TestSecret(unittest.TestCase):
    def setUp(self):
        del sys.argv[1:]
        self.project = get_project('.secret').load()

    def project_name(self):
        return self.project['project']

    def test_cli_without_arguments(self):
        with self.assertRaises(SystemExit):
            run_runner()

    def test_put(self):
        sys.argv.append('put')
        with self.assertRaises(SystemExit):
            with capture(run_runner) as output:
                self.assertEquals(output, 'Error! No value provided.\n')

    def test_put_key(self):
        sys.argv.append('put')
        sys.argv.append('key')
        with self.assertRaises(SystemExit):
            with capture(run_runner) as output:
                self.assertEquals(output, 'Error! No value provided.\n')

    def test_put_key_value(self):
        sys.argv.append('put')
        sys.argv.append('key')
        sys.argv.append('value')
        with capture(run_runner) as output:
            self.assertEquals(output, 'Success! Wrote: {}/default/key\n'.format(self.project_name()))

        del sys.argv[1:]
        sys.argv.append('get')
        sys.argv.append('key')
        with capture(run_runner) as output:
            self.assertEquals(output, 'value\n')

        del sys.argv[1:]
        sys.argv.append('config')
        sys.argv.append('-F')
        sys.argv.append('docker')
        with capture(run_runner) as output:
            self.assertEquals(output, '-e key="value"\n')

        del sys.argv[1:]
        sys.argv.append('config')
        sys.argv.append('-F')
        sys.argv.append('json')
        with capture(run_runner) as output:
            self.assertEquals(output, '{"key": "value"}\n')

        del sys.argv[1:]
        sys.argv.append('delete')
        sys.argv.append('key')
        with capture(run_runner) as output:
            self.assertEquals(output, 'Success! Deleted: {}/default/key\n'.format(self.project_name()))

    def test_put_key_value_nonascii(self):
        sys.argv.append('put')
        sys.argv.append('key')
        sys.argv.append('val%€')
        with capture(run_runner) as output:
            self.assertEquals(output, 'Success! Wrote: {}/default/key\n'.format(self.project_name()))

        del sys.argv[1:]
        sys.argv.append('get')
        sys.argv.append('key')
        with capture(run_runner) as output:
            self.assertEquals(output, 'val%€\n')

        del sys.argv[1:]
        sys.argv.append('delete')
        sys.argv.append('key')
        with capture(run_runner) as output:
            self.assertEquals(output, 'Success! Deleted: {}/default/key\n'.format(self.project_name()))

    def test_put_key_file_nonascii(self):
        sys.argv.append('put')
        sys.argv.append('keyfile')
        sys.argv.append(os.path.join(datadir(), 'upload_nonascii.txt'))
        with capture(run_runner) as output:
            self.assertEquals(output, 'Success! Wrote: {}/default/keyfile\n'.format(self.project_name()))

        del sys.argv[1:]
        sys.argv.append('get')
        sys.argv.append('keyfile')
        with capture(run_runner) as output:
            self.assertEquals(output, 'h€llo Ä ö Å\n')

        del sys.argv[1:]
        sys.argv.append('delete')
        sys.argv.append('keyfile')
        with capture(run_runner) as output:
            self.assertEquals(output, 'Success! Deleted: {}/default/keyfile\n'.format(self.project_name()))

    def test_put_key_file(self):
        sys.argv.append('put')
        sys.argv.append('keyfile')
        sys.argv.append(os.path.join(datadir(), 'upload.txt'))
        with capture(run_runner) as output:
            self.assertEquals(output, 'Success! Wrote: {}/default/keyfile\n'.format(self.project_name()))

        del sys.argv[1:]
        sys.argv.append('get')
        sys.argv.append('keyfile')
        with capture(run_runner) as output:
            self.assertEquals(output, 'upload test\n')

        del sys.argv[1:]
        sys.argv.append('delete')
        sys.argv.append('keyfile')
        with capture(run_runner) as output:
            self.assertEquals(output, 'Success! Deleted: {}/default/keyfile\n'.format(self.project_name()))

    def test_file_listing(self):
        sys.argv.append('put')
        sys.argv.append('key')
        sys.argv.append('value')
        with capture(run_runner) as output:
            self.assertEquals(output, 'Success! Wrote: {}/default/key\n'.format(self.project_name()))

        del sys.argv[1:]
        sys.argv.append('put')
        sys.argv.append('keyfile')
        sys.argv.append(os.path.join(datadir(), 'upload.txt'))
        with capture(run_runner) as output:
            self.assertEquals(output, 'Success! Wrote: {}/default/keyfile\n'.format(self.project_name()))

        del sys.argv[1:]
        sys.argv.append('config')
        with capture(run_runner) as output:
            self.assertEquals(output, 'Key      Value\nkey      value\nkeyfile  <FILE>\n')

        del sys.argv[1:]
        sys.argv.append('config')
        sys.argv.append('--skip-files')
        with capture(run_runner) as output:
            self.assertEquals(output, 'Key  Value\nkey  value\n')
