# BE-03 — Agent Orchestration Specification

**Project:** AI Vendor Selection System  
**Dokumen:** BE-03 — Agent Orchestration  
**Versi:** 3.0.0  
**Tanggal:** 2026-06-13  
**Status:** Draft  
**Author:** —  
**Direview oleh:** —

---

## Daftar Isi

1. [Tujuan Dokumen](#1-tujuan-dokumen)
2. [Referensi Dokumen](#2-referensi-dokumen)
3. [Gambaran Sistem Orchestration](#3-gambaran-sistem-orchestration)
4. [Lima Sub-Agent](#4-lima-sub-agent)
5. [Orchestration Flow](#5-orchestration-flow)
6. [State Machine Agent](#6-state-machine-agent)
7. [Penanganan Error & Resiliensi](#7-penanganan-error--resiliensi)
8. [Komunikasi dengan Database](#8-komunikasi-dengan-database)
9. [Ekstraksi Dokumen](#9-ekstraksi-dokumen)
10. [Batasan & Throttling](#10-batasan--throttling)
11. [Aturan & Larangan](#11-aturan--larangan)
12. [Catatan untuk Dokumen Lanjutan](#12-catatan-untuk-dokumen-lanjutan)

---

## 1. Tujuan Dokumen

Dokumen ini mendefinisikan **bagaimana proses evaluasi AI dikoordinasikan** — agent apa saja yang ada, apa tanggung jawab masing-masing, bagaimana mereka dijalankan, dan bagaimana sistem tetap berfungsi saat salah satu agent mengalami masalah.

Dokumen ini menjawab pertanyaan: siapa yang memimpin proses evaluasi, bagaimana tujuh agent bekerja dengan dependency yang tepat, data apa yang dihasilkan tiap agent, dan apa yang terjadi jika satu agent gagal.

Dokumen ini **tidak** mendefinisikan algoritma scoring TOPSIS, detail prompt, atau mekanisme RAG secara mendalam — itu masing-masing ada di BE-05, BE-04, dan BE-08.

---

## 2. Referensi Dokumen

| Kode | Nama Dokumen | Keterangan |
|---|---|---|
| BE-02 | API Contract | Endpoint yang memicu dan memonitor orchestration |
| BE-04 | Prompt Library | Template prompt yang digunakan tiap agent |
| BE-05 | Scoring Engine | Dipanggil oleh Orchestrator setelah semua agent selesai |
| BE-08 | RAG Specification | Pipeline indexing dokumen yang dipicu saat upload |
| BE-09 | Qualitative Analyzer Agent | Spesifikasi agent keenam |
| BE-10 | Preference Matcher Agent | Spesifikasi agent ketujuh |
| DB-01 | Data Model & ERD | Tabel `agent_progress` yang ditulis orchestration |
| DB-03 | Query & Performance | Pola write burst ke `agent_progress` |

---

## 3. Gambaran Sistem Orchestration

### 3.1 Framework

Orchestration dibangun menggunakan **LangGraph** — framework Python untuk membangun agent berbasis graph state machine. LangGraph dipilih karena memodelkan alur agent sebagai directed graph yang eksplisit, sehingga alur dapat divisualisasikan, di-debug, dan diaudit.

**Mengapa LangGraph, bukan CrewAI atau AutoGen:** LangGraph memberikan kontrol yang lebih eksplisit atas alur eksekusi dan state management. Untuk sistem yang harus dapat diaudit (keputusan procurement harus bisa dijelaskan), kontrol eksplisit lebih penting dari kemudahan setup. CrewAI dan AutoGen lebih cocok untuk sistem yang bersifat conversational — bukan pipeline terstruktur seperti ini.

### 3.2 LLM yang digunakan

Semua agent menggunakan **DeepSeek-V4-Flash** (via OpenRouter API) sebagai LLM utama. Model ini dipilih karena kemampuan instruction-following yang kompetitif dengan biaya yang lebih efisien — keduanya relevan untuk sistem yang hasilnya dikonsumsi oleh scoring engine dan membutuhkan banyak iterasi testing.

Akses menggunakan OpenAI SDK dengan `base_url` override ke OpenRouter. Model dapat dikonfigurasi per environment — development bisa menggunakan model yang lebih ringan jika diperlukan, production menggunakan DeepSeek-V4-Flash. Detail keputusan ada di ADR-033 (SH-01).

### 3.3 Peran Orchestrator

Orchestrator adalah komponen pusat yang:
- Menerima trigger dari Next.js API Routes
- Membagi pekerjaan ke tujuh sub-agent
- Menjalankan agent sesuai dependency graph
- Mengagregasi hasil dari semua agent
- Memicu scoring engine setelah semua agent selesai
- Menulis status dan progress ke database secara real-time

Orchestrator bukan agent — ia adalah coordinator yang tidak menggunakan LLM secara langsung. LLM hanya digunakan oleh sub-agent.

---

## 4. Tujuh Sub-Agent

Setiap sub-agent memiliki tanggung jawab yang terdefinisi dengan jelas dan tidak tumpang tindih. Satu agent hanya boleh memiliki satu tugas utama. Masing-masing menerima konteks yang relevan dengan tugasnya tetapi memproses dimensi yang berbeda.

---

### 4.1 Data Collector Agent

**Tanggung jawab:** Mengumpulkan informasi tambahan tentang setiap vendor dari sumber eksternal yang tidak ada dalam data yang diinput user.

**Apa yang dikumpulkan:**
- Informasi publik perusahaan: tahun berdiri, ukuran perusahaan, bidang usaha utama
- Keberadaan dan validitas sertifikasi (ISO, SNI, atau sertifikasi industri relevan)
- Berita atau informasi terkini tentang vendor dalam 6 bulan terakhir
- Review atau rating publik jika tersedia

**Sumber data:**
- Web search menggunakan tool search yang tersedia di LangGraph
- Data yang sudah diinput user sebagai baseline (tidak di-override, hanya dilengkapi)

**Output yang dihasilkan:** Objek terstruktur per vendor berisi informasi tambahan yang sudah dikumpulkan, beserta sumber dan tingkat kepercayaan informasi tersebut.

**Mengapa agent ini perlu:** User sering tidak memiliki informasi lengkap tentang vendor baru. Agent ini mengisi celah tersebut secara otomatis sehingga evaluasi tidak hanya bergantung pada klaim vendor sendiri.

---

### 4.2 Financial Analyzer Agent

**Tanggung jawab:** Menganalisa aspek finansial dari setiap penawaran vendor — bukan hanya membandingkan harga nominal, tetapi menghitung nilai sebenarnya dalam konteks requirement.

**Apa yang dianalisa:**
- Perbandingan harga penawaran dengan estimasi harga pasar untuk kebutuhan serupa
- Kalkulasi TCO (Total Cost of Ownership) jika ada komponen biaya tersembunyi yang teridentifikasi (misalnya biaya lisensi tahunan, biaya maintenance, biaya training)
- Apakah harga penawaran masuk akal dalam konteks spesifikasi yang diminta
- Posisi harga relatif antar vendor yang dievaluasi

**Input yang dibutuhkan:** Harga penawaran dari setiap vendor, requirement pengadaan (termasuk spesifikasi teknis jika ada), budget range yang ditetapkan user.

**Output yang dihasilkan:** Skor finansial per vendor (0–100), estimasi TCO jika bisa dihitung, dan catatan naratif singkat tentang temuan finansial yang signifikan.

---

### 4.3 Risk Assessor Agent

**Tanggung jawab:** Menilai risiko yang berkaitan dengan setiap vendor dari perspektif legalitas, stabilitas bisnis, dan kepatuhan.

**Apa yang dinilai:**
- Status legalitas: apakah vendor terlihat memiliki badan hukum yang valid
- Indikasi masalah hukum atau sengketa yang teridentifikasi dari informasi publik
- Stabilitas bisnis: indikasi apakah vendor dalam kondisi operasional yang stabil
- Relevansi pengalaman: apakah vendor memiliki track record di kategori pengadaan yang relevan

**Catatan penting:** Agent ini tidak melakukan verifikasi legalitas secara resmi — ia menilai risiko berdasarkan informasi yang tersedia secara publik. Verifikasi resmi tetap menjadi tanggung jawab tim procurement sebelum kontrak ditandatangani. Keterbatasan ini harus tercermin dalam output agent.

**Output yang dihasilkan:** Skor risiko per vendor (0–100, di mana 100 = risiko sangat rendah), level risiko kategoris (rendah/sedang/tinggi), dan catatan tentang temuan yang memerlukan perhatian khusus.

---

### 4.4 Performance Scorer Agent

**Tanggung jawab:** Mengevaluasi kemampuan delivery dan kualitas layanan vendor berdasarkan track record dan kapabilitas yang teridentifikasi.

**Apa yang dievaluasi:**
- Portofolio dan referensi proyek yang relevan dengan kebutuhan saat ini
- Indikasi kapasitas produksi atau kapabilitas delivery
- Kesesuaian spesifikasi yang ditawarkan dengan yang diminta
- Layanan purna jual: garansi, support, SLA yang disebutkan dalam penawaran

**Input yang dibutuhkan:** Data vendor dari Data Collector Agent (jika sudah tersedia) dan data yang diinput user (catatan, dokumen penawaran).

**Ketergantungan pada Data Collector:** Performance Scorer sebaiknya menunggu Data Collector selesai sebelum mulai bekerja — atau berjalan paralel dengan memanfaatkan data yang sudah diinput user sambil menunggu data tambahan dari Data Collector. Keputusan ini ada di level Orchestrator.

**Output yang dihasilkan:** Skor performa per vendor (0–100) dan catatan naratif tentang kekuatan dan kelemahan delivery capability.

---

### 4.5 Negotiation Assistant Agent

**Tanggung jawab:** Menghasilkan rekomendasi strategi negosiasi berdasarkan hasil analisa keempat agent sebelumnya.

**Apa yang dihasilkan:**
- Identifikasi vendor mana yang paling memiliki ruang negosiasi (berdasarkan posisi harga relatif)
- Poin-poin spesifik yang bisa dinegosiasikan: harga, masa garansi, payment terms, delivery schedule
- Batas bawah yang wajar untuk negosiasi berdasarkan konteks pasar
- Risiko yang perlu diklarifikasi sebelum kontrak

**Ketergantungan:** Agent ini harus menunggu Performance Scorer selesai karena rekomendasinya bergantung pada hasil analisa finansial, risiko, dan performa dari semua vendor. Agent ini berjalan paralel dengan Qualitative Analyzer Agent (4.6).

**Output yang dihasilkan:** Rekomendasi negosiasi naratif yang menjadi bagian dari reasoning final di halaman hasil evaluasi.

---

### 4.6 Qualitative Analyzer Agent

**Tanggung jawab:** Mengidentifikasi dan menganalisis nilai tambah unik tiap vendor di luar lima kriteria kuantitatif utama.

**Apa yang dianalisis:**
- Unique offerings yang disebutkan dalam dokumen penawaran (via RAG context dari BE-08)
- Keunggulan atau kapabilitas khusus yang tidak masuk ke dalam kriteria TOPSIS
- Perbandingan profil kualitatif antar vendor dalam satu evaluasi
- Potensi tie-breaking jika skor TOPSIS vendor berdekatan

**Ketergantungan:** Membutuhkan output Performance Scorer (field `kekuatan` dan `kelemahan`) dan RAG context dari dokumen penawaran yang sudah diindeks. Berjalan paralel dengan Negotiation Assistant.

**Output yang dihasilkan:** Narasi `profil_kualitatif` per vendor dan `summary_komparatif` antar semua vendor — tidak ada skor numerik. Detail lengkap di BE-09.

---

### 4.7 Preference Matcher Agent

**Tanggung jawab:** Mencocokkan profil vendor dengan preferensi bisnis perusahaan yang diinput secara opsional oleh procurement staff.

**Dua mode operasi:**
- **Mode netral** (tidak ada preferensi): menghasilkan framing objektif tanpa rekomendasi berbasis preferensi
- **Mode opinionated** (ada preferensi): menghasilkan rekomendasi 1–3 vendor yang paling sesuai dengan preferensi, disertai penjelasan dan catatan konflik jika ada

**Ketergantungan:** Membutuhkan output Qualitative Analyzer Agent (`profil_kualitatif` dan `unique_offerings`) untuk dapat mencocokkan preferensi yang mungkin berkaitan dengan dimensi kualitatif. Ini adalah agent terakhir sebelum Scoring Engine.

**Output yang dihasilkan:** Narasi rekomendasi berbasis preferensi (atau framing netral), analisis kesesuaian tiap vendor, dan catatan konflik jika rekomendasi preferensi bertentangan dengan ranking TOPSIS. Detail lengkap di BE-10.

---

## 5. Orchestration Flow

### 5.1 Alur keseluruhan

```
Trigger dari Next.js
        ↓
Orchestrator menerima payload
(requirement + daftar vendor + konfigurasi kriteria + preferensi)
        ↓
Inisialisasi: buat 7 row di tabel agent_progress
dengan status 'idle' untuk evaluasi ini
        ↓
Jalankan paralel:
  ├── Data Collector Agent
  ├── Financial Analyzer Agent
  └── Risk Assessor Agent
        ↓
Saat Data Collector selesai:
  └── Performance Scorer Agent mulai berjalan
        ↓
Saat Performance Scorer selesai:
  ├── Negotiation Assistant Agent ──┐ (paralel)
  └── Qualitative Analyzer Agent ──┘
        ↓
Saat Negotiation Assistant DAN Qualitative Analyzer keduanya selesai:
  └── Preference Matcher Agent mulai berjalan
        ↓
Semua agent selesai
        ↓
Orchestrator mengagregasi semua output agent
        ↓
Kirim data agregat ke Scoring Engine (BE-05)
        ↓
Scoring Engine menghitung skor TOPSIS, reasoning naratif,
analisis kualitatif, dan rekomendasi preferensi
        ↓
Orchestrator menyimpan hasil ke tabel
hasil_evaluasi dan hasil_vendor
        ↓
Update status evaluasi menjadi 'selesai'
        ↓
Selesai
```

### 5.2 Mengapa urutan ini

Data Collector, Financial Analyzer, dan Risk Assessor berjalan paralel karena ketiganya bekerja secara independen — masing-masing tidak membutuhkan output dari yang lain.

Performance Scorer menunggu Data Collector karena ia memanfaatkan data tambahan yang dikumpulkan Data Collector (sertifikasi, portofolio) untuk penilaian yang lebih akurat. Jika Data Collector gagal, Performance Scorer tetap berjalan dengan data yang sudah ada dari input user.

Negotiation Assistant dan Qualitative Analyzer berjalan paralel setelah Performance Scorer selesai. Keduanya membutuhkan output Performance Scorer tetapi tidak saling bergantung satu sama lain — menjalankan keduanya paralel menghemat waktu total evaluasi.

Preference Matcher adalah agent terakhir karena ia membutuhkan output Qualitative Analyzer (`profil_kualitatif` dan `unique_offerings`) untuk pencocokan preferensi yang komprehensif. Tanpa output kualitatif, agent ini tidak bisa mencocokkan preferensi yang berkaitan dengan dimensi di luar metrik TOPSIS.

### 5.3 Payload yang dikirim ke setiap agent

Payload dasar yang diterima semua agent:
- Judul dan deskripsi requirement pengadaan
- Kategori pengadaan
- Budget range
- Deadline
- Daftar vendor dengan semua data yang diinput user
- Konfigurasi kriteria yang aktif (nama kriteria dan bobotnya)

Agent tertentu menerima payload tambahan:

**Qualitative Analyzer** — menerima tambahan RAG context dari BE-08: potongan relevan dari dokumen penawaran tiap vendor yang diambil menggunakan query pencarian unique offerings.

**Negotiation Assistant** — menerima tambahan rangkuman output dari Financial Analyzer, Risk Assessor, dan Performance Scorer per vendor.

**Preference Matcher** — menerima tambahan: teks preferensi perusahaan (nullable), rangkuman output semua agent sebelumnya, dan output lengkap Qualitative Analyzer.

Agent tidak perlu melakukan query ke database sendiri — semua data yang dibutuhkan sudah ada dalam payload. Ini menjaga agent tetap stateless dan dapat diuji secara independen.

---

## 6. State Machine Agent

Setiap agent memiliki state yang dilacak secara individual di tabel `agent_progress`.

```
idle
  ↓  Orchestrator memulai agent
running
  ↓  Agent selesai dengan sukses        ↓  Agent mengalami error
done                                   error
```

### 6.1 Update progress selama running

Saat agent berstatus `running`, Orchestrator menulis update ke tabel `agent_progress` secara berkala untuk menunjukkan kemajuan:

- Saat agent dimulai: status → `running`, progress → 0
- Selama agent bekerja: progress diperbarui bertahap (25%, 50%, 75%) bersamaan dengan pesan singkat tentang apa yang sedang dikerjakan
- Saat agent selesai: status → `done`, progress → 100, `finished_at` diisi

Nilai progress tidak harus akurat secara presisi — tujuannya adalah memberi user rasa bahwa sistem sedang bekerja, bukan laporan kemajuan yang eksak.

### 6.2 Granularitas update progress

Update progress tidak perlu dilakukan setiap detik. Frekuensi yang wajar adalah:
- Saat memulai tahap baru dalam proses agent (misalnya: mulai search, mulai analisa, mulai generate output)
- Tidak lebih dari sekali per 3 detik untuk menghindari write burst yang berlebihan

---

## 7. Penanganan Error & Resiliensi

### 7.1 Prinsip: kegagalan satu agent tidak menghentikan yang lain

Jika satu agent gagal, agent lain yang sedang berjalan harus tetap melanjutkan pekerjaannya. Orchestrator tidak boleh membatalkan seluruh proses evaluasi hanya karena satu agent mengalami masalah.

### 7.2 Retry per agent

Setiap agent diberi maksimum **2 kali percobaan ulang** sebelum dinyatakan gagal. Retry dilakukan dengan jeda eksponensial (misalnya: jeda 5 detik sebelum retry pertama, 15 detik sebelum retry kedua) untuk memberikan waktu jika kegagalan disebabkan oleh rate limit API atau masalah sementara.

### 7.3 Fallback saat agent gagal

Jika agent tetap gagal setelah semua retry:

**Data Collector gagal:** Performance Scorer tetap berjalan menggunakan data dari input user saja. Output Data Collector dikosongkan. Scoring Engine diberi tahu bahwa data dari sumber eksternal tidak tersedia untuk vendor tertentu.

**Financial Analyzer gagal:** Dimensi finansial dalam scoring dihitung hanya dari harga penawaran yang diinput user, tanpa konteks pasar. Catatan peringatan ditambahkan ke reasoning bahwa analisa finansial tidak lengkap.

**Risk Assessor gagal:** Dimensi risiko dalam scoring menggunakan nilai default (risiko sedang) dengan catatan bahwa penilaian risiko tidak bisa dilakukan. User diingatkan untuk melakukan verifikasi risiko secara manual.

**Performance Scorer gagal:** Dimensi performa dalam scoring menggunakan data dari input user saja.

**Negotiation Assistant gagal:** Bagian rekomendasi negosiasi dalam reasoning final dikosongkan. Evaluasi tetap menghasilkan ranking dan skor — hanya bagian negosiasi yang tidak ada.

**Qualitative Analyzer gagal:** Bagian profil kualitatif dan summary komparatif dikosongkan. TOPSIS tetap dihitung dan ditampilkan. Preference Matcher tetap berjalan tetapi hanya bisa mencocokkan preferensi dengan data kuantitatif dari agent lain.

**Preference Matcher gagal:** Bagian rekomendasi berbasis preferensi dikosongkan. Evaluasi tetap selesai dengan hasil TOPSIS dan analisis kualitatif. Procurement staff perlu menginterpretasikan hasil terhadap preferensi mereka sendiri secara manual.

### 7.4 Evaluasi dengan data parsial

Jika ada agent yang gagal, evaluasi tetap diselesaikan dengan data yang tersedia. Status evaluasi tetap berubah menjadi `selesai`, tetapi disertai flag `ada_agent_gagal: true` dan daftar agent mana yang gagal.

Di halaman hasil (P-05), ditampilkan peringatan bahwa beberapa dimensi evaluasi tidak lengkap beserta penjelasan dimensi mana yang terpengaruh.

**Mengapa tidak membatalkan evaluasi saat ada agent yang gagal:** Membatalkan seluruh evaluasi akan memaksa user mengulang dari awal, padahal sebagian besar analisa sudah berhasil. Evaluasi parsial dengan peringatan lebih berguna dari tidak ada evaluasi sama sekali.

### 7.5 Timeout per agent

Setiap agent memiliki timeout maksimum **3 menit**. Jika agent tidak selesai dalam 3 menit, ia dianggap gagal dan diperlakukan sama seperti kasus error. Timeout ini mencegah satu agent yang hang memblokir seluruh proses evaluasi selamanya.

---

## 8. Komunikasi dengan Database

### 8.1 Inisialisasi row agent_progress

Sebelum menjalankan satu pun agent, Orchestrator membuat **7 row** di tabel `agent_progress` — satu per agent — semua dengan status `idle`. Ini memastikan frontend bisa langsung menampilkan semua agent (meskipun belum mulai) begitu halaman P-04 dibuka.

### 8.2 Penulisan status harus idempotent

Jika karena suatu hal penulisan status yang sama dikirim dua kali (misalnya karena retry), operasi tersebut harus aman untuk dieksekusi ulang tanpa mengubah state yang benar. Operasi UPDATE yang menyertakan kondisi (misalnya hanya update jika status saat ini adalah nilai tertentu) lebih aman dari UPDATE tanpa kondisi.

### 8.3 Orchestrator tidak membaca dari database selama proses berlangsung

Selama proses evaluasi berjalan, Orchestrator mengelola semua state di memori — bukan dengan membaca ulang dari database setiap kali membutuhkan informasi. Database hanya digunakan untuk menulis progress (agar bisa di-broadcast via Realtime) dan menyimpan hasil akhir.

**Mengapa:** Membaca dari database secara berulang selama proses berlangsung menambah latensi dan meningkatkan beban database tanpa manfaat yang nyata.

### 8.4 Penulisan hasil akhir sebagai satu transaksi

Penulisan ke `hasil_evaluasi` dan semua row `hasil_vendor` dilakukan dalam satu database transaction. Jika penulisan sebagian gagal, seluruh transaksi dibatalkan dan evaluasi tetap berstatus `processing` sehingga bisa dicoba ulang.

---

## 9. Ekstraksi Dokumen & Indexing RAG

### 9.1 Proses yang berbeda dari evaluasi utama

Ekstraksi dokumen penawaran vendor dan indexing RAG berjalan secara terpisah dari proses evaluasi utama. Keduanya dipicu saat user mengupload dokumen di P-03, jauh sebelum evaluasi disubmit.

### 9.2 Alur ekstraksi dan indexing (satu pipeline)

```
File diupload ke Supabase Storage oleh Next.js
        ↓
Next.js memanggil POST /v1/agent/ekstrak-dokumen
        ↓
FastAPI mengunduh file dari Storage URL
        ↓
Konten file diekstrak (teks dari PDF, atau data dari Excel)
        ↓
Pipeline bercabang — dua proses berjalan bersamaan:

  CABANG A — Ekstraksi field terstruktur:
  LLM menganalisa konten dan mengekstrak:
    - Nama perusahaan vendor
    - Nilai penawaran
    - Spesifikasi yang ditawarkan
    - Informasi kontak
    - Ketentuan khusus (garansi, payment terms, dll.)
  → Hasil + confidence score disimpan ke tabel dokumen_upload
  → Status ekstraksi diperbarui

  CABANG B — Indexing RAG (detail di BE-08):
  Teks dibagi menjadi chunk hierarkis parent-child
  → Child chunk di-embed via Google Gemini text-embedding-004
  → Chunk + vektor + metadata disimpan ke tabel dokumen_chunk
  → Full-text search index (tsvector) di-populate
        ↓
Kedua cabang selesai
        ↓
Status dokumen_upload diperbarui menjadi 'done'
(mencerminkan selesainya KEDUA proses)
```

### 9.3 Status pipeline yang dilaporkan ke frontend

User melihat satu status yang merepresentasikan progress kedua cabang. Status `done` hanya diberikan setelah ekstraksi field terstruktur **dan** indexing RAG keduanya selesai. Jika indexing RAG gagal tetapi ekstraksi field terstruktur berhasil, status diset ke `done_partial` dengan flag `indexing_rag_failed: true`.

Evaluasi tetap bisa disubmit meski `indexing_rag_failed: true` — namun AI Chat Panel tidak akan bisa menjawab pertanyaan berbasis isi dokumen untuk vendor tersebut.

### 9.4 Confidence score

LLM diminta untuk menilai seberapa yakin ia terhadap hasil ekstraksi setiap field. Field yang diekstrak dengan ambiguitas (misalnya tabel harga yang kompleks atau format dokumen yang tidak standar) mendapat confidence score rendah.

Field dengan confidence di bawah 0.7 ditampilkan dengan indikator visual di VendorInputCard sehingga user tahu field mana yang perlu diverifikasi secara manual.

### 9.5 Penanganan format yang tidak didukung

Jika dokumen tidak bisa diproses (file rusak, format yang tidak bisa dibaca, atau konten yang tidak relevan), status ekstraksi diset ke `failed` dan user diarahkan untuk menginput data secara manual. Pesan error harus menjelaskan mengapa ekstraksi gagal jika memungkinkan.

---

## 10. Batasan & Throttling

### 10.1 Evaluasi yang bisa diproses bersamaan

Untuk MVP, FastAPI service membatasi **maksimum 5 evaluasi yang diproses secara bersamaan**. Evaluasi ke-6 dan seterusnya masuk ke antrian dan diproses begitu salah satu slot tersedia.

**Mengapa 5:** Setiap evaluasi dengan 5–10 vendor dapat menghasilkan puluhan LLM call secara paralel. Lima evaluasi bersamaan berarti puluhan hingga ratusan LLM call aktif sekaligus — sudah cukup untuk menguji performa dan berada dalam batas rate limit API yang wajar.

### 10.2 Antrian evaluasi

Evaluasi yang menunggu ditampilkan dengan status `menunggu_antrian` di frontend — berbeda dari `processing`. User diberi estimasi waktu tunggu berdasarkan jumlah evaluasi di antrian.

**Catatan:** Status `menunggu_antrian` belum terdefinisi di DB-01. Perlu ditambahkan sebagai nilai enum baru di tabel `evaluasi` atau dikelola sebagai state di level aplikasi saja (tidak disimpan ke database).

### 10.3 Rate limit LLM API

Semua LLM call melalui satu OpenRouter API key. FastAPI harus mengelola rate limit ini dengan menambahkan jeda antara call jika diperlukan. Jika rate limit tercapai, agent melakukan retry dengan backoff eksponensial (sama dengan retry untuk error — lihat section 7.2).

### 10.4 Ukuran konteks

Setiap LLM call memiliki batas ukuran konteks. Jika requirement pengadaan sangat panjang atau ada dokumen penawaran yang di-attach, konten perlu di-truncate sebelum dikirim ke LLM. Truncation dilakukan dari bagian yang paling tidak relevan, dan jika terjadi, dicatat dalam metadata agent.

---

## 11. Aturan & Larangan

**Dilarang agent melakukan query langsung ke database.** Semua data yang dibutuhkan agent sudah ada dalam payload dari Orchestrator. Ini menjaga agent tetap stateless dan mudah diuji.

**Dilarang agent memodifikasi data input.** Agent hanya menghasilkan output baru — tidak boleh mengubah data vendor yang diinput user. Data input adalah sumber kebenaran yang immutable selama proses evaluasi.

**Dilarang Orchestrator membatalkan evaluasi karena satu agent gagal.** Prinsip resiliensi (section 7) tidak boleh dilanggar meskipun agent yang gagal adalah agent yang "penting".

**Dilarang Preference Matcher mengubah atau mempengaruhi kalkulasi TOPSIS.** Preference matching adalah lapisan interpretasi di atas hasil scoring — bukan intervensi terhadap proses kalkulasi.

**Dilarang Qualitative Analyzer menghasilkan skor numerik.** Output agent ini adalah narasi murni. Jika ada kebutuhan perbandingan numerik dimensi kualitatif, itu bukan tanggung jawab agent ini.

**Dilarang menyimpan API key atau kredensial dalam kode atau log.** Semua kredensial dikelola melalui environment variables dan tidak boleh muncul dalam log apapun.

**Dilarang menjalankan agen tanpa timeout.** Setiap agent harus memiliki timeout yang terdefinisi (section 7.5) untuk mencegah proses yang hang selamanya.

**Output agent harus selalu dalam format terstruktur yang terdefinisi.** LLM diminta untuk menghasilkan output dalam format JSON yang spesifik (didefinisikan di BE-04 dan BE-09/BE-10). Output yang tidak sesuai format dianggap sebagai kegagalan partial dan dicatat.

---

## 12. Catatan untuk Dokumen Lanjutan

### Untuk BE-04 (Prompt Library)

Setiap agent membutuhkan minimal dua prompt: system prompt yang mendefinisikan peran dan output format, serta user prompt template yang menyertakan data vendor dan requirement. BE-04 perlu mendefinisikan kedua prompt untuk ketujuh agent. Qualitative Analyzer dan Preference Matcher memiliki karakteristik prompt yang berbeda karena outputnya naratif, bukan JSON terstruktur.

### Untuk BE-05 (Scoring Engine)

Orchestrator memanggil Scoring Engine setelah semua agent selesai. BE-05 perlu mendefinisikan format data agregat yang diharapkan — termasuk output dari Qualitative Analyzer dan Preference Matcher sebagai input tambahan untuk reasoning naratif.

### Untuk BE-08 (RAG Specification)

Pipeline indexing RAG berjalan sebagai bagian dari proses ekstraksi dokumen (section 9). BE-08 mendefinisikan detail teknis chunking, embedding, dan penyimpanan ke pgvector yang dipicu dari pipeline ini.

### Untuk DB-01 (Data Model)

Tabel `agent_progress` perlu menambahkan dua nilai enum baru: `qualitative_analyzer` dan `preference_matcher`. Status `menunggu_antrian` juga perlu diputuskan apakah menjadi nilai enum di database atau dikelola sebagai state aplikasi.

### Untuk SH-03 (Testing Strategy)

Sistem multi-agent dengan tujuh agent dan dependency graph yang lebih kompleks membutuhkan integration testing yang lebih ekstensif — terutama untuk skenario kegagalan rantai (Qualitative Analyzer gagal memengaruhi Preference Matcher).

---

**Riwayat Perubahan**

| Versi | Tanggal | Perubahan | Author |
|---|---|---|---|
| 1.0.0 | 2026-06-07 | Versi awal — lima agent | — |
| 2.0.0 | 2026-06-11 | Tambah Qualitative Analyzer Agent (BE-09) dan Preference Matcher Agent (BE-10); perbarui orchestration flow menjadi tujuh agent; perbarui pipeline ekstraksi dokumen untuk menyertakan RAG indexing (BE-08) | — |
| 3.0.0 | 2026-06-13 | Ganti LLM dari Claude Sonnet (Anthropic API) ke DeepSeek-V4-Flash (OpenRouter API) di section 3.2; ganti referensi embedding dari OpenAI text-embedding-3-small ke Google Gemini text-embedding-004 di diagram section 9.2; ganti referensi Anthropic API key ke OpenRouter di section 10.3 | — |
