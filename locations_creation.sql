-- Recreate locations from public_transit_master with safe types and casting
DROP TABLE IF EXISTS locations;

CREATE TABLE locations
(
    location_id   SERIAL PRIMARY KEY,
    city          TEXT,
    state         TEXT,
    sa_sq_miles   NUMERIC,
    sa_population NUMERIC
);

-- Note: we explicitly name target columns so location_id auto-populates
WITH src AS (SELECT DISTINCT NULLIF(pmt."HQ City", '')  AS city,
                             NULLIF(pmt."HQ State", '') AS state,
                             REGEXP_REPLACE(TRIM(pmt."Service Area SQ Miles"), '[^0-9.+-]', '',
                                            'g')        AS sa_sq_miles_raw,
                             REGEXP_REPLACE(TRIM(pmt."Service Area Population"), '[^0-9.+-]', '',
                                            'g')        AS sa_population_raw
             FROM public_transit_master AS pmt),
     clean AS (SELECT city,
                      state,
                      NULLIF(sa_sq_miles_raw, '')   AS sa_sq_miles_s,
                      NULLIF(sa_population_raw, '') AS sa_population_s
               FROM src)
INSERT
INTO locations (city, state, sa_sq_miles, sa_population)
SELECT city,
       state,
       CASE WHEN sa_sq_miles_s ~ '^[+-]?[0-9]*\.?[0-9]+$' THEN sa_sq_miles_s::NUMERIC ELSE NULL END     AS sa_sq_miles,
       CASE WHEN sa_population_s ~ '^[+-]?[0-9]*\.?[0-9]+$' THEN sa_population_s::NUMERIC ELSE NULL END AS sa_population
FROM clean
ORDER BY city;



-- Diagnostics to find rows that would not cast to numeric (uncomment to investigate)
-- WITH prep AS (
--   SELECT
--     REGEXP_REPLACE(TRIM(pmt."Service Area SQ Miles"),    '[^0-9.+-]', '', 'g')    AS miles_raw,
--     REGEXP_REPLACE(TRIM(pmt."Service Area Population"), '[^0-9.+-]', '', 'g')    AS pop_raw
--   FROM public_transit_master pmt
-- )
-- SELECT *
-- FROM prep
-- WHERE miles_raw IS NOT NULL AND miles_raw <> '' AND miles_raw !~ '^[+-]?[0-9]*\.?[0-9]+$'
--    OR pop_raw   IS NOT NULL AND pop_raw   <> '' AND pop_raw   !~ '^[+-]?[0-9]*\.?[0-9]+$';
