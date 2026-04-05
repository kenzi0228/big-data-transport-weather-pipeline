USE bigdata_transport_weather;

DROP VIEW IF EXISTS vw_transport_weather_summary;

CREATE VIEW vw_transport_weather_summary AS
SELECT
    t.ingestion_time_utc AS transport_ingestion_time_utc,
    t.line_ref,
    t.line_label,
    t.filtered_journey_count,
    w.ingestion_time_utc AS weather_ingestion_time_utc,
    w.latitude,
    w.longitude,
    w.timezone
FROM ext_idfm_line_raw t
CROSS JOIN ext_openmeteo_raw w;