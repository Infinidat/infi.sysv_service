__import__("pkg_resources").declare_namespace(__name__)

import logging
import os
logger = logging.getLogger()

class NoPidFile(Exception):
    pass

import logging # pylint: disable=W0403
logger = logging.getLogger(__name__)

def find_executable(executable_name):
    locations = [location for location in os.environ.get("PATH", "").split(':') + ['/sbin', '/usr/sbin'] if location != '']
    return [executable_path for executable_path in [os.path.join(dirname, executable_name) for dirname in locations] if os.path.exists(executable_path)][0]

def execute_command(cmd, check_returncode=True): # pragma: no cover
    from infi.execute import execute
    logger.info("executing {}".format(cmd))
    process = execute(cmd)
    process.wait()
    logger.info("execution returned {}".format(process.get_returncode()))
    logger.debug("stdout: {}".format(process.get_stdout()))
    logger.debug("stderr: {}".format(process.get_stderr()))
    if check_returncode and process.get_returncode() != 0:
        raise RuntimeError("execution of {} failed. see log file for more details".format(cmd))
    return process

class InitService(object): # pylint: disable=R0922
    def __init__(self, service_name, process_name):
        self._service_name = service_name
        self._process_name = process_name

    def is_running(self):
        try:
            pid = self._get_pid_from_run_file()
            logger.debug("Found PID: {!r}".format(pid))
            return self._is_process_alive(pid)
        except NoPidFile:
            logger.debug("No PID file")
            return self._find_process_with_psutil()

    def start(self): # pragma: no cover
        raise NotImplementedError()

    def stop(self): # pragma: no cover
        raise NotImplementedError()

    def is_auto_start(self): # pragma: no cover
        raise NotImplementedError()

    def set_auto_start(self): # pragma: no cover
        raise NotImplementedError()

    def _find_process_with_psutil(self):
        import psutil
        for process in psutil.process_iter():
            if process.name() == self._process_name:
                return True
        return False

    def _get_run_file_path(self):
        from os.path import exists, join, sep
        pid_filepath = join(sep , "var", "run", "{}.pid".format(self._process_name))
        pid_filewithfolderpath = join(sep , "var", "run", self._process_name, "{}.pid".format(self._process_name))
        if exists(pid_filepath):
            return pid_filepath
        elif exists(pid_filewithfolderpath):
            return pid_filewithfolderpath
        else:
            raise NoPidFile("pid file {} does not exist, service is not running?".format(pid_filepath))

    def _get_pid_from_run_file(self):
        pid_filepath = self._get_run_file_path()
        with open(pid_filepath, 'r') as fd:
            pid = int(fd.read().strip("\n"))
            return pid

    def _is_process_alive(self, pid):
        alive = os.path.exists("/proc/{}".format(pid))
        logger.debug("PID {} is {} running".format(pid, '' if alive else 'not'))
        return alive

    def __repr__(self):
        try:
            return "<{}(service_name={!r}, process_name={!r})>".format(self.__class__.__name__, self._service_name, self._process_name)
        except:
            return super(InitService, self).__repr__()

class LinuxInitService(InitService):
    def _run_service_subcommand(self, sub_command, check_returncode=True):
        cmd = "service {} {}".format(self._service_name, sub_command).split()
        _ = execute_command(cmd, check_returncode)

    def start(self):
        # We can't rely on the return codes of Init Scripts:
        self._run_service_subcommand("start", check_returncode=False)
        # The pid file is not created immediately
        from time import sleep
        sleep(3)
        return self.is_running()

    def force_start(self):
        self._run_service_subcommand("force-start", check_returncode=False)
        # The pid file is not created immediately
        from time import sleep
        sleep(3)

    def stop(self):
        self._run_service_subcommand("stop")

    def is_auto_start(self):
        from glob import glob
        from os.path import join, sep
        if len(glob(join(sep, "etc", "rc*.d", "S*{}".format(self._service_name)))) > 0:
            return True
        elif len(glob(join(sep, "etc", "systemd", "system", "*.target.wants", "{}.service".format(self._service_name)))) > 0:
            return True
        elif len(glob(join(sep, "etc", "rc.d", "rc*.d", "S*{}".format(self._service_name)))) > 0:
            return True
        elif len(glob(join(sep, "etc", "rc.d", "boot.d", "S*{}".format(self._service_name)))) > 0:
            return True
        else:
            return False

class UbuntuInitService(LinuxInitService):
    def set_auto_start(self):
        cmd = [find_executable("update-rc.d"), "-f", self._service_name, "defaults"]
        _ = execute_command(cmd)

class RedHatInitService(LinuxInitService):
    def set_auto_start(self):
        cmd = [find_executable("chkconfig"), self._service_name, "on"]
        _ = execute_command(cmd)

class SuseInitService(LinuxInitService):
    def set_auto_start(self):
        cmd = [find_executable("chkconfig"), self._service_name, "on"]
        _ = execute_command(cmd)

class LinuxSystemdService(object):
    def __init__(self, service_name, process_name=None):
        self._service_name = service_name

    def is_running(self):
        return execute_command(["systemctl", "status", self._service_name], False).get_returncode() == 0

    def start(self):
        execute_command(["systemctl", "start", self._service_name])

    def force_start(self):
        self.start()

    def stop(self):
        execute_command(["systemctl", "stop", self._service_name])

    def is_auto_start(self):
        return execute_command(["systemctl", "is-enabled", self._service_name], False).get_returncode() == 0

    def set_auto_start(self):
        execute_command(["systemctl", "enable", self._service_name])
