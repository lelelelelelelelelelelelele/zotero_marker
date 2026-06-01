from zotero_marker import report


def test_write_reports_creates_all_three(tmp_path, make_resolution):
    r1 = make_resolution(item_key="K1", title="Paper One",
                         target_item_type="conferencePaper", fields={"proceedingsTitle": "ICLR"})
    r2 = make_resolution(item_key="K2", title="Paper Two", acceptance="unknown",
                         canonical=None, core_tier=None, confidence=0.0,
                         citation_count=None, target_item_type=None, fields={})
    csv_p, json_p, html_p = report.write_reports([r1, r2], tmp_path)
    assert csv_p.exists() and json_p.exists() and html_p.exists()
    html = html_p.read_text(encoding="utf-8")
    assert "Paper One" in html
    assert "审核台" in html
    assert "K1" in html


def test_html_escapes_title(tmp_path, make_resolution):
    r = make_resolution(title="Evil <script>alert(1)</script>",
                        target_item_type="conferencePaper", fields={"proceedingsTitle": "X"})
    _, _, html_p = report.write_reports([r], tmp_path)
    html = html_p.read_text(encoding="utf-8")
    assert "<script>alert(1)" not in html        # the injected payload must be escaped
    assert "&lt;script&gt;alert(1)" in html


def test_csv_has_header_and_row(tmp_path, make_resolution):
    csv_p, _, _ = report.write_reports([make_resolution(item_key="ZZZ")], tmp_path)
    text = csv_p.read_text(encoding="utf-8-sig")
    assert "item_key" in text.splitlines()[0]
    assert "ZZZ" in text


def test_report_surfaces_collections(tmp_path, make_resolution):
    r = make_resolution(item_key="K1", collections=["Long-Term Alignment"])
    csv_p, _, html_p = report.write_reports([r], tmp_path)
    csv_text = csv_p.read_text(encoding="utf-8-sig")
    assert "collections" in csv_text.splitlines()[0]      # CSV column added
    assert "Long-Term Alignment" in csv_text
    html = html_p.read_text(encoding="utf-8")
    assert "Long-Term Alignment" in html                  # collection filter + cell
    assert "可写入" in html                                # new will-write chip
