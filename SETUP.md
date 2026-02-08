# Healthcare Compliance Copilot - Setup Guide

## Prerequisites

- Python 3.9 or higher
- pip (Python package manager)
- AWS account with Bedrock access
- AWS credentials configured

## Installation Steps

### 1. Clone the repository and navigate to the project directory

```bash
cd healthcare-compliance-copilot
```

### 2. Create a virtual environment (recommended)

```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Download spaCy English model

```bash
python -m spacy download en_core_web_sm
```

### 5. Configure environment variables

Copy the example environment file and update with your credentials:

```bash
copy .env.example .env  # Windows
# or
cp .env.example .env    # macOS/Linux
```

Edit `.env` and add your AWS credentials:
- `AWS_ACCESS_KEY_ID`: Your AWS access key
- `AWS_SECRET_ACCESS_KEY`: Your AWS secret key
- `AWS_REGION`: AWS region (default: us-east-1)

### 6. Verify installation

```bash
python -c "import fastapi, streamlit, boto3, PyPDF2, spacy; print('All dependencies installed successfully!')"
```

## Running the Application

### Start the FastAPI backend

```bash
uvicorn app.api.main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at: http://localhost:8000

### Start the Streamlit frontend (in a separate terminal)

```bash
streamlit run app/ui/streamlit_app.py --server.port 8501
```

The UI will be available at: http://localhost:8501

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific test file
pytest tests/test_preprocessing.py
```

## Project Structure

```
healthcare-compliance-copilot/
├── app/
│   ├── __init__.py
│   ├── models/          # Data models and configuration
│   │   ├── __init__.py
│   │   └── config.py
│   ├── services/        # Core business logic
│   │   └── __init__.py
│   ├── api/             # FastAPI endpoints
│   │   └── __init__.py
│   └── ui/              # Streamlit interface
│       └── __init__.py
├── tests/               # Test suite
│   └── __init__.py
├── requirements.txt     # Python dependencies
├── .env.example         # Environment variables template
└── SETUP.md            # This file
```

## AWS Bedrock Setup

1. Ensure you have access to Amazon Bedrock in your AWS account
2. Enable the Nova Lite model in the Bedrock console
3. (Optional) Configure guardrails for responsible AI:
   - Create a guardrail in the Bedrock console
   - Add the guardrail ID and version to your `.env` file

## Troubleshooting

### spaCy model not found
```bash
python -m spacy download en_core_web_sm
```

### AWS credentials error
- Verify your credentials in `.env` file
- Ensure your AWS account has Bedrock access
- Check that the region supports Bedrock Nova models

### Port already in use
- Change the port in the run command:
  ```bash
  uvicorn app.api.main:app --port 8001
  streamlit run app/ui/streamlit_app.py --server.port 8502
  ```

## Security Notes

- Never commit `.env` file to version control
- Use only synthetic or public data for testing
- Do not upload real protected health information (PHI)
- This tool is for educational purposes only

## Next Steps

After setup is complete, you can:
1. Run the test suite to verify everything works
2. Start implementing the core components (preprocessing, scanning, analysis)
3. Test with synthetic healthcare documents
