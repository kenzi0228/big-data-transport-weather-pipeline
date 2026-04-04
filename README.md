# Big Data Transport Weather Pipeline

## Project goal
Hybrid Big Data pipeline for quasi real-time IDFM stop monitoring and weather impact analysis.

## Main components
- IDFM real-time API
- Open-Meteo API
- Kafka
- Hadoop / HDFS
- HBase
- Hive
- MapReduce
- Oozie

## Current repository structure
- config/: configuration files
- data/raw/: raw ingested data
- data/refined/: cleaned and normalized data
- data/analytics/: batch analytics outputs
- docs/: architecture, report, tests
- scripts/: ingestion, consumers, hive, hbase, mapreduce, oozie, tests
- outputs/: csv exports and reports
- archive/: archived legacy local simulation

## Notes
The previous local simulation version has been archived under archive/legacy_local_simulation/.