# AI-06 — Qualitative Analyzer Agent Specification

**Project:** AI Vendor Selection System  
**Dokumen:** AI-06 — Qualitative Analyzer Agent  
**Versi:** 1.0.0  
**Tanggal:** 2026-06-11  
**Status:** Draft  
**Author:** —  
**Direview oleh:** —

---

## Daftar Isi

1. [Tujuan Dokumen](#1-tujuan-dokumen)
2. [Referensi Dokumen](#2-referensi-dokumen)
3. [Mengapa Agent Ini Diperlukan](#3-mengapa-agent-ini-diperlukan)
4. [Tanggung Jawab Agent](#4-tanggung-jawab-agent)
5. [Posisi dalam Orchestration Flow](#5-posisi-dalam-orchestration-flow)
6. [Input yang Diterima](#6-input-yang-diterima)
7. [Proses Analisis](#7-proses-analisis)
8. [Format Output](#8-format-output)
9. [Penanganan Kasus Khusus](#9-penanganan-kasus-khusus)
10. [Prompt Specification](#10-prompt-specification)
11. [Integrasi dengan Scoring Engine](#11-integrasi-dengan-scoring-engine)
12. [Aturan & Larangan](#12-aturan--larangan)
13. [Catatan untuk Dokumen Lanjutan](#13-catatan-untuk-dokumen-lanjutan)

---

## 1. Tujuan Dokumen

Dokumen ini mendefinisikan **tanggung jawab, input, proses, dan output Qualitative Analyzer Agent** — agent keenam dalam sistem evaluasi vendor yang bertugas mengidentifikasi dan menganalisis nilai tambah unik tiap vendor di luar lima kriteria utama yang diukur secara kuantitatif.

Dokumen ini menjawab pertanyaan: apa yang dianalisis agent ini, bagaimana ia menemukan nilai tambah yang tidak terstruktur, dan dalam format apa outputnya dihasilkan.

Dokumen ini **tidak** mendefinisikan implementasi kode atau detail teknis orchestration — itu ada di AI-01. Dokumen ini fokus pada **apa** yang dilakukan agent ini dan **mengapa** ia perlu ada.

---

## 2. Referensi Dokumen

| Kode | Nama Dokumen | Keterangan |
|---|---|---|
| AI-01 | Agent Orchestration | Posisi agent dalam alur orchestration |
| AI-02 | Prompt Library | Template prompt agent ini (perlu diperbarui) |
| AI-03 | Scoring Engine | Integrasi output kualitatif ke dalam hasil akhir |
| AI-05 | RAG Specification | Sumber data dokumen yang digunakan agent ini |
| DB-01 | Data Model & ERD | Tabel `hasil_vendor` yang menyimpan output agent ini |

---

## 3. Mengapa Agent Ini Diperlukan

### 3.1 Keterbatasan metrik kuantitatif

Lima kriteria TOPSIS (Harga & TCO, Kualitas & Track Record, Kemampuan Delivery, Risiko & Legalitas, Support & After-sales) dirancang untuk mengukur dimensi yang universal — ada di semua penawaran vendor dalam bentuk yang sebanding.

Namun dalam praktik pengadaan nyata, vendor sering menawarkan hal-hal di luar standar yang sulit dikuantifikasi namun sangat relevan untuk keputusan akhir:

- Vendor A menawarkan free on-site training selama 6 bulan
- Vendor B menawarkan dedicated account manager yang bisa dihubungi 24/7
- Vendor C menyertakan garansi buyback setelah 3 tahun
- Vendor D menawarkan pilot project gratis sebelum kontrak penuh

Nilai tambah seperti ini tidak masuk ke mana pun dalam kalkulasi TOPSIS karena tidak sebanding antar vendor — vendor B tidak "lebih baik dari vendor A di dimensi training" karena keduanya menawarkan sesuatu yang berbeda, bukan hal yang sama dalam skala berbeda.

### 3.2 Masalah tie-breaking

TOPSIS dapat menghasilkan skor yang sama atau sangat berdekatan antar dua atau lebih vendor — terutama jika konfigurasi bobot kriteria seimbang dan profil vendor mirip. Dalam kondisi ini, procurement staff tidak memiliki dasar yang kuat untuk memilih salah satu.

Analisis kualitatif memberikan dimensi pembeda yang tidak bisa dimanipulasi oleh angka — nilai tambah nyata yang ditawarkan vendor dalam dokumen penawarannya.

### 3.3 Satu agent, satu tugas

Sesuai prinsip sistem ini, agent ini **hanya** bertugas mengidentifikasi dan menganalisis nilai tambah unik per vendor. Agent ini tidak menghitung skor, tidak menilai risiko, dan tidak membuat rekomendasi final — itu adalah tanggung jawab komponen lain.

---

## 4. Tanggung Jawab Agent

Qualitative Analyzer Agent bertugas untuk:

**Mengidentifikasi unique offerings** — hal-hal yang ditawarkan vendor di luar lima kriteria utama, yang ditemukan dalam dokumen penawaran atau data yang dikumpulkan Data Collector Agent.

**Mengklasifikasikan relevansi** — menilai apakah setiap unique offering relevan dengan kebutuhan pengadaan yang didefinisikan dalam requirement, atau hanya "bonus" yang tidak terlalu berdampak.

**Membandingkan secara naratif** — menghasilkan narasi yang menggambarkan profil kualitatif tiap vendor dan apa yang membedakannya dari vendor lain dalam evaluasi yang sama.

**Mengidentifikasi potensi tie-breaking** — jika dua atau lebih vendor memiliki skor TOPSIS yang berdekatan, agent ini secara eksplisit menyoroti unique offerings mana yang bisa menjadi faktor pembeda yang signifikan.

Agent ini **tidak** bertugas:
- Menghitung skor numerik untuk unique offerings
- Membuat keputusan final tentang vendor mana yang dipilih
- Menggantikan atau mengoverride hasil TOPSIS

---

## 5. Posisi dalam Orchestration Flow

Qualitative Analyzer Agent adalah **agent keenam** yang berjalan setelah kelima agent awal selesai, **paralel dengan Negotiation Assistant Agent**.

```
Data Collector ─────────────────────────────────┐
Financial Analyzer ─────────────────────────────┤ (paralel)
Risk Assessor ──────────────────────────────────┘
        ↓ semua selesai
Performance Scorer
        ↓ selesai
        ├── Negotiation Assistant ──────────────┐ (paralel)
        └── Qualitative Analyzer ───────────────┘
                ↓ keduanya selesai
        Preference Matcher (AI-07)
                ↓ selesai
        Scoring Engine (AI-03)
```

**Mengapa paralel dengan Negotiation Assistant:** Keduanya membutuhkan output dari lima agent pertama sebagai input, tetapi tidak saling bergantung satu sama lain. Menjalankan keduanya paralel menghemat waktu total evaluasi.

**Mengapa sebelum Scoring Engine:** Output Qualitative Analyzer Agent dibutuhkan oleh Scoring Engine untuk disertakan dalam reasoning naratif hasil akhir, dan oleh Preference Matcher (AI-07) untuk pencocokan preferensi.

---

## 6. Input yang Diterima

Agent ini menerima payload dari Orchestrator yang berisi:

**Data requirement pengadaan:**
- Judul dan deskripsi kebutuhan
- Kategori pengadaan
- Spesifikasi teknis yang diminta (jika ada)

**Output dari lima agent sebelumnya (per vendor):**
- Data profil dari Data Collector (sertifikasi, berita, profil perusahaan)
- Catatan finansial dari Financial Analyzer (komponen biaya yang teridentifikasi)
- Faktor risiko dari Risk Assessor
- Kekuatan dan kelemahan dari Performance Scorer

**Konteks RAG (via AI-05):**
- Top chunks dari dokumen penawaran tiap vendor yang relevan dengan identifikasi unique offerings
- Agent ini menggunakan retrieval dengan query: *"nilai tambah khusus keunggulan tambahan layanan ekstra yang ditawarkan"* untuk setiap vendor

**Mengapa agent ini butuh RAG context:** Unique offerings sering tersembunyi di bagian "nilai tambah", "keunggulan kami", atau di klausul-klausul spesifik dalam dokumen penawaran yang tidak selalu tertangkap oleh ekstraksi field terstruktur. RAG memungkinkan agent ini menemukan informasi ini langsung dari teks dokumen.

---

## 7. Proses Analisis

### 7.1 Identifikasi unique offerings per vendor

Agent menganalisis setiap vendor secara individual untuk mengidentifikasi apa yang ditawarkan vendor tersebut di luar standar yang diminta dalam requirement. Sumber informasi yang diperiksa:

- Teks dokumen penawaran (via RAG context)
- Field `komponen_biaya_tambahan` dari Financial Analyzer (program bundling, layanan gratis)
- Field `kekuatan` dari Performance Scorer (kapabilitas khusus yang menonjol)
- Data sertifikasi dari Data Collector (sertifikasi yang tidak diminta tapi relevan)

### 7.2 Klasifikasi relevansi

Setiap unique offering diklasifikasikan berdasarkan relevansinya terhadap requirement pengadaan:

**Sangat relevan** — langsung mendukung kebutuhan utama yang dinyatakan dalam requirement. Contoh: requirement menyebut butuh training, vendor menawarkan extended training program.

**Relevan** — tidak langsung disebutkan dalam requirement tetapi memberikan nilai nyata untuk penggunaan yang dimaksud.

**Netral** — merupakan keunggulan vendor secara umum tetapi tidak spesifik relevan untuk pengadaan ini.

### 7.3 Analisis komparatif

Setelah semua vendor dianalisis secara individual, agent melakukan perbandingan untuk mengidentifikasi:

- Unique offering yang hanya dimiliki satu vendor (benar-benar unik)
- Pola nilai tambah yang membedakan kelompok vendor
- Potensi tie-breaker — vendor mana yang unique offerings-nya paling relevan jika skor TOPSIS mereka berdekatan

Agent tidak mengetahui skor TOPSIS saat analisis ini dilakukan — skor belum dihitung. Agent hanya membandingkan profil kualitatif berdasarkan isi dokumen dan output agent lain.

---

## 8. Format Output

Output agent ini adalah **narasi per vendor** dalam Bahasa Indonesia, bukan skor numerik. Setiap vendor menghasilkan satu objek dengan struktur berikut:

```json
{
  "vendor_id": "string",
  "unique_offerings": [
    {
      "deskripsi": "string (Bahasa Indonesia, maks 50 kata)",
      "relevansi": "sangat_relevan | relevan | netral",
      "sumber": "dokumen_penawaran | data_collector | performance_scorer | financial_analyzer"
    }
  ],
  "profil_kualitatif": "string (Bahasa Indonesia, 100-150 kata — narasi singkat yang menggambarkan karakter dan keunggulan unik vendor ini secara keseluruhan)",
  "potensi_tie_breaker": "boolean (true jika unique offerings vendor ini signifikan sebagai pembeda)",
  "catatan_tie_breaker": "string atau null (Bahasa Indonesia — penjelasan mengapa ini bisa jadi tie-breaker, hanya diisi jika potensi_tie_breaker = true)"
}
```

**Output keseluruhan evaluasi** adalah array dari objek di atas (satu per vendor), ditambah satu objek summary:

```json
{
  "analisis_per_vendor": [...],
  "summary_komparatif": "string (Bahasa Indonesia, 100-150 kata — narasi yang membandingkan profil kualitatif semua vendor secara ringkas, tanpa menyebut angka skor)"
}
```

**Mengapa output tidak berupa skor numerik:**

Unique offerings tidak sebanding secara kuantitatif. Vendor A yang menawarkan free training tidak bisa diberi skor 80 dan vendor B yang menawarkan dedicated account manager diberi skor 70 — perbandingan ini tidak bermakna karena keduanya adalah hal yang berbeda, bukan hal yang sama dalam derajat berbeda. Narasi adalah medium yang tepat untuk menggambarkan perbedaan yang sifatnya kualitatif.

---

## 9. Penanganan Kasus Khusus

### 9.1 Vendor tanpa unique offering yang teridentifikasi

Tidak semua vendor menawarkan sesuatu di luar standar. Jika agent tidak menemukan unique offering yang nyata setelah memeriksa semua sumber:

- `unique_offerings` diisi dengan array kosong
- `profil_kualitatif` menggambarkan vendor sebagai penawaran standar tanpa keunggulan tambahan yang teridentifikasi
- `potensi_tie_breaker` diset `false`

Agent tidak boleh mengarang unique offering yang tidak ada dalam data.

### 9.2 RAG context tidak tersedia

Jika indexing dokumen gagal atau tidak selesai untuk vendor tertentu (AI-05 section 12.1 dan 12.2), agent tetap berjalan menggunakan output dari agent lain sebagai sumber utama. Dalam kasus ini:

- Output mungkin kurang lengkap karena tidak bisa mengakses detail dokumen
- Flag `sumber` pada setiap unique offering tidak akan mengandung nilai `dokumen_penawaran`
- Tidak ada pesan error — agent melakukan yang terbaik dengan data yang tersedia

### 9.3 Semua vendor memiliki profil kualitatif yang mirip

Dalam beberapa evaluasi, semua vendor menawarkan hal yang serupa tanpa diferensiasi signifikan. Dalam kasus ini, `summary_komparatif` menyatakan secara eksplisit bahwa diferensiasi kualitatif antar vendor minimal — ini adalah informasi yang valid dan berguna untuk procurement staff.

---

## 10. Prompt Specification

### 10.1 Karakteristik prompt yang berbeda

Berbeda dari lima agent lain yang menghasilkan output JSON dengan skor numerik, Qualitative Analyzer Agent menghasilkan narasi. Prompt dirancang untuk mendorong analisis yang:
- Spesifik dan berbasis data — tidak membuat klaim yang tidak didukung dokumen
- Komparatif — sadar bahwa ada beberapa vendor yang sedang dibandingkan
- Jujur tentang keterbatasan — mengakui jika informasi tidak cukup

### 10.2 System prompt — inti instruksi

Agent berperan sebagai analis pengadaan yang bertugas mengidentifikasi nilai tambah unik dan diferensiasi kualitatif dari setiap vendor kandidat di luar kriteria evaluasi standar.

Agent harus fokus pada hal-hal yang *nyata* dan *spesifik* yang disebutkan dalam dokumen penawaran atau data yang tersedia — bukan klaim umum tentang kualitas vendor. Contoh yang salah: "vendor ini terkenal berkualitas." Contoh yang benar: "vendor ini menawarkan garansi penggantian unit dalam 24 jam yang tidak disebutkan dalam penawaran vendor lain."

Agent harus mengakui jika informasi tidak tersedia daripada membuat asumsi.

Semua output naratif dalam Bahasa Indonesia. Output keseluruhan dalam format JSON yang terdefinisi.

### 10.3 User prompt template

User prompt menyertakan:
- Deskripsi requirement pengadaan (apa yang dibutuhkan, untuk apa)
- Per vendor: nama, output ringkas dari lima agent sebelumnya, dan RAG context dari dokumen penawaran
- Instruksi eksplisit untuk membandingkan antar vendor dalam summary

### 10.4 Lokasi file prompt

Mengikuti konvensi AI-02 section 8.2:

```
vendor-ai-agent/
└── prompts/
    └── agents/
        └── qualitative_analyzer/
            ├── system.md
            └── user_template.md
```

---

## 11. Integrasi dengan Scoring Engine

### 11.1 Output yang dikonsumsi Scoring Engine

Scoring Engine (AI-03) mengonsumsi output Qualitative Analyzer Agent untuk dua tujuan:

**Reasoning naratif** — `profil_kualitatif` dan `summary_komparatif` disertakan sebagai input ke LLM yang menghasilkan reasoning naratif akhir (AI-03 section 9). Ini memperkaya penjelasan dengan dimensi kualitatif yang tidak tertangkap oleh angka skor.

**Penyimpanan hasil** — `unique_offerings` dan `profil_kualitatif` per vendor disimpan di tabel `hasil_vendor` dalam kolom JSONB tersendiri, terpisah dari `skor_per_kriteria`.

### 11.2 Ditampilkan di halaman hasil (P-05)

Output kualitatif ditampilkan di P-05 sebagai bagian tambahan setelah ranking TOPSIS — bukan menggantikannya. Procurement staff melihat:

1. Ranking TOPSIS dengan skor per kriteria (seperti sebelumnya)
2. **Seksi baru: Profil Kualitatif** — narasi unique offerings per vendor
3. Summary komparatif kualitatif

---

## 12. Aturan & Larangan

**Dilarang menghasilkan skor numerik untuk unique offerings.** Output agent ini adalah narasi murni — tidak ada angka, tidak ada rating, tidak ada persentase. Jika ada kebutuhan untuk membandingkan secara kuantitatif, itu bukan tanggung jawab agent ini.

**Dilarang membuat klaim tanpa dasar data.** Setiap unique offering yang disebutkan harus bisa ditelusuri ke sumber spesifik — dokumen penawaran (dengan referensi halaman jika memungkinkan) atau output agent lain. Klaim yang tidak bisa diverifikasi tidak boleh masuk ke output.

**Dilarang menggantikan atau mengoverride hasil TOPSIS.** Output agent ini adalah lapisan tambahan, bukan pengganti evaluasi kuantitatif. Jika unique offerings sebuah vendor sangat impressive tetapi skor TOPSIS-nya rendah karena alasan yang valid, agent ini tidak boleh mengklaim vendor tersebut layak direkomendasikan.

**Dilarang mengakses database secara langsung.** Semua data yang dibutuhkan sudah ada dalam payload dari Orchestrator dan RAG context. Agent tetap stateless.

**Dilarang berjalan sebelum Performance Scorer selesai.** Agent ini bergantung pada output Performance Scorer (field `kekuatan` dan `kelemahan`). Orchestrator harus memastikan dependency ini terpenuhi.

---

## 13. Catatan untuk Dokumen Lanjutan

### Untuk AI-01 (Agent Orchestration)

Agent ini perlu ditambahkan ke dalam alur orchestration sebagai agent keenam. Posisinya paralel dengan Negotiation Assistant, setelah Performance Scorer selesai. Tabel `agent_progress` perlu menambahkan nilai enum baru: `qualitative_analyzer`.

### Untuk AI-02 (Prompt Library)

Prompt system dan user template untuk agent ini perlu ditambahkan ke dalam dokumen prompt library, mengikuti format yang sudah ada untuk lima agent lainnya.

### Untuk AI-03 (Scoring Engine)

Section 9 (Generasi Reasoning Naratif) perlu diperbarui untuk menyertakan output Qualitative Analyzer Agent sebagai salah satu input ke LLM reasoning. Section 10 (Output Scoring Engine) perlu diperbarui untuk mendefinisikan field tambahan di `hasil_vendor` yang menyimpan data kualitatif.

### Untuk DB-01 (Data Model & ERD)

Tabel `hasil_vendor` perlu menambahkan dua kolom JSONB: `unique_offerings` dan `profil_kualitatif` untuk menyimpan output agent ini.

### Untuk FE-03 (Page & User Flow)

Halaman P-05 perlu seksi baru untuk menampilkan profil kualitatif dan summary komparatif. FE-02 perlu komponen baru untuk menampilkan unique offerings dalam format yang mudah dibaca.

### Untuk SH-03 (Testing Strategy)

Testing agent ini berfokus pada kualitas output naratif — apakah unique offerings yang teridentifikasi nyata dan spesifik, apakah klaim dapat ditelusuri ke sumber data. Test case perlu mencakup: vendor dengan banyak unique offerings, vendor tanpa unique offering, dan skenario RAG context tidak tersedia.

---

*Dokumen ini adalah living document — definisi "unique offering" dan kriteria relevansi dapat disempurnakan berdasarkan feedback dari pengguna sistem.*

---

**Riwayat Perubahan**

| Versi | Tanggal | Perubahan | Author |
|---|---|---|---|
| 1.0.0 | 2026-06-11 | Versi awal | — | 
| 1.1.0 | 2026-06-13 | Rename dari BE-09 ke AI-06 (ADR-035); perbarui semua referensi kode dokumen ke namespace AI | — |
