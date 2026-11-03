from pystonic.shell.backends import Bash, Cmd, Powershell


class TestBash:
    def test_get_run_command(self):
        backend = Bash()
        assert backend.get_run_command("echo", "hello, world") == [
            "echo",
            "hello, world",
        ]

    def test_get_file_command(self):
        backend = Bash()
        assert backend.get_file_command("/script/file") == ["bash", "/script/file"]


class TestPowershell:
    def test_get_run_command(self):
        backend = Powershell()
        assert backend.get_run_command("echo", "hello, world") == [
            "powershell",
            "-Command",
            "echo 'hello, world'",
        ]

    def test_get_file_command(self):
        backend = Powershell()
        assert backend.get_file_command("/script/file") == [
            "powershell",
            "-File",
            "/script/file",
        ]


class TestCmd:
    def test_get_run_command(self):
        backend = Cmd()
        assert backend.get_run_command("echo", "hello, world") == [
            "cmd.exe",
            "/c",
            "echo 'hello, world'",
        ]

    def test_get_file_command(self):
        backend = Cmd()
        assert backend.get_file_command("/script/file") == [
            "cmd.exe",
            "/c",
            "/script/file",
        ]
