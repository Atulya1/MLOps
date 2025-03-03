"""
test_preprocessing.py

Unit tests for functions in data_preprocessing.py
"""

import pytest
import json
from data_preprocessing import (
    removeHashTags, remove_links, remove_special_characters
)

def test_removeHashTags():
    text = "Hello #World this is a #test"
    hashtags_json = json.dumps([
        {"text": "World", "indices": [6, 12]},
        {"text": "test", "indices": [22, 27]}
    ])
    new_text, tags = removeHashTags(text, hashtags_json)
    assert "World" in tags
    assert "test" in tags
    # "#World" and "#test" removed from text
    assert "World" not in new_text
    assert "test" not in new_text

def test_remove_links():
    text = "This is a link: http://example.com"
    new_text = remove_links(text)
    assert "http://example.com" not in new_text

def test_remove_special_characters():
    text = "Hello!!! #test??"
    new_text = remove_special_characters(text)
    # "!" and "?" removed, "#" removed
    assert "!" not in new_text
    assert "?" not in new_text
    assert "#" not in new_text
