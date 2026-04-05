#!/usr/bin/env bash
set -e

OOZIE_WF_PATH="${OOZIE_WF_PATH:-/user/${USER}/oozie/wf_idfm_weather_daily}"

echo "=== OOZIE WORKFLOW SUBMISSION ==="
echo "Workflow path: ${OOZIE_WF_PATH}"

hdfs dfs -mkdir -p "${OOZIE_WF_PATH}" || true
hdfs dfs -put -f scripts/oozie/workflow.xml "${OOZIE_WF_PATH}/workflow.xml"
hdfs dfs -put -f scripts/ingestion/ingest_openmeteo_to_hdfs.py "${OOZIE_WF_PATH}/ingest_openmeteo_to_hdfs.py"
hdfs dfs -put -f scripts/hive/create_external_tables.hql "${OOZIE_WF_PATH}/create_external_tables.hql"
hdfs dfs -put -f scripts/hive/create_enriched_view.hql "${OOZIE_WF_PATH}/create_enriched_view.hql"
hdfs dfs -put -f scripts/mapreduce/run_mapreduce_hadoop.sh "${OOZIE_WF_PATH}/run_mapreduce_hadoop.sh"
hdfs dfs -put -f scripts/mapreduce/mapper.py "${OOZIE_WF_PATH}/mapper.py"
hdfs dfs -put -f scripts/mapreduce/reducer.py "${OOZIE_WF_PATH}/reducer.py"

oozie job -config config/oozie/job.properties -run