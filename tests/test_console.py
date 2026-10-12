"""Console-script installed entry point must use a success exit status."""
from phylocloud import cli


def test_console_success_exit_code(monkeypatch):
    messages = []
    monkeypatch.setattr(cli, 'main', lambda: messages.append('called') or {'tips': 69})
    assert cli.console_main() == 0
    assert messages == ['called']
