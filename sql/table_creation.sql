-- Tao bang (PostgreSQL 17)
-- Y tuong: nap file csv tho vao bang stg_employee (de het kieu text cho khoi loi),
-- xong moi lam sach va do sang bang employee (xem file data_cleaning.sql).
-- Chay:  psql -U postgres -d employee_analytics -f sql/table_creation.sql

\c employee_analytics

-- Bang tho: de het kieu text de file csv (co o trong, co "Oct-49", ">20"...) nap vao
-- ma khong bi loi kieu du lieu. Lam sach sau.
DROP TABLE IF EXISTS stg_employee;

CREATE TABLE stg_employee (
    enrollee_id            TEXT,
    city                   TEXT,
    city_development_index TEXT,
    gender                 TEXT,
    relevent_experience    TEXT,
    enrolled_university    TEXT,
    education_level        TEXT,
    major_discipline       TEXT,
    experience             TEXT,
    company_size           TEXT,
    company_type           TEXT,
    last_new_job           TEXT,
    training_hours         TEXT,
    target                 TEXT
);

-- Nap du lieu tho bang lenh \copy cua psql (chay ben may client, khong can quyen file cua server).
-- Nho mo psql tu thu muc goc project thi duong dan ben duoi moi dung.
--   \copy stg_employee FROM 'dataset/aug_train.csv' WITH (FORMAT csv, HEADER true)
-- Neu dung pgAdmin thi thay bang COPY voi duong dan tuyet doi:
--   COPY stg_employee FROM 'D:/.../dataset/aug_train.csv' WITH (FORMAT csv, HEADER true);

-- Bang sach: da dung kieu du lieu, dung de phan tich. Do du lieu vao o file data_cleaning.sql.
-- experience / last_new_job luu thanh so nam (">20"->21, "<1"->0, "never"->0, ">4"->5).
DROP TABLE IF EXISTS employee;

CREATE TABLE employee (
    enrollee_id            INTEGER       PRIMARY KEY,
    city                   VARCHAR(20)   NOT NULL,
    city_development_index NUMERIC(4, 3) NOT NULL,
    gender                 VARCHAR(20),                  -- thieu ~23%
    relevent_experience    VARCHAR(40)   NOT NULL,
    enrolled_university    VARCHAR(40),
    education_level        VARCHAR(40),
    major_discipline       VARCHAR(40),
    experience_years       INTEGER,                      -- tach tu cot "experience"
    company_size           VARCHAR(20),                  -- da sua "Oct-49" -> "10-49"
    company_type           VARCHAR(40),
    last_new_job_years     INTEGER,                      -- tach tu cot "last_new_job"
    training_hours         INTEGER       NOT NULL,
    target                 SMALLINT      NOT NULL        -- 1 = doi viec, 0 = o lai
);

-- Tao index cho may cot hay loc/nhom (Postgres tao rieng tung cau).
CREATE INDEX idx_employee_city         ON employee (city);
CREATE INDEX idx_employee_target       ON employee (target);
CREATE INDEX idx_employee_education    ON employee (education_level);
CREATE INDEX idx_employee_company_size ON employee (company_size);
