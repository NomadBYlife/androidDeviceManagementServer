# Configuring syslog as localhost on Windows makes no sense. Don't do it.
syslog_flag = False
console_flag = True

log_host = 'localhost'
log_host_port = 514


# Do not change
syslog_tup = (log_host, log_host_port)
handler_list = []
if syslog_flag:
    handler_list.append('adms.syslog')
if console_flag:
    handler_list.append('adms.console')
if len(handler_list) == 0:
    handler_list.append('adms.console')


def set_log_level():
    import logging
    import os
    log = logging.getLogger('adms.views')

    def log_switch(log_lvl_name):
        switch = {
            'NOTSET': logging.NOTSET,  # _0
            'DEBUG': logging.DEBUG,  # 10
            'INFO': logging.INFO,  # 20
            'WARNING': logging.WARNING,  # 30
            'ERROR': logging.ERROR,  # 40
            'CRITICAL': logging.CRITICAL,  # 50
            'FATAL': logging.FATAL,  # 50
        }
        # return switch.get(log_lvl_name, logging.DEBUG)
        return switch.get(log_lvl_name, logging.CRITICAL)

    selected_log_level = log_switch(os.environ.get('ADMS_TEST_LOG_LEVEL'))
    log.setLevel(selected_log_level)

    return log
