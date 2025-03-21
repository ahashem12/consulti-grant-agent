from typing import List, Dict, Any, Optional
import numpy as np
from openai import OpenAI
from config.supabase import supabase

class SupabaseVectorStore:
    def __init__(self, project_name: str, openai_key: str):
        """
        Initialize the Supabase vector store
        
        Args:
            project_name: Name of the project
            openai_key: OpenAI API key for embeddings
        """
        self.project_name = project_name
        self.client = OpenAI(api_key=openai_key)
        self.collection_id = None
        self._init_collection()

    def _init_collection(self):
        """Initialize or get the collection for this project"""
        try:
            # Try to get existing collection
            result = supabase.table('collections').select('id').eq('name', self.project_name).execute()
            
            if result.data:
                self.collection_id = result.data[0]['id']
            else:
                # Create new collection
                result = supabase.table('collections').insert({
                    'name': self.project_name,
                    'project_name': self.project_name
                }).execute()
                self.collection_id = result.data[0]['id']
                
        except Exception as e:
            print(f"[ERROR] Failed to initialize collection: {e}")
            raise

    def get_embedding(self, text: str) -> List[float]:
        """Get embedding for text using OpenAI"""
        try:
            response = self.client.embeddings.create(
                model="text-embedding-ada-002",
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"[ERROR] Failed to get embedding: {e}")
            raise

    async def add_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """
        Add documents to the vector store
        
        Args:
            documents: List of documents with content and metadata
        """
        try:
            # Get embeddings for all documents
            embeddings = []
            for doc in documents:
                embedding = self.get_embedding(doc['content'])
                embeddings.append(embedding)

            # Prepare data for insertion
            data = []
            for doc, embedding in zip(documents, embeddings):
                data.append({
                    'collection_id': self.collection_id,
                    'chunk_id': doc['id'],
                    'content': doc['content'],
                    'metadata': doc['metadata'],
                    'embedding': embedding
                })

            # Insert documents in batches
            batch_size = 100
            for i in range(0, len(data), batch_size):
                batch = data[i:i + batch_size]
                supabase.table('document_chunks').insert(batch).execute()

            return True

        except Exception as e:
            print(f"[ERROR] Failed to add documents: {e}")
            return False

    async def delete_documents(self, document_ids: List[str]) -> bool:
        """
        Delete documents from the vector store
        
        Args:
            document_ids: List of document IDs to delete
        """
        try:
            supabase.table('document_chunks').delete().eq('collection_id', self.collection_id).in_('chunk_id', document_ids).execute()
            return True
        except Exception as e:
            print(f"[ERROR] Failed to delete documents: {e}")
            return False

    async def query(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """
        Query the vector store for similar documents
        
        Args:
            query: Query text
            n_results: Number of results to return
            
        Returns:
            List of documents with content and metadata
        """
        try:
            # Get query embedding
            query_embedding = self.get_embedding(query)

            # Query using vector similarity
            result = supabase.rpc(
                'match_documents',
                {
                    'query_embedding': query_embedding,
                    'match_count': n_results,
                    'collection_id': self.collection_id
                }
            ).execute()

            # Format results
            documents = []
            for row in result.data:
                documents.append({
                    'content': row['content'],
                    'metadata': row['metadata'],
                    'relevance_score': row['similarity']
                })

            return documents

        except Exception as e:
            print(f"[ERROR] Failed to query documents: {e}")
            return [] 