import importlib.util


def is_package_installed(package_name):
    """检查指定的包是否已安装

    Args:
        package_name (str): 要检查的包名

    Returns:
        bool: 如果包已安装返回 True，否则返回 False
    """
    return importlib.util.find_spec(package_name) is not None
