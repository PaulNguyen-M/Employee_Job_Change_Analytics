-- Lam sach du lieu: doc tu bang tho stg_employee, xu ly roi do sang bang employee.
-- Logic lam giong het ben Python (file ml/data_preprocessing.py) cho dong bo.
--
-- Cac buoc lam sach:
--   1. company_size "Oct-49" -> "10-49" (loi excel tu doi thanh ngay thang)
--   2. experience ">20"->21, "<1"->0, con lai -> so
--   3. last_new_job "never"->0, ">4"->5, con lai -> so
--   4. o trong / khoang trang -> NULL
--   5. bo dong trung enrollee_id
-- Luu y: cot so bi thieu thi de NULL luon (khong dien), de con thay du lieu thieu bao nhieu.
-- Ben Python moi dien gia tri thieu (va chi dien tren tap train).

\c employee_analytics

TRUNCATE TABLE employee;

INSERT INTO employee (
    enrollee_id, city, city_development_index, gender, relevent_experience,
    enrolled_university, education_level, major_discipline, experience_years,
    company_size, company_type, last_new_job_years, training_hours, target
)
SELECT DISTINCT ON (s.enrollee_id::INTEGER)
    s.enrollee_id::INTEGER,
    s.city,
    s.city_development_index::NUMERIC(4, 3),
    NULLIF(TRIM(s.gender), ''),
    TRIM(s.relevent_experience),
    NULLIF(TRIM(s.enrolled_university), ''),
    NULLIF(TRIM(s.education_level), ''),
    NULLIF(TRIM(s.major_discipline), ''),
    -- experience: ">20" -> 21, "<1" -> 0, o trong -> NULL, con lai -> so
    CASE
        WHEN TRIM(s.experience) = '>20' THEN 21
        WHEN TRIM(s.experience) = '<1'  THEN 0
        WHEN TRIM(s.experience) = ''    THEN NULL
        ELSE TRIM(s.experience)::INTEGER
    END,
    -- company_size: sua loi "Oct-49", o trong -> NULL
    CASE
        WHEN TRIM(s.company_size) = 'Oct-49' THEN '10-49'
        WHEN TRIM(s.company_size) = ''       THEN NULL
        ELSE TRIM(s.company_size)
    END,
    NULLIF(TRIM(s.company_type), ''),
    -- last_new_job: "never" -> 0, ">4" -> 5, o trong -> NULL, con lai -> so
    CASE
        WHEN TRIM(s.last_new_job) = 'never' THEN 0
        WHEN TRIM(s.last_new_job) = '>4'    THEN 5
        WHEN TRIM(s.last_new_job) = ''      THEN NULL
        ELSE TRIM(s.last_new_job)::INTEGER
    END,
    s.training_hours::INTEGER,
    s.target::SMALLINT
FROM stg_employee s
WHERE s.enrollee_id IS NOT NULL AND TRIM(s.enrollee_id) <> ''
ORDER BY s.enrollee_id::INTEGER;   -- DISTINCT ON giu lai 1 dong cho moi id

-- Kiem tra lai cho chac an sau khi nap.
-- So dong (phai ra 19158):
SELECT COUNT(*) AS rows_loaded FROM employee;

-- Kiem tra da het loi "Oct-49" chua (phai ra 0):
SELECT COUNT(*) AS bad_company_size FROM employee WHERE company_size = 'Oct-49';

-- Dem so o bi thieu tung cot (Postgres dung FILTER de dem co dieu kien):
SELECT
    COUNT(*) FILTER (WHERE gender IS NULL)           AS null_gender,
    COUNT(*) FILTER (WHERE company_size IS NULL)     AS null_company_size,
    COUNT(*) FILTER (WHERE company_type IS NULL)     AS null_company_type,
    COUNT(*) FILTER (WHERE major_discipline IS NULL) AS null_major_discipline,
    COUNT(*) FILTER (WHERE experience_years IS NULL) AS null_experience
FROM employee;
