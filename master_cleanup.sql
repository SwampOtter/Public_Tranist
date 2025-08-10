UPDATE public_transit_master
SET "HQ City"  = UPPER(TRIM("HQ City")),
    "HQ State" = UPPER(TRIM("HQ State"))
WHERE "HQ City" IS NOT NULL
   OR "HQ State" IS NOT NULL;