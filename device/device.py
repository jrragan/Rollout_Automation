import functools
import logging
import sys
import traceback

logger = logging.getLogger(__name__)


def check_connection(func):
    @functools.wraps(func)
    def decorator(self, *args, **kwargs):
        self.logger.debug("instance %s of class %s is now decorated whee!" % (self, self.__class__))
        self.logger.debug("Checking connection to " + self.name)
        try:
            is_alive = self.connector_object.is_alive()
            if not is_alive['is_alive']:
                self.logger.info("SSH Connection to {} is not alive. Attempting to Open Connection.")
                self.connector_object.open()
            value = func(self, *args, **kwargs)
            return value
        except:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            stacktrace = traceback.extract_tb(exc_traceback)
            self.logger.error("Error with SSH Connection to {} ".format(self.name))
            self.logger.debug(sys.exc_info())
            self.logger.debug(stacktrace)
            raise
    return decorator


class Device:
    def __init__(self, hostname, host_type, username, password, timeout=60, optional_args=None):
        """
        :param name
        :param driver: String representing a class for an object with NAPALM like APIs
        """
        self.logger = logging.getLogger("device.Device")
        self.logger.info("Instantiating device object for {}".format(hostname))
        self.name = hostname
        self.username = username
        self.password = password
        self.optional_args = optional_args
        self.timeout = timeout
        self.connector_object = host_type(hostname, username, password, timeout=timeout, optional_args=optional_args)
        self._configuration = {}
        self._running_config = ""
        self._cli_command_list = {}

    @check_connection
    def get_config(self, retrieve='all'):
        """
        Gets the device's running config
        :return: None
        """
        self.logger.debug("Getting configurations for {}".format(self.name))
        try:
            self._configuration = self.connector_object.get_config(retrieve = retrieve)
            if retrieve == 'all' or retrieve == 'running':
                self._running_config = self._configuration['running']
        except:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            stacktrace = traceback.extract_tb(exc_traceback)
            self.logger.critical("Device: get_config: error retrieving configs from: {}".format(self.name))
            self.logger.debug(sys.exc_info())
            self.logger.debug(stacktrace)
            raise

    @property
    def configuration(self):
        return self._configuration

    @property
    def running_config(self):
        return self._running_config

    @check_connection
    def get_cli_command(self, command):
        """

        :param command:
        :return:
        """
        self.logger.debug("get_cli_command: cmd: {}".format(command))
        if command not in self._cli_command_list:
            self.logger.debug("get_cli: cmd not in dictionary")
            output = self.connector_object._send_command(command)
            if 'Invalid input detected' in output:
                self.logger.error("Error running command {}".format(command))
                raise ValueError('Unable to execute command "{}"'.format(command))
            self._cli_command_list[command] = output
        return self._cli_command_list[command]

    @property
    def cli_command_output(self):
        return self._cli_command_list

    @check_connection
    def run_cli_command_list(self, commands):
        """

        :param commands: list of commands
        :return:
        """
        commands = list(commands)
        self.logger.debug("get_cli_command_list: cmd list: {}".format(commands))
        try:
            self._cli_command_list = self.connector_object.cli(commands)
        except:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            stacktrace = traceback.extract_tb(exc_traceback)
            logger.critical("Device: run_cli_command: error retrieving command output from: {}".format(self.name))
            logger.debug(sys.exc_info())
            logger.debug(stacktrace)
            raise

    def close(self):
        self.connector_object.close()

    def __getattr__(self, name):
        if hasattr(self.connector_object, name):
            def method(*args, **kwargs):
                value = getattr(self.connector_object, name)(*args, **kwargs)
                return value
            return method

        raise AttributeError(
            "'{0} object has no attribute '{1}'"
                .format(self.__class__.__name__, name))

    def __enter__(self):
        self.logger.info("opening connection to {}".format(self.name))
        self.connector_object.open()
        self.logger.debug("connection to {} opened".format(self.name))
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.logger.debug("Exiting")
        if exc_type is None:
            try:
                self.connector_object.close()
            except:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                stacktrace = traceback.extract_tb(exc_traceback)
                self.logger.critical("Device: error closing napalm/ssh connection to: {}".format(self.name))
                self.logger.debug(sys.exc_info())
                self.logger.debug(stacktrace)
                raise
            else:
                return True
        else:
            self.logger.critical("device: Error with context manager for device {}: {} - {}".format(self.name, exc_type, exc_value))
            self.logger.debug(exc_traceback)

