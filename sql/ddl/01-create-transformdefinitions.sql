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

-- Example insert (only via vetted CI/PR):
-- INSERT INTO dbo.TransformDefinitions (TransformId, Description, ExecutionType, ExecutionTarget) VALUES ('TransformA','Example SP-based transform','StoredProc','dbo.usp_TransformA');
