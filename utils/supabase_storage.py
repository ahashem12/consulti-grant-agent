import os
from typing import Dict, List, Any, Optional, BinaryIO
from datetime import datetime
import io
import json
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

class SupabaseStorage:
    def __init__(self):
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        
        if not supabase_url or not supabase_key:
            raise ValueError("Please set SUPABASE_URL and SUPABASE_KEY in .env file")
            
        self.supabase: Client = create_client(supabase_url, supabase_key)
        self.bucket_name = "project-data"
        
    async def upload_file(self, file_path: str, project_name: str, file_content: BinaryIO) -> Dict[str, Any]:
        """Upload a file to Supabase Storage"""
        try:
            # Create path in format: project-name/filename
            storage_path = f"{project_name}/{os.path.basename(file_path)}"
            
            # Upload file
            response = self.supabase.storage.from_(self.bucket_name).upload(
                storage_path,
                file_content,
                {"content-type": "application/octet-stream"}
            )
            
            return {
                "success": True,
                "path": storage_path,
                "metadata": response
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
            
    async def download_file(self, project_name: str, file_name: str) -> Optional[bytes]:
        """Download a file from Supabase Storage"""
        try:
            storage_path = f"{project_name}/{file_name}"
            response = self.supabase.storage.from_(self.bucket_name).download(storage_path)
            return response
        except Exception as e:
            print(f"Error downloading file {storage_path}: {e}")
            return None
            
    async def list_files(self, project_name: str) -> List[str]:
        """List all files in a project directory"""
        try:
            response = self.supabase.storage.from_(self.bucket_name).list(project_name)
            return [item["name"] for item in response]
        except Exception as e:
            print(f"Error listing files for project {project_name}: {e}")
            return []
            
    async def delete_file(self, project_name: str, file_name: str) -> bool:
        """Delete a file from Supabase Storage"""
        try:
            storage_path = f"{project_name}/{file_name}"
            self.supabase.storage.from_(self.bucket_name).remove([storage_path])
            return True
        except Exception as e:
            print(f"Error deleting file {storage_path}: {e}")
            return False 