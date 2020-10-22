import api


def connect(ip):
    api.enter_input("{/}connect " + api.escape(ip))
