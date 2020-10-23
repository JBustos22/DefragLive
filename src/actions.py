import api


def connect(ip):
    api.exec_command("/connect " + ip)
