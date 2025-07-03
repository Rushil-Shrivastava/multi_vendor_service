import pytest
from backend.utils.cleaner import clean_data

def test_clean_data_trims_and_redacts():
    raw = {
        " name ": "  Alice  ",
        "email": "alice@example.com ",
        "nested": {
            "phone": " 12345 ",
            "note": " hi "
        }
    }
    expect = {
        " name ": "Alice",
        "email": None,
        "nested": {
            "phone": None,
            "note": "hi"
        }
    }
    assert clean_data(raw) == expect
