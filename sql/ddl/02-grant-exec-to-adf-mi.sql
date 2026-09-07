-- 02-grant-exec-to-adf-mi.sql
-- Replace [adf_mi_user] with the database user mapped to ADF Managed Identity
-- Grant minimal permissions: SELECT on Metadata and TransformDefinitions, EXECUTE on vetted procedures
GRANT SELECT ON dbo.Metadata TO [adf_mi_user];
GRANT SELECT ON dbo.TransformDefinitions TO [adf_mi_user];
GRANT EXECUTE ON SCHEMA :: dbo TO [adf_mi_user]; -- Prefer granting EXECUTE only on specific procs in production
