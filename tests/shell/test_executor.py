from pystonic.shell.executor import execute, execute_code


def test_execute():
    assert execute("echo", "hello, world") == "hello, world"


def test_execute_code():
    assert execute_code("echo 'hello, world';\necho foo") == "hello, world\nfoo"
