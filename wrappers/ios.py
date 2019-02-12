import logging
import socket
import sys
import traceback

import paramiko
from napalm.base.exceptions import ConnectionException
from napalm.ios import IOSDriver
from netmiko import NetMikoTimeoutException, NetMikoAuthenticationException

logger = logging.getLogger(__name__)

class IosNapalmWrapper(IOSDriver):
    def open(self):
        """Open a connection to the device."""
        device_type = 'cisco_ios'
        if self.transport == 'telnet':
            device_type = 'cisco_ios_telnet'
        try:
            logger.debug("device is type {}: Attempting connection with transport {}".format(device_type, self.transport))
            self.device = self._netmiko_open(
                device_type,
                netmiko_optional_args=self.netmiko_optional_args,
            )
        except ConnectionException as err:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            stacktrace = traceback.extract_tb(exc_traceback)
            logger.critical("IOSNapalmWrapper: open: SSH Connection for {} timed out".format(self.hostname))
            logger.critical("{}".format(err))
            logger.debug(sys.exc_info())
            logger.debug(stacktrace)
            self.close()
            raise NetMikoTimeoutException("Connection to {} timed out".format(self.hostname))
        except NetMikoAuthenticationException as err:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            stacktrace = traceback.extract_tb(exc_traceback)
            logger.critical("NetMiko Authentication Failure Accessing " + self.hostname)
            logger.critical("{}".format(err))
            logger.debug(sys.exc_info())
            logger.debug(stacktrace)
            self.close()
            raise
        except socket.gaierror as err:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            stacktrace = traceback.extract_tb(exc_traceback)
            logger.critical("Connection Failure for " + self.hostname + ":  DNS Lookup Failure")
            logger.critical("{}".format(err))
            logger.debug(sys.exc_info())
            logger.debug(stacktrace)
            self.close()
            raise
        except socket.error as err:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            stacktrace = traceback.extract_tb(exc_traceback)
            logger.critical("Connection Failure for" + self.hostname + ":  Socket Error")
            logger.critical("{}".format(err))
            logger.debug(sys.exc_info())
            logger.debug(stacktrace)
            self.close()
            raise
        except paramiko.AuthenticationException as err:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            stacktrace = traceback.extract_tb(exc_traceback)
            logger.critical("Authentication Failure Accessing " + self.hostname)
            logger.critical("{}".format(err))
            logger.debug(sys.exc_info())
            logger.debug(stacktrace)
            self.close()
            raise
        except:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            stacktrace = traceback.extract_tb(exc_traceback)
            logger.critical("Connection Failure for " + self.hostname)
            logger.debug(sys.exc_info())
            logger.debug(stacktrace)
            self.close()
            raise

    def send_config_set(self, config_commands=None, exit_config_mode=True, delay_factor=1,
                        max_loops=150, strip_prompt=False, strip_command=False,
                        config_mode_command=None):
        """
        Exposes netmiko method...

        Send configuration commands down the SSH channel.
        config_commands is an iterable containing all of the configuration commands.
        The commands will be executed one after the other.
        Automatically exits/enters configuration mode.
        :param config_commands: Multiple configuration commands to be sent to the device
        :type config_commands: list or string
        :param exit_config_mode: Determines whether or not to exit config mode after complete
        :type exit_config_mode: bool
        :param delay_factor: Factor to adjust delays
        :type delay_factor: int
        :param max_loops: Controls wait time in conjunction with delay_factor (default: 150)
        :type max_loops: int
        :param strip_prompt: Determines whether or not to strip the prompt
        :type strip_prompt: bool
        :param strip_command: Determines whether or not to strip the command
        :type strip_command: bool
        :param config_mode_command: The command to enter into config mode
        :type config_mode_command: str
        """
        try:
            output = self.device.send_config_set(config_commands=config_commands, exit_config_mode=exit_config_mode, delay_factor=delay_factor,
                        max_loops=max_loops, strip_prompt=strip_prompt, strip_command=strip_command,
                        config_mode_command=config_mode_command)
        except:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            stacktrace = traceback.extract_tb(exc_traceback)
            logger.critical("send_config_set: Configuration Command Set Failure for " + self.hostname)
            logger.debug("send_config_set: Configuration Command Set: {}".format(config_commands))
            logger.debug(sys.exc_info())
            logger.debug(stacktrace)
            raise

        return output

    def send_command(self, command_string, expect_string=None, delay_factor=1, max_loops=500, auto_find_prompt=True,
                     strip_prompt=True, strip_command=True, normalize=True, use_textfsm=False):
        """
        Exposes netmiko api

        Execute command_string on the SSH channel using a pattern-based mechanism. Generally used for show commands.
        By default this method will keep waiting to receive data until the network device prompt is detected. The
        current network device prompt will be determined automatically.

        Parameters:

        command_string (str) – The command to be executed on the remote device.
        expect_string (str) – Regular expression pattern to use for determining end of output. If left blank will default to being based on router prompt.
        delay_factor (int) – Multiplying factor used to adjust delays (default: 1).
        max_loops (int) – Controls wait time in conjunction with delay_factor. Will default to be based upon self.timeout.
        strip_prompt (bool) – Remove the trailing router prompt from the output (default: True).
        strip_command (bool) – Remove the echo of the command from the output (default: True).
        normalize (bool) – Ensure the proper enter is sent at end of command (default: True).
        use_textfsm – Process command output through TextFSM template (default: False).

        """

        try:
            output = self.device.send_command(command_string, expect_string=expect_string, delay_factor=delay_factor,
                                              max_loops=max_loops, auto_find_prompt=auto_find_prompt,
                                              strip_prompt=strip_prompt, strip_command=strip_command,
                                              normalize=normalize, use_textfsm=use_textfsm)
        except:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            stacktrace = traceback.extract_tb(exc_traceback)
            logger.critical("send_command: Configuration Command Set Failure for " + self.hostname)
            logger.debug("send_command: Configuration Command Set: {}".format(command_string))
            logger.debug(sys.exc_info())
            logger.debug(stacktrace)
            raise

        return output




