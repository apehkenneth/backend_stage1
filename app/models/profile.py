from pydantic import BaseModel, ConfigDict
from typing import Dict
from datetime import datetime, timezone
import hashlib


class StringProperties(BaseModel):
    length: int
    is_palindrome: bool
    unique_characters: int
    word_count: int
    sha256_hash: str
    character_frequency_map: Dict[str, int]


class StringRecord(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {"value": "racecar"}})
    
    id: str  # This will be the sha256_hash
    value: str
    properties: StringProperties
    created_at: str

    @classmethod
    def create(cls, value: str):
        """
        Create a new StringRecord with automatic analysis
        
        Args:
            value: The string to analyze
            
        Returns:
            StringRecord instance with computed properties
        """
        # Generate SHA256 hash
        sha_hash = hashlib.sha256(value.encode('utf-8')).hexdigest()
        
        # Check if palindrome (case-insensitive)
        cleaned = value.lower().replace(" ", "")
        is_palindrome = cleaned == cleaned[::-1]
        
        # Calculate length
        length = len(value)
        
        # Count unique characters
        unique_characters = len(set(value))
        
        # Count words
        word_count = len(value.split())
        
        # Create character frequency map
        character_frequency_map = {}
        for char in value:
            character_frequency_map[char] = character_frequency_map.get(char, 0) + 1
        
        # Create properties
        props = StringProperties(
            length=length,
            is_palindrome=is_palindrome,
            unique_characters=unique_characters,
            word_count=word_count,
            sha256_hash=sha_hash,
            character_frequency_map=character_frequency_map
        )
        
        # Create timestamp
        created_at = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        
        return cls(
            id=sha_hash,
            value=value,
            properties=props,
            created_at=created_at
        )