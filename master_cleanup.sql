UPDATE public_transit_master
SET "HQ City"  = UPPER(TRIM("HQ City")),
    "HQ State" = UPPER(TRIM("HQ State"))
WHERE "HQ City" IS NOT NULL
   OR "HQ State" IS NOT NULL;

VACUUM FULL ANALYZE public_transit_master;

WITH text_cols AS (SELECT column_name
                   FROM information_schema.columns
                   WHERE table_schema = 'public'
                     AND table_name = 'public_transit_master'
                     AND data_type IN ('text', 'character varying', 'character')),
     flat AS (SELECT j.key   AS column_name,
                     j.value AS val
              FROM public.public_transit_master t
                       CROSS JOIN LATERAL jsonb_each_text(to_jsonb(t)) AS j(key, value)
                       JOIN text_cols tc ON tc.column_name = j.key
              WHERE j.value IS NOT NULL)
SELECT column_name,
       COUNT(*) FILTER (
           WHERE val !~ '^\s*[-+]?\d+(\.\d+)?\s*$'
           )    AS bad_rows,
       COUNT(*) AS total_checked
FROM flat
GROUP BY column_name
HAVING COUNT(*) FILTER (
    WHERE val !~ '^\s*[-+]?\d+(\.\d+)?\s*$'
    ) > 0
ORDER BY bad_rows DESC;