$ErrorActionPreference = "Stop"

function Write-Utf8NoBom {
    param(
        [string]$Path,
        [string]$Content
    )

    $parent = Split-Path -Parent $Path
    if ($parent -and -not (Test-Path $parent)) {
        New-Item -ItemType Directory -Path $parent -Force | Out-Null
    }

    [System.IO.File]::WriteAllText(
        $Path,
        $Content,
        [System.Text.UTF8Encoding]::new($false)
    )
}

# ---------------------------------------------------------
# 1. create_external_tables.hql
# ---------------------------------------------------------
$createTables = @'
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
'@
Write-Utf8NoBom -Path "scripts/hive/create_external_tables.hql" -Content $createTables

# ---------------------------------------------------------
# 2. create_enriched_view.hql
# ---------------------------------------------------------
$createView = @'
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
'@
Write-Utf8NoBom -Path "scripts/hive/create_enriched_view.hql" -Content $createView

# ---------------------------------------------------------
# 3. mapping doc
# ---------------------------------------------------------
$mappingDoc = @'
# Hive layer mapping

## ext_idfm_line_raw
External table for raw IDFM line-based transport ingestion.

Main fields:
- source
- ingestion_time_utc
- line_ref
- line_label
- target_stop_refs
- filtered_journey_count
- filtered_journeys
- payload

## ext_openmeteo_raw
External table for raw Open-Meteo ingestion.

Main fields:
- source
- ingestion_time_utc
- latitude
- longitude
- timezone
- payload

## vw_transport_weather_summary
Simple analytical view exposing transport and weather ingestion metadata.

Note:
This first Hive layer keeps raw payloads as strings to stay simple and coherent with the project scope.
A more advanced version could flatten JSON fields into refined tables.
'@
Write-Utf8NoBom -Path "docs/architecture/hive_layer_mapping.md" -Content $mappingDoc

Write-Host ""
Write-Host "Hive layer files created successfully." -ForegroundColor Green
Write-Host ""
Write-Host "Run next:" -ForegroundColor Cyan
Write-Host "Get-ChildItem .\scripts\hive"