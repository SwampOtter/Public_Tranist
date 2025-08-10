--Ridership includes Passenger Miles (Traveled) which is the cumulative sum of the distances
--traveled by each passenger
--The number of passengers who board public transportation vehicles. Passengers are counted
--each time they board vehicles no matter how many vehicles they use to travel from their
-- origin to their destination.

-- Drop any old versions
DROP TABLE IF EXISTS ridership;
DROP TABLE IF EXISTS ridership_unpivoted;

-- Step 1: Make a wide table with just agency_id + date columns
-- In Postgres, you can't select COLUMNS() dynamically, so either:
--   A) Manually list them, or
--   B) Just pull all columns now and filter in the unpivot step
-- Here we'll just keep all cols, we'll filter later.
CREATE TABLE ridership AS
SELECT m.*, m."NTD ID"::int AS agency_id
FROM public_transit_master m;

-- Step 2: Unpivot wide -> long using JSONB
CREATE TABLE ridership_unpivoted AS
WITH kv AS (SELECT r.agency_id,
                   e.key,
                   e.value
            FROM ridership r
                     CROSS JOIN LATERAL jsonb_each(to_jsonb(r)) AS e(key, value)
            -- Keep only the date-like columns such as '1/2022' or '11/2022'
            WHERE e.key ~ '^[0-9]{1,2}/[0-9]{4}$')
SELECT agency_id,
       split_part(key, '/', 1)::int                                                          AS month,
       split_part(key, '/', 2)::int                                                          AS year,
       NULLIF(regexp_replace(COALESCE(value #>> '{}', ''), '[^0-9\-]', '', 'g'), '')::bigint AS rider
FROM kv;

CREATE INDEX IF NOT EXISTS ridership_unpivoted_agency_year_month_idx
    ON ridership_unpivoted (agency_id, year, month);