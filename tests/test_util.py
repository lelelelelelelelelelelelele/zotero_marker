from zotero_marker import util


class TestExtractArxivId:
    def test_archiveid_tagged(self):
        assert util.extract_arxiv_id({"archiveID": "arXiv:2106.09685"}) == "2106.09685"

    def test_archiveid_bare(self):
        assert util.extract_arxiv_id({"archiveID": "2106.09685"}) == "2106.09685"

    def test_archiveid_versioned(self):
        assert util.extract_arxiv_id({"archiveID": "arXiv:2106.09685v3"}) == "2106.09685"

    def test_doi_arxiv(self):
        assert util.extract_arxiv_id({"DOI": "10.48550/arXiv.2302.03693"}) == "2302.03693"

    def test_url(self):
        assert util.extract_arxiv_id({"url": "http://arxiv.org/abs/2302.03693"}) == "2302.03693"

    def test_extra(self):
        assert util.extract_arxiv_id({"extra": "arXiv:2106.09685 [cs.LG]"}) == "2106.09685"

    def test_none_when_no_arxiv(self):
        assert util.extract_arxiv_id({"DOI": "10.1109/CVPR.2021.00123", "url": "https://x"}) is None

    def test_empty(self):
        assert util.extract_arxiv_id({}) is None


class TestTitleMatching:
    def test_jaccard_identical_after_norm(self):
        assert util.title_jaccard("Attention Is All You Need", "attention is all you need!") == 1.0

    def test_jaccard_empty(self):
        assert util.title_jaccard("", "x") == 0.0
        assert util.title_jaccard(None, "x") == 0.0

    def test_jaccard_partial(self):
        v = util.title_jaccard("deep residual learning",
                               "deep residual learning for image recognition")
        assert 0.0 < v < 1.0

    def test_match_threshold(self):
        assert util.title_match("Generative Adversarial Nets", "Generative Adversarial Nets")
        assert not util.title_match("apples", "oranges entirely different fruit")

    def test_norm_title_strips_punct_and_space(self):
        assert util.norm_title("  Hello,  World! ") == "hello world"


class TestFirstAuthor:
    def test_first_author_skips_non_author(self):
        data = {"creators": [
            {"creatorType": "editor", "lastName": "Ed"},
            {"creatorType": "author", "lastName": "Goodfellow"},
        ]}
        assert util.first_author_lastname(data) == "Goodfellow"

    def test_no_author(self):
        assert util.first_author_lastname({"creators": []}) == ""
        assert util.first_author_lastname({}) == ""
