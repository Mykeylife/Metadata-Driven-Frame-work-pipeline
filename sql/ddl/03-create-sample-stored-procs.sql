-- 03-create-sample-stored-procs.sql
-- Sample stored procedures for TransformDefinitions ExecutionType = 'StoredProc'.
-- These are templates. Review and adapt to your environment before deploying.

CREATE TABLE IF NOT EXISTS dbo.TransformAudit (
  AuditId INT IDENTITY(1,1) PRIMARY KEY,
  TransformId NVARCHAR(100),
  PipelineId NVARCHAR(100),
  ExecutedAt DATETIME2 DEFAULT SYSUTCDATETIME(),
  Details NVARCHAR(MAX)
);

GO

CREATE PROCEDURE dbo.usp_TransformA
  @srcPath NVARCHAR(1000),
  @sinkPath NVARCHAR(1000),
  @pipelineId NVARCHAR(100) = NULL
AS
BEGIN
  SET NOCOUNT ON;
  -- Example safe operation: perform parameterized insert/select or call into external ETL
  -- IMPORTANT: Do NOT build SQL by concatenating @srcPath/@sinkPath into statements. Use parameters and validated objects.

  -- This example assumes source and sink are accessible tables; replace with your safe logic.
  BEGIN TRY
    -- Placeholder: record that the transform ran
    INSERT INTO dbo.TransformAudit (TransformId, PipelineId, Details)
    VALUES ('TransformA', @pipelineId, CONCAT('src=', @srcPath, ';sink=', @sinkPath));

    -- Actual transform logic should be implemented here with parameterized statements
  END TRY
  BEGIN CATCH
    DECLARE @err NVARCHAR(4000) = ERROR_MESSAGE();
    INSERT INTO dbo.TransformAudit (TransformId, PipelineId, Details)
    VALUES ('TransformA', @pipelineId, CONCAT('ERROR: ', @err));
    THROW;
  END CATCH
END

GO

-- If you have TransformB implemented as a stored procedure (rather than a Data Flow), add it here.
