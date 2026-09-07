-- 00-create-metadata-table.sql
-- Create Metadata table. Requires TransformDefinitions to exist first if adding FK.
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

-- Add FK to enforce TransformId is valid (run AFTER TransformDefinitions exists):
ALTER TABLE dbo.Metadata
ADD CONSTRAINT FK_Metadata_Transform FOREIGN KEY (TransformId)
REFERENCES dbo.TransformDefinitions(TransformId);

-- Example metadata insert (use vetted insert or UI; avoid uncontrolled edits):
-- INSERT INTO dbo.Metadata (PipelineId, PipelineName, SourceType, SourcePath, SinkType, SinkPath, TransformId, PipelineParameters)
-- VALUES ('pipeline_example_01','Example pipeline','Blob','container/path/file.csv','Sql','dbo.TargetTable','TransformA','{"param1":"value1"}');
