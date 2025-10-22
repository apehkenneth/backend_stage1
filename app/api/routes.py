from fastapi import APIRouter, HTTPException, Query, status, Body
from typing import List, Optional, Dict, Any
import json
import os
import re

from app.models.profile import StringRecord
from app.core.config import settings

router = APIRouter()

# JSON file database
DATA_FILE = settings.DATA_FILE


def load_data() -> List[dict]:
    """Load data from JSON file"""
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def save_data(data: List[dict]):
    """Save data to JSON file"""
    # Ensure directory exists
    dir_path = os.path.dirname(DATA_FILE)
    if dir_path:
        os.makedirs(dir_path, exist_ok=True)
    
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


@router.post("/strings", response_model=StringRecord, status_code=status.HTTP_201_CREATED, tags=["Strings"])
async def analyze_string(payload: Dict[str, Any] = Body(...)):
    """
    Create and analyze a new string
    
    Args:
        payload: Dictionary containing 'value' field
        
    Returns:
        StringRecord with analysis properties
        
    Raises:
        400: If 'value' field is missing
        409: If string already exists (duplicate hash)
        422: If 'value' is not a string
    """
    # Check if 'value' key exists
    if "value" not in payload:
        raise HTTPException(status_code=400, detail="Missing 'value' field")
    
    value = payload.get("value")
    
    # Check if value is None
    if value is None:
        raise HTTPException(status_code=400, detail="Missing 'value' field")
    
    # Check if value is a string
    if not isinstance(value, str):
        raise HTTPException(status_code=422, detail="Invalid data type for 'value' (must be string)")

    record = StringRecord.create(value)
    data = load_data()

    # Check for duplicate SHA256 hash
    if any(item["id"] == record.id for item in data):
        raise HTTPException(status_code=409, detail="String already exists in the system")

    data.append(record.model_dump())
    save_data(data)
    return record


