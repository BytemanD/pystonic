from pystonic.core.pkg import is_package_installed


def test_is_package_installed_with_existing_package():
    """测试已安装的包"""
    # pytest 应该已安装
    assert is_package_installed("pytest") is True

    # pytest_mock 应该已安装
    assert is_package_installed("pytest_mock") is True


def test_is_package_installed_with_stdlib():
    """测试标准库模块"""
    # 标准库模块应该返回 True
    assert is_package_installed("os") is True
    assert is_package_installed("sys") is True
    assert is_package_installed("json") is True


def test_is_package_installed_with_nonexistent_package():
    """测试不存在的包"""
    # 不存在的包应该返回 False
    assert is_package_installed("nonexistent_package_xyz_123") is False
    assert is_package_installed("this_package_definitely_does_not_exist") is False


def test_is_package_installed_with_partial_name():
    """测试部分包名"""
    # httpx 的依赖
    assert is_package_installed("httpx") is True
    assert is_package_installed("certifi") is True


def test_is_package_installed_returns_bool():
    """测试返回值类型为布尔值"""
    result = is_package_installed("pytest")
    assert isinstance(result, bool)

    result = is_package_installed("nonexistent_package")
    assert isinstance(result, bool)
