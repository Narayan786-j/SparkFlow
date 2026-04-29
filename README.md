Based on the ALL_INDIA4 project

Option 1: Concise (2-3 lines)
ClickHouse Data Pipeline Engineer Architected and implemented a high-throughput IPDR data pipeline processing 100+ billion rows/day across an 11-feed enrichment system on a 9-node sharded ClickHouse cluster. Designed a dual-cluster split (CH1→CH2) architecture to separate ingestion/enrichment from analytics, reducing query latency by 50-100x on 54% of production workloads.

Option 2: Bullet Points (for detailed experience section)
Real-time Telecom Data Platform | ClickHouse, Bash, Python

Engineered an end-to-end ETL pipeline ingesting 70+ files/minute from 23 telecom circles, processing CGN, PGW, CHF, EPC, UPF, and AAA feeds with 6-way chained enrichment joins
Optimized ClickHouse schema with strategic ORDER BY reordering and bloom filter indices, cutting dest-IP query times from 15-25 min to sub-second (500x improvement)
Designed cross-cluster data routing using Distributed tables with sipHash64 sharding, enabling horizontal scaling from 9 to 14 nodes with zero downtime
Built real-time monitoring dashboard (FastAPI + vanilla JS) with cluster health metrics, merge tracking, and distribution queue observability for 10M+ daily BA queries
Reduced storage footprint by 30-40% through LowCardinality types, native codecs (Delta, ZSTD, T64), and eliminating Nullable columns
Option 3: Impact-Focused One-Liner
Scaled a ClickHouse-based analytics platform to handle 2+ years of telecom records (100B+ rows/day) with sub-second query response on 95% of traffic patterns through schema optimization, cluster sharding, and automated enrichment pipelines.

Key Metrics to Highlight
100+ billion rows/day ingestion
23 circles × 11 feeds data sources
9→14 node cluster architecture
500x query speedup on dominant workloads
2-year retention at petabyte scale
