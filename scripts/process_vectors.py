import os
import sys
import asyncio
from typing import Dict, Any
from dotenv import load_dotenv

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from utils.project_storage import ProjectStorage
from grant_rag import ProjectRAG

# Load environment variables
load_dotenv()

async def process_project(project_name: str):
    """Process all files in a project into vectors"""
    print(f"[INFO] Processing project: {project_name}")
    
    try:
        # Initialize RAG system
        rag = ProjectRAG(project_name)
        
        # Process all files
        results = await rag.ingest_project()
        
        if "error" in results:
            print(f"[ERROR] Failed to process project: {results['error']}")
        else:
            print("\nProcessing Results:")
            print(f"Total processed: {results['total_processed']}")
            print(f"Total skipped: {results['total_skipped']}")
            print(f"Total errors: {results['total_errors']}")
            print(f"Time taken: {results['elapsed_time']:.2f} seconds")
            
            if results['processed_files']:
                print("\nProcessed files:")
                for file in results['processed_files']:
                    print(f"✓ {file['file']}")
            
            if results['error_files']:
                print("\nFiles with errors:")
                for file in results['error_files']:
                    print(f"✗ {file['file']}: {file['error']}")
        
    except Exception as e:
        print(f"[ERROR] Failed to process project {project_name}: {e}")
        raise

async def main():
    """Main function to process all projects"""
    # Initialize storage to get project list
    storage = ProjectStorage()
    
    try:
        # Get all projects from Supabase
        projects = []
        result = storage.supabase.table('projects').select('name').execute()
        if result.data:
            projects = [p['name'] for p in result.data]
        
        if not projects:
            print("[INFO] No projects found in Supabase")
            return
        
        print(f"[INFO] Found {len(projects)} projects to process")
        
        # Process each project
        for project_name in projects:
            await process_project(project_name)
        
        print("[INFO] All projects processed")
        
    except Exception as e:
        print(f"[ERROR] Failed to get projects: {e}")
        return

if __name__ == "__main__":
    asyncio.run(main()) 