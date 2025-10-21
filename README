# String Analyzer Service - Backend Stage 1

A RESTful API service that analyzes strings and stores their computed properties.

## Features

The service analyzes strings and computes the following properties:
- **length**: Number of characters in the string
- **is_palindrome**: Boolean indicating if the string reads the same forwards and backwards (case-insensitive)
- **unique_characters**: Count of distinct characters in the string
- **word_count**: Number of words separated by whitespace
- **sha256_hash**: SHA-256 hash of the string for unique identification
- **character_frequency_map**: Dictionary mapping each character to its occurrence count

## API Endpoints

### 1. Create/Analyze String
```
POST /strings
Content-Type: application/json

Request Body:
{
  "value": "string to analyze"
}

Success Response (201 Created):
{
  "id": "sha256_hash_value",
  "value": "string to analyze",
  "properties": {
    "length": 17,
    "is_palindrome": false,
    "unique_characters": 12,
    "word_count": 3,
    "sha256_hash": "abc123...",
    "character_frequency_map": { "s": 2, "t": 3, ... }
  },
  "created_at": "2025-08-27T10:00:00Z"
}
```

### 2. Get Specific String
```
GET /strings/{string_value}

Success Response (200 OK):
Returns the stored string record
```

### 3. Get All Strings with Filtering
```
GET /strings?is_palindrome=true&min_length=5&max_length=20&word_count=2&contains_character=a

Query Parameters:
- is_palindrome: boolean (true/false)
- min_length: integer (minimum string length)
- max_length: integer (maximum string length)
- word_count: integer (exact word count)
- contains_character: string (single character to search for)

Success Response (200 OK):
{
  "data": [ /* array of string records */ ],
  "count": 15,
  "filters_applied": { ... }
}
```

### 4. Natural Language Filtering
```
GET /strings/filter-by-natural-language?query=all%20single%20word%20palindromic%20strings

Supported queries:
- "all single word palindromic strings"
- "strings longer than 10 characters"
- "strings containing the letter z"
```

### 5. Delete String
```
DELETE /strings/{string_value}

Success Response (204 No Content)
```

## Setup Instructions

### Prerequisites
- Python 3.12 or higher
- pip (Python package manager)

### Installation

1. **Clone the repository**
```bash
git clone <your-repo-url>
cd backend_stage1
```

2. **Create a virtual environment**
```bash
python -m venv .venv
```

3. **Activate the virtual environment**

Windows:
```bash
.venv\Scripts\activate
```

macOS/Linux:
```bash
source .venv/bin/activate
```

4. **Install dependencies**
```bash
pip install -r requirements.txt
```

### Running Locally

1. **Start the development server**
```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

2. **Access the API documentation**
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Running Tests

```bash
pytest tests/test_api.py -v
```

For coverage report:
```bash
pytest tests/test_api.py --cov=app --cov-report=html
```

## Dependencies

Key dependencies (see `requirements.txt` for full list):
- **FastAPI**: Modern web framework for building APIs
- **Uvicorn**: ASGI server for running the application
- **Pydantic**: Data validation using Python type annotations
- **pytest**: Testing framework
- **httpx**: HTTP client for testing

## Environment Variables

Optional environment variables:

- `DATA_FILE`: Path to the JSON file for data storage (default: `data.json`)

Create a `.env` file in the project root:
```
DATA_FILE=data.json
```

## Project Structure

```
backend_stage1/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py           # API endpoints
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py           # Configuration settings
│   └── models/
│       ├── __init__.py
│       └── profile.py          # Data models
├── tests/
│   ├── __init__.py
│   └── test_api.py             # API tests
├── .env                        # Environment variables (optional)
├── requirements.txt            # Python dependencies
├── README.md                   # This file
└── data.json                   # Data storage (created automatically)
```

## API Examples

### Create a string
```bash
curl -X POST "http://localhost:8000/strings" \
  -H "Content-Type: application/json" \
  -d '{"value": "racecar"}'
```

### Get all palindromes
```bash
curl "http://localhost:8000/strings?is_palindrome=true"
```

### Natural language query
```bash
curl "http://localhost:8000/strings/filter-by-natural-language?query=all%20single%20word%20palindromic%20strings"
```

### Delete a string
```bash
curl -X DELETE "http://localhost:8000/strings/racecar"
```

## Deployment

This application can be deployed to:
- Railway
- Heroku
- AWS (EC2, Elastic Beanstalk, Lambda)
- Digital Ocean
- Any platform supporting Python/FastAPI applications



## License

MIT License

## Author
Kenneth Apeh

## Support

For issues and questions, please open an issue in the GitHub repository.
