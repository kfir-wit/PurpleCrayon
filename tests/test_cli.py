import sys

import main as cli_main
from purplecrayon import OperationResult


def test_main_errors_when_prompt_missing(monkeypatch, tmp_path, capsys):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["main.py"])

    cli_main.main()

    captured = capsys.readouterr()
    assert "input/prompt.md not found" in captured.out


def test_main_scrape_invokes_runner(monkeypatch, tmp_path, capsys):
    monkeypatch.chdir(tmp_path)

    class DummyCrayon:
        def __init__(self, assets_dir: str):
            self.assets_dir = assets_dir
            self.sort_calls = 0

        def sort_catalog(self):  # pragma: no cover - not used but keeps CLI happy if called
            self.sort_calls += 1
            return {"success": True, "rename_stats": {"renamed": 0, "skipped": 0, "errors": 0}, "catalog_stats": {"added": 0, "updated": 0, "removed": 0}, "final_stats": {}}

        def scrape(self, url: str) -> OperationResult:
            return OperationResult(success=True, message=f"Scraped {url}", images=[])

    monkeypatch.setattr(cli_main, "PurpleCrayon", DummyCrayon)
    test_url = "https://example.com/gallery"
    monkeypatch.setattr(sys, "argv", ["main.py", "--mode", "scrape", "--url", test_url])

    cli_main.main()

    captured = capsys.readouterr()
    assert "Scrape Results" in captured.out
    assert test_url in captured.out
