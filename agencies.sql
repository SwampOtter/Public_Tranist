CREATE TABLE agencies
(
    agency_id INTEGER PRIMARY KEY,
    agency    TEXT NOT NULL,
    city      TEXT,
    state     TEXT
);

INSERT INTO agencies (agency_id, agency, city, state)
SELECT DISTINCT ON (m."NTD ID"::integer)
       m."NTD ID"::integer AS agency_id,
       m."Agency"          AS agency,
       m."HQ City"         AS city,
       m."HQ State"        AS state
FROM public_transit_master m
WHERE m."NTD ID" IS NOT NULL
ORDER BY m."NTD ID"::integer,
         CASE WHEN m."Status" ILIKE 'Active%' THEN 0 ELSE 1 END,
         m."Agency";
