import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def clear_data_file(tmp_path, monkeypatch):
    """Clear data file before each test"""
    # Point DATA_FILE to a temp file for tests
    test_file = tmp_path / "test_data.json"
    monkeypatch.setenv("DATA_FILE", str(test_file))
    
    # Reload modules to pick up new DATA_FILE
    import importlib
    
    # Reload config module first
    if 'app.core.config' in sys.modules:
        import app.core.config
        importlib.reload(app.core.config)
    
    # Reload model module
    if 'app.models.profile' in sys.modules:
        import app.models.profile
        importlib.reload(app.models.profile)
    
    # Reload routes module
    if 'app.api.routes' in sys.modules:
        import app.api.routes
        importlib.reload(app.api.routes)
    
    # Reload main app
    if 'app.main' in sys.modules:
        import app.main
        importlib.reload(app.main)
    
    yield
    
    # Cleanup
    if test_file.exists():
        test_file.unlink()


# Initialize client
from app.main import app
client = TestClient(app)


# Original tests
def test_create_and_get_string():
    """Test creating a string and retrieving it"""
    payload = {"value": "racecar"}
    r = client.post("/strings", json=payload)
    assert r.status_code == 201
    body = r.json()
    assert body["value"] == "racecar"
    assert body["properties"]["is_palindrome"] is True
    
    # Retrieve by query parameter
    r2 = client.get("/strings", params={"is_palindrome": "true"})
    assert r2.status_code == 200


def test_conflict_on_duplicate():
    """Test that duplicate strings return 409 Conflict"""
    payload = {"value": "hello"}
    r = client.post("/strings", json=payload)
    assert r.status_code == 201
    r2 = client.post("/strings", json=payload)
    assert r2.status_code == 409


def test_filter_by_query_params():
    """Test filtering strings by query parameters"""
    client.post("/strings", json={"value": "madam"})
    client.post("/strings", json={"value": "hello world"})
    r = client.get("/strings", params={"is_palindrome": "true"})
    assert r.status_code == 200
    data = r.json()
    assert data["count"] >= 1


# Additional tests for full requirements
def test_string_properties():
    """Test that all required properties are computed correctly"""
    payload = {"value": "hello world"}
    r = client.post("/strings", json=payload)
    assert r.status_code == 201
    body = r.json()
    
    # Check all required properties
    props = body["properties"]
    assert props["length"] == 11
    assert props["is_palindrome"] is False
    assert props["unique_characters"] == 8  # h, e, l, o, space, w, r, d
    assert props["word_count"] == 2
    assert "sha256_hash" in props
    assert "character_frequency_map" in props
    assert props["character_frequency_map"]["l"] == 3
    assert "created_at" in body


def test_get_string_by_value():
    """Test retrieving a specific string by its value"""
    payload = {"value": "test string"}
    r = client.post("/strings", json=payload)
    assert r.status_code == 201
    
    # Get by value
    r2 = client.get("/strings/test string")
    assert r2.status_code == 200
    body = r2.json()
    assert body["value"] == "test string"
    
    # Test 404 for non-existent string
    r3 = client.get("/strings/nonexistent")
    assert r3.status_code == 404


def test_advanced_filtering():
    """Test advanced filtering with multiple parameters"""
    # Create test data
    client.post("/strings", json={"value": "a"})
    client.post("/strings", json={"value": "abc"})
    client.post("/strings", json={"value": "hello world"})
    client.post("/strings", json={"value": "racecar"})
    
    # Filter by min_length
    r = client.get("/strings", params={"min_length": 5})
    assert r.status_code == 200
    data = r.json()
    assert all(len(item["value"]) >= 5 for item in data["data"])
    
    # Filter by word_count
    r = client.get("/strings", params={"word_count": 2})
    assert r.status_code == 200
    data = r.json()
    assert all(item["properties"]["word_count"] == 2 for item in data["data"])
    
    # Filter by contains_character
    r = client.get("/strings", params={"contains_character": "a"})
    assert r.status_code == 200
    data = r.json()
    assert all("a" in item["value"] for item in data["data"])


def test_natural_language_query():
    """Test natural language filtering"""
    # Create test data
    client.post("/strings", json={"value": "racecar"})
    client.post("/strings", json={"value": "hello world"})
    client.post("/strings", json={"value": "mom"})
    
    # Test palindrome query
    r = client.get("/strings/filter-by-natural-language", params={"query": "all single word palindromic strings"})
    assert r.status_code == 200
    data = r.json()
    assert data["interpreted_query"]["parsed_filters"]["word_count"] == 1
    assert data["interpreted_query"]["parsed_filters"]["is_palindrome"] is True
    
    # Test character query
    r = client.get("/strings/filter-by-natural-language", params={"query": "strings containing the letter z"})
    assert r.status_code == 200


def test_delete_string():
    """Test deleting a string"""
    payload = {"value": "delete me"}
    r = client.post("/strings", json=payload)
    assert r.status_code == 201
    
    # Delete the string
    r2 = client.delete("/strings/delete me")
    assert r2.status_code == 204
    
    # Verify it's gone
    r3 = client.get("/strings/delete me")
    assert r3.status_code == 404
    
    # Test deleting non-existent string
    r4 = client.delete("/strings/nonexistent")
    assert r4.status_code == 404


def test_invalid_input():
    """Test error handling for invalid input"""
    # Test missing value field
    r = client.post("/strings", json={})
    assert r.status_code == 400
    
    # Test invalid data type
    r = client.post("/strings", json={"value": 123})
    assert r.status_code == 422