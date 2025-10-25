# UTS Sistem Paralel dan Terdistribusi: Pub-Sub Log Aggregator dengan Idempotent Consumer dan Deduplication

## Identitas

- Nama: Ilham Al Basith
- NIM: 11221077
- Program Studi: Informatika

## Ringkasan Sistem dan Arsitektur

Dalam sistem Pub-Sub Log Aggregator ini, service-service yang biasanya disebut Publisher dapat mengirimkan event dalam bentuk singular maupun batched ke API Aggregator. Selanjutnya, Aggregator akan menyimpan setiap event ke internal queue. Consumer (Subscriber) akan mengambil event dari queue, melakukan deduplication yang akan memberhentikan pemrosesan jika terdeksi duplikat. Jika bukan maka akan disimpan ke dedup store berbasis SQLite dan ditambahkan pada log.

![Diagram Arsitektur](architecture.svg)

## Keputusan Desain

Keputusan desain aggregator mencakup alur proses antara publisher dan consumer, dedup store yang digunakan, penamaan `topic` dan `event_id`, dan teknik ordering. Aggregator di-desain untuk menerima single ataupun batched event. Alur di-desain agar publisher tidak menunggu hingga event diproses yang dimana server akan langsung mengirim response jika event yang dikirim telah masuk ke queue. Event dari queue akan di-consume dan di-deduplicate. Store yang digunakan untuk dedup adalah SQLite karena merupakan solusi file-based database yang telah matang. Penamaan `topic` hierarkikal yang dibatasi hingga 5 level seperti `a.b.c` dimana `b` adalah sub-topic dari `a` dan `c` adalah sub-topic dari `b`. Untuk menghidari collision, penamaan `event_id` menggunakan UUIDv4 yang dimana peluang collision-nya 1 dalam 2.71 * 10**18. Dengan asumsi bahwa maksud dari "lokal" dan "internal" adalah berjalan di satu host yang sama, ordering dilakukan dengan timestamp saja karena waktu pada container akan disinkronisasi terhadap host yang dimana container-container berjalan pada satu host saja.

Selain itu, telah dibuat contoh service publisher yang di-desain untuk mengirimkan 5000 events dengan duplikasi lebih dari 20% terus menerus setiap 15-30 detik. Pengiriman secara random dapat berupa single event atau dapat berupa batched events. Perlu diperhatikan bahwa service ini tidak akan mati kecuali dimatikan secara eksplisit

## Analisis Performa dan Metrik

***Cases**: 50,100,500,1000,5000,10000*
*20.00% <= **Duplicate Rate** <= 100.00%* 

*Catatan: Throughput dan Latency di sini diukur dari sisi publisher saja yaitu dari waktu request dikirim hingga response telah masuk queue**

**Single**

| Event Count | Elapsed (s)  | Throughput (event/s) | Latency (s/event) |
| ----------- | ------------ | -------------------- | ----------------- |
| 50          | 0.0449380875 | 1112.0               | 0.0008987617      |
| 100         | 0.0855674744 | 1168.0               | 0.0008556747      |
| 500         | 0.4417712688 | 1131.0               | 0.0008835425      |
| 1000        | 0.9103057384 | 1098.0               | 0.0009103057      |
| 5000        | 4.3617818356 | 1146.0               | 0.0008723564      |
| 10000       | 8.4676251411 | 1180.0               | 0.0008467625      |
| **Average** | -            | **1139.0**           | **0.0008779006**  |

**Batched**

| Event Count | Elapsed (s)  | Throughput (event/s) | Latency (s/event) |
| ----------- | ------------ | -------------------- | ----------------- |
| 50          | 0.0104634762 | 4778.0               | 0.0002092695      |
| 100         | 0.0148611069 | 6728.0               | 0.0001486111      |
| 500         | 0.0765211582 | 6534.0               | 0.0001530423      |
| 1000        | 0.0497426987 | 20103.0              | 0.0000497427      |
| 5000        | 0.4617681503 | 10827.0              | 0.0000923536      |
| 10000       | 0.6149528027 | 16261.0              | 0.0000614953      |
| **Average** | -            | **10871.0**          | **0.0001190858**  |

