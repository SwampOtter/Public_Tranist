UPDATE public_transit_master
SET "HQ City"  = UPPER(TRIM("HQ City")),
    "HQ State" = UPPER(TRIM("HQ State"))
WHERE "HQ City" IS NOT NULL
   OR "HQ State" IS NOT NULL;

VACUUM FULL ANALYZE public_transit_master;

DO
$$
    DECLARE
        r   record;
        sql text;
    BEGIN
        FOR r IN
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = 'public_transit_master'
              AND data_type IN ('text', 'character varying')
            LOOP
                sql := format(
                        'SELECT ''%s'' AS column_name, COUNT(*) AS bad_rows
                         FROM public_transit_master
                         WHERE %I !~ ''^\d+(\.\d+)?$'' AND %I IS NOT NULL;',
                        r.column_name, r.column_name, r.column_name
                       );
                RAISE NOTICE '%', sql;
                EXECUTE sql;
            END LOOP;
    END
$$;