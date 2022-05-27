# listen local only 127.0.0.1
# listen own default IP <ip> or 0.0.0.0

# listen local only IPv6 [::1]
# listen IPv6 [<ipv6>] or [::]

# our network does not support ipv6 so don't try that
# you will also get issues with allowed hosts

listen_addr: str = '0.0.0.0'
server_port: int = 11359

notification_min_time: int = 15
notification_max_time: int = 50


# Do NOT change values below here
asd: int = (notification_max_time - notification_min_time) / 2
background_sleep_time: int = 20
if asd > 0:
    # noinspection PyRedeclaration
    background_sleep_time = asd
