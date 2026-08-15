import setproctitle


def set_app_name(name: str):
    setproctitle.setproctitle(name)


def app_name():
    return setproctitle.getproctitle() or "pystonic"
