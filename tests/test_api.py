"""
Comprehensive test suite for String Analyzer API
Run with: pytest test_api.py -v
"""
import pytest
from fastapi.testclient import TestClient
import os
import json

# Test data file is set in conftest.py
TEST_DATA_FILE = "test_data.json"

from app.main import app

client = TestClient(app)

@pytest.fixture(autouse=True, scope="function")
def cleanup():
    """Clean up test data before and after each test"""
    # Clean up before test
    if os.path.exists(TEST_DATA_FILE):
        os.remove(TEST_DATA_FILE)
    
    # Also clear any data.json if it exists
    if os.path.exists("data.json"):
        os.remove("data.json")
    
    yield
    
    # Clean up after test
    if os.path.exists(TEST_DATA_FILE):
        os.remove(TEST_DATA_FILE)
    
    if os.path.exists("data.json"):
        os.remove("data.json")


class TestPostStrings:
    """Test POST /strings endpoint"""
    
    def test_create_string_success(self):
        """Test creating a new string returns 201"""
        response = client.post("/strings", json={"value": "hello"})
        assert response.status_code == 201
        data = response.json()
        assert data["value"] == "hello"
        assert "id" in data
        assert "properties" in data
        assert "created_at" in data
        
    def test_create_duplicate_string(self):
        """Test creating duplicate string returns 409"""
        # Create first string
        client.post("/strings", json={"value": "test"})
        # Try to create same string again
        response = client.post("/strings", json={"value": "test"})
        assert response.status_code == 409
        
    def test_missing_value_field(self):
        """Test missing 'value' field returns 400"""
        response = client.post("/strings", json={})
        assert response.status_code == 400
        
    def test_invalid_data_type(self):
        """Test invalid data type for 'value' returns 422"""
        response = client.post("/strings", json={"value": 123})
        assert response.status_code == 422
        
    def test_null_value(self):
        """Test null value returns 400"""
        response = client.post("/strings", json={"value": None})
        assert response.status_code == 400


class TestStringProperties:
    """Test string property calculations"""
    
    def test_palindrome_case_insensitive(self):
        """Test palindrome detection is case-insensitive"""
        response = client.post("/strings", json={"value": "RaceCar"})
        assert response.status_code == 201
        data = response.json()
        assert data["properties"]["is_palindrome"] == True
        
    def test_non_palindrome(self):
        """Test non-palindrome detection"""
        response = client.post("/strings", json={"value": "world"})  # Changed from "hello" to avoid conflicts
        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["properties"]["is_palindrome"] == False
        
    def test_length_calculation(self):
        """Test length calculation"""
        response = client.post("/strings", json={"value": "hello world"})
        data = response.json()
        assert data["properties"]["length"] == 11
        
    def test_word_count(self):
        """Test word count calculation"""
        response = client.post("/strings", json={"value": "hello world test"})
        data = response.json()
        assert data["properties"]["word_count"] == 3
        
    def test_unique_characters(self):
        """Test unique character count"""
        response = client.post("/strings", json={"value": "hello"})
        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["properties"]["unique_characters"] == 4  # h, e, l, o
        
    def test_character_frequency(self):
        """Test character frequency map"""
        response = client.post("/strings", json={"value": "test"})  # Changed from "hello" to avoid conflicts
        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
        data = response.json()
        freq_map = data["properties"]["character_frequency_map"]
        assert freq_map["t"] == 2
        assert freq_map["e"] == 1
        assert freq_map["s"] == 1


class TestGetString:
    """Test GET /strings/{string_value} endpoint"""
    
    def test_get_existing_string(self):
        """Test getting an existing string returns 200"""
        client.post("/strings", json={"value": "test"})
        response = client.get("/strings/test")
        assert response.status_code == 200
        data = response.json()
        assert data["value"] == "test"
        
    def test_get_nonexistent_string(self):
        """Test getting non-existent string returns 404"""
        response = client.get("/strings/nonexistent")
        assert response.status_code == 404