Berdasarkan hasil evaluasi performa didapati bahwa berdasarkan throughput maupun juga latency, batched event lebih baik. Alasannya adalah karena pada single event, publisher harus mengirim satu-persatu request ke POST `/publish` yang dimana terdapat bottleneck HTTP roundtrip sebanyak jumlah event yang dikirim. Sedangkan, untuk setiap kasus batched HTTP roundtrip hanya dilakukan sekali. Dari evaluasi ini dapat dilihat juga waktu yang diperlukan untuk memasukkan event ke dalam queue tidak signifikan dibanding dengan HTTP roundtrip.

## Keterkaitan ke BAB 1-7

### T1: Karekteristik Sistem Terdistribusi dan Trade-off Pub-Sub Log Aggregator

Sistem terdistribusi yang baik harus memenuhi beberapa karakteristik desain. Suatu sistem terdistribusi harus memudahkan akses terhadap sumber daya; menyembunyikan fakta bahwa sumber daya terdistribusi terhadap suatu jaringan; harus terbuka; dan harus scalable (Steen & Tanenbaum, 2023). Berbagi sumber daya (resource sharing) pada sistem terdistribusi tidak hanya bertujuan untuk aspek ekonomis saja namun juga memudahkan pengguna untuk berkolaborasi dan bertukar informasi (Steen & Tanenbaum, 2023). Karakteristik yang memudahkan pengguna dalam menggunakan suatu sistem terdistribusi adalah transparansi. Transparansi akan menyembunyikan fakta bahwa sistem terpisah secara fisik bahkan mungkin sangat berjauhan. Keterbukaan akan memudahkan penggunaan atau integrasi komponen-komponen ke sistem lain. Selain itu, tentu saja sistem terdistribusi harus bersifat scalable yaitu dengan menambahkan sumber daya, sistem harus dapat menerima pekerjaan yang lebih banyak tanpa menurunkan performa.

Salah satu arsitektur sistem terdistribusi adalah publish-subscribe (pub-sub) dimana terdapat publisher mengirim event ke sistem dan terdapat subsriber yang berlangganan kepada sistem untuk mendapatkan event. Pada log aggregator yang berbasis topic-based pub-sub tentu memiliki trade-off. Salah satu nya adalah penamaan topic dimana jika terlalu banyak topic terlalu spesifik maka pencarian log akan menyusahkan, namun jika topic terlalu umum maka memungkinkan event yang sangat banyak di topic tersebut. Deduplication juga menjadi trade-off terhadap seberapa banyak event yang dapat diterima dalam suatu periode. Selain itu, fault tolerance juga meningkatkan kompleksitas dari sistem.

### T2: Client-Server vs Publish-Subscribe

Dalam arsitektur client-server, proses dalam sistem terbagi menjadi 2: server yang mengimplementasikan suatu layanan seperti layanan file system atau database dan client yang mengirim request ke suatu layanan di suatu server dan menunggu balasan (reply/response) dari server (Steen & Tanenbaum, 2023). Pada log aggregator, client akan mengirimkan log dan menunggu hingga log berhasil diproses untuk mendapatkan response. Ini akan meningkatkan latency, apalagi setelah ditambahkan deduplication. Untuk menambahkah deduplication dalam arsitektur ini juga menantang sehingga meningkagkan kompleksitas.

Berbeda dengan client-server, arsitektur pub-sub menggabungkan shared data space dan event-based coordination dimana suatu proses berlangganan (subscribe) ke suatu tuple dengan memberikan search pattern dan saat suatu proses menambahkan tuple ke data space, subscriber akan diberitahu (Steen & Tanenbaum, 2023). Pada konteks log aggregator, publisher akan mengirimkan log event dan langsung diberitahu saat event telah masuk dalam queue. Sehingga latency sangatlah kecil dan queue memudahkan implementasi deduplication.

Untuk sistem terdistribusi dalam skala kecil dan tidak sibuk, mungkin client-server saja cukup. Namun semakin besar dan sibuk sistem, tentunya pub-sub menjadi opsi yang trivial.

### T3: At-least-once Semantics, Exactly-once Semantics, dan Idempotent Consumer

Salah satu menanggulangi server yang crash di sisi publisher adalah dengan menerapkan at-least-once semantics. At-least-once semantics adalah teknik yang menjamin suatu RPC dikirimkan setidaknya sekali, dan kemungkinan lebih (Steen & Tananenbaum, 2023). Pada konteks log aggregator, publisher akan mengirimkan log event berkali-kali hingga server memberikan response. Berdasarkan definisi, dapat disimpulkan bahwa akan terdapat duplikat. Idealnya, dapat diterapkan exactly-once semantics, namun secara umum, tidak ada cara untuk mengaturnya (Steen & Tanenbaum, 2023). Pada buku, terlihat bahawa dengan permutasi kondisi apapun request akan hilang atau dikirim/diproses dua kali. 

