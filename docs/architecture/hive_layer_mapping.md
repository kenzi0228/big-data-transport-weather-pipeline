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