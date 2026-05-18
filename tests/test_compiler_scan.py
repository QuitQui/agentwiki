"""Tests for --scan multi-source report discovery in compiler.py."""
from pathlib import Path

import pytest

from compiler.compiler import _collect_report_dirs, _extra_reports_dirs, compile_inputs


def _make_report_dir(parent: Path, name: str) -> Path:
    d = parent / name
    d.mkdir(parents=True)
    (d / "report.html").write_text(
        f'<article data-node-id="report:{name}" data-node-type="agent_report">'
        f'<h1>{name}</h1></article>'
    )
    (d / "manifest.json").write_text(
        f'{{"id": "report:{name}", "type": "agent_report", "title": "{name}", '
        f'"created_at": "2026-01-01T00:00:00Z", "agent": {{"name": "claude-code", '
        f'"model": "claude-sonnet-4-6", "run_id": "{name}"}}}}'
    )
    (d / "chunks.jsonl").write_text("")
    return d


class TestCollectReportDirs:
    def test_returns_empty_for_missing_dir(self, tmp_path: Path) -> None:
        assert _collect_report_dirs(tmp_path / "nonexistent") == []

    def test_returns_dirs_with_report_html(self, tmp_path: Path) -> None:
        reports = tmp_path / "reports"
        _make_report_dir(reports, "alpha")
        _make_report_dir(reports, "beta")
        result = _collect_report_dirs(reports)
        assert len(result) == 2
        assert all((d / "report.html").exists() for d in result)

    def test_excludes_dirs_without_report_html(self, tmp_path: Path) -> None:
        reports = tmp_path / "reports"
        _make_report_dir(reports, "with-html")
        no_html = reports / "no-html"
        no_html.mkdir()
        result = _collect_report_dirs(reports)
        assert len(result) == 1
        assert result[0].name == "with-html"


class TestExtraReportsDirs:
    def test_finds_reports_directly_under_scan_dir(self, tmp_path: Path) -> None:
        project = tmp_path / "myproject"
        reports = project / "reports"
        reports.mkdir(parents=True)
        result = _extra_reports_dirs([project])
        assert any(r == reports for r in result)

    def test_finds_reports_in_depth1_children(self, tmp_path: Path) -> None:
        workspace = tmp_path / "workspace"
        child_reports = workspace / "subproject" / "reports"
        child_reports.mkdir(parents=True)
        result = _extra_reports_dirs([workspace])
        assert any(r == child_reports for r in result)

    def test_deduplicates_same_resolved_path(self, tmp_path: Path) -> None:
        project = tmp_path / "myproject"
        reports = project / "reports"
        reports.mkdir(parents=True)
        result = _extra_reports_dirs([project, project])
        paths = [r.resolve() for r in result]
        assert len(paths) == len(set(paths))

    def test_returns_empty_when_no_reports_dirs_exist(self, tmp_path: Path) -> None:
        empty = tmp_path / "empty"
        empty.mkdir()
        assert _extra_reports_dirs([empty]) == []


class TestCompileInputsScan:
    def test_picks_up_reports_from_scan_dir(self, tmp_path: Path) -> None:
        # Primary input_dir (no reports)
        input_dir = tmp_path / "samples"
        (input_dir / "reports").mkdir(parents=True)

        # External project with a report
        ext_project = tmp_path / "ext-project"
        _make_report_dir(ext_project / "reports", "external-report")

        nodes = compile_inputs(input_dir, scan_dirs=[ext_project])
        ids = [n["id"] for n in nodes]
        assert "report:external-report" in ids

    def test_primary_and_scan_reports_both_included(self, tmp_path: Path) -> None:
        input_dir = tmp_path / "samples"
        _make_report_dir(input_dir / "reports", "primary-report")

        ext_project = tmp_path / "ext-project"
        _make_report_dir(ext_project / "reports", "ext-report")

        nodes = compile_inputs(input_dir, scan_dirs=[ext_project])
        ids = [n["id"] for n in nodes]
        assert "report:primary-report" in ids
        assert "report:ext-report" in ids

    def test_no_duplicates_when_scan_overlaps_input_dir(self, tmp_path: Path) -> None:
        input_dir = tmp_path / "samples"
        _make_report_dir(input_dir / "reports", "my-report")

        # scan the parent — depth-1 walk would find samples/reports again
        nodes = compile_inputs(input_dir, scan_dirs=[tmp_path])
        ids = [n["id"] for n in nodes]
        assert ids.count("report:my-report") == 1

    def test_scan_dirs_none_behaves_like_empty(self, tmp_path: Path) -> None:
        input_dir = tmp_path / "samples"
        _make_report_dir(input_dir / "reports", "only-report")
        nodes_with_none = compile_inputs(input_dir, scan_dirs=None)
        nodes_with_empty = compile_inputs(input_dir, scan_dirs=[])
        assert [n["id"] for n in nodes_with_none] == [n["id"] for n in nodes_with_empty]
