# Grant RAG System

A Retrieval-Augmented Generation (RAG) system for analyzing grant applications and generating donor recommendations.

## Features

- Document ingestion from multiple formats (PDF, Excel, Word, TXT)
- Project-specific knowledge bases
- Eligibility checking against customizable criteria
- Detailed project reports
- Donor recommendations
- Comparative analysis of multiple projects
- Persistent caching for improved performance
- Asynchronous processing

## Project Structure

```
GrantRAG/
├── projects_data/           # Directory containing project folders
│   ├── project1/           # Each project has its own folder
│   │   ├── docs/          # Project documents
│   │   └── metadata.json  # Project metadata
│   └── project2/
├── grant_rag.py           # Main RAG system implementation
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## Setup

1. Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create a `.env` file with your OpenAI API key:

```
OPENAI_API_KEY=your_api_key_here
```

4. Create the project structure:

```bash
mkdir -p GrantRAG/projects_data
```

## Usage

1. Place project documents in their respective folders under `projects_data/`

2. Run the system:

```bash
python grant_rag.py
```

The system will:

- Initialize project knowledge bases
- Ingest all documents
- Check project eligibility
- Generate recommendations
- Perform comparative analysis

## Project Organization

Each project should be organized as follows:

```
projects_data/
└── project_name/
    ├── docs/              # Project documents
    │   ├── proposal.pdf
    │   ├── budget.xlsx
    │   └── timeline.docx
    └── metadata.json      # Optional project metadata
```

## Features in Detail

### Document Ingestion

- Supports PDF, Excel, Word, and TXT files
- Automatic text extraction and chunking
- Metadata tracking for efficient updates
- Persistent storage using ChromaDB

### Eligibility Checking

- Customizable criteria
- Evidence-based assessment
- Detailed reporting of criteria fulfillment
- Automatic disqualification tracking

### Report Generation

- Comprehensive project analysis
- Standardized question templates
- Source tracking and citations
- Customizable report sections

### Donor Recommendations

- Evidence-based funding recommendations
- Risk assessment
- Impact analysis
- Portfolio optimization suggestions

### Comparative Analysis

- Multi-project comparison
- Ranking and prioritization
- Synergy identification
- Portfolio allocation recommendations

## Configuration

The system can be configured through environment variables:

- `OPENAI_API_KEY`: Your OpenAI API key
- `LLM_MODEL`: The OpenAI model to use (default: "gpt-4o-mini")
- `CHUNK_SIZE`: Size of text chunks for processing (default: 1000)
- `CHUNK_OVERLAP`: Overlap between chunks (default: 200)

## Error Handling

The system includes comprehensive error handling:

- Document processing errors
- API failures
- Cache management
- File system operations
- Invalid input handling

## Performance Optimization

- Persistent caching of queries and responses
- Efficient document chunking
- Asynchronous processing
- Metadata-based update tracking
- Batch processing capabilities

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
