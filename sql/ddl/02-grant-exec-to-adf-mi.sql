-- 02-grant-exec-to-adf-mi.sql
-- Replace [adf_mi_user] with the database user mapped to ADF Managed Identity
-- Grant minimal permissions: SELECT on Metadata and TransformDefinitions, EXECUTE on vetted procedures
GRANT SELECT ON dbo.Metadata TO [adf_mi_user];
GRANT SELECT ON dbo.TransformDefinitions TO [adf_mi_user];
-- Grant EXECUTE only on approved stored procedures (prefer this to schema-wide EXECUTE)
GRANT EXECUTE ON dbo.usp_TransformA TO [adf_mi_user];
-- If you add more stored procedures, grant EXECUTE on those specific procs as well.
