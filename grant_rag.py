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

# Vector store
from utils.project_storage import ProjectStorage
from utils.vector_store import SupabaseVectorStore

# Caching
from diskcache import Cache as PersistentCache

# LLM
import openai
from openai import OpenAI

# Constants
DEBUG = False
DEFAULT_LLM_MODEL = "gpt-4-turbo-preview"  # Default model
CHUNK_SIZE = 1000  # Characters per chunk
CHUNK_OVERLAP = 200  # Overlap between chunks

# =================== LOAD ENVIRONMENT VARIABLES ===================
load_dotenv()
openai_key = os.getenv("OPENAI_API_KEY")
if not openai_key:
    raise ValueError("Please set your OPENAI_API_KEY in the environment variables.")

def sanitize_name(name: str) -> str:
    """
    Sanitize a name to be used as a collection name.
    Rules:
    1. Contains 3-63 characters
    2. Starts and ends with alphanumeric
    3. Contains only alphanumeric, underscores or hyphens
    4. No consecutive periods
    5. Not a valid IPv4 address
    """
    # Replace spaces and other invalid characters with underscores
    sanitized = re.sub(r'[^a-zA-Z0-9-]', '_', name)
    # Remove consecutive underscores
    sanitized = re.sub(r'_+', '_', sanitized)
    # Ensure it starts and ends with alphanumeric
    sanitized = re.sub(r'^[^a-zA-Z0-9]+', '', sanitized)
    sanitized = re.sub(r'[^a-zA-Z0-9]+$', '', sanitized)
    
    # If name is too short, pad it
    if len(sanitized) < 3:
        sanitized = sanitized + "_collection"
    # If name is too long, truncate it
    if len(sanitized) > 63:
        sanitized = sanitized[:63]
        # Ensure it ends with alphanumeric
        sanitized = re.sub(r'[^a-zA-Z0-9]+$', '', sanitized)
    
    return sanitized

