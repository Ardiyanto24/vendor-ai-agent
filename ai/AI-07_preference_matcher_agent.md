# AI-07 — Preference Matcher Agent Specification

**Project:** AI Vendor Selection System  
**Dokumen:** AI-07 — Preference Matcher Agent  
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
4. [Konsep Preferensi Perusahaan](#4-konsep-preferensi-perusahaan)
5. [Tanggung Jawab Agent](#5-tanggung-jawab-agent)
6. [Posisi dalam Orchestration Flow](#6-posisi-dalam-orchestration-flow)
7. [Input yang Diterima](#7-input-yang-diterima)
8. [Dua Mode Output](#8-dua-mode-output)
9. [Format Output](#9-format-output)
10. [Form Input Preferensi](#10-form-input-preferensi)
11. [Penanganan Kasus Khusus](#11-penanganan-kasus-khusus)
12. [Prompt Specification](#12-prompt-specification)
13. [Integrasi dengan Scoring Engine & UI](#13-integrasi-dengan-scoring-engine--ui)
14. [Aturan & Larangan](#14-aturan--larangan)
15. [Catatan untuk Dokumen Lanjutan](#15-catatan-untuk-dokumen-lanjutan)

---

## 1. Tujuan Dokumen

Dokumen ini mendefinisikan **tanggung jawab, input, dan output Preference Matcher Agent** — agent ketujuh dan terakhir dalam pipeline evaluasi yang bertugas mencocokkan profil vendor (hasil evaluasi kuantitatif dan kualitatif) dengan preferensi bisnis perusahaan yang diinput secara opsional oleh procurement staff.

Dokumen ini menjawab pertanyaan: apa itu preferensi perusahaan dalam konteks sistem ini, bagaimana preferensi diinput, bagaimana agent menggunakannya, dan apa perbedaan output saat preferensi ada versus tidak ada.

Dokumen ini **tidak** mendefinisikan implementasi kode atau detail teknis orchestration — itu ada di AI-01.

---

## 2. Referensi Dokumen

| Kode | Nama Dokumen | Keterangan |
|---|---|---|
| AI-01 | Agent Orchestration | Posisi agent dalam alur orchestration |
| AI-02 | Prompt Library | Template prompt agent ini (perlu diperbarui) |
| AI-03 | Scoring Engine | Integrasi output preference matching ke hasil akhir |
| AI-06 | Qualitative Analyzer Agent | Output kualitatif yang dikonsumsi agent ini |
| DB-01 | Data Model & ERD | Tabel preferensi dan tabel hasil yang menyimpan output |
| FE-03 | Page & User Flow | Form input preferensi di P-03 dan tampilan di P-05 |

---

## 3. Mengapa Agent Ini Diperlukan

### 3.1 Netralitas TOPSIS adalah kekuatan sekaligus keterbatasan

Skor TOPSIS bersifat objektif dan netral — ia tidak memihak vendor manapun selama bobot kriteria sama. Ini adalah kekuatan sistem: hasil tidak dipengaruhi preferensi subjektif pengevaluasi.

Namun dalam kenyataannya, perusahaan sering memiliki konteks bisnis yang membuat vendor tertentu lebih cocok dari yang lain — bukan karena skor TOPSIS-nya lebih tinggi, tetapi karena ada faktor strategis yang tidak tercermin dalam lima kriteria standar:

- Perusahaan sedang dalam program go-green dan memprioritaskan vendor bersertifikasi lingkungan
- Perusahaan memiliki kebijakan untuk memprioritaskan vendor lokal atau UMKM
- Perusahaan sedang membangun ekosistem vendor jangka panjang dan memprioritaskan yang memiliki rekam jejak kolaborasi
- Manajemen memutuskan bahwa untuk pengadaan kali ini, kecepatan delivery lebih penting dari harga

Preferensi seperti ini tidak bisa dimasukkan ke dalam bobot kriteria TOPSIS karena sifatnya kontekstual — tidak berlaku untuk semua evaluasi.

### 3.2 Dua mode rekomendasi

Dengan adanya Preference Matcher Agent, sistem bisa beroperasi dalam dua mode yang berbeda secara fundamental:

**Mode netral** (tanpa preferensi) — sistem memberikan ranking objektif berbasis TOPSIS ditambah analisis kualitatif. Output-nya informatif: "ini urutan vendor berdasarkan metrik terukur, ini keunggulan unik masing-masing."

**Mode opinionated** (dengan preferensi) — sistem memberikan rekomendasi yang benar-benar mempertimbangkan konteks bisnis perusahaan. Output-nya actionable: "berdasarkan preferensi yang Anda nyatakan, vendor ini adalah pilihan terbaik karena alasan ini."

### 3.3 Satu agent, satu tugas

Agent ini hanya bertugas mencocokkan profil vendor dengan preferensi yang dinyatakan. Ia tidak menghitung skor TOPSIS, tidak menganalisis unique offerings dari awal, dan tidak membuat keputusan yang bersifat final. Semua data yang dibutuhkan sudah dihasilkan oleh agent-agent sebelumnya.

---

## 4. Konsep Preferensi Perusahaan

### 4.1 Apa itu preferensi dalam konteks ini

Preferensi perusahaan adalah sekumpulan pernyataan yang diinput oleh procurement staff (atau manager) yang mengekspresikan prioritas, nilai, atau constraint bisnis yang relevan untuk pengadaan tertentu — di luar apa yang sudah tercermin dalam bobot kriteria TOPSIS.

Preferensi bersifat **deklaratif** — procurement staff menyatakan apa yang penting, bukan bagaimana cara mengukurnya. LLM yang menentukan bagaimana preferensi tersebut diterapkan terhadap profil vendor yang ada.

### 4.2 Bentuk preferensi yang valid

Preferensi bisa berupa:

**Prioritas spesifik** — *"untuk pengadaan ini, kami memprioritaskan vendor yang memiliki pengalaman dengan perusahaan manufaktur skala besar"*

**Constraint bisnis** — *"perusahaan kami memiliki kebijakan mendahulukan vendor lokal jika harga tidak berbeda lebih dari 15%"*

**Nilai strategis** — *"kami sedang membangun kemitraan jangka panjang, sehingga vendor yang menunjukkan komitmen after-sales lebih diutamakan"*

**Konteks situasional** — *"proyek ini memiliki deadline ketat, kecepatan delivery adalah faktor paling kritis"*

**Kombinasi** — preferensi bisa berisi lebih dari satu pernyataan yang saling melengkapi

### 4.3 Preferensi bersifat opsional

Form preferensi tidak wajib diisi. Sistem bekerja sepenuhnya tanpa preferensi — dalam mode netral yang tetap memberikan nilai besar bagi procurement staff. Preferensi adalah fitur tambahan untuk procurement yang ingin rekomendasi yang lebih kontekstual.

### 4.4 Preferensi tidak mengubah skor TOPSIS

Penting untuk dipahami: preferensi tidak mengubah kalkulasi TOPSIS sama sekali. TOPSIS tetap dihitung secara objektif berdasarkan data dan bobot yang terkonfigurasi. Preference matching adalah lapisan interpretasi di atas hasil TOPSIS — bukan intervensi terhadap proses kalkulasi.

---

## 5. Tanggung Jawab Agent

Preference Matcher Agent bertugas untuk:

**Memahami preferensi** — menginterpretasikan pernyataan preferensi dalam konteks requirement pengadaan yang spesifik.

**Mencocokkan dengan profil vendor** — menganalisis sejauh mana setiap vendor memenuhi preferensi yang dinyatakan, berdasarkan seluruh data yang tersedia dari agent-agent sebelumnya.

**Menghasilkan rekomendasi opinionated** (mode preferensi) — menyebutkan 1–3 vendor yang paling sesuai dengan preferensi, disertai penjelasan konkret mengapa.

**Menghasilkan framing netral** (mode tanpa preferensi) — menyiapkan narasi pengantar yang memperjelas bahwa output adalah ranking objektif tanpa filter preferensi khusus.

Agent ini **tidak** bertugas:
- Mengubah atau menggantikan ranking TOPSIS
- Mendiskualifikasi vendor dari evaluasi
- Membuat keputusan final — hanya memberikan rekomendasi untuk dipertimbangkan

---

## 6. Posisi dalam Orchestration Flow

Preference Matcher Agent adalah **agent ketujuh** dan terakhir sebelum Scoring Engine. Ia berjalan setelah Qualitative Analyzer Agent selesai, karena membutuhkan output kualitatif sebagai input.

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
        Preference Matcher  ← agent ketujuh
                ↓ selesai
        Scoring Engine (AI-03)
```

**Mengapa setelah Qualitative Analyzer:** Preference Matcher membutuhkan `profil_kualitatif` dan `unique_offerings` dari Qualitative Analyzer untuk mencocokkan preferensi yang mungkin berkaitan dengan dimensi kualitatif (misalnya preferensi terhadap vendor yang menawarkan training atau dedicated support).

**Mengapa sebelum Scoring Engine:** Output Preference Matcher dibutuhkan oleh Scoring Engine sebagai input ke LLM reasoning naratif akhir.

---

## 7. Input yang Diterima

Agent ini menerima payload dari Orchestrator yang berisi:

**Preferensi perusahaan** — teks bebas yang diinput user di form preferensi. Bisa berupa satu kalimat atau beberapa paragraf. Jika tidak ada preferensi yang diinput, field ini bernilai `null`.

**Ringkasan output semua agent sebelumnya per vendor:**
- Skor finansial dan catatan dari Financial Analyzer
- Level risiko dan faktor risiko dari Risk Assessor
- Kekuatan, kelemahan, kesesuaian spesifikasi dari Performance Scorer
- Data sertifikasi dan profil publik dari Data Collector
- `profil_kualitatif` dan `unique_offerings` dari Qualitative Analyzer

**Data requirement pengadaan:**
- Kategori, deskripsi kebutuhan, budget range
- Konteks yang membantu agent memahami "relevansi" preferensi

**Catatan:** Agent ini tidak menerima skor TOPSIS numerik sebagai input — skor belum dihitung saat agent ini berjalan. Agent bekerja murni berdasarkan data kualitatif dan semi-kualitatif dari agent sebelumnya.

---

## 8. Dua Mode Output

### 8.1 Mode netral — tidak ada preferensi

Saat `preferensi` bernilai `null` atau string kosong, agent beroperasi dalam mode netral. Output berupa narasi pengantar singkat yang:

- Menyatakan bahwa evaluasi dilakukan tanpa filter preferensi khusus
- Menjelaskan bahwa ranking yang ditampilkan adalah hasil objektif berdasarkan metrik terukur
- Mendorong procurement staff untuk mempertimbangkan konteks bisnis mereka sendiri dalam interpretasi hasil

Output mode netral **tidak** mencoba membuat rekomendasi — ia hanya menyiapkan framing yang jujur untuk hasil TOPSIS.

### 8.2 Mode opinionated — ada preferensi

Saat preferensi diinput, agent beroperasi dalam mode opinionated. Output berupa:

- Interpretasi preferensi yang diinput — agent menjelaskan bagaimana ia memahami preferensi tersebut
- Analisis kesesuaian tiap vendor terhadap preferensi
- Rekomendasi 1–3 vendor yang paling sesuai, disertai reasoning konkret
- Catatan jika ada konflik antara preferensi dan hasil TOPSIS (misalnya vendor yang paling sesuai preferensi ternyata skor TOPSIS-nya rendah)

**Mengapa maksimum 3 rekomendasi:** Memberikan terlalu banyak pilihan mengurangi nilai rekomendasi. 1–3 vendor adalah rentang yang actionable — cukup untuk memberikan pilihan, tidak terlalu banyak sehingga membingungkan.

### 8.3 Transparansi konflik preferensi vs TOPSIS

Jika vendor yang paling sesuai preferensi memiliki skor TOPSIS yang jauh lebih rendah dari vendor lain, agent harus secara eksplisit menyebutkan konflik ini. Output tidak boleh menyembunyikan informasi ini demi membuat rekomendasi terlihat lebih meyakinkan.

Contoh narasi konflik yang baik: *"Vendor C paling sesuai dengan preferensi Anda untuk vendor bersertifikasi lingkungan, namun perlu diperhatikan bahwa skor TOPSIS Vendor C berada di posisi ke-3. Keputusan untuk memprioritaskan Vendor C berarti ada trade-off terhadap dimensi [kriteria yang lebih rendah]."*

---

## 9. Format Output

```json
{
  "mode": "netral | opinionated",
  "interpretasi_preferensi": "string atau null (Bahasa Indonesia — hanya diisi di mode opinionated, menjelaskan bagaimana agent memahami preferensi yang dinyatakan)",
  "analisis_kesesuaian": [
    {
      "vendor_id": "string",
      "tingkat_kesesuaian": "tinggi | sedang | rendah | tidak_relevan",
      "penjelasan": "string atau null (Bahasa Indonesia, maks 75 kata — hanya diisi jika tingkat_kesesuaian bukan tidak_relevan)"
    }
  ],
  "rekomendasi_vendor": [
    {
      "vendor_id": "string",
      "urutan": "integer (1 = paling direkomendasikan)",
      "alasan_utama": "string (Bahasa Indonesia, maks 100 kata)"
    }
  ],
  "ada_konflik_topsis": "boolean",
  "catatan_konflik": "string atau null (Bahasa Indonesia — diisi jika ada_konflik_topsis = true)",
  "narasi_pengantar": "string (Bahasa Indonesia, 75-100 kata — narasi pembuka yang akan ditampilkan di halaman hasil, berbeda tergantung mode)"
}
```

**Catatan field `rekomendasi_vendor`:**
- Di mode netral: array kosong `[]`
- Di mode opinionated: berisi 1–3 vendor yang direkomendasikan, diurutkan dari yang paling sesuai

**Catatan field `analisis_kesesuaian`:**
- Di mode netral: array kosong `[]`
- Di mode opinionated: berisi semua vendor dalam evaluasi

---

## 10. Form Input Preferensi

### 10.1 Posisi dalam alur user

Form preferensi berada di **P-03 Buat Evaluasi Baru, Langkah 1** (Requirement Pengadaan) sebagai bagian opsional di bawah form requirement utama.

Penempatannya di langkah pertama (bukan langkah terpisah) karena preferensi adalah bagian dari konteks pengadaan — sama seperti anggaran dan deadline. Procurement staff memasukkannya bersamaan dengan informasi requirement lainnya sebelum mulai menambahkan vendor.

### 10.2 Desain form

Form preferensi terdiri dari satu komponen utama:

**Textarea bebas** dengan label: *"Preferensi atau Prioritas Perusahaan (opsional)"*

Placeholder teks memberikan contoh: *"Contoh: Kami memprioritaskan vendor lokal. Proyek ini memiliki deadline ketat sehingga kecepatan delivery adalah prioritas utama. Kami sedang membangun ekosistem vendor jangka panjang."*

Tidak ada field terstruktur (dropdown, checkbox) untuk preferensi — teks bebas dipilih karena preferensi bisnis sifatnya terlalu bervariasi untuk distandarisasi dalam form terstruktur. LLM lebih baik dalam menginterpretasikan teks bebas yang natural daripada mengisi kotak-kotak yang kaku.

### 10.3 Batas input

Preferensi dibatasi maksimum **1.000 karakter** untuk menjaga fokus dan mencegah input yang terlalu panjang yang bisa membingungkan agent.

### 10.4 Preferensi tidak disimpan sebagai konfigurasi global

Preferensi bersifat **per evaluasi** — bukan konfigurasi global perusahaan. Setiap evaluasi bisa memiliki preferensi yang berbeda karena konteks pengadaan selalu berbeda. Preferensi yang diinput disimpan sebagai bagian dari data evaluasi di tabel `evaluasi`.

---

## 11. Penanganan Kasus Khusus

### 11.1 Preferensi yang bertentangan dengan requirement

Jika preferensi mengandung pernyataan yang secara logis bertentangan dengan requirement pengadaan (misalnya requirement menyebut butuh vendor internasional bersertifikasi ISO, tapi preferensi menyatakan "utamakan vendor lokal tanpa sertifikasi tertentu"), agent harus:

- Mengakui kontradiksi ini secara eksplisit dalam `interpretasi_preferensi`
- Memberikan rekomendasi berdasarkan interpretasi yang paling masuk akal
- Tidak memaksakan preferensi yang bertentangan dengan constraint teknis requirement

### 11.2 Preferensi yang sangat umum

Jika preferensi terlalu umum untuk memberikan guidance yang bermakna (misalnya hanya *"pilih yang terbaik"*), agent beroperasi mendekati mode netral — outputnya informatif tetapi tidak memberikan rekomendasi spesifik karena tidak ada dasar yang cukup untuk membedakan vendor berdasarkan preferensi tersebut.

### 11.3 Preferensi yang merujuk informasi tidak tersedia

Jika preferensi menyebut kriteria yang tidak bisa dinilai dari data yang tersedia (misalnya *"utamakan vendor yang pernah bekerja sama dengan perusahaan Fortune 500"* tapi tidak ada data portofolio klien dalam evaluasi), agent mengakui keterbatasan ini dan memberikan analisis berdasarkan data yang memang tersedia.

### 11.4 Semua vendor memiliki kesesuaian yang sama terhadap preferensi

Jika tidak ada vendor yang secara jelas lebih sesuai dengan preferensi (semua vendor memiliki `tingkat_kesesuaian` yang sama), agent menyatakan ini secara jujur daripada memaksakan urutan rekomendasi yang tidak berdasar.

---

## 12. Prompt Specification

### 12.1 Dua mode, dua versi user prompt

Agent ini menggunakan satu system prompt yang sama untuk kedua mode, tetapi user prompt template berbeda tergantung apakah preferensi ada atau tidak.

**User prompt mode netral:** Memberitahu LLM bahwa tidak ada preferensi yang diinput dan meminta output framing netral.

**User prompt mode opinionated:** Menyertakan teks preferensi dan meminta analisis kesesuaian serta rekomendasi.

Mode ditentukan oleh Orchestrator berdasarkan ada/tidaknya preferensi, sebelum memanggil agent.

### 12.2 System prompt — inti instruksi

Agent berperan sebagai konsultan pengadaan yang membantu procurement staff memahami implikasi preferensi bisnis mereka terhadap pilihan vendor yang tersedia.

Agent harus bersikap jujur tentang keterbatasan data dan tidak mengklaim bahwa preferensi adalah satu-satunya faktor yang relevan. Hasil TOPSIS dan analisis kualitatif harus tetap dihormati — preferensi adalah lensa tambahan, bukan pengganti evaluasi objektif.

Jika ada trade-off antara preferensi dan hasil kuantitatif, trade-off ini harus disampaikan secara transparan agar procurement staff bisa membuat keputusan yang informed.

Semua output naratif dalam Bahasa Indonesia. Output keseluruhan dalam format JSON yang terdefinisi.

### 12.3 Lokasi file prompt

Mengikuti konvensi AI-02 section 8.2:

```
vendor-ai-agent/
└── prompts/
    └── agents/
        └── preference_matcher/
            ├── system.md
            ├── user_template_neutral.md
            └── user_template_opinionated.md
```

---

## 13. Integrasi dengan Scoring Engine & UI

### 13.1 Output yang dikonsumsi Scoring Engine

Scoring Engine (AI-03) mengonsumsi output Preference Matcher untuk memperkaya reasoning naratif akhir:

- `narasi_pengantar` digunakan sebagai pembuka halaman hasil P-05 — procurement staff langsung melihat framing yang tepat (netral atau opinionated) saat membuka halaman hasil
- `rekomendasi_vendor` (jika ada) disertakan dalam section rekomendasi di P-05, terpisah dari ranking TOPSIS
- `catatan_konflik` (jika ada) ditampilkan sebagai callout khusus — peringatan yang tidak bisa diabaikan oleh procurement staff

### 13.2 Tampilan di P-05

Di halaman hasil, output preference matching ditampilkan sebagai **Bagian 4 — Rekomendasi Berbasis Preferensi**, setelah tiga bagian yang sudah ada:

**Jika mode netral:**
Ditampilkan narasi pendek yang menjelaskan bahwa evaluasi ini menggunakan metrik objektif tanpa filter preferensi khusus, dengan ajakan untuk mempertimbangkan konteks bisnis mereka sendiri.

**Jika mode opinionated:**
Ditampilkan rekomendasi 1–3 vendor yang paling sesuai preferensi, dengan reasoning per vendor. Jika ada konflik dengan TOPSIS, callout kuning (warning) ditampilkan secara prominan.

### 13.3 Penyimpanan di database

Output preference matcher disimpan di tabel `hasil_evaluasi` dalam kolom JSONB `preference_matching_result`. Ini memungkinkan:
- Audit trail — manager bisa melihat preferensi apa yang digunakan saat evaluasi
- Referensi historis — evaluasi lama bisa dilihat dengan konteks preferensi yang digunakan saat itu

Teks preferensi asli (yang diinput user) disimpan di tabel `evaluasi` dalam kolom `preferensi_perusahaan`.

---

## 14. Aturan & Larangan

**Dilarang mengubah atau mempengaruhi kalkulasi TOPSIS.** Preference matching terjadi setelah data dikumpulkan dari semua agent — bukan sebelum atau selama proses scoring. Agent ini tidak boleh memanipulasi data input scoring agar vendor tertentu mendapat skor lebih tinggi.

**Dilarang membuat rekomendasi final yang bersifat mutlak.** Output agent ini selalu bersifat "untuk dipertimbangkan" — bukan keputusan yang harus diikuti. Framing dalam prompt dan output harus mencerminkan ini.

**Dilarang menyembunyikan konflik antara preferensi dan TOPSIS.** Transparansi adalah prinsip utama sistem ini. Jika ada trade-off, trade-off tersebut harus dikomunikasikan secara jelas kepada procurement staff.

**Dilarang menerima preferensi lebih dari 1.000 karakter.** Validasi panjang preferensi dilakukan di level frontend (P-03) dan dikonfirmasi di level backend sebelum memanggil agent.

**Dilarang berjalan sebelum Qualitative Analyzer selesai.** Agent ini bergantung pada `profil_kualitatif` dan `unique_offerings` dari AI-06. Orchestrator harus memastikan dependency ini terpenuhi.

**Dilarang menyimpan preferensi sebagai konfigurasi global.** Preferensi selalu terikat pada satu evaluasi spesifik dan tidak boleh diterapkan secara otomatis ke evaluasi lain tanpa konfirmasi eksplisit user.

---

## 15. Catatan untuk Dokumen Lanjutan

### Untuk AI-01 (Agent Orchestration)

Agent ini perlu ditambahkan ke dalam alur orchestration sebagai agent ketujuh, setelah Qualitative Analyzer dan paralel selesai. Dependency-nya terhadap AI-06 harus eksplisit dalam alur. Tabel `agent_progress` perlu menambahkan nilai enum baru: `preference_matcher`.

### Untuk AI-02 (Prompt Library)

Dua user prompt template (mode netral dan mode opinionated) perlu ditambahkan ke dokumen prompt library. System prompt juga perlu terdokumentasi secara lengkap mengikuti format yang sudah ada.

### Untuk AI-03 (Scoring Engine)

Section 9 (Generasi Reasoning Naratif) perlu diperbarui untuk menyertakan output Preference Matcher sebagai salah satu input. Section 10 (Output) perlu mendefinisikan kolom `preference_matching_result` di tabel `hasil_evaluasi` dan bagaimana `narasi_pengantar` digunakan di halaman hasil.

### Untuk DB-01 (Data Model & ERD)

Dua perubahan diperlukan: (1) tambah kolom `preferensi_perusahaan` (Text, nullable) di tabel `evaluasi` untuk menyimpan teks preferensi yang diinput user, dan (2) tambah kolom `preference_matching_result` (JSONB, nullable) di tabel `hasil_evaluasi` untuk menyimpan output agent ini.

### Untuk FE-03 (Page & User Flow)

Halaman P-03 Langkah 1 perlu menambahkan textarea preferensi dengan label, placeholder, dan batas karakter yang terdefinisi di section 10. Halaman P-05 perlu Bagian 4 baru untuk menampilkan output preference matching, termasuk callout konflik jika ada.

### Untuk FE-02 (Component Library)

Perlu komponen baru: `PreferenceRecommendationCard` (menampilkan rekomendasi vendor berdasarkan preferensi) dan `ConflictCallout` (menampilkan peringatan konflik antara preferensi dan TOPSIS secara prominan).

### Untuk SH-03 (Testing Strategy)

Testing agent ini perlu mencakup tiga skenario utama: (1) mode netral — output framing yang benar tanpa rekomendasi, (2) mode opinionated dengan preferensi yang jelas — rekomendasi yang tepat sasaran, dan (3) mode opinionated dengan konflik preferensi vs TOPSIS — konflik harus terdeteksi dan dilaporkan dengan benar.

---

*Dokumen ini adalah living document — definisi dan mekanisme pencocokan preferensi dapat disempurnakan berdasarkan feedback penggunaan nyata dari procurement staff.*

---

**Riwayat Perubahan**

| Versi | Tanggal | Perubahan | Author |
|---|---|---|---|
| 1.0.0 | 2026-06-11 | Versi awal | — |
