-- 00-create-metadata-table.sql
CREATE TABLE dbo.Metadata (
  PipelineId NVARCHAR(100) NOT NULL PRIMARY KEY,
  PipelineName NVARCHAR(200) NOT NULL,
  Enabled BIT NOT NULL DEFAULT 1,
  SourceType NVARCHAR(50) NOT NULL,
  SourcePath NVARCHAR(1000) NOT NULL,
  SinkType NVARCHAR(50) NOT NULL,
  SinkPath NVARCHAR(1000) NOT NULL,
  TransformId NVARCHAR(100) NOT NULL,
  PipelineParameters NVARCHAR(MAX) NULL, -- JSON
  Parallelism INT DEFAULT 1,
  Schedule NVARCHAR(200) NULL,
  CreatedAt DATETIME2 DEFAULT SYSUTCDATETIME()
);

-- FK will be added after TransformDefinitions exists
