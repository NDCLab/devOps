import pytest
from hmutils import get_unique_sub_ses


# Mock Identifier class for testing
class MockIdentifier:
    def __init__(self, subject, session):
        self.subject = subject
        self.session = session

    def __str__(self):
        return f"{self.subject}_{self.session}"

    @classmethod
    def from_str(cls, identifier_str):
        parts = identifier_str.split("_")
        if len(parts) != 2:
            raise ValueError(f"Invalid identifier format: {identifier_str}")
        return cls(subject=parts[0], session=parts[1])


@pytest.fixture
def mock_identifier():
    # Mock the Identifier class for testing
    return MockIdentifier


@pytest.mark.parametrize(
    "identifiers, expected",
    [
        # Case: Valid strings parsed into unique subject-session pairs
        (["sub1_ses1", "sub2_ses1", "sub1_ses1"], [("sub1", "ses1"), ("sub2", "ses1")]),
        # Case: Unique subject-session pairs from Identifier objects
        (
            [
                MockIdentifier("sub1", "ses1"),
                MockIdentifier("sub2", "ses1"),
                MockIdentifier("sub1", "ses1"),
            ],
            [("sub1", "ses1"), ("sub2", "ses1")],
        ),
        # Case: Mixed subjects and sessions
        (
            ["sub1_ses1", "sub1_ses2", "sub2_ses1"],
            [("sub1", "ses1"), ("sub1", "ses2"), ("sub2", "ses1")],
        ),
        # Case: Identifiers already unique, no duplicates
        (
            ["sub1_ses1", "sub3_ses3"],
            [("sub1", "ses1"), ("sub3", "ses3")],
        ),
    ],
)
def test_get_unique_sub_ses(identifiers, expected, mock_identifier, monkeypatch):
    monkeypatch.setattr("hmutils.Identifier", mock_identifier)

    result = get_unique_sub_ses(identifiers)
    assert sorted(result) == sorted(expected)


def test_get_unique_sub_ses_invalid_format(monkeypatch, mock_identifier):
    # Patch Identifier to use the mock
    monkeypatch.setattr("hmutils.Identifier", mock_identifier)

    # Identifiers with invalid formats (too many or too few parts)
    with pytest.raises(ValueError, match="Invalid identifier format"):
        get_unique_sub_ses(["sub1ses1"])  # Missing delimiter

    with pytest.raises(ValueError, match="Invalid identifier format"):
        get_unique_sub_ses(["sub1_ses1_extra"])  # Too many parts


def test_get_unique_sub_ses_mixed_types(monkeypatch, mock_identifier):
    monkeypatch.setattr("hmutils.Identifier", mock_identifier)

    # Mixed list of strings and Identifier objects
    identifiers = [
        "sub1_ses1",
        mock_identifier("sub2", "ses2"),
        mock_identifier("sub1", "ses1"),
    ]
    result = get_unique_sub_ses(identifiers)
    assert sorted(result) == [("sub1", "ses1"), ("sub2", "ses2")]


def test_get_unique_sub_ses_already_unique(monkeypatch, mock_identifier):
    monkeypatch.setattr("hmutils.Identifier", mock_identifier)

    identifiers = ["sub1_ses1", "sub2_ses2", "sub3_ses3"]
    result = get_unique_sub_ses(identifiers)
    assert sorted(result) == [("sub1", "ses1"), ("sub2", "ses2"), ("sub3", "ses3")]


def test_get_unique_sub_ses_empty_list():
    # Case: Empty list should return an empty list
    result = get_unique_sub_ses([])
    assert result == []
