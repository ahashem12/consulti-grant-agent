-- Create projects table
CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Create project_files table
CREATE TABLE IF NOT EXISTS project_files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    file_name TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_type TEXT NOT NULL,
    file_size BIGINT NOT NULL,
    storage_path TEXT NOT NULL,  -- Path in Supabase Storage
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    UNIQUE(project_id, file_path)
);

-- Create project_folders table
CREATE TABLE IF NOT EXISTS project_folders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    folder_name TEXT NOT NULL,
    folder_path TEXT NOT NULL,
    parent_folder_id UUID REFERENCES project_folders(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    UNIQUE(project_id, folder_path)
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_project_files_project_id ON project_files(project_id);
CREATE INDEX IF NOT EXISTS idx_project_folders_project_id ON project_folders(project_id);
CREATE INDEX IF NOT EXISTS idx_project_folders_parent_folder_id ON project_folders(parent_folder_id);

-- Create triggers for updated_at
CREATE TRIGGER update_projects_updated_at
    BEFORE UPDATE ON projects
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_project_files_updated_at
    BEFORE UPDATE ON project_files
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_project_folders_updated_at
    BEFORE UPDATE ON project_folders
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Function to get project structure
CREATE OR REPLACE FUNCTION get_project_structure(project_id uuid)
RETURNS TABLE (
    id uuid,
    name text,
    path text,
    type text,
    size bigint,
    is_folder boolean,
    parent_id uuid,
    created_at timestamptz,
    updated_at timestamptz
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        f.id,
        CASE 
            WHEN f.folder_name IS NOT NULL THEN f.folder_name
            ELSE f.file_name
        END as name,
        CASE 
            WHEN f.folder_path IS NOT NULL THEN f.folder_path
            ELSE f.file_path
        END as path,
        CASE 
            WHEN f.folder_name IS NOT NULL THEN 'folder'
            ELSE f.file_type
        END as type,
        CASE 
            WHEN f.file_size IS NOT NULL THEN f.file_size
            ELSE 0
        END as size,
        f.folder_name IS NOT NULL as is_folder,
        f.parent_folder_id as parent_id,
        f.created_at,
        f.updated_at
    FROM (
        SELECT 
            id,
            file_name,
            file_path,
            file_type,
            file_size,
            NULL as folder_name,
            NULL as folder_path,
            NULL as parent_folder_id,
            created_at,
            updated_at
        FROM project_files
        WHERE project_id = get_project_structure.project_id
        UNION ALL
        SELECT 
            id,
            NULL as file_name,
            NULL as file_path,
            NULL as file_type,
            NULL as file_size,
            folder_name,
            folder_path,
            parent_folder_id,
            created_at,
            updated_at
        FROM project_folders
        WHERE project_id = get_project_structure.project_id
    ) f
    ORDER BY f.path;
END;
$$; 