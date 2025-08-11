CREATE TABLE types_of_service
(
    tos_id   TEXT PRIMARY KEY,
    tos_name TEXT
);

INSERT INTO types_of_service (tos_id)
SELECT DISTINCT public_transit_master."TOS"
FROM public_transit_master
WHERE "TOS" IS NOT NULL
ON CONFLICT (tos_id) DO NOTHING;

UPDATE types_of_service
SET tos_name = 'Directly Operated (DO)'
WHERE tos_id LIKE '%DO';

UPDATE types_of_service
SET tos_name = 'Purchased Transportation — General (PT)'
WHERE tos_id LIKE '%PT';

UPDATE types_of_service
SET tos_name = 'Purchased Transportation – Taxi (TX)'
WHERE tos_id LIKE '%TX';

UPDATE types_of_service
SET tos_name = 'Purchased Transportation — Transportation Network Company (TN)'
WHERE tos_id LIKE '%TN';
