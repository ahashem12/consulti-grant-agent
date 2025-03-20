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
- Vector similarity search using Supabase and pgvector

## Project Structure

```
GrantRAG/
├── projects_data/           # Directory containing project folders
│   ├── project1/           # Each project has its own folder
│   │   ├── docs/          # Project documents
│   │   └── metadata.json  # Project metadata
│   └── project2/
├── config/                 # Configuration files
│   └── supabase.py        # Supabase configuration
├── utils/                  # Utility modules
│   └── vector_store.py    # Vector store implementation
├── supabase/              # Supabase database files
│   └── functions/         # Database functions
│       └── match_documents.sql
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

3. Create a `.env` file with your API keys:

```
OPENAI_API_KEY=your_openai_api_key_here
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key
```

4. Set up Supabase:
   - Create a new project at https://supabase.com
   - Get your project URL and anon key from the project settings
   - Go to the SQL editor in your Supabase project
   - Copy and paste the contents of `supabase/functions/match_documents.sql`
   - Run the SQL to create the necessary tables and functions

5. Create the project structure:

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
- Persistent storage using Supabase with pgvector for vector similarity search

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
