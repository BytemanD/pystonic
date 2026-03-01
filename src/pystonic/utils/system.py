import platform


def is_windows():
    return platform.system() == 'Window'

def is_linux():
    return platform.system() == 'Linux'