# =================== PROJECT RAG CLASS ===================
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
        
        # Initialize storage and vector store
        self.storage = ProjectStorage()
        collection_name = sanitize_name(project_name)
        self.vector_store = SupabaseVectorStore(collection_name, openai_key)
        
        # Caching
        self.cache = PersistentCache(cache_dir=f"./cache/{collection_name}", ttl=3600)
        self.response_cache = PersistentCache(cache_dir=f"./response_cache/{collection_name}", ttl=3600)
        
        # Statistics
        self.stats = {
            "documents_processed": 0,
            "chunks_stored": 0,
            "last_update": None
        }

    def load_ingestion_metadata(self) -> dict:
        if os.path.exists(self.metadata_path):
            try:
                with open(self.metadata_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[ERROR] Loading metadata failed: {e}")
        return {}

    def save_ingestion_metadata(self):
        try:
            with open(self.metadata_path, "w", encoding="utf-8") as f:
                json.dump(self.ingestion_metadata, f)
        except Exception as e:
            print(f"[ERROR] Saving metadata failed: {e}")

    # ------------------ DOCUMENT PREPROCESSING ------------------
    def preprocess_text(self, text: str) -> List[str]:
        """Split text into chunks with overlap"""
        if not text.strip():
            return []
            
        # Simple chunking by characters with overlap
        chunks = []
        for i in range(0, len(text), CHUNK_SIZE - CHUNK_OVERLAP):
            chunk = text[i:i + CHUNK_SIZE]
            if chunk.strip():
                chunks.append(chunk)
        return chunks

    # ------------------ DOCUMENT INGESTION METHODS ------------------
    async def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract all text from a PDF file"""
        try:
            reader = PdfReader(pdf_path)
            text = ""
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n\n"
            return text
        except Exception as e:
            print(f"[ERROR] Failed to extract PDF {pdf_path}: {e}")
            return ""

    async def extract_text_from_docx(self, docx_path: str) -> str:
        """Extract all text from a Word document"""
        try:
            doc = docx.Document(docx_path)
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
            print(f"[ERROR] Failed to extract DOCX {docx_path}: {e}")
            return ""

    async def extract_data_from_excel(self, excel_path: str) -> Tuple[str, List[str]]:
        """
        Extract all data from Excel as text, including sheet names and file path context
        Returns tuple of (text content, list of sheet names)
        """
        try:
            print(f"[INFO] Processing Excel file: {excel_path}")
            # Add timeout protection
            wb = load_workbook(excel_path, data_only=True, read_only=True)
            
            text = []
            sheet_names = []
            
            # Add file path context
            file_name = os.path.basename(excel_path)
            parent_folder = os.path.basename(os.path.dirname(excel_path))
            text.append(f"File: {file_name}")
            text.append(f"Location: {parent_folder}")
            
            for sheet_name in wb.sheetnames:
                sheet_names.append(sheet_name)
                sheet = wb[sheet_name]
                text.append(f"\nSheet: {sheet_name}")
                
                # Process rows with a limit to prevent hanging
                row_count = 0
                max_rows = 1000  # Limit number of rows to process
                
                for row in sheet.iter_rows(values_only=True):
                    row_count += 1
                    if row_count > max_rows:
                        text.append(f"[Note: Truncated after {max_rows} rows]")
                        break
                        
                    # Filter out empty cells and convert to strings
                    row_values = [str(cell) if cell is not None else "" for cell in row]
                    # Only add rows that have some content
                    if any(val.strip() for val in row_values):
                        text.append(" | ".join(row_values))
            
            wb.close()
            return "\n".join(text), sheet_names
            
        except Exception as e:
            print(f"[ERROR] Failed to extract Excel {excel_path}: {e}")
            return "", []

    async def ingest_document(self, storage_path: str) -> bool:
        """Ingest a document from Supabase Storage"""
        try:
            # Extract the file name from the storage path
            file_name = os.path.basename(storage_path)
            
            # Get file content directly from storage using the full storage path
            file_content = await self.storage.get_bucket_file(storage_path)
            if not file_content:
                print(f"[ERROR] Could not read file from storage: {storage_path}")
                return False
            
            # Create a temporary file to process the content
            temp_dir = os.path.join(os.getcwd(), "temp")
            os.makedirs(temp_dir, exist_ok=True)
            temp_file = os.path.join(temp_dir, file_name)
            
            try:
                # Write content to temp file
                with open(temp_file, 'wb') as f:
                    f.write(file_content)
                
                # Extract text based on file type
                file_ext = os.path.splitext(file_name)[1].lower()
                document_text = ""
                metadata = {
                    "source": storage_path,
                    "type": file_ext[1:],  # Remove the dot
                    "project": self.project_name
                }
                
                if file_ext == '.pdf':
                    with open(temp_file, 'rb') as f:
                        pdf = PdfReader(f)
                        for page in pdf.pages:
                            document_text += page.extract_text() + "\n"
                        metadata["pages"] = len(pdf.pages)
                
                elif file_ext in ['.docx', '.doc']:
                    doc = docx.Document(temp_file)
                    for para in doc.paragraphs:
                        document_text += para.text + "\n"
                    metadata["paragraphs"] = len(doc.paragraphs)
                
                elif file_ext in ['.xlsx', '.xls']:
                    workbook = load_workbook(temp_file)
                    for sheet in workbook.sheetnames:
                        worksheet = workbook[sheet]
                        for row in worksheet.iter_rows(values_only=True):
                            document_text += " ".join(str(cell) for cell in row if cell is not None) + "\n"
                    metadata["sheets"] = len(workbook.sheetnames)
                
                elif file_ext == '.txt':
                    with open(temp_file, 'r', encoding='utf-8') as f:
                        document_text = f.read()
                
                if not document_text.strip():
                    print(f"[WARN] No text extracted from: {storage_path}")
                    return False
                
                # Process the text into chunks
                chunks = self.preprocess_text(document_text)
                if not chunks:
                    print(f"[WARN] No chunks created for: {storage_path}")
                    return False
                
                # Prepare documents for vector store
                documents = []
                for i, chunk in enumerate(chunks):
                    chunk_id = f"{sanitize_name(file_name)}_{i}"
                    chunk_metadata = metadata.copy()
                    chunk_metadata["chunk_index"] = i
                    chunk_metadata["total_chunks"] = len(chunks)
                    
                    documents.append({
                        "id": chunk_id,
                        "content": chunk,
                        "metadata": chunk_metadata
                    })
                
                # Delete existing chunks for this file
                existing_chunks = [doc["id"] for doc in documents]
                try:
                    await self.vector_store.delete_documents(existing_chunks)
                except Exception as e:
                    print(f"[ERROR] Failed to delete existing chunks: {e}")

                # Add new chunks to vector store
                success = await self.vector_store.add_documents(documents)
                if not success:
                    print(f"[ERROR] Failed to add chunks to vector store: {storage_path}")
                    return False
                
                # Update stats
                self.stats["documents_processed"] += 1
                self.stats["chunks_stored"] += len(chunks)
                self.stats["last_update"] = datetime.now().isoformat()
                
                print(f"[INFO] Successfully ingested {storage_path} with {len(chunks)} chunks")
                return True
                
            finally:
                # Clean up temp file
                try:
                    os.remove(temp_file)
                except:
                    pass
            
        except Exception as e:
            print(f"[ERROR] Failed to ingest {storage_path}: {e}")
            return False

    async def ingest_project(self) -> Dict[str, Any]:
        """Ingest all supported documents in the project"""
        start_time = time.time()
        processed_count = 0
        skipped_count = 0
        error_count = 0
        
        print(f"[INFO] Starting ingestion for project: {self.project_name}")
        
        # Track ingestion metrics
        ingestion_results = {
            "processed_files": [],
            "skipped_files": [],
            "error_files": [],
            "start_time": datetime.now().isoformat()
        }
        
        try:
            print(f"[DEBUG] Listing files for project: {self.project_name}")
            # List all files in the project's storage bucket folder recursively
            files = await self.storage.list_bucket_files(prefix=self.project_name)
            
            if not files:
                print(f"[INFO] No files found in storage for project: {self.project_name}")
                return ingestion_results
            
            print(f"[INFO] Found {len(files)} files in project {self.project_name}")
            print(f"[DEBUG] Files to process: {[f['name'] for f in files]}")
            
            # Process each file
            for idx, file_info in enumerate(files, 1):
                file_name = file_info['name']
                print(f"[DEBUG] Processing file {idx}/{len(files)}: {file_name}")
                
                # Skip if this is a directory (no period in the basename)
                if '.' not in os.path.basename(file_name):
                    print(f"[INFO] Skipping directory: {file_name}")
                    continue
                
                file_ext = os.path.splitext(file_name)[1].lower()
                
                # Skip unsupported file types
                if file_ext not in ['.pdf', '.docx', '.doc', '.xlsx', '.xls', '.txt']:
                    print(f"[INFO] Skipping unsupported file type: {file_name}")
                    skipped_count += 1
                    ingestion_results["skipped_files"].append(file_name)
                    continue
                
                try:
                    print(f"[DEBUG] Starting ingestion of file: {file_name}")
                    # Ingest the document using the file path directly from the bucket
                    success = await self.ingest_document(file_name)
                    if success:
                        processed_count += 1
                        ingestion_results["processed_files"].append(file_name)
                        print(f"[INFO] Successfully processed: {file_name}")
                    else:
                        error_count += 1
                        ingestion_results["error_files"].append(file_name)
                        print(f"[ERROR] Failed to process: {file_name}")
                except Exception as e:
                    error_count += 1
                    ingestion_results["error_files"].append(file_name)
                    print(f"[ERROR] Error processing {file_name}: {e}")
                
                print(f"[DEBUG] Progress: {idx}/{len(files)} files processed")
            
            elapsed_time = time.time() - start_time
            # Update ingestion results
            ingestion_results.update({
                "end_time": datetime.now().isoformat(),
                "total_time": elapsed_time,
                "processed_count": processed_count,
                "skipped_count": skipped_count,
                "error_count": error_count
            })
            
            print(f"[INFO] Ingestion complete for {self.project_name}")
            print(f"[INFO] Processed: {processed_count}, Skipped: {skipped_count}, Errors: {error_count}")
            print(f"[INFO] Total time: {elapsed_time:.2f} seconds")
            
            return ingestion_results
            
        except Exception as e:
            print(f"[ERROR] Failed to ingest project {self.project_name}: {e}")
            return {
                "error": str(e),
                "start_time": datetime.now().isoformat(),
                "end_time": datetime.now().isoformat()
            }

    # ------------------ QUERY & RESPONSE METHODS ------------------
    async def query_collection(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """
        Query the collection and return the most relevant chunks with metadata
        """
        try:
            # Generate cache key
            query_hash = hashlib.md5(query.encode()).hexdigest()
            cached = self.cache.get(query_hash)
            if cached:
                if DEBUG:
                    print(f"[DEBUG] Using cached chunks for query: {query}")
                return cached
                
            # Query the vector store
            results = await self.vector_store.query(query, n_results=n_results)
            
            if not results:
                return []
                
            # Cache the results
            self.cache.set(query_hash, results)
            
            if DEBUG:
                print(f"[DEBUG] Found {len(results)} chunks for query: {query}")
            return results
            
        except Exception as e:
            print(f"[ERROR] Error retrieving data for '{query}': {e}")
            return []

    async def generate_response(self, query: str, context_chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate a response based on the query and retrieved context chunks
        """
        # Generate cache key
        query_hash = hashlib.md5(query.encode()).hexdigest()
        cached_response = self.response_cache.get(query_hash)
        if cached_response:
            if DEBUG:
                print(f"[DEBUG] Using cached response for query: {query}")
            return cached_response
            
        # Format context for the prompt
        formatted_context = ""
        sources = []
        for i, chunk in enumerate(context_chunks):
            formatted_context += f"[CHUNK {i+1}] {chunk['content']}\n\n"
            if "metadata" in chunk and "source" in chunk["metadata"]:
                source_file = os.path.basename(chunk["metadata"]["source"])
                if source_file not in sources:
                    sources.append(source_file)
                    
        if not formatted_context:
            formatted_context = "No relevant information found in the project documents."
            
        # Create prompt for the LLM
        system_prompt = (
            "You are an AI assistant specialized in analyzing grant applications and project documents. "
            "You will be provided with context chunks from a project's documents. "
            "Use this information to answer the query accurately and concisely. "
            "If the information is not in the context, state that clearly. "
            "Include specific facts, figures, and quotes from the documents when relevant. "
            "Always cite your sources when quoting from specific documents."
        )
        
        user_prompt = (
            f"Query: {query}\n\n"
            f"Context from project documents:\n{formatted_context}"
        )
        
        try:
            # Call the LLM
            response = self.client.chat.completions.create(
                model=self.llm_model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3
            )
            
            # Extract and cache the response
            answer = response.choices[0].message.content
            
            result = {
                "answer": answer,
                "sources": sources,
                "timestamp": datetime.now().isoformat(),
                "context_used": len(context_chunks)
            }
            
            self.response_cache.set(query_hash, result)
            return result
            
        except Exception as e:
            print(f"[ERROR] Failed to generate response: {e}")
            return {
                "answer": f"Error generating response: {str(e)}",
                "sources": [],
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }

    async def ask(self, query: str) -> Dict[str, Any]:
        """
        Main method to ask a question about the project
        """
        print(f"[INFO] Processing query for {self.project_name}: {query}")
        
        # 1. Retrieve relevant chunks
        retrieved_chunks = await self.query_collection(query, n_results=5)
        
        # 2. Generate response
        response = await self.generate_response(query, retrieved_chunks)
        
        return response

    # ------------------ REPORT GENERATION METHODS ------------------
    async def check_eligibility(self, criteria: Dict[str, str]) -> Dict[str, Any]:
        """
        Check project's eligibility based on specified criteria
        
        Args:
            criteria: Dictionary mapping criteria names to questions
            
        Returns:
            Dictionary with criteria names, questions, answers, and eligibility assessment
        """
        results = {
            "project_name": self.project_name,
            "timestamp": datetime.now().isoformat(),
            "criteria": [],
            "eligible": True,  # Initially assume eligible
            "summary": ""
        }
        
        for criterion_name, question in criteria.items():
            print(f"[INFO] Checking criterion '{criterion_name}' for {self.project_name}")
            
            # Format the question to explicitly ask about eligibility
            eligibility_question = (
                f"Based on the project documents, {question} "
                f"Answer with 'Yes' or 'No' first, then provide supporting evidence."
            )
            
            # Get answer from the RAG system
            response = await self.ask(eligibility_question)
            
            # Determine eligibility by checking if the answer starts with "Yes"
            answer = response["answer"].strip()
            is_eligible = answer.lower().startswith("yes")
            
            # If any criterion fails, the project is not eligible
            if not is_eligible:
                results["eligible"] = False
                
            # Add criterion result
            results["criteria"].append({
                "name": criterion_name,
                "question": question,
                "answer": answer,
                "meets_criterion": is_eligible,
                "sources": response.get("sources", [])
            })
        
        # Generate summary
        if results["eligible"]:
            results["summary"] = f"Project '{self.project_name}' meets all eligibility criteria."
        else:
            failed_criteria = [c["name"] for c in results["criteria"] if not c["meets_criterion"]]
            results["summary"] = (
                f"Project '{self.project_name}' does not meet the following criteria: "
                f"{', '.join(failed_criteria)}."
            )
            
        return results

    async def generate_detailed_report(self, questions: List[str]) -> Dict[str, Any]:
        """
        Generate a detailed report by answering a list of questions about the project
        
        Args:
            questions: List of questions to answer about the project
            
        Returns:
            Dictionary with project name, timestamp, and answers to questions
        """
        report = {
            "project_name": self.project_name,
            "timestamp": datetime.now().isoformat(),
            "sections": []
        }
        
        for question in questions:
            print(f"[INFO] Answering report question for {self.project_name}: {question}")
            
            response = await self.ask(question)
            
            report["sections"].append({
                "question": question,
                "answer": response["answer"],
                "sources": response.get("sources", [])
            })
            
        return report

    async def generate_recommendation(self, eligibility_result: Dict[str, Any], detailed_report: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a recommendation for the donor based on eligibility and detailed report
        
        Args:
            eligibility_result: Result from check_eligibility
            detailed_report: Result from generate_detailed_report
            
        Returns:
            Dictionary with recommendation details
        """
        # Prepare context about the project for the LLM
        context = f"Project Name: {self.project_name}\n\n"
        
        # Add eligibility information
        context += "ELIGIBILITY ASSESSMENT:\n"
        context += f"Overall Eligibility: {eligibility_result['eligible']}\n"
        for criterion in eligibility_result["criteria"]:
            context += f"- {criterion['name']}: {'Meets criterion' if criterion['meets_criterion'] else 'Does not meet criterion'}\n"
            context += f"  Question: {criterion['question']}\n"
            context += f"  Answer: {criterion['answer']}\n\n"
            
        # Add report information
        context += "DETAILED REPORT:\n"
        for section in detailed_report["sections"]:
            context += f"Question: {section['question']}\n"
            context += f"Answer: {section['answer']}\n\n"
            
        # Prepare prompt for recommendation generation
        system_prompt = (
            "You are a grant evaluation expert assisting a donor in making funding decisions. "
            "Your role is to provide an objective recommendation based on project eligibility and "
            "detailed assessment, highlighting strengths, weaknesses, risks, and potential impact. "
            "Your recommendation should be clear, substantiated with evidence from the project documents, "
            "and include specific funding suggestions or alternatives if appropriate. "
            "You MUST start your response with one of these exact phrases on the first line:\n"
            "DECISION: Fund\n"
            "DECISION: Do Not Fund\n"
            "DECISION: Partially Fund\n"
        )
        
        user_prompt = (
            "Based on the following project assessment, provide a donor recommendation that includes:\n"
            "1. Funding decision (Must start with DECISION: followed by Fund/Do Not Fund/Partially Fund)\n"
            "2. Executive summary (2-3 sentences)\n"
            "3. Key strengths and weaknesses\n"
            "4. Risks and mitigations\n"
            "5. Expected impact if funded\n"
            "6. Any conditions or special considerations\n\n"
            f"{context}"
        )
        
        try:
            # Generate recommendation using OpenAI
            response = self.client.chat.completions.create(
                model=self.llm_model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2
            )
            
            recommendation_text = response.choices[0].message.content
            
            # Extract the funding decision from the first line
            first_line = recommendation_text.split('\n')[0].strip()
            funding_decision = "Pending"
            if first_line.startswith("DECISION:"):
                funding_decision = first_line.replace("DECISION:", "").strip()
                # Remove the decision line from the recommendation text
                recommendation_text = '\n'.join(recommendation_text.split('\n')[1:]).strip()
            
            recommendation = {
                "project_name": self.project_name,
                "timestamp": datetime.now().isoformat(),
                "funding_decision": funding_decision,
                "recommendation": recommendation_text
            }
            
            return recommendation
            
        except Exception as e:
            print(f"[ERROR] Failed to generate recommendation: {e}")
            return {
                "project_name": self.project_name,
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "recommendation": "Error generating recommendation."
            }

# =================== GRANT ASSESSMENT SYSTEM ===================
class GrantAssessmentSystem:
    def __init__(self):
        """Initialize the grant assessment system"""
        self.projects = {}
        self.openai_key = openai_key
        self.storage = ProjectStorage()  # Initialize Supabase storage

    async def initialize_projects(self):
        """Initialize all projects from Supabase"""
        try:
            # Get all projects from Supabase
            result = self.storage.supabase.table('projects').select('*').execute()
            if not result.data:
                print("[INFO] No projects found in Supabase")
                return

            # Initialize RAG for each project
            for project in result.data:
                project_name = project['name']
                print(f"[INFO] Initializing project: {project_name}")
                self.projects[project_name] = ProjectRAG(project_name)

            print(f"[INFO] Initialized {len(self.projects)} projects")

        except Exception as e:
            print(f"[ERROR] Failed to initialize projects: {e}")
            raise

    async def add_project(self, project_name: str) -> bool:
        """Add a new project"""
        try:
            # Create project in Supabase
            project_id = await self.storage.create_project(project_name)
            
            # Initialize ProjectRAG
            self.projects[project_name] = ProjectRAG(project_name)
            print(f"[INFO] Successfully added project: {project_name}")
            
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to add project: {e}")
            return False

    async def get_project_info(self, project_name: str) -> Dict[str, Any]:
        """Get project information including file count and stats"""
        try:
            # Get project from Supabase
            project = await self.storage.get_project(project_name)
            if not project:
                return None

            # Get file count from Supabase
            result = self.storage.supabase.table('project_files').select('*', count='exact').eq('project_id', project['id']).execute()
            file_count = len(result.data) if result.data else 0

            # Get project stats if available
            stats = self.projects[project_name].stats if project_name in self.projects else {}

            return {
                "name": project_name,
                "file_count": file_count,
                "stats": stats,
                "last_modified": project['updated_at']
            }

        except Exception as e:
            print(f"[ERROR] Failed to get project info: {e}")
            return None

    async def search_across_projects(self, query: str, n_results: int = 3) -> Dict[str, str]:
        """Search across all projects"""
        results = {}
        
        try:
            for project_name, rag in self.projects.items():
                project_results = await rag.query_project(query, n_results)
                if project_results:
                    results[project_name] = project_results
            
            return results
            
        except Exception as e:
            print(f"[ERROR] Failed to search across projects: {e}")
            return {"error": str(e)}

# =================== MAIN FUNCTION ===================
async def main():
    # Setup the grant assessment system
    system = GrantAssessmentSystem()
    await system.initialize_projects()
    
    # Ingest all project documents
    print("[INFO] Starting document ingestion for all projects...")
    await system.ingest_all_projects()
    print("[INFO] Document ingestion completed")
    
    # Example of checking eligibility for all projects
    print("[INFO] Checking eligibility for all projects...")
    eligibility_results = await system.check_all_projects_eligibility()
    for project_name, result in eligibility_results.items():
        print(f"Project '{project_name}' eligible: {result['eligible']}")
    
    # Example of generating recommendations
    print("[INFO] Generating recommendations for all projects...")
    recommendations = await system.generate_all_recommendations()
    
    # Example of comparative analysis
    print("[INFO] Generating comparative analysis...")
    analysis = await system.generate_comparative_analysis()
    print("[INFO] Analysis completed")

if __name__ == "__main__":
    asyncio.run(main()) 