Efek dari exactly-once semantics dapat dicapai dengan at-least-once semantics yang dilengkapi dengan idempotent consumer. Saat suatu operasi dapat diulang lebih dari sekali tanpa menimbulkan masalah, operasi tersebut bersifat idempotent. Maka, idempotent consumer adalah consumer yang bersifat idempotent. Saat publisher mengirim ulang (retry) log event dan kebetulan event sebelumnya telah diproses, idempotent consumer pada server akan mendeteksi duplikasi dan tidak akan memproses pengiriman ulang tersebut.

### T4: Skema Penamaan dan Dampak Terhadap Deduplication

Salah satu aspek penting dari sistem pub-sub ialah komunikasi dilakukan dengan mendeskripsikan event yang diinginkan subscriber. Konsekuensinya, penamaan (naming) merupakan hal yang krusial (Steen & Tanenbaum, 2023). Pada topic-based pub-sub, deskripsi tersebut adalah topic dari event. Untuk mengakomodasi situasi yang bermacam-macam, digunakan structured naming pada topic. Topic dapat berupa `namaservice` saja atau bahkan `namaservice.fitur.tipelog` dan seterusnya sesuai kebutuhan. Namun agar tidak terlalu banyak topic yang spesifik, level hierarki topic akan dibatasi hingga 5 level.

Selain memiliki topic, setiap event memiliki id yang dimana butuh penamaan juga. Untuk menghindari duplikasi sebanyak-banyaknya, event_id harus di-desan se-unik mungkin yang terhindar dari nama yang sama atau disebut sebagai collision-resistant. Untuk itu, event_id di-desain menggunakan UUID (v4). UUID atau Universally Unique Identifier adalah angka 128-bit yang direpresentasikan sebagai 32 digit heksadesimal yang dibagi menjadi 5 dengan "-" menyatukannya. Peluang collision antara 2 UUID adalah 1 dalam 2.71 * 10**18, sehingga di setiap topic kemungkinan terjadinya colllision pada event_id sangat-sangatlah kecil. Akibatnya, peluang terjadinya proses deduplikasi akan sangat kecil juga.

### T5: Ordering dan Pendekatannya

Banyak proses terkadang harus menyepakati mengenai urutan (ordering) dari beberapa event, seperti apakah pesan m1 dari proses P dikirim sebelum atau sesudah pesan m2 dari proses Q (Steen & Tanenbaum, 2023). Kesepakatan atas urutan semua event-event yang terjadi disebut total ordering. Total ordering dibutuhkan pada sistem yang sangat sensitif terhadap pengurutan terjadinya event. Dalam sistem log aggregator, total ordering untuk banyak event sangatlah krusial karena tujuan utama dari log aggregator melakukan troubleshooting lebih dari satu service secara bersamaan. Pada sistem yang terdistribusi secara fisik, ordering menggunakan sinkronisasi waktu absolut seperti NTP UTC tidak memungkinkan karena network latency. Cara untuk mencapai total ordering adalah dengan tidak bergantung pada waktu asli melainkan menggunakan logical clock. Salah satu logical clock yang menetapkan total ordering adalah Lamport's logical clock. Untuk mensinkronisasi logical clock, lamport mendefinisikan relasi bernama "happens-before" atau "terjadi sebelum" (Steen & Tanenbaum, 2023). Relasi ini ditetapkan untuk dua event dalam satu proses dan dua event komunikasi (kirim dan terima) antara dua proses. Namun, dengan Lamport's clock, relasi sebab akibat antara dua event tidak dapat diperoleh hanya dengan membandingkan nilai waktu-nya (Steen & Tanenbaum, 2023). Selain itu, metode ini terlalu memakan sumber daya untuk lingkup log aggregator lokal. Dikarenakan service-service publisher dan aggregator hanya berjalan secara lokal dalam satu host, maka waktu asli pada setiap service saja sudah cukup mengingat docker container akan mensinkronisasi waktu terhadap host.

### T6: Failure Modes dan Mitigasi

