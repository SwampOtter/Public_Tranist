CREATE TABLE costs_and_trips AS
SELECT a.agency_id,
       NULLIF(regexp_replace(m."Avg Trip Length FY"::text, '[^0-9.+-]', '', 'g'),
              '')::numeric(10, 2)                                                                        AS avg_trip_length_fy,
       NULLIF(regexp_replace(m."Fares FY"::text, '[^0-9.+-]', '', 'g'), '')::numeric(14, 2)              AS fares_fy,
       NULLIF(regexp_replace(m."Operating Expenses FY"::text, '[^0-9.+-]', '', 'g'), '')::numeric(14, 2) AS ops_exps_fy,
       NULLIF(regexp_replace(m."Avg Cost Per Trip FY"::text, '[^0-9.+-]', '', 'g'),
              '')::numeric(10, 2)                                                                        AS avg_cost_per_trip_fy,
       NULLIF(regexp_replace(m."Avg Fares Per Trip FY"::text, '[^0-9.+-]', '', 'g'),
              '')::numeric(10, 2)                                                                        AS avg_fares_per_trip_fy,
       NULLIF(regexp_replace(m."Passenger Miles FY"::text, '[^0-9+-]', '', 'g'),
              '')::bigint                                                                                AS rider_miles_fy
FROM public_transit_master m
         JOIN agencies a
              ON a.agency_id = m."NTD ID"::integer;

ALTER TABLE costs_and_trips
    ADD CONSTRAINT costs_and_trips_agency_id_fkey
        FOREIGN KEY (agency_id) REFERENCES agencies (agency_id);

DROP VIEW IF EXISTS costs_and_trips_metrics;
CREATE VIEW costs_and_trips_metrics AS
SELECT c.*,
       --Calculated values
       (c.fares_fy / NULLIF(c.ops_exps_fy, 0))                AS cost_recovery_ratio,
       (c.fares_fy / NULLIF(c.rider_miles_fy::numeric, 0))    AS fare_per_mile,
       (c.ops_exps_fy / NULLIF(c.rider_miles_fy::numeric, 0)) AS cost_per_mile,
       (c.avg_cost_per_trip_fy - c.avg_fares_per_trip_fy)     AS avg_net_cost_per_trip,
       -- Presentation-friendly formatted versions
       to_char(c.fares_fy, 'FM$999,999,999,990.00')           AS fares_fy_fmt,
       to_char(c.ops_exps_fy, 'FM$999,999,999,990.00')        AS ops_exps_fy_fmt,
       to_char(c.avg_cost_per_trip_fy, 'FM$999,999,990.00')   AS avg_cost_per_trip_fy_fmt,
       to_char(c.avg_fares_per_trip_fy, 'FM$999,999,990.00')  AS avg_fares_per_trip_fy_fmt
FROM costs_and_trips c;
