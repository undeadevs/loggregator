# Loggregator

Pub-Sub Log Aggregator dengan Python untuk UTS Sistem Terdistibusi dan Paralel dari Ilham Al Basith dengan NIM 11221077

## Asumsi

- Semua komponen berjalan di lingkungan lokal
- Timestamp dikirim oleh publisher yang dimana karena bersifat lokal telah tersinkronisasi berdasarkan waktu pada host
- Dedup store menggunakan SQLite yang dianggap sudah cukup
- Query parameter `topic` pada endpoint `/events` wajib
- Response untuk `/publish` akan langsung dikirim setelah event masuk ke internal queue
- Internal queue tidak persistent
- Service `publisher` pada repo ini merupakan service contoh dimana akan mengirimkan 5000 events (duplikat > 20%) terus menerus setiap 15-30 detik. Pengiriman secara random dapat berupa single event atau dapat berupa batched events. Perlu diperhatikan bahwa service ini tidak akan mati kecuali dimatikan secara eksplisit
- Docker build untuk service `aggregator` juga akan menjalankan unit test

## Penggunaan

### Docker Compose

Menjalankan service `aggregator` dan `publisher`


```bash
docker-compose -f ./docker/compose.yaml up -d
```

Menjalankan service `aggregator` secara standalone


```bash
docker-compose -f ./docker/compose.yaml up -d `aggregator`
```

### Docker (tanpa Compose)

Build service `aggregator`

```bash
docker build -t undeadevs/loggregator-aggregator --file ./docker/Dockerfile.aggregator .
```

Jalankan service `aggregator`

```bash
docker run -p 8002:8002 -d undeadevs/loggregator-aggregator
```

Build service `publisher`

```bash
docker build -t undeadevs/loggregator-publisher --file ./docker/Dockerfile.publisher .
```

Jalankan service `aggregator`

```bash
docker run -d undeadevs/loggregator-publisher
```

### Tanpa Docker

Buat dan isi file `.env` pada `src/aggregator` dan `src/publisher` sesuai dengan `.env.example`

Instal python packages

```bash
pip install -e .
```

Menjalankan unit tests

```bash
pytest
```

Jalankan `aggregator`

```bash
python ./src/aggregator/main.py
```

Jalankan `publisher`

```bash
python ./src/publisher/main.py
```

## Endpoint

- POST `/publish` dengan schema request body `{ "topic": string, "event_id": UUIDv4, "timestamp": ISO8601, "source": string, "payload": object }`
- GET `/events` dengan query parameter wajib `topic`
- GET `/stats` dengan schema response `{ "received": int, "unique_processed": int, "duplicate_dropped": int, "topics": string[], uptime: float }`

Endpoint tambahan yang generated dari FastAPI

- GET `/openapi.json` OpenAPI schema
- GET `/docs` API docs (Swagger UI)
- GET `/redoc` API docs (ReDoc)
