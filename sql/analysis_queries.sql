-- Cac cau truy van phan tich tren bang employee da lam sach (PostgreSQL 17).
-- Moi cau tra loi 1 cau hoi: nhom nao co ti le muon doi viec (target = 1) cao.

\c employee_analytics

-- Q0. Ti le muon doi viec chung
SELECT
    COUNT(*)                                   AS total_candidates,
    SUM(target)                                AS looking_for_change,
    ROUND(100.0 * AVG(target), 2)              AS change_rate_pct
FROM employee;

-- Q1. Ti le doi viec theo trinh do hoc van
SELECT
    education_level,
    COUNT(*)                       AS n,
    ROUND(100.0 * AVG(target), 2)  AS change_rate_pct
FROM employee
WHERE education_level IS NOT NULL
GROUP BY education_level
ORDER BY change_rate_pct DESC;

-- Q2. Ti le doi viec theo viec co kinh nghiem lien quan hay khong
SELECT
    relevent_experience,
    COUNT(*)                       AS n,
    ROUND(100.0 * AVG(target), 2)  AS change_rate_pct
FROM employee
GROUP BY relevent_experience
ORDER BY change_rate_pct DESC;

-- Q3. Ti le doi viec theo so nam kinh nghiem (chia khoang)
--     Xem nguoi moi di lam co hay nhay viec khong.
SELECT
    CASE
        WHEN experience_years IS NULL      THEN 'Unknown'
        WHEN experience_years <= 2         THEN '0-2 yrs'
        WHEN experience_years <= 5         THEN '3-5 yrs'
        WHEN experience_years <= 10        THEN '6-10 yrs'
        WHEN experience_years <= 20        THEN '11-20 yrs'
        ELSE '20+ yrs'
    END                            AS experience_band,
    COUNT(*)                       AS n,
    ROUND(100.0 * AVG(target), 2)  AS change_rate_pct
FROM employee
GROUP BY experience_band
ORDER BY change_rate_pct DESC;

-- Q4. Chi so phat trien thanh pho (CDI) anh huong the nao
--     Xem nguoi o thanh pho kem phat trien co hay muon di hon khong.
SELECT
    CASE
        WHEN city_development_index >= 0.90 THEN 'High (>=0.90)'
        WHEN city_development_index >= 0.80 THEN 'Medium (0.80-0.90)'
        WHEN city_development_index >= 0.70 THEN 'Low (0.70-0.80)'
        ELSE 'Very low (<0.70)'
    END                            AS city_dev_band,
    COUNT(*)                       AS n,
    ROUND(AVG(city_development_index), 3) AS avg_cdi,
    ROUND(100.0 * AVG(target), 2)  AS change_rate_pct
FROM employee
GROUP BY city_dev_band
ORDER BY change_rate_pct DESC;

-- Q5. Top 10 thanh pho co ti le doi viec cao nhat (lay cac tp >= 100 nguoi cho dang tin)
SELECT
    city,
    COUNT(*)                       AS n,
    ROUND(AVG(city_development_index), 3) AS cdi,
    ROUND(100.0 * AVG(target), 2)  AS change_rate_pct
FROM employee
GROUP BY city, city_development_index
HAVING COUNT(*) >= 100
ORDER BY change_rate_pct DESC
LIMIT 10;

-- Q6. Ti le doi viec theo loai cong ty dang lam
SELECT
    COALESCE(company_type, 'Unknown') AS company_type,
    COUNT(*)                          AS n,
    ROUND(100.0 * AVG(target), 2)     AS change_rate_pct
FROM employee
GROUP BY company_type
ORDER BY change_rate_pct DESC;

-- Q7. Ti le doi viec theo quy mo cong ty
--     Sap xep theo thu tu quy mo (array_position) chu khong theo bang chu cai.
SELECT
    COALESCE(company_size, 'Unknown') AS company_size,
    COUNT(*)                          AS n,
    ROUND(100.0 * AVG(target), 2)     AS change_rate_pct
FROM employee
GROUP BY company_size
ORDER BY array_position(
    ARRAY['<10', '10-49', '50-99', '100-500', '500-999',
          '1000-4999', '5000-9999', '10000+', NULL],
    company_size);

-- Q8. Ti le doi viec theo tinh trang dang di hoc
--     Xem nguoi dang di hoc co hay nhay viec hon khong.
SELECT
    COALESCE(enrolled_university, 'Unknown') AS enrolled_university,
    COUNT(*)                                 AS n,
    ROUND(100.0 * AVG(target), 2)            AS change_rate_pct
FROM employee
GROUP BY enrolled_university
ORDER BY change_rate_pct DESC;

-- Q9. Ti le doi viec theo thoi gian tu lan doi viec gan nhat
SELECT
    CASE
        WHEN last_new_job_years IS NULL THEN 'Unknown'
        WHEN last_new_job_years = 0     THEN 'Never / new'
        WHEN last_new_job_years <= 2    THEN '1-2 yrs'
        WHEN last_new_job_years <= 4    THEN '3-4 yrs'
        ELSE '4+ yrs'
    END                            AS tenure_band,
    COUNT(*)                       AS n,
    ROUND(100.0 * AVG(target), 2)  AS change_rate_pct
FROM employee
GROUP BY tenure_band
ORDER BY change_rate_pct DESC;

-- Q10. Ket hop trinh do hoc van x kinh nghiem lien quan
--      Dung de tim nhom can uu tien giu chan nhat cho bao cao.
SELECT
    education_level,
    relevent_experience,
    COUNT(*)                       AS n,
    ROUND(100.0 * AVG(target), 2)  AS change_rate_pct
FROM employee
WHERE education_level IS NOT NULL
GROUP BY education_level, relevent_experience
HAVING COUNT(*) >= 50
ORDER BY change_rate_pct DESC;

-- Q11. Ti le doi viec theo so gio dao tao da hoc
--      Xem nguoi hoc it gio co hay nghi hon khong.
SELECT
    CASE
        WHEN training_hours < 25  THEN '0-24 h'
        WHEN training_hours < 50  THEN '25-49 h'
        WHEN training_hours < 100 THEN '50-99 h'
        ELSE '100+ h'
    END                            AS training_band,
    COUNT(*)                       AS n,
    ROUND(AVG(training_hours), 1)  AS avg_hours,
    ROUND(100.0 * AVG(target), 2)  AS change_rate_pct
FROM employee
GROUP BY training_band
ORDER BY change_rate_pct DESC;
