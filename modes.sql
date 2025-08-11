CREATE TABLE modes
(
    mode_id   CHAR(1) PRIMARY KEY,
    mode_name VARCHAR(8),
    mode_desc TEXT
);

INSERT INTO modes (mode_id, mode_name)
SELECT DISTINCT SUBSTRING("3 Mode", 1, 1) AS mode_id, "3 Mode" AS mode_name
FROM public_transit_master
WHERE "3 Mode" IS NOT NULL
  AND SUBSTRING("3 Mode"
          , 1, 1) <> ''
ON CONFLICT(mode_id) DO NOTHING;

UPDATE modes
SET mode_desc = ' includes only Ferryboat mode'
WHERE mode_id LIKE 'F';

UPDATE modes
SET mode_desc = 'includes all modes that run along rails, as well as Aerial Tramway'
WHERE mode_id LIKE 'R';

UPDATE modes
SET mode_desc = 'all surface transportation modes, including Demand Response mode'
WHERE mode_id like 'B';
