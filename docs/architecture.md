# Architecture du projet

## Type d'architecture
Architecture hybride :
- Streaming pour les données de transport
- Batch pour les données météo et les analyses historiques

## Composants
- Source transport temps réel
- Source météo
- Kafka
- HDFS / stockage simulé localement
- Spark Streaming
- Spark Batch
- Export CSV / reporting
