# Final architecture

## Type
Hybrid Big Data pipeline

## Sources
- IDFM real-time stop monitoring
- Open-Meteo weather API

## Components
- Kafka for transport ingestion
- HDFS for raw and historical storage
- HBase for latest state serving
- Hive for SQL analytics
- MapReduce for daily aggregation
- Oozie for orchestration

## End-to-end flow
1. Poll IDFM stop monitoring API
2. Publish raw events to Kafka
3. Consume Kafka and write raw events to HDFS
4. Consume Kafka and update HBase latest state
5. Fetch weather data and store it in HDFS
6. Create Hive external tables
7. Build enriched analytics view
8. Run daily MapReduce aggregation
9. Orchestrate batch pipeline with Oozie