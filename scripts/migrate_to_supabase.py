import os
import asyncio
from typing import Dict, Any
from utils.project_storage import ProjectStorage

async def migrate_project(project_name: str, project_path: str):
    """Migrate a single project to Supabase"""
    print(f"[INFO] Migrating project: {project_name}")
    
    # Initialize storage
    storage = ProjectStorage()
    
    try:
        # Create project in Supabase
        project_id = await storage.create_project(project_name)
        print(f"[INFO] Created project in Supabase: {project_id}")
        
        # Walk through project directory
        for root, dirs, files in os.walk(project_path):
            # Create folders
            for dir_name in dirs:
                dir_path = os.path.join(root, dir_name)
                rel_path = os.path.relpath(dir_path, project_path)
                await storage.create_folder(rel_path)
                print(f"[INFO] Created folder: {rel_path}")
            
            # Process files
            for file_name in files:
                file_path = os.path.join(root, file_name)
                rel_path = os.path.relpath(file_path, project_path)
                
                # Save file to Supabase Storage
                await storage.save_file(rel_path, file_path)
                print(f"[INFO] Saved file: {rel_path}")
        
        print(f"[INFO] Successfully migrated project: {project_name}")
        
    except Exception as e:
        print(f"[ERROR] Failed to migrate project {project_name}: {e}")
        raise

async def main():
    """Main migration function"""
    # Get projects directory
    projects_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "GrantRAG", "projects_data")
    
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