class TestGetStringsWithFilters:
    """Test GET /strings with query parameters"""
    
    @pytest.fixture(autouse=True)
    def setup_test_data(self):
        """Setup test data for each test"""
        # Ensure clean state
        if os.path.exists(TEST_DATA_FILE):
            os.remove(TEST_DATA_FILE)
            
        # Create test data
        client.post("/strings", json={"value": "racecar"})  # palindrome, 7 chars, 1 word
        client.post("/strings", json={"value": "hello world"})  # not palindrome, 11 chars, 2 words
        client.post("/strings", json={"value": "a"})  # palindrome, 1 char, 1 word
        client.post("/strings", json={"value": "test data"})  # not palindrome, 9 chars, 2 words
        
        yield
        
        # Cleanup after test
        if os.path.exists(TEST_DATA_FILE):
            os.remove(TEST_DATA_FILE)
        
    def test_filter_by_palindrome(self):
        """Test filtering by palindrome status"""
        # First, verify setup data
        all_strings = client.get("/strings").json()
        print(f"\nAll strings in DB: {[(s['value'], s['properties']['is_palindrome']) for s in all_strings['data']]}")
        
        response = client.get("/strings?is_palindrome=true")
        assert response.status_code == 200
        data = response.json()
        # Debug: print what we got
        palindromes = [(item["value"], item["properties"]["is_palindrome"]) for item in data["data"]]
        print(f"Palindromes found: {palindromes}")
        assert data["count"] == 2, f"Expected 2 palindromes (racecar, a), got {data['count']}: {palindromes}"
        assert all(item["properties"]["is_palindrome"] for item in data["data"])
        
    def test_filter_by_min_length(self):
        """Test filtering by minimum length"""
        response = client.get("/strings?min_length=5")
        data = response.json()
        assert all(item["properties"]["length"] >= 5 for item in data["data"])
        
    def test_filter_by_max_length(self):
        """Test filtering by maximum length"""
        response = client.get("/strings?max_length=5")
        data = response.json()
        assert all(item["properties"]["length"] <= 5 for item in data["data"])
        
    def test_filter_by_word_count(self):
        """Test filtering by word count"""
        response = client.get("/strings?word_count=2")
        data = response.json()
        assert all(item["properties"]["word_count"] == 2 for item in data["data"])
        
    def test_filter_by_contains_character(self):
        """Test filtering by contains character"""
        response = client.get("/strings?contains_character=a")
        data = response.json()
        assert all("a" in item["value"] for item in data["data"])
        
    def test_multiple_filters(self):
        """Test combining multiple filters"""
        response = client.get("/strings?is_palindrome=true&word_count=1")
        data = response.json()
        palindromes = [item["value"] for item in data["data"]]
        assert data["count"] == 2, f"Expected 2 palindromes with 1 word, got {data['count']}: {palindromes}"
        
    def test_invalid_contains_character(self):
        """Test invalid contains_character (not single char) returns 400"""
        response = client.get("/strings?contains_character=ab")
        assert response.status_code == 400


class TestNaturalLanguageFilter:
    """Test GET /strings/filter-by-natural-language endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup_test_data(self):
        """Setup test data for each test"""
        # Ensure clean state
        if os.path.exists(TEST_DATA_FILE):
            os.remove(TEST_DATA_FILE)
            
        # Create test data
        client.post("/strings", json={"value": "racecar"})
        client.post("/strings", json={"value": "hello world"})
        client.post("/strings", json={"value": "a"})
        
        yield
        
        # Cleanup after test
        if os.path.exists(TEST_DATA_FILE):
            os.remove(TEST_DATA_FILE)
        
    def test_single_word_palindrome(self):
        """Test 'all single word palindromic strings'"""
        response = client.get("/strings/filter-by-natural-language?query=all single word palindromic strings")
        assert response.status_code == 200
        data = response.json()
        assert "interpreted_query" in data
        assert data["interpreted_query"]["parsed_filters"]["word_count"] == 1
        assert data["interpreted_query"]["parsed_filters"]["is_palindrome"] == True
        
    def test_longer_than_query(self):
        """Test 'strings longer than 5 characters'"""
        response = client.get("/strings/filter-by-natural-language?query=strings longer than 5 characters")
        data = response.json()
        assert data["interpreted_query"]["parsed_filters"]["min_length"] == 6
        
    def test_contains_letter_query(self):
        """Test 'strings containing the letter a'"""
        response = client.get("/strings/filter-by-natural-language?query=strings containing the letter a")
        data = response.json()
        assert data["interpreted_query"]["parsed_filters"]["contains_character"] == "a"
        
    def test_unparseable_query(self):
        """Test unparseable query returns 400"""
        response = client.get("/strings/filter-by-natural-language?query=gibberish xyz 123")
        assert response.status_code == 400


class TestDeleteString:
    """Test DELETE /strings/{string_value} endpoint"""
    
    def test_delete_existing_string(self):
        """Test deleting existing string returns 204"""
        client.post("/strings", json={"value": "to_delete"})
        response = client.delete("/strings/to_delete")
        assert response.status_code == 204
        
        # Verify it's deleted
        get_response = client.get("/strings/to_delete")
        assert get_response.status_code == 404
        
    def test_delete_nonexistent_string(self):
        """Test deleting non-existent string returns 404"""
        response = client.delete("/strings/nonexistent")
        assert response.status_code == 404


if __name__ == "__main__":
    pytest.main([__file__, "-v"])