from infi import unittest
from infi.pyutils.contexts import contextmanager
from . import InitService, NoPidFile
from mock import patch

import os
import sys

#pylint: disable-all

EXECUTABLE = sys.executable.split(os.path.sep)[-1]

class TestInitServiceBaseClass(unittest.TestCase):
    @contextmanager
    def _patch_get_pid(self, return_value=os.getpid()):
        from os import getpid
        with patch.object(InitService, "_get_pid_from_run_file") as patched:
            patched.return_value = return_value
            yield

    def test_is_running__current_process(self):
        with self._patch_get_pid():
            self.assertTrue(InitService(EXECUTABLE, EXECUTABLE).is_running())

    def test_is_running__no_such_process(self):
        with self._patch_get_pid(999999):
            self.assertFalse(InitService(EXECUTABLE, EXECUTABLE).is_running())

    def test_get_pid(self):
        with self._patch_get_run_file():
            self.assertEqual(InitService(EXECUTABLE, EXECUTABLE)._get_pid_from_run_file(),
                             os.getpid())

    def test_get_run_file_path_no_such_file(self):
        with self.assertRaises(NoPidFile):
            InitService(EXECUTABLE, EXECUTABLE)._get_run_file_path()

    def test_get_run_file_path(self):
        with patch("os.path.exists") as exists:
            exists.return_value = True
            self.assertEqual(InitService(EXECUTABLE, EXECUTABLE)._get_run_file_path(),
                             os.path.join(os.path.sep, "var", "run", "python.pid"))

    @contextmanager
    def _patch_get_run_file(self):
        with self._create_run_file_for_current_process() as path:
            with patch.object(InitService, "_get_run_file_path") as patched:
                patched.return_value = path
                yield

    @contextmanager
    def _create_run_file_for_current_process(self):
        from tempfile import mkstemp
        fd, path = mkstemp()
        os.close(fd)
        with open(path, 'w') as fd:
            fd.write("{}\n".format(os.getpid()))
        try:
            yield path
        finally:
            os.remove(path)
