import os
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import openai
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

class SupabaseVector:
    def __init__(self):
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        openai.api_key = os.getenv("OPENAI_API_KEY")
        
        if not supabase_url or not supabase_key:
            raise ValueError("Please set SUPABASE_URL and SUPABASE_KEY in .env file")
            
        self.supabase: Client = create_client(supabase_url, supabase_key)
        
    async def create_embedding(self, text: str) -> List[float]:
        """Create embedding using OpenAI API"""
        try:
            response = openai.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Error creating embedding: {e}")
            return []
            
    async def insert_document(self, 
                            project_name: str,
                            content: str,
                            metadata: Dict[str, Any]) -> bool:
        """Insert a document into Supabase vector store"""
        try:
            # Create embedding
            embedding = await self.create_embedding(content)
            if not embedding:
                return False
                
            # Insert into vector store
            data = {
                "project_name": project_name,
                "content": content,
                "embedding": embedding,
                "metadata": json.dumps(metadata),
                "created_at": datetime.utcnow().isoformat()
            }
            
            self.supabase.table("documents").insert(data).execute()
            return True
            
        except Exception as e:
            print(f"Error inserting document: {e}")
            return False
            
    async def search_documents(self, 
                             query: str,
                             project_name: Optional[str] = None,
                             limit: int = 5) -> List[Dict[str, Any]]:
        """Search documents using vector similarity"""
        try:
            # Create query embedding
            query_embedding = await self.create_embedding(query)
            if not query_embedding:
                return []
                
            # Construct query
            query_params = {
                "query_embedding": query_embedding,
                "match_count": limit
            }
            
            if project_name:
                query_params["project_name"] = project_name
                
            # Execute similarity search
            rpc_response = self.supabase.rpc(
                "match_documents",
                query_params
            ).execute()
            
            return rpc_response.data
            
        except Exception as e:
            print(f"Error searching documents: {e}")
            return []
            
    async def delete_project_documents(self, project_name: str) -> bool:
        """Delete all documents for a project"""
        try:
            self.supabase.table("documents").delete().eq("project_name", project_name).execute()
            return True
        except Exception as e:
            print(f"Error deleting project documents: {e}")
            return False 