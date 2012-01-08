__import__("pkg_resources").declare_namespace(__name__)

import logging
logger = logging.getLogger()

from infi.vendata.powertools.utils import execute_command
from infi.exceptools import InfiException

class NoPidFile(InfiException):
    pass

class InitService(object): # pylint: disable=R0922
    def __init__(self, service_name, process_name):
        self._service_name = service_name
        self._process_name = process_name

    def is_running(self):
        try:
            pid = self._get_pid_from_run_file()
            return self._is_process_alive(pid)
        except NoPidFile:
            return False

    def start(self): # pragma: no cover
        raise NotImplementedError()

    def stop(self): # pragma: no cover
        raise NotImplementedError()

    def is_auto_start(self): # pragma: no cover
        raise NotImplementedError()

    def set_auto_start(self): # pragma: no cover
        raise NotImplementedError()

    def _get_run_file_path(self):
        from os.path import exists, join, sep
        pid_filepath = join(sep , "var", "run", "{}.pid".format(self._process_name))
        if not exists(pid_filepath):
            raise NoPidFile("pid file {} does not exist, service is not running?".format(pid_filepath))
        return pid_filepath

    def _get_pid_from_run_file(self):
        pid_filepath = self._get_run_file_path()
        with open(pid_filepath, 'r') as fd:
            pid = int(fd.read().strip("\n"))
            return pid

    def _is_process_alive(self, pid):
        from psutil import Process, NoSuchProcess
        result = False
        try:
            process = Process(pid)
            result = True
        except NoSuchProcess:
            logger.error("No Such process, {}".format(pid))
        return result


class LinuxInitService(InitService):
    def _run_service_subcommand(self, sub_command):
        cmd = "service {} {}".format(self._service_name, sub_command).split()
        _ = execute_command(cmd)

    def start(self):
        self._run_service_subcommand("start")
        # The pid file is not created immediately
        from time import sleep
        sleep(1)

    def stop(self):
        self._run_service_subcommand("stop")

    def is_auto_start(self):
        from glob import glob
        from os.path import join, sep
        return len(glob(join(sep, "etc", "rc*.d", "S*{}".format(self._service_name)))) > 0

class UbuntuInitService(LinuxInitService):
    def set_auto_start(self):
        cmd = "update-rc.d -f {} defaults".format(self._service_name).split()
        _ = execute_command(cmd)

class RedHatInitService(LinuxInitService):
    def set_auto_start(self):
        cmd = "chkconfig {} on".format(self._service_name).split()
        _ = execute_command(cmd)
