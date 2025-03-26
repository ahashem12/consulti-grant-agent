import asyncio
import os
import json
import re
import hashlib
import time
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime
from pathlib import Path

# Document processing
from pypdf import PdfReader
from openpyxl import load_workbook
import docx
from dotenv import load_dotenv

# LLM
import openai
from openai import OpenAI

# Caching
from diskcache import Cache as PersistentCache

# Custom utils
from utils.supabase_storage import SupabaseStorage
from utils.supabase_vector import SupabaseVector

# Constants
DEBUG = False
DEFAULT_LLM_MODEL = "gpt-4-turbo-preview"
CHUNK_SIZE = 1000  # Characters per chunk
CHUNK_OVERLAP = 200  # Overlap between chunks

# Load environment variables
load_dotenv()
openai_key = os.getenv("OPENAI_API_KEY")
if not openai_key:
    raise ValueError("Please set your OPENAI_API_KEY in the environment variables.")

class ProjectRAG:
    def __init__(self, project_name: str):
        """
        Initialize a RAG system for a specific project
        
        Args:
            project_name: Name of the project
        """
        self.project_name = project_name
        self.openai_key = openai_key
        self.client = OpenAI(api_key=self.openai_key)
        self.llm_model_name = os.getenv('LLM_MODEL', DEFAULT_LLM_MODEL)
        
        # Initialize Supabase clients
        self.storage = SupabaseStorage()
        self.vector_store = SupabaseVector()
        
        # Caching
        cache_dir = f"./cache/{project_name}"
        os.makedirs(cache_dir, exist_ok=True)
        self.cache = PersistentCache(cache_dir=cache_dir, ttl=3600)
        self.response_cache = PersistentCache(cache_dir=f"./response_cache/{project_name}", ttl=3600)
        
        # Statistics
        self.stats = {
            "documents_processed": 0,
            "chunks_stored": 0,
            "last_update": None
        }

    def preprocess_text(self, text: str) -> List[str]:
        """Split text into chunks with overlap"""
        if not text.strip():
            return []
            
        chunks = []
        for i in range(0, len(text), CHUNK_SIZE - CHUNK_OVERLAP):
            chunk = text[i:i + CHUNK_SIZE]
            if chunk.strip():
                chunks.append(chunk)
        return chunks

    async def extract_text_from_pdf(self, file_content: bytes) -> str:
        """Extract all text from a PDF file"""
        try:
            # Create BytesIO object from bytes
            from io import BytesIO
            pdf_file = BytesIO(file_content)
            
            reader = PdfReader(pdf_file)
            text = ""
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n\n"
            return text
        except Exception as e:
            print(f"[ERROR] Failed to extract PDF: {e}")
            return ""

    async def extract_text_from_docx(self, file_content: bytes) -> str:
        """Extract all text from a Word document"""
        try:
            from io import BytesIO
            doc_file = BytesIO(file_content)
            
            doc = docx.Document(doc_file)
            text = ""
            for para in doc.paragraphs:
                text += para.text + "\n"
            for table in doc.tables:
                for row in table.rows:
                    row_text = []
                    for cell in row.cells:
                        row_text.append(cell.text)
                    text += " | ".join(row_text) + "\n"
            return text
        except Exception as e:
            print(f"[ERROR] Failed to extract DOCX: {e}")
            return ""

    async def extract_data_from_excel(self, file_content: bytes) -> Tuple[str, List[str]]:
        """Extract all data from Excel as text"""
        try:
            from io import BytesIO
            excel_file = BytesIO(file_content)
            
            wb = load_workbook(excel_file, data_only=True, read_only=True)
            text = []
            sheet_names = []
            
            for sheet_name in wb.sheetnames:
                sheet_names.append(sheet_name)
                sheet = wb[sheet_name]
                text.append(f"\nSheet: {sheet_name}")
                
                row_count = 0
                max_rows = 1000
                
                for row in sheet.iter_rows(values_only=True):
                    row_count += 1
                    if row_count > max_rows:
                        text.append(f"[Note: Truncated after {max_rows} rows]")
                        break
                        
                    row_values = [str(cell) if cell is not None else "" for cell in row]
                    if any(val.strip() for val in row_values):
                        text.append(" | ".join(row_values))
            
            wb.close()
            return "\n".join(text), sheet_names
            
        except Exception as e:
            print(f"[ERROR] Failed to extract Excel: {e}")
            return "", []

    async def process_file(self, file_name: str) -> bool:
        """Process a single file from Supabase storage"""
        try:
            # Download file from Supabase
            file_content = await self.storage.download_file(self.project_name, file_name)
            if not file_content:
                return False
                
            # Extract text based on file type
            ext = os.path.splitext(file_name)[1].lower()
            document_text = ""
            metadata = {
                "file_name": file_name,
                "project_name": self.project_name,
                "file_type": ext.replace(".", ""),
                "timestamp": datetime.now().isoformat()
            }
            
            if ext == ".pdf":
                document_text = await self.extract_text_from_pdf(file_content)
            elif ext in [".docx", ".doc"]:
                document_text = await self.extract_text_from_docx(file_content)
            elif ext in [".xlsx", ".xls"]:
                document_text, sheet_names = await self.extract_data_from_excel(file_content)
                metadata["sheet_names"] = sheet_names
            elif ext == ".txt":
                document_text = file_content.decode('utf-8')
            else:
                print(f"[WARN] Unsupported file type: {file_name}")
                return False
                
            if not document_text.strip():
                print(f"[WARN] No content extracted from: {file_name}")
                return False
                
            # Process the text into chunks
            chunks = self.preprocess_text(document_text)
            if not chunks:
                print(f"[WARN] No chunks created for: {file_name}")
                return False
                
            # Store chunks in Supabase vector store
            for i, chunk in enumerate(chunks):
                chunk_metadata = metadata.copy()
                chunk_metadata["chunk_index"] = i
                chunk_metadata["total_chunks"] = len(chunks)
                
                success = await self.vector_store.insert_document(
                    self.project_name,
                    chunk,
                    chunk_metadata
                )
                
                if not success:
                    print(f"[ERROR] Failed to store chunk {i} for {file_name}")
                    continue
                
            # Update stats
            self.stats["documents_processed"] += 1
            self.stats["chunks_stored"] += len(chunks)
            self.stats["last_update"] = datetime.now().isoformat()
            
            print(f"[INFO] Successfully processed {file_name} with {len(chunks)} chunks")
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to process {file_name}: {e}")
            return False

    async def process_all_files(self) -> Dict[str, Any]:
        """Process all files in the project"""
        start_time = time.time()
        processed_count = 0
        error_count = 0
        
        print(f"[INFO] Starting processing for project: {self.project_name}")
        
        # Get list of files from Supabase storage
        files = await self.storage.list_files(self.project_name)
        
        for file_name in files:
            try:
                success = await self.process_file(file_name)
                if success:
                    processed_count += 1
                else:
                    error_count += 1
            except Exception as e:
                error_count += 1
                print(f"[ERROR] Failed to process {file_name}: {e}")
        
        elapsed_time = time.time() - start_time
        
        results = {
            "processed_count": processed_count,
            "error_count": error_count,
            "elapsed_time": elapsed_time,
            "timestamp": datetime.now().isoformat()
        }
        
        print(f"[INFO] Processing completed. Processed: {processed_count}, Errors: {error_count}")
        print(f"[INFO] Elapsed time: {elapsed_time:.2f} seconds")
        
        return results

    async def query(self, query: str, n_results: int = 5) -> Dict[str, Any]:
        """Query the project's documents"""
        try:
            # Generate cache key
            query_hash = hashlib.md5(query.encode()).hexdigest()
            cached = self.cache.get(query_hash)
            if cached:
                return cached
                
            # Search documents
            results = await self.vector_store.search_documents(
                query,
                self.project_name,
                limit=n_results
            )
            
            if not results:
                return {
                    "answer": "No relevant information found.",
                    "sources": [],
                    "timestamp": datetime.now().isoformat()
                }
                
            # Format context for the prompt
            context = "\n\n".join([doc["content"] for doc in results])
            sources = list(set([json.loads(doc["metadata"])["file_name"] for doc in results]))
            
            # Create prompt for the LLM
            system_prompt = (
                "You are an AI assistant specialized in analyzing grant applications and project documents. "
                "Use the provided context to answer the query accurately and concisely. "
                "If the information is not in the context, state that clearly. "
                "Include specific facts and quotes when relevant, citing the source documents."
            )
            
            user_prompt = f"Query: {query}\n\nContext:\n{context}"
            
            # Generate response
            response = self.client.chat.completions.create(
                model=self.llm_model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3
            )
            
            result = {
                "answer": response.choices[0].message.content,
                "sources": sources,
                "timestamp": datetime.now().isoformat()
            }
            
            # Cache the result
            self.cache.set(query_hash, result)
            return result
            
        except Exception as e:
            print(f"[ERROR] Query failed: {e}")
            return {
                "answer": f"Error processing query: {str(e)}",
                "sources": [],
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }

class GrantAssessmentSystem:
    def __init__(self):
        """Initialize the grant assessment system"""
        self.projects = {}  # Map of project_name -> ProjectRAG
        self.storage = SupabaseStorage()
        
    async def initialize_projects(self):
        """Initialize RAG systems for all projects"""
        try:
            # List all project folders in Supabase storage
            response = self.storage.supabase.storage.from_("project-data").list("")
            project_folders = [item["name"] for item in response if item["id"].endswith("/")]
            
            # Initialize ProjectRAG for each project
            for project_name in project_folders:
                print(f"[INFO] Initializing project: {project_name}")
                self.projects[project_name] = ProjectRAG(project_name)
                
            print(f"[INFO] Initialized {len(self.projects)} projects")
            
        except Exception as e:
            print(f"[ERROR] Failed to initialize projects: {e}")
            raise
            
    async def process_project(self, project_name: str) -> bool:
        """Process all documents for a specific project"""
        if project_name not in self.projects:
            print(f"[ERROR] Project not found: {project_name}")
            return False
            
        try:
            results = await self.projects[project_name].process_all_files()
            return results["processed_count"] > 0
        except Exception as e:
            print(f"[ERROR] Failed to process project {project_name}: {e}")
            return False
            
    async def process_all_projects(self) -> Dict[str, Any]:
        """Process all documents for all projects"""
        results = {}
        for project_name in self.projects:
            success = await self.process_project(project_name)
            results[project_name] = {"success": success}
        return results
        
    async def search_projects(self, query: str) -> Dict[str, List[Dict[str, Any]]]:
        """Search across all projects"""
        results = {}
        for project_name, project in self.projects.items():
            response = await project.query(query, n_results=3)
            if response and "answer" in response:
                results[project_name] = response
        return results

# =================== MAIN FUNCTION ===================
async def main():
    # Setup the grant assessment system
    system = GrantAssessmentSystem()
    await system.initialize_projects()
    
    # Process all project documents
    print("[INFO] Starting document processing for all projects...")
    await system.process_all_projects()
    print("[INFO] Document processing completed")

if __name__ == "__main__":
    asyncio.run(main()) 