Pada log aggregator, kesalahan-kesalahan yang dapat terjadi dapat diklasifikasikan menjadi communication failures. Khususnya, sebuah channel komunikasi dapat memperlihatkan crash, omission, timing, dan arbitrary failures (Steen & Tanenbaum, 2023). Suatu crash failure terjadi saat server berhenti secara tiba-tiba meskipun sebelumnya masih bekerja dengan baik (Steen & Tanenbaum, 2023). Dalam konteks log aggregator, crash failure dapat terjadi saat event dalam queue terlalu banyak hingga memakan sebagian besar memori (memory leak). Untuk melakukan mitigasi hal tersebut, dapat diimplementasikan dedup store yang tahan terhadap crash atau durable. Sedangkan, omission failure terjadi saat server gagal merespon ke suatu request (Steen, Tanenbaum, 2023). Omission failure sendiri dapat disebabkan oleh crash failure yang mana crash terjadi sebelum server dapat merespon. Jika terjadi omission failure pada log aggregator, publisher akan melakukan mitigasi dengan mengirim ulang log event secara periodik (retry). Retry dapat dilakukan dengan exponential backoff dimana semakin banyak retry, semakin tinggi periode retry secara eksponensial. Timing failure terjadi saat response berada di luar interval waktu nyata yang ditentukan (Steen & Tanenbaum, 2023). Failure ini dapat menyebabkan event yang out of order atau tidak terurut. Arbitrary failure atau kesalahan tak tentu mungkin terjadi dalam bentuk pesan duplikat, dihasilkan dari fakta bahwa dalam jaringan komputer pesan mungkin buffered untuk waktu yang relatif lama, dan dimasukkan kembali ke jaringan setelah pengirim asli telah melakukan retransmission (Steen & Tanenbaum, 2023). Sebelumnya retransmission atau retry pada log aggregator mungkin terjadi, hal ini berpotensi duplikat.

### T7: Eventual Consistency dan Kaitannya Pada Idempotent + Deduplication

Eventual consistency adalah kejadian dimana jika tidak ada update untuk waktu yang lama, semua replika akan menjadi konsisten secara gradual, yaitu memiliki data yang sama (Steen & Tanenbaum, 2023). Pada kasus log aggregator, eventual consistency menjamin semua service/node memiliki data yang konsisten. Saat banyak event masuk dalam queue tentu saja event tidak diproses secara instan dan membutuhkan waktu, sehingga dedup store tidak akan konsisten pada awalnya dan akan konsisten setelah semua event telah diproses. Eventual consistency ini juga terjadi pada response untuk route statistik GET /stats dengan alasan yang sama. Data konsisten juga mengimplikasikan state yang konsisten. Pada log aggregator, state yang konsisten akan memastikan dengan pengiriman event yang sama akan mencapai state yang sama juga. Untuk itulah, consumer pada log aggregator harus bersifat idempotent. Deduplication memiliki peran yang besar dalam idempotent consumer dimana event duplikat tidak akan diproses sehingga state tidak akan berubah. Dapat disimpulkan bahwa idempotent consumer dan deduplication pada log aggregator membantu sistem meraih konsistensi.

### T8: Metrik Evaluasi dan Keputusan Desain

Metrik yang baik untuk dijadikan bahan evaluasi performa pada kasus ini adalah throughput dan latency. Seperti yang disebutkan pada (Steen & Tanenbaum, 2023): "Yang kita pedulikan adalah waktu response R: berapa lama waktu yang dibutuhkan sebelum layanan memproses sebuah request, termasuk waktu dalam queue. Dengan tujuan itu, kita perlu rata-rata throughput" dimana queue yang dimaksud di sini adalah request queue secara umum. Untuk latency, pada buku (Steen & Tanenbaum, 2023) saja terdapat 35 kali okurens penyebutan kata tersebut. Jelas bahwa latency merupakan masalah yang besar untuk skalabilitas sistem terdistribusi. Untuk meminimalisir waktu response, log aggregator di-desain agar secara langsung mengirim response setelah log event masuk dalam internal queue. Sehingga semakin makin kecil waktu response, semakin tinggi juga jumlah throughput. Memperbolehkan banyak event dikirim sebagai batch juga berpengaruh dalam waktu response. Pemrosesan event dalam internal queue dapat memberikan dampak pada penerimaan request yang secara transitif akan berdampak terhadap response time. Maka dari itu, query SQLite untuk dedup didesain sesimpel mungkin. Keputusan penggunaan SQLite untuk dedup store sendiri diambil karena merupakan file-based database yang mature dan stable.

## Referensi

Van Steen, M. dan Tanenbaum, A. S. (2023). Distributed Systems (Edisi ke-4). Amazon Digital Services LLC - Kdp. https://distributed-systems.net
