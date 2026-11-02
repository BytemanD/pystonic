import setproctitle

# 稳定的应用名：不随进程标题（完整 argv）变化。
# 不能用 setproctitle.getproctitle() 兜底——未显式 setName 前，标题就是完整命令行，
# 会导致 user_app_data() 拼出 ~/.{整个argv} 的垃圾路径
_APP_NAME = "pystonic"


def set_app_name(name: str):
    global _APP_NAME
    _APP_NAME = name
    setproctitle.setproctitle(name)


def app_name():
    return _APP_NAME or "pystonic"
