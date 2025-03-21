import os
from typing import Dict, List, Any, Optional
from datetime import datetime
from config.supabase import supabase

class ProjectStorage:
    def __init__(self):
        """Initialize the project storage system"""
        self.project_id = None
        self.storage_bucket = "project-files"  # Name of the storage bucket
        self.supabase = supabase  # Expose supabase client
        print(f"[INFO] Using storage bucket: {self.storage_bucket}")

    async def create_project(self, project_name: str, metadata: Dict[str, Any] = None) -> str:
        """
        Create a new project in Supabase
        
        Args:
            project_name: Name of the project
            metadata: Optional project metadata
            
        Returns:
            Project ID
        """
        try:
            result = self.supabase.table('projects').insert({
                'name': project_name,
                'metadata': metadata or {}
            }).execute()
            
            self.project_id = result.data[0]['id']
            return self.project_id
            
        except Exception as e:
            print(f"[ERROR] Failed to create project: {e}")
            raise

    async def get_project(self, project_name: str) -> Optional[Dict[str, Any]]:
        """
        Get project details by name
        
        Args:
            project_name: Name of the project
            
        Returns:
            Project details or None if not found
        """
        try:
            result = self.supabase.table('projects').select('*').eq('name', project_name).execute()
            if result.data:
                self.project_id = result.data[0]['id']
                return result.data[0]
            return None
            
        except Exception as e:
            print(f"[ERROR] Failed to get project: {e}")
            return None

    async def create_folder(self, folder_path: str, parent_folder_id: Optional[str] = None) -> str:
        """
        Create a folder in the project
        
        Args:
            folder_path: Path to the folder
            parent_folder_id: Optional parent folder ID
            
        Returns:
            Folder ID
        """
        try:
            folder_name = os.path.basename(folder_path)
            result = self.supabase.table('project_folders').insert({
                'project_id': self.project_id,
                'folder_name': folder_name,
                'folder_path': folder_path,
                'parent_folder_id': parent_folder_id
            }).execute()
            
            return result.data[0]['id']
            
        except Exception as e:
            print(f"[ERROR] Failed to create folder: {e}")
            raise

    async def get_folder(self, folder_path: str) -> Optional[Dict[str, Any]]:
        """
        Get folder details by path
        
        Args:
            folder_path: Path to the folder
            
        Returns:
            Folder details or None if not found
        """
        try:
            result = self.supabase.table('project_folders').select('*').eq('project_id', self.project_id).eq('folder_path', folder_path).execute()
            return result.data[0] if result.data else None
            
        except Exception as e:
            print(f"[ERROR] Failed to get folder: {e}")
            return None

    async def save_file(self, file_path: str, local_file_path: str, metadata: Dict[str, Any] = None) -> str:
        """
        Save a file to Supabase Storage and create a database record
        
        Args:
            file_path: Path to the file in the project
            local_file_path: Path to the local file to upload
            metadata: Optional file metadata
            
        Returns:
            File ID
        """
        try:
            file_name = os.path.basename(file_path)
            file_type = os.path.splitext(file_name)[1].lower()
            file_size = os.path.getsize(local_file_path)
            
            # Upload file to Supabase Storage
            storage_path = f"{self.project_id}/{file_path}"
            with open(local_file_path, 'rb') as f:
                self.supabase.storage.from_(self.storage_bucket).upload(storage_path, f)
            
            # Create database record
            result = self.supabase.table('project_files').insert({
                'project_id': self.project_id,
                'file_name': file_name,
                'file_path': file_path,
                'file_type': file_type,
                'file_size': file_size,
                'storage_path': storage_path,
                'metadata': metadata or {}
            }).execute()
            
            return result.data[0]['id']
            
        except Exception as e:
            print(f"[ERROR] Failed to save file: {e}")
            raise

    async def get_file(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Get file details and download URL
        
        Args:
            file_path: Path to the file
            
        Returns:
            File details with download URL or None if not found
        """
        try:
            result = self.supabase.table('project_files').select('*').eq('project_id', self.project_id).eq('file_path', file_path).execute()
            if not result.data:
                return None
                
            file_data = result.data[0]
            
            # Get download URL from storage
            download_url = self.supabase.storage.from_(self.storage_bucket).create_signed_url(
                file_data['storage_path'],
                3600  # URL valid for 1 hour
            )
            
            file_data['download_url'] = download_url
            return file_data
            
        except Exception as e:
            print(f"[ERROR] Failed to get file: {e}")
            return None

    async def download_file(self, file_path: str, local_path: str) -> bool:
        """
        Download a file from Supabase Storage
        
        Args:
            file_path: Path to the file in the project
            local_path: Local path to save the file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            result = self.supabase.table('project_files').select('storage_path').eq('project_id', self.project_id).eq('file_path', file_path).execute()
            if not result.data:
                return False
                
            storage_path = result.data[0]['storage_path']
            
            # Download file from storage
            with open(local_path, 'wb') as f:
                data = self.supabase.storage.from_(self.storage_bucket).download(storage_path)
                f.write(data)
            
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to download file: {e}")
            return False

    async def get_project_structure(self) -> List[Dict[str, Any]]:
        """
        Get the complete project structure
        
        Returns:
            List of files and folders with their details
        """
        try:
            result = self.supabase.rpc('get_project_structure', {'project_id': self.project_id}).execute()
            return result.data
            
        except Exception as e:
            print(f"[ERROR] Failed to get project structure: {e}")
            return []

    async def delete_file(self, file_path: str) -> bool:
        """
        Delete a file from the project
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get storage path
            result = self.supabase.table('project_files').select('storage_path').eq('project_id', self.project_id).eq('file_path', file_path).execute()
            if result.data:
                storage_path = result.data[0]['storage_path']
                # Delete from storage
                self.supabase.storage.from_(self.storage_bucket).remove([storage_path])
            
            # Delete database record
            self.supabase.table('project_files').delete().eq('project_id', self.project_id).eq('file_path', file_path).execute()
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to delete file: {e}")
            return False

    async def delete_folder(self, folder_path: str) -> bool:
        """
        Delete a folder and all its contents from the project
        
        Args:
            folder_path: Path to the folder
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get all files in the folder
            result = self.supabase.table('project_files').select('storage_path').eq('project_id', self.project_id).like('file_path', f"{folder_path}/%").execute()
            
            # Delete files from storage
            if result.data:
                storage_paths = [file['storage_path'] for file in result.data]
                self.supabase.storage.from_(self.storage_bucket).remove(storage_paths)
            
            # Delete database records
            self.supabase.table('project_files').delete().eq('project_id', self.project_id).like('file_path', f"{folder_path}/%").execute()
            self.supabase.table('project_folders').delete().eq('project_id', self.project_id).eq('folder_path', folder_path).execute()
            
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to delete folder: {e}")
            return False

    async def update_file(self, file_path: str, content: str, metadata: Dict[str, Any] = None) -> bool:
        """
        Update a file's content and metadata
        
        Args:
            file_path: Path to the file
            content: New file content
            metadata: Optional new metadata
            
        Returns:
            True if successful, False otherwise
        """
        try:
            file_size = len(content.encode('utf-8'))
            update_data = {
                'content': content,
                'file_size': file_size
            }
            if metadata is not None:
                update_data['metadata'] = metadata
                
            self.supabase.table('project_files').update(update_data).eq('project_id', self.project_id).eq('file_path', file_path).execute()
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to update file: {e}")
            return False

    async def list_bucket_files(self, prefix: str = "") -> List[Dict[str, Any]]:
        """
        List all files in the storage bucket recursively, optionally filtered by prefix
        
        Args:
            prefix: Optional prefix to filter files (e.g. project ID)
            
        Returns:
            List of file information
        """
        try:
            all_files = []
            
            # Get initial list of files/folders
            items = self.supabase.storage.from_(self.storage_bucket).list(prefix)
            print(f"[DEBUG] Listing contents with prefix '{prefix}': {[item['name'] for item in items]}")
            
            for item in items:
                item_name = item['name']
                # Construct the full path by combining the prefix with the item name
                full_path = f"{prefix}/{item_name}" if prefix else item_name
                
                # If the item name contains a period, it's a file
                if '.' in os.path.basename(item_name):
                    print(f"[DEBUG] Found file: {full_path}")
                    # Update the item's name to include the full path
                    item['name'] = full_path
                    all_files.append(item)
                else:
                    # It's a directory, recursively list its contents using the full path as the new prefix
                    print(f"[DEBUG] Found directory: {full_path}")
                    subfolder_files = await self.list_bucket_files(full_path)
                    all_files.extend(subfolder_files)
            
            return all_files
            
        except Exception as e:
            print(f"[ERROR] Failed to list bucket files: {e}")
            return []

    async def get_bucket_file(self, file_path: str) -> Optional[bytes]:
        """
        Get file content directly from storage bucket
        
        Args:
            file_path: Path to the file in the bucket
            
        Returns:
            File content as bytes if successful, None otherwise
        """
        try:
            data = self.supabase.storage.from_(self.storage_bucket).download(file_path)
            return data
        except Exception as e:
            print(f"[ERROR] Failed to get bucket file {file_path}: {e}")
            return None 