@router.get("/strings/filter-by-natural-language", tags=["Strings"])
async def filter_by_natural_language(query: str = Query(..., description="Natural language query")):
    """
    Filter strings using natural language query
    
    Args:
        query: Natural language query string
        
    Returns:
        Dictionary with data, count, and interpreted_query
        
    Raises:
        400: Unable to parse natural language query
        422: Query parsed but resulted in conflicting filters
    """
    query_lower = query.lower()
    parsed_filters = {}
    
    try:
        # Parse "palindrome" or "palindromic"
        if "palindrome" in query_lower or "palindromic" in query_lower:
            parsed_filters["is_palindrome"] = True
        
        # Parse "single word" or "one word"
        if "single word" in query_lower or "one word" in query_lower:
            parsed_filters["word_count"] = 1
        
        # Parse "longer than X characters" or "more than X characters"
        length_match = re.search(r'longer than (\d+)|more than (\d+) character', query_lower)
        if length_match:
            length_val = int(length_match.group(1) or length_match.group(2))
            parsed_filters["min_length"] = length_val + 1
        
        # Parse "containing letter X" or "contain letter X" or "contains the letter X"
        char_match = re.search(r'contain(?:s|ing)?\s+(?:the\s+)?(?:letter\s+)?([a-z])', query_lower)
        if char_match:
            parsed_filters["contains_character"] = char_match.group(1)
        
        # Parse "first vowel" (interpret as 'a')
        if "first vowel" in query_lower:
            parsed_filters["contains_character"] = "a"
        
        # If no filters parsed, return error
        if not parsed_filters:
            raise HTTPException(status_code=400, detail="Unable to parse natural language query")
        
        # Check for conflicting filters
        if "min_length" in parsed_filters and "max_length" in parsed_filters:
            if parsed_filters["min_length"] > parsed_filters["max_length"]:
                raise HTTPException(
                    status_code=422, 
                    detail="Query parsed but resulted in conflicting filters"
                )
        
        # Apply filters
        data = load_data()
        
        if "is_palindrome" in parsed_filters:
            data = [d for d in data if d["properties"]["is_palindrome"] == parsed_filters["is_palindrome"]]
        
        if "word_count" in parsed_filters:
            data = [d for d in data if d["properties"]["word_count"] == parsed_filters["word_count"]]
        
        if "min_length" in parsed_filters:
            data = [d for d in data if d["properties"]["length"] >= parsed_filters["min_length"]]
        
        if "max_length" in parsed_filters:
            data = [d for d in data if d["properties"]["length"] <= parsed_filters["max_length"]]
        
        if "contains_character" in parsed_filters:
            data = [d for d in data if parsed_filters["contains_character"] in d["value"].lower()]
        
        return {
            "data": data,
            "count": len(data),
            "interpreted_query": {
                "original": query,
                "parsed_filters": parsed_filters
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Unable to parse natural language query: {str(e)}")


@router.get("/strings", tags=["Strings"])
async def get_strings(
    is_palindrome: Optional[str] = Query(None, description="Filter by palindrome status (true/false)"),
    min_length: Optional[int] = Query(None, description="Minimum string length"),
    max_length: Optional[int] = Query(None, description="Maximum string length"),
    word_count: Optional[int] = Query(None, description="Exact word count"),
    contains_character: Optional[str] = Query(None, description="Single character to search for"),
):
    """
    Get all strings with optional filtering
    
    Args:
        is_palindrome: Filter by palindrome status ("true" or "false")
        min_length: Minimum string length
        max_length: Maximum string length
        word_count: Exact word count
        contains_character: Single character to search for
        
    Returns:
        Dictionary with data, count, and filters_applied
        
    Raises:
        400: Invalid query parameter values or types
    """
    data = load_data()
    
    # Validate parameters
    if contains_character is not None and len(contains_character) != 1:
        raise HTTPException(status_code=400, detail="contains_character must be a single character")
    
    if min_length is not None and min_length < 0:
        raise HTTPException(status_code=400, detail="min_length must be non-negative")
    
    if max_length is not None and max_length < 0:
        raise HTTPException(status_code=400, detail="max_length must be non-negative")
    
    if word_count is not None and word_count < 0:
        raise HTTPException(status_code=400, detail="word_count must be non-negative")
    
    # Track applied filters
    filters_applied = {}
    
    # Filter by palindrome
    if is_palindrome is not None:
        is_palindrome_bool = is_palindrome.lower() == "true"
        data = [d for d in data if d["properties"]["is_palindrome"] == is_palindrome_bool]
        filters_applied["is_palindrome"] = is_palindrome_bool
    
    # Filter by min_length
    if min_length is not None:
        data = [d for d in data if d["properties"]["length"] >= min_length]
        filters_applied["min_length"] = min_length
    
    # Filter by max_length
    if max_length is not None:
        data = [d for d in data if d["properties"]["length"] <= max_length]
        filters_applied["max_length"] = max_length
    
    # Filter by word_count
    if word_count is not None:
        data = [d for d in data if d["properties"]["word_count"] == word_count]
        filters_applied["word_count"] = word_count
    
    # Filter by contains_character (case-insensitive)
    if contains_character is not None:
        data = [d for d in data if contains_character.lower() in d["value"].lower()]
        filters_applied["contains_character"] = contains_character
    
    return {
        "data": data,
        "count": len(data),
        "filters_applied": filters_applied
    }


@router.get("/strings/{string_value}", response_model=StringRecord, tags=["Strings"])
async def get_string_by_value(string_value: str):
    """
    Get a specific string by its value
    
    Args:
        string_value: The exact string value to retrieve
        
    Returns:
        StringRecord object
        
    Raises:
        404: If string not found
    """
    data = load_data()
    
    for item in data:
        if item["value"] == string_value:
            return StringRecord(**item)
    
    raise HTTPException(status_code=404, detail="String does not exist in the system")


@router.delete("/strings/{string_value}", status_code=status.HTTP_204_NO_CONTENT, tags=["Strings"])
async def delete_string(string_value: str):
    """
    Delete a specific string by its value
    
    Args:
        string_value: The exact string value to delete
        
    Raises:
        404: If string not found
    """
    data = load_data()
    
    # Find and remove the string
    original_length = len(data)
    data = [item for item in data if item["value"] != string_value]
    
    if len(data) == original_length:
        raise HTTPException(status_code=404, detail="String does not exist in the system")
    
    save_data(data)
    return None  # 204 No Content returns empty body