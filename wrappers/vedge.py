import logging
import re
import time
from io import StringIO
from pprint import pprint

import textfsm
from netmiko import BaseConnection
from netmiko.py23_compat import text_type

logger = logging.getLogger("vedge drivers")


class VEdgeSSH(BaseConnection):
    def session_preparation(self):
        """Prepare the session after the connection has been established."""
        self._test_channel_read(pattern=r'[#]')
        self.set_base_prompt()
        self.disable_paging("paginate false")
        self.set_terminal_width(command='screen-width 256')
        # Clear the read buffer
        time.sleep(.3 * self.global_delay_factor)
        self.clear_buffer()

    def check_config_mode(self, check_string=')#', pattern=''):
        """
        Checks if the device is in configuration mode or not.
        Cisco IOS devices abbreviate the prompt at 20 chars in config mode
        """
        return super().check_config_mode(check_string=check_string,
                                         pattern=pattern)

    def config_mode(self, config_command='config exclusive', pattern=''):
        """
        Enter into configuration mode on remote device.
        Cisco IOS devices abbreviate the prompt at 20 chars in config mode
        """
        if not pattern:
            pattern = re.escape(self.base_prompt[:16])
        return super().config_mode(config_command=config_command,
                                   pattern=pattern)

    def exit_config_mode(self, exit_config='end', pattern='#'):
        """Exit from configuration mode."""
        output = ""
        if self.check_config_mode():
            output = self.send_command_timing(exit_config, strip_prompt=False, strip_command=False)
            if 'Uncommitted changes found, commit them? [yes/no/CANCEL]' in output:
                output += self.send_command_timing('yes', strip_prompt=False, strip_command=False)
            if pattern not in output or self.check_config_mode():
                logger.error("Failed to exit configuration mode")
                logger.debug("Output from failure: {}".format(output))
                raise ValueError("Failed to exit configuration mode")
        logger.debug("exit_config_mode: {}".format(output))
        return output

    def cleanup(self):
        """Gracefully exit the SSH session."""
        try:
            self.exit_config_mode()
        except Exception:
            # Always try to send 'exit' regardless of whether exit_config_mode works or not.
            pass
        self._session_log_fin = True
        self.write_channel("exit" + self.RETURN)

    def check_enable_mode(self, *args, **kwargs):
        """No enable mode on vedge."""
        pass

    def enable(self, *args, **kwargs):
        """No enable mode on vedge."""
        pass

    def exit_enable_mode(self, *args, **kwargs):
        """No enable mode on vedge."""
        pass

    def commit(self, confirm=False, confirm_delay=None, check=False, comment='',
               and_quit=False, delay_factor=1):
        """
        Commit the candidate configuration.
        Commit the entered configuration. Raise an error and return the failure
        if the commit fails.
        Automatically enters configuration mode
        default:
            command_string = commit
        check and (confirm or confirm_dely or comment):
            Exception
        confirm_delay and no confirm:
            Exception
        confirm:
            confirm_delay option
            comment option
            command_string = commit confirmed or commit confirmed <confirm_delay>
        check:
            command_string = commit check
        """
        delay_factor = self.select_delay_factor(delay_factor)

        if check and (confirm or confirm_delay or comment):
            raise ValueError("Invalid arguments supplied with commit check")

        if confirm_delay and not confirm:
            raise ValueError("Invalid arguments supplied to commit method both confirm and check")

        # Select proper command string based on arguments provided
        command_string = 'commit'
        commit_marker = 'Commit complete.'
        if check:
            command_string = 'commit check'
            commit_marker = 'Validation complete'
        elif confirm:
            if confirm_delay:
                command_string = 'commit confirmed ' + text_type(confirm_delay)
            else:
                command_string = 'commit confirmed'
            commit_marker = 'Warning: The configuration will be reverted if you exit the CLI without'

        # wrap the comment in quotes
        if comment:
            if '"' in comment:
                raise ValueError("Invalid comment contains double quote")
            comment = '"{0}"'.format(comment)
            command_string += ' comment ' + comment

        if and_quit:
            command_string += ' and-quit'

        # Enter config mode (if necessary)
        output = self.config_mode()
        # and_quit will get out of config mode on commit
        if and_quit:
            prompt = self.base_prompt
            output += self.send_command_expect(command_string, expect_string=prompt,
                                               strip_prompt=False,
                                               strip_command=False, delay_factor=delay_factor)
        else:
            output += self.send_command_expect(command_string, strip_prompt=False,
                                               strip_command=False, delay_factor=delay_factor)

        if commit_marker not in output:
            raise ValueError("Commit failed with the following errors:\n\n{0}"
                             .format(output))

        return output

    def save_config(self, *args, **kwargs):
        """Not Implemented"""
        pass

if __name__ == '__main__':
    LOGFILE = "netmkio_vedge_test" + time.strftime("_%y%m%d%H%M%S", time.gmtime()) + ".log"
    SCREENLOGLEVEL = logging.DEBUG
    FILELOGLEVEL = logging.DEBUG
    logformat = logging.Formatter(
        '%(asctime)s: %(process)d - %(threadName)s - %(funcName)s - %(name)s - %(levelname)s - message: %(message)s')
    logging.basicConfig(format='%(asctime)s: %(threadName)s - %(funcName)s - %(name)s - %(levelname)s - %(message)s',
                        level=logging.DEBUG)
    logger = logging.getLogger('netmiko_vedge')

    DEVICE = '172.16.1.105'
    USERNAME = 'admin'
    PASSWORD = 'admin'

    net_connect = VEdgeSSH(DEVICE, username=USERNAME,
                          password=PASSWORD, verbose=True)

    print(net_connect.find_prompt())
    output = net_connect.send_command("show interface | tab")
    print(output)
    template = """Value VPN (\d+)
Value Interface (\S+)
Value Type (\S+)
Value IPAddress (\S+)
Value Admin_Status (\w+)
Value Oper_Status (\w+)
Value Port_Type (\w+)
Value MTU (\d+)
Value MAC (\S+)
Value Speed (\d+)
Value Duplex (\w+)
Value MSS_Adjust (\d+)
Value Uptime (\S+)
Value RX_Packets (\d+)
Value TX_Packets (\d+)

Start
  ^\s*-+
  ^\s*${VPN}\s+${Interface}\s+${Type}\s+${IPAddress}\s+${Admin_Status}\s+${Oper_Status}\s+\S+\s+\S+\s+${Port_Type}\s+${MTU}\s+${MAC}\s+${Speed}\s+${Duplex}\s+${MSS_Adjust}\s+${Uptime}\s+${RX_Packets}\s+${TX_Packets} -> Record  
"""
    template = StringIO(template)
    fsm = textfsm.TextFSM(template)

    # Read stdin until EOF, then pass this to the FSM for parsing.
    fsm_results = fsm.ParseText(output)
    pprint(fsm_results)
    keys = [s for s in fsm.header]
    interfaces = {'result': {}}
    for row_num, row in enumerate(fsm_results):
        temp_dict = {}
        for index, value in enumerate(row):
            temp_dict[keys[index]] = value
        interfaces['result']['row{}'.format(row_num + 1)] = temp_dict
    pprint(interfaces)
    net_connect.disconnect()