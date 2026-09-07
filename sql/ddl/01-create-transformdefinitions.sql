-- 01-create-transformdefinitions.sql
CREATE TABLE dbo.TransformDefinitions (
  TransformId NVARCHAR(100) PRIMARY KEY,
  Description NVARCHAR(400) NULL,
  ExecutionType NVARCHAR(20) NOT NULL, -- 'StoredProc' | 'DataFlow' | 'Copy'
  ExecutionTarget NVARCHAR(200) NOT NULL, -- stored procedure name or dataflow name
  AllowedParameters NVARCHAR(MAX) NULL, -- optional JSON schema or param list
  CreatedBy NVARCHAR(100) NULL,
  CreatedAt DATETIME2 DEFAULT SYSUTCDATETIME()
);

-- Example inserts (these should be applied via a vetted deployment process / PR):
INSERT INTO dbo.TransformDefinitions (TransformId, Description, ExecutionType, ExecutionTarget, AllowedParameters)
VALUES
('TransformA','SP-based example transform that reads from source and writes to sink','StoredProc','dbo.usp_TransformA', '{"params":["srcPath","sinkPath"]}'),
('TransformB','DataFlow-based example transform','DataFlow','DataFlow_TransformB', '{"params":["srcPath","sinkPath"]}');

-- Note: In production, do not allow direct inserts to this table by non-privileged users. Changes to TransformDefinitions should be managed via CI/PR and database migration scripts.
