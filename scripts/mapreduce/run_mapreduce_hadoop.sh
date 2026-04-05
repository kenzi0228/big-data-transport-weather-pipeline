#!/usr/bin/env bash
set -e

INPUT_PATH="/data/raw/idfm_stop_monitoring"
OUTPUT_PATH="/data/analytics/daily_kpis/mapreduce_line_destination_counts"
STREAMING_JAR="${HADOOP_STREAMING_JAR:-/usr/lib/hadoop-mapreduce/hadoop-streaming.jar}"

echo "=== HADOOP STREAMING MAPREDUCE ==="
echo "Input path: ${INPUT_PATH}"
echo "Output path: ${OUTPUT_PATH}"
echo "Streaming jar: ${STREAMING_JAR}"

hdfs dfs -rm -r -f "${OUTPUT_PATH}" || true

hadoop jar "${STREAMING_JAR}" \
  -input "${INPUT_PATH}" \
  -output "${OUTPUT_PATH}" \
  -mapper "python3 scripts/mapreduce/mapper.py" \
  -reducer "python3 scripts/mapreduce/reducer.py" \
  -file scripts/mapreduce/mapper.py \
  -file scripts/mapreduce/reducer.py

echo "MapReduce job completed."
echo "To inspect output:"
echo "hdfs dfs -cat ${OUTPUT_PATH}/part-*"