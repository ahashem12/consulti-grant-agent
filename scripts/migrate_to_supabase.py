import os
import sys
import asyncio
from typing import Dict, Any

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from utils.project_storage import ProjectStorage
from utils.vector_store import SupabaseVectorStore

async def migrate_project(project_name: str, project_path: str):
    """Migrate a single project to Supabase"""
    print(f"[INFO] Migrating project: {project_name}")
    
    # Initialize storage
    storage = ProjectStorage()
    vector_store = SupabaseVectorStore(project_name, os.getenv("OPENAI_API_KEY"))
    
    try:
        # Get or create project in Supabase
        project = await storage.get_project(project_name)
        if project:
            print(f"[INFO] Using existing project: {project['id']}")
            storage.project_id = project['id']
        else:
            project_id = await storage.create_project(project_name)
            print(f"[INFO] Created new project: {project_id}")
        
        # Walk through project directory
        for root, dirs, files in os.walk(project_path):
            # Create folders
            for dir_name in dirs:
                dir_path = os.path.join(root, dir_name)
                rel_path = os.path.relpath(dir_path, project_path)
                try:
                    # Check if folder exists
                    folder = await storage.get_folder(rel_path)
                    if not folder:
                        await storage.create_folder(rel_path)
                        print(f"[INFO] Created folder: {rel_path}")
                    else:
                        print(f"[INFO] Folder already exists: {rel_path}")
                except Exception as e:
                    print(f"[WARN] Error with folder {rel_path}: {e}")
            
            # Process files
            for file_name in files:
                file_path = os.path.join(root, file_name)
                rel_path = os.path.relpath(file_path, project_path)
                
                try:
                    # Check if file exists
                    file_info = await storage.get_file(rel_path)
                    if not file_info:
                        # Save file to Supabase Storage
                        await storage.save_file(rel_path, file_path)
                        print(f"[INFO] Saved file: {rel_path}")
                    else:
                        print(f"[INFO] File already exists: {rel_path}")
                    
                    # Process file for vector store if it's a supported type
                    ext = os.path.splitext(file_name)[1].lower()
                    if ext in ['.pdf', '.docx', '.doc', '.xlsx', '.xls', '.txt']:
                        # Use existing document processing logic
                        from grant_rag import ProjectRAG
                        rag = ProjectRAG(project_name)  # Updated to match new constructor
                        await rag.ingest_document(rel_path)  # Use relative path
                        print(f"[INFO] Processed file for vector store: {rel_path}")
                except Exception as e:
                    print(f"[WARN] Error with file {rel_path}: {e}")
        
        print(f"[INFO] Successfully migrated project: {project_name}")
        
    except Exception as e:
        print(f"[ERROR] Failed to migrate project {project_name}: {e}")
        raise

async def main():
    """Main migration function"""
    # Get projects directory
    projects_dir = os.path.join(project_root, "projects_data")
    
    if not os.path.exists(projects_dir):
        print(f"[ERROR] Projects directory not found: {projects_dir}")
        return
    
    # Get list of projects
    projects = [d for d in os.listdir(projects_dir) if os.path.isdir(os.path.join(projects_dir, d))]
    
    if not projects:
        print("[INFO] No projects found to migrate")
        return
    
    print(f"[INFO] Found {len(projects)} projects to migrate")
    
    # Migrate each project
    for project_name in projects:
        project_path = os.path.join(projects_dir, project_name)
        await migrate_project(project_name, project_path)
    
    print("[INFO] Migration completed")

if __name__ == "__main__":
    asyncio.run(main()) 