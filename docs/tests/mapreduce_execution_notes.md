# Hadoop Streaming execution notes

## Objective
Run a simple MapReduce aggregation on raw transport data.

## Input
HDFS raw transport directory:
`/data/raw/idfm_stop_monitoring`

## Output
HDFS analytics directory:
`/data/analytics/daily_kpis/mapreduce_line_destination_counts`

## Mapper logic
Emit:
- key = `line_label|destination`
- value = `1`

## Reducer logic
Sum occurrences for each key.

## Expected output example
- `metro_6|Nation    42`
- `metro_6|Charles de Gaulle-Etoile    51`
- `metro_7|Pont de SÃ¨vres    37`

## Local validation
Before Hadoop execution, validate logic with:
`python .\scripts\mapreduce\run_mapreduce_local.py`