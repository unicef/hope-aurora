from aurora.config import parse_bookmarks, parse_emails


def test_parse_emails():
    assert parse_emails("user@example.com,user1@example.com,") == [
        ("user", "user@example.com"),
        ("user1", "user1@example.com"),
    ]


def test_parse_bookmarks():
    assert parse_bookmarks(r"a\nb\nc") == "abc"
