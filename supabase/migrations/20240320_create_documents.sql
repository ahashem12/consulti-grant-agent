-- Enable the pgvector extension to work with embedding vectors
create extension if not exists vector;

-- Create a table for storing document chunks with their embeddings
create table if not exists documents (
    id bigint primary key generated always as identity,
    project_name text not null,
    content text not null,
    embedding vector(1536), -- OpenAI text-embedding-3-small uses 1536 dimensions
    metadata jsonb not null default '{}',
    created_at timestamp with time zone default timezone('utc'::text, now()) not null,
    updated_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Create an index for the project_name for faster filtering
create index if not exists idx_documents_project_name on documents(project_name);

-- Create a vector index for similarity search
create index if not exists idx_documents_embedding on documents using ivfflat (embedding vector_cosine_ops)
with (lists = 100);

-- Function to match similar documents
create or replace function match_documents(
    query_embedding vector(1536),
    match_count int default 5,
    project_name text default null
)
returns table (
    id bigint,
    content text,
    metadata jsonb,
    similarity float
)
language plpgsql
as $$
begin
    return query
    select
        d.id,
        d.content,
        d.metadata,
        1 - (d.embedding <=> query_embedding) as similarity
    from documents d
    where
        case
            when project_name is not null then d.project_name = project_name
            else true
        end
    order by d.embedding <=> query_embedding
    limit match_count;
end;
$$; 