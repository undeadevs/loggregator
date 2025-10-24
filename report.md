# UTS Sistem Terdistribusi dan Paralel: Pub-Sub Log Aggregator dengan Idempotent Consumer dan Deduplication

## Identitas

- Nama: Ilham Al Basith
- NIM: 11221077
- Program Studi: Informatika

## Ringkasan Sistem dan Arsitektur

```mermaid
architecture-beta
    service publisher1(server)[Publisher 1]
    service publisher2(server)[Publisher 2]
    service publishern(server)[Publisher N]

    group api(server)[Aggregator FastAPI]

    service queue(server)[asycio_Queue] in api
    service consumer(server)[Consumer] in api
    service sqlite(database)[SQLite Dedup] in api

    publisher1:R --> T:queue
    publisher2:R --> L:queue
    publishern:R --> B:queue
    queue:R --> L:consumer
    consumer:R --> L:sqlite

```

## Keputusan Desain

## Analisis Performa dan Metrik

## Keterkaitan ke BAB 1-7

## Referensi
