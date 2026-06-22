-- Tao database cho project (PostgreSQL 17)
-- Chay theo thu tu: database_creation -> table_creation -> data_cleaning -> analysis_queries
-- Cach chay:  psql -U postgres -f sql/database_creation.sql

-- Postgres khong co "CREATE DATABASE IF NOT EXISTS" nen lam kieu nay:
-- chi tao khi database chua ton tai (\gexec se chay cau lenh do SELECT sinh ra)
SELECT 'CREATE DATABASE employee_analytics ENCODING ''UTF8'' TEMPLATE template0'
WHERE NOT EXISTS (
    SELECT FROM pg_database WHERE datname = 'employee_analytics'
)\gexec

-- chuyen sang database vua tao
\c employee_analytics

-- Tao them user chi co quyen doc (cho phan dashboard/BI) - khong bat buoc.
-- Bo comment di neu can dung.
-- DO $$
-- BEGIN
--     IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'analytics_ro') THEN
--         CREATE ROLE analytics_ro LOGIN PASSWORD 'change_me';
--     END IF;
-- END $$;
--
-- GRANT CONNECT ON DATABASE employee_analytics TO analytics_ro;
-- GRANT USAGE ON SCHEMA public TO analytics_ro;
-- GRANT SELECT ON ALL TABLES IN SCHEMA public TO analytics_ro;
-- ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO analytics_ro;
