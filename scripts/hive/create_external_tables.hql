CREATE DATABASE IF NOT EXISTS bigdata_transport_weather;

USE bigdata_transport_weather;

DROP TABLE IF EXISTS ext_idfm_line_raw;
CREATE EXTERNAL TABLE ext_idfm_line_raw (
    source STRING,
    ingestion_time_utc STRING,
    line_ref STRING,
    line_label STRING,
    target_stop_refs ARRAY<STRING>,
    filtered_journey_count INT,
    filtered_journeys STRING,
    payload STRING
)
STORED AS JSONFILE
LOCATION '/data/raw/idfm_stop_monitoring';

DROP TABLE IF EXISTS ext_openmeteo_raw;
CREATE EXTERNAL TABLE ext_openmeteo_raw (
    source STRING,
    ingestion_time_utc STRING,
    latitude DOUBLE,
    longitude DOUBLE,
    timezone STRING,
    payload STRING
)
STORED AS JSONFILE
LOCATION '/data/raw/openmeteo';