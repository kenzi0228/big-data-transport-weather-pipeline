# Oozie execution notes

## Objective
Orchestrate the batch side of the project.

## Workflow steps
1. ingest Open-Meteo raw data
2. create Hive external tables
3. create Hive enriched view
4. launch Hadoop Streaming MapReduce
5. end

## Main files
- scripts/oozie/workflow.xml
- scripts/oozie/run_oozie.sh
- config/oozie/job.properties

## Notes
This workflow is intentionally simple and aligned with the project scope.
It demonstrates orchestration of batch ingestion, SQL analytics preparation, and batch aggregation.