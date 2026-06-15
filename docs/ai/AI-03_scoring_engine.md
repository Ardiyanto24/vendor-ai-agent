# AI-03 — Scoring Engine Specification

**Project:** AI Vendor Selection System  
**Dokumen:** AI-03 — Scoring Engine  
**Versi:** 2.0.0  
**Tanggal:** 2026-06-11  
**Status:** Draft  
**Author:** —  
**Direview oleh:** —

---

## Daftar Isi

1. [Tujuan Dokumen](#1-tujuan-dokumen)
2. [Referensi Dokumen](#2-referensi-dokumen)
3. [Gambaran Scoring Engine](#3-gambaran-scoring-engine)
4. [Metodologi: TOPSIS](#4-metodologi-topsis)
5. [Tahapan Kalkulasi](#5-tahapan-kalkulasi)
6. [Normalisasi Data Mentah dari Agent](#6-normalisasi-data-mentah-dari-agent)
7. [Penanganan Data Tidak Lengkap](#7-penanganan-data-tidak-lengkap)
8. [Threshold Minimum](#8-threshold-minimum)
9. [Generasi Reasoning Naratif](#9-generasi-reasoning-naratif)
10. [Integrasi Output Kualitatif & Preferensi](#10-integrasi-output-kualitatif--preferensi)
11. [Output Scoring Engine](#11-output-scoring-engine)
12. [Validasi & Sanity Check](#12-validasi--sanity-check)
13. [Aturan & Larangan](#13-aturan--larangan)
14. [Catatan untuk Dokumen Lanjutan](#14-catatan-untuk-dokumen-lanjutan)

---

## 1. Tujuan Dokumen

Dokumen ini mendefinisikan **bagaimana skor akhir vendor dihitung** — metodologi yang digunakan, bagaimana data mentah dari agent dinormalisasi, bagaimana bobot diterapkan, dan bagaimana reasoning naratif dihasilkan dari angka-angka tersebut.

Dokumen ini menjawab pertanyaan: mengapa TOPSIS dipilih, bagaimana data dari lima agent yang berbeda format disatukan menjadi satu skor yang adil, dan bagaimana sistem menghasilkan penjelasan yang dapat dimengerti manusia dari proses matematis ini.

Dokumen ini **tidak** mendefinisikan implementasi kode — itu diserahkan ke engineer. Dokumen ini mendefinisikan **apa** yang dihitung dan **mengapa** demikian.

---

## 2. Referensi Dokumen

| Kode | Nama Dokumen | Keterangan |
|---|---|---|
| AI-01 | Agent Orchestration | Memanggil Scoring Engine setelah semua agent selesai |
| AI-02 | Prompt Library | Format JSON output agent yang menjadi input scoring |
| AI-06 | Qualitative Analyzer Agent | Output kualitatif yang diintegrasikan ke hasil akhir |
| AI-07 | Preference Matcher Agent | Output preferensi yang diintegrasikan ke hasil akhir |
| DB-01 | Data Model & ERD | Tabel `hasil_evaluasi` dan `hasil_vendor` yang diisi |
| FE-03 | Page & User Flow | Halaman P-05 yang menampilkan output scoring |

---

## 3. Gambaran Scoring Engine

### 3.1 Posisi dalam sistem

Scoring Engine adalah komponen Python murni — tidak menggunakan LLM. Ia menerima data agregat dari Orchestrator (hasil kelima agent), menjalankan kalkulasi matematis, dan menghasilkan ranking beserta skor yang dapat dijelaskan.

**Mengapa scoring tidak menggunakan LLM:** Scoring adalah proses matematis yang harus deterministik dan reproducible. Input yang sama harus selalu menghasilkan output yang sama. LLM bersifat non-deterministik — tidak cocok untuk kalkulasi yang hasilnya harus dapat diaudit.

**LLM tetap digunakan untuk satu bagian:** Generasi reasoning naratif (section 9) — mengubah angka menjadi penjelasan bahasa alami. Bagian ini tidak mempengaruhi skor numerik.

### 3.2 Library yang digunakan

Kalkulasi TOPSIS menggunakan **numpy** dan **scipy** — library standar Python untuk komputasi numerik. Tidak ada library MCDM eksternal yang digunakan agar tim memiliki kontrol penuh atas implementasi dan dapat mengaudit setiap langkah kalkulasi.

### 3.3 Input yang diterima

Scoring Engine menerima satu payload dari Orchestrator yang berisi:
- Data agregat dari kelima agent kuantitatif per vendor (dalam format yang sudah dinormalisasi — lihat section 6)
- Konfigurasi kriteria aktif: nama kriteria, bobot, dan threshold minimum
- Metadata evaluasi: ID evaluasi, kategori, jumlah vendor
- Output Qualitative Analyzer: `analisis_per_vendor` dan `summary_komparatif` (dari AI-06)
- Output Preference Matcher: `mode`, `rekomendasi_vendor`, `narasi_pengantar`, dan `catatan_konflik` jika ada (dari AI-07)

---

## 4. Metodologi: TOPSIS

### 4.1 Apa itu TOPSIS

TOPSIS (Technique for Order Preference by Similarity to Ideal Solution) adalah metode pengambilan keputusan multi-kriteria yang meranking alternatif berdasarkan jaraknya terhadap solusi ideal positif (vendor terbaik yang mungkin) dan solusi ideal negatif (vendor terburuk yang mungkin).

Vendor dengan skor TOPSIS tertinggi adalah vendor yang paling dekat dengan solusi ideal positif sekaligus paling jauh dari solusi ideal negatif.

### 4.2 Mengapa TOPSIS dipilih

**Dapat dijelaskan secara intuitif:** Konsep "vendor ini paling mendekati kondisi ideal dan paling jauh dari kondisi terburuk" mudah dikomunikasikan ke stakeholder non-teknis dibanding metode lain seperti AHP yang membutuhkan pairwise comparison matrix.

**Menangani trade-off dengan baik:** TOPSIS tidak hanya mencari vendor yang terbaik di satu kriteria — ia mencari vendor dengan keseimbangan terbaik secara keseluruhan. Vendor yang sangat unggul di satu dimensi tapi sangat buruk di dimensi lain tidak akan otomatis menang.

**Cocok untuk latar belakang statistika:** TOPSIS berbasis aljabar linear dan jarak Euclidean — konsep yang familiar bagi siapapun dengan background statistika atau ML.

**Deterministik:** Dengan input yang sama, TOPSIS selalu menghasilkan output yang sama. Tidak ada elemen probabilistik yang membuat hasil sulit direproduksi.

### 4.3 Keterbatasan yang perlu disadari

TOPSIS mengasumsikan bahwa semua kriteria sudah dalam skala yang sebanding. Oleh karena itu, normalisasi data mentah (section 6) adalah langkah yang sama pentingnya dengan kalkulasi TOPSIS itu sendiri.

TOPSIS juga sensitif terhadap penambahan atau pengurangan alternatif — menambahkan vendor baru ke evaluasi yang sudah berjalan bisa mengubah ranking vendor yang sudah ada. Untuk alasan ini, daftar vendor dikunci saat evaluasi disubmit dan tidak bisa diubah setelah proses dimulai.

---

## 5. Tahapan Kalkulasi

TOPSIS dijalankan dalam enam tahap yang berurutan. Setiap tahap menghasilkan matriks atau vektor yang menjadi input tahap berikutnya.

### Tahap 1 — Bangun decision matrix

Decision matrix adalah tabel dengan baris = vendor dan kolom = kriteria. Setiap sel berisi nilai mentah vendor tersebut di kriteria tersebut, setelah dinormalisasi ke skala 0–100 (proses normalisasi dijelaskan di section 6).

Pada tahap ini, semua nilai sudah dalam skala yang sama dan semua kriteria sudah dikonversi ke arah "semakin tinggi semakin baik" (benefit criteria). Untuk kriteria yang awalnya "semakin rendah semakin baik" (misalnya risiko), nilai sudah di-invert sebelum masuk ke matriks ini.

### Tahap 2 — Normalisasi vektor (vector normalization)

Setiap nilai dalam decision matrix dibagi dengan akar kuadrat dari jumlah kuadrat seluruh nilai dalam kolom yang sama. Ini menghasilkan matriks ternormalisasi di mana setiap kolom memiliki magnitude vektor yang sama — memastikan tidak ada satu kriteria pun yang mendominasi hanya karena skala nilainya lebih besar.

### Tahap 3 — Terapkan bobot

Setiap elemen dalam matriks ternormalisasi dikalikan dengan bobot kriteria yang dikonfigurasi manager (dalam desimal, total = 1.0). Ini menghasilkan weighted normalized decision matrix.

### Tahap 4 — Tentukan solusi ideal positif dan negatif

- **Solusi ideal positif (A+):** Untuk setiap kriteria, ambil nilai tertinggi dari semua vendor
- **Solusi ideal negatif (A-):** Untuk setiap kriteria, ambil nilai terendah dari semua vendor

A+ merepresentasikan "vendor sempurna yang unggul di semua kriteria". A- merepresentasikan "vendor terburuk yang lemah di semua kriteria". Keduanya tidak harus merepresentasikan vendor yang nyata — mereka adalah referensi matematis.

### Tahap 5 — Hitung jarak ke solusi ideal

Untuk setiap vendor, hitung:
- **D+:** Jarak Euclidean vendor tersebut ke solusi ideal positif (A+)
- **D-:** Jarak Euclidean vendor tersebut ke solusi ideal negatif (A-)

Vendor yang baik memiliki D+ kecil (dekat dengan ideal) dan D- besar (jauh dari yang terburuk).

### Tahap 6 — Hitung skor akhir dan ranking

Skor TOPSIS setiap vendor dihitung sebagai:

```
Skor = D- / (D+ + D-)
```

Nilai skor berkisar antara 0 hingga 1. Skor kemudian dikalikan 100 untuk menghasilkan skala 0–100 yang lebih intuitif.

Vendor diurutkan dari skor tertinggi ke terendah. Vendor dengan skor tertinggi adalah rekomendasi utama, dengan asumsi ia juga lolos threshold minimum (section 8).

---

## 6. Normalisasi Data Mentah dari Agent

Data mentah dari kelima agent memiliki format yang berbeda-beda dan perlu dinormalisasi ke skala 0–100 yang seragam sebelum masuk ke decision matrix TOPSIS.

### 6.1 Pemetaan output agent ke kriteria scoring

Lima kriteria evaluasi dipetakan dari output agent sebagai berikut:

| Kriteria | Sumber Data | Field yang Digunakan |
|---|---|---|
| Harga & TCO | Financial Analyzer | `skor_finansial` |
| Kualitas & Track Record | Performance Scorer | `skor_performa` |
| Kemampuan Delivery | Performance Scorer | `kesesuaian_spesifikasi` + `skor_garansi_support` |
| Risiko & Legalitas | Risk Assessor | `skor_risiko` |
| Support & After-sales | Performance Scorer | `skor_garansi_support` + Data Collector `sertifikasi` |

Beberapa kriteria mengambil data dari lebih dari satu agent — dalam kasus ini, nilai digabungkan dengan rata-rata tertimbang yang sudah terdefinisi.

### 6.2 Field yang sudah dalam skala 0–100

Field berikut dari output agent sudah dalam skala 0–100 dan dapat langsung digunakan tanpa transformasi tambahan:
- `skor_finansial` (Financial Analyzer)
- `skor_risiko` (Risk Assessor)
- `skor_performa` (Performance Scorer)
- `skor_garansi_support` (Performance Scorer)

### 6.3 Field kategorikal yang perlu dikonversi

Field `kesesuaian_spesifikasi` dan `posisi_harga` adalah enum yang perlu dikonversi ke angka:

**`kesesuaian_spesifikasi`:**

| Nilai | Skor |
|---|---|
| `sangat_sesuai` | 100 |
| `sesuai` | 80 |
| `sebagian_sesuai` | 50 |
| `tidak_sesuai` | 10 |
| `tidak_dapat_dinilai` | 50 (nilai tengah, dengan flag ketidakpastian) |

**`posisi_harga`:**

| Nilai | Skor |
|---|---|
| `sangat_kompetitif` | 100 |
| `kompetitif` | 80 |
| `wajar` | 60 |
| `mahal` | 30 |
| `tidak_dapat_dinilai` | 60 (nilai tengah, dengan flag ketidakpastian) |

### 6.4 Penanganan `tidak_dapat_dinilai`

Nilai `tidak_dapat_dinilai` mendapat skor tengah (50 atau 60 tergantung konteks) dengan flag `data_tidak_lengkap: true` yang disertakan dalam output. Flag ini ditampilkan sebagai indikator visual di halaman hasil untuk memberi tahu user bahwa skor kriteria tertentu kurang dapat diandalkan.

---

## 7. Penanganan Data Tidak Lengkap

### 7.1 Skenario data tidak lengkap

Data bisa tidak lengkap karena dua alasan: agent gagal (dijelaskan di AI-01 section 7) atau agent tidak bisa menemukan informasi yang dibutuhkan (melaporkan `null`).

### 7.2 Strategi per kriteria

**Jika Financial Analyzer gagal total:** Skor `harga_tco` dihitung hanya dari harga penawaran nominal — vendor dengan harga terendah mendapat skor tertinggi, dilinearkan ke skala 0–100. Catatan peringatan ditambahkan ke reasoning.

**Jika Risk Assessor gagal total:** Skor `risiko_legalitas` diset ke nilai default 50 (risiko sedang) untuk semua vendor. Peringatan ditambahkan bahwa penilaian risiko tidak dilakukan.

**Jika Performance Scorer gagal total:** Skor `kualitas_track_record` dan `kemampuan_delivery` diset ke nilai default 50. Peringatan ditambahkan.

**Jika Data Collector gagal:** Komponen sertifikasi dalam kriteria `support_aftersales` tidak dihitung. Bobot dari komponen tersebut dialihkan ke komponen lain dalam kriteria yang sama secara proporsional.

**Jika Negotiation Assistant gagal:** Tidak mempengaruhi skor — reasoning negosiasi dikosongkan dengan catatan bahwa rekomendasi negosiasi tidak tersedia.

**Jika Qualitative Analyzer gagal:** Bagian kualitatif dalam output dikosongkan. TOPSIS tetap dihitung penuh. Reasoning naratif dihasilkan tanpa komponen kualitatif. Preference Matcher yang bergantung pada output kualitatif akan beroperasi dalam mode terdegradasi (lihat section 7.4).

**Jika Preference Matcher gagal:** Bagian rekomendasi berbasis preferensi dikosongkan. Output hanya berisi ranking TOPSIS dan analisis kualitatif tanpa layer preferensi. Procurement staff perlu menginterpretasikan hasil terhadap preferensi mereka sendiri.

### 7.4 Degradasi bertingkat

Jika Qualitative Analyzer gagal dan ada preferensi yang diinput, Preference Matcher tetap berjalan tetapi hanya mencocokkan preferensi dengan data kuantitatif dari agent 1–5. Output-nya dihasilkan dengan flag `kualitas_terdegradasi: true` dan catatan bahwa pencocokan tidak mencakup dimensi kualitatif karena Qualitative Analyzer gagal.

### 7.3 Minimum data untuk menghasilkan skor

Scoring Engine harus dapat menghasilkan output selama minimal **tiga dari lima** kriteria memiliki data yang cukup. Jika kurang dari tiga kriteria memiliki data, evaluasi ditandai sebagai `tidak_dapat_dihitung` dan user diminta untuk mengevaluasi ulang.

---

## 8. Threshold Minimum

### 8.1 Fungsi threshold

Threshold minimum adalah skor terendah yang harus dicapai vendor di satu kriteria tertentu agar dianggap layak. Vendor yang tidak memenuhi threshold di satu atau lebih kriteria ditandai dengan `lolos_threshold: false` — meskipun skor TOPSIS totalnya tinggi.

**Mengapa threshold penting:** TOPSIS bisa menghasilkan vendor dengan skor total tinggi meskipun sangat buruk di satu dimensi tertentu, jika vendor tersebut unggul di semua dimensi lain. Untuk pengadaan, ada dimensi yang tidak boleh dikompromikan — misalnya risiko legalitas. Threshold mencegah vendor dengan masalah serius tetap direkomendasikan hanya karena harganya sangat kompetitif.

### 8.2 Penerapan threshold

Threshold diterapkan **setelah** kalkulasi TOPSIS selesai — bukan sebelumnya. Ini memastikan ranking TOPSIS tetap mencerminkan perbandingan holistik, sementara threshold berfungsi sebagai filter kelayakan terpisah.

Vendor yang tidak lolos threshold tetap ditampilkan dalam ranking dengan skor TOPSIS-nya, tetapi diberi label "Tidak Memenuhi Syarat Minimum" di halaman hasil. Vendor ini tidak bisa menjadi rekomendasi utama.

### 8.3 Rekomendasi utama saat semua vendor tidak lolos threshold

Jika semua vendor tidak lolos threshold minimum, tidak ada vendor yang direkomendasikan. Output tetap menampilkan ranking TOPSIS dengan label tidak lolos, disertai catatan bahwa tim procurement perlu mencari vendor alternatif atau merevisi threshold.

---

## 9. Generasi Reasoning Naratif

### 9.1 Pemisahan kalkulasi dan narasi

Skor numerik dihasilkan oleh algoritma deterministik (TOPSIS). Penjelasan naratif dihasilkan terpisah oleh LLM berdasarkan skor yang sudah dihitung — bukan sebaliknya. Narasi tidak boleh mempengaruhi atau dipengaruhi oleh proses kalkulasi.

### 9.2 Input untuk generasi reasoning

LLM menerima sebagai input:
- Skor final dan ranking semua vendor
- Skor per kriteria semua vendor
- Bobot kriteria yang digunakan
- Catatan naratif per kriteria dari masing-masing agent (dalam Bahasa Indonesia)
- Output Negotiation Assistant
- Output Qualitative Analyzer: `profil_kualitatif` per vendor dan `summary_komparatif`
- Output Preference Matcher: `narasi_pengantar` dan `rekomendasi_vendor` (jika mode opinionated)
- Flag data tidak lengkap jika ada

### 9.3 Output reasoning yang dihasilkan

Tiga bagian reasoning yang dihasilkan (sesuai struktur di DB-01 tabel `hasil_evaluasi`):

**`reasoning_utama`** — Penjelasan mengapa vendor rank 1 direkomendasikan. Harus menyebutkan dimensi spesifik di mana vendor tersebut unggul dan apa yang membedakannya dari vendor rank 2.

**`kelemahan_utama`** — Aspek yang perlu diwaspadai dari vendor yang direkomendasikan. Bersumber dari field `kelemahan` di Performance Scorer dan `faktor_risiko` di Risk Assessor.

**`rekomendasi_negosiasi`** — Ringkasan dari output Negotiation Assistant dalam format yang lebih ringkas dan langsung dapat dikomunikasikan ke atasan.

### 9.4 Prinsip reasoning yang baik

Reasoning harus:
- Menyebutkan angka konkret jika relevan (contoh: "harga 12% di bawah rata-rata pasar")
- Menghindari klaim yang tidak didukung oleh data dari agent
- Mengakui keterbatasan data jika ada agent yang gagal
- Ditulis dalam Bahasa Indonesia yang formal namun mudah dipahami

Reasoning **tidak boleh:**
- Membuat klaim tentang vendor yang tidak ada dalam data agent
- Menjamin bahwa vendor yang direkomendasikan pasti bebas masalah
- Mengabaikan peringatan yang dihasilkan agent

---

## 10. Integrasi Output Kualitatif & Preferensi

### 10.1 Posisi dalam output akhir

Scoring Engine menghasilkan output berlapis — bukan satu angka tunggal. Tiga lapisan utama:

**Lapisan 1 — TOPSIS Score:** Ranking numerik objektif berdasarkan lima kriteria dengan bobot yang dikonfigurasi. Ini adalah lapisan deterministik yang tidak berubah meskipun output kualitatif atau preferensi berbeda.

**Lapisan 2 — Analisis Kualitatif:** Profil kualitatif per vendor dan summary komparatif dari Qualitative Analyzer Agent. Lapisan ini naratif — tidak ada angka. Ditampilkan terpisah dari ranking TOPSIS di halaman P-05.

**Lapisan 3 — Rekomendasi Berbasis Preferensi:** Output dari Preference Matcher. Hadir hanya jika preferensi diinput (mode opinionated). Ini adalah lapisan paling kontekstual — sangat bergantung pada apa yang dinyatakan procurement staff sebagai prioritas.

### 10.2 Aturan non-interferensi

Ketiga lapisan ini **tidak boleh saling mempengaruhi kalkulasi**:

- Output Qualitative Analyzer **tidak** mengubah skor TOPSIS
- Output Preference Matcher **tidak** mengubah skor TOPSIS
- Urutan pemrosesan selalu: kalkulasi TOPSIS selesai → lapisan kualitatif ditambahkan → lapisan preferensi ditambahkan → reasoning naratif dihasilkan berdasarkan ketiganya

Reasoning naratif adalah satu-satunya komponen yang "membaca" output dari semua lapisan secara bersamaan — dan reasoning tidak mengubah skor, hanya menjelaskannya.

### 10.3 Conflict callout

Jika Preference Matcher melaporkan `ada_konflik_topsis: true` — artinya vendor yang paling sesuai preferensi bukan vendor dengan skor TOPSIS tertinggi — Scoring Engine menyertakan conflict callout dalam output. Callout ini ditampilkan secara prominan di P-05 agar procurement staff tidak melewatkannya.

Format conflict callout yang disimpan:
```json
{
  "ada_konflik": true,
  "vendor_topsis_terbaik": "vendor_id",
  "vendor_preferensi_terbaik": "vendor_id",
  "narasi_konflik": "string (dari Preference Matcher catatan_konflik)"
}
```

---

## 11. Output Scoring Engine

### 11.1 Struktur output lengkap

Scoring Engine menghasilkan satu objek output yang langsung ditulis ke database oleh Orchestrator dalam satu transaksi.

**Untuk tabel `hasil_evaluasi`:**
- ID evaluasi
- Metodologi yang digunakan (`TOPSIS`)
- ID vendor yang direkomendasikan (rank 1 yang lolos threshold)
- Tiga bagian reasoning naratif TOPSIS (reasoning_utama, kelemahan_utama, rekomendasi_negosiasi)
- Summary komparatif kualitatif (dari Qualitative Analyzer)
- Narasi pengantar preferensi (dari Preference Matcher — `narasi_pengantar`)
- Conflict callout (jika ada — dari section 10.3)
- Output lengkap Preference Matcher sebagai JSONB (`preference_matching_result`)
- Waktu kalkulasi selesai
- Flag `ada_data_tidak_lengkap` dan daftar kriteria yang terdampak

**Untuk tabel `hasil_vendor` (satu row per vendor):**
- ID hasil evaluasi dan ID vendor
- Rank (urutan dari skor tertinggi)
- Skor total (skala 0–100, satu desimal)
- Skor per kriteria dalam JSONB
- Catatan naratif per kriteria dalam JSONB (dari output agent)
- Status `lolos_threshold` (boolean)
- `profil_kualitatif` per vendor dalam JSONB (dari Qualitative Analyzer)
- `unique_offerings` per vendor dalam JSONB (dari Qualitative Analyzer)
- `tingkat_kesesuaian_preferensi` (dari Preference Matcher — jika mode opinionated)

### 11.2 Reproducibility

Scoring Engine menyimpan snapshot konfigurasi kriteria yang digunakan saat kalkulasi sebagai bagian dari output — bukan hanya merujuk ke konfigurasi aktif saat ini. Ini memastikan hasil dapat diinterpretasikan dengan benar meskipun konfigurasi sudah berubah setelah evaluasi selesai.

Teks preferensi asli yang diinput user juga disimpan di tabel `evaluasi` (kolom `preferensi_perusahaan`) — bukan hanya output Preference Matcher — sehingga konteks penuh keputusan tersedia untuk audit di masa mendatang.

---

## 12. Validasi & Sanity Check

Sebelum output ditulis ke database, Scoring Engine menjalankan serangkaian validasi untuk mendeteksi anomali.

### 11.1 Validasi input

- Semua vendor yang dikirim harus memiliki minimal satu field data dari agent (tidak boleh semuanya null)
- Total bobot kriteria harus tepat 1.0 (setelah konversi dari persen)
- Jumlah vendor minimal 2 (TOPSIS tidak bermakna untuk satu vendor)

### 11.2 Validasi output

- Skor total semua vendor harus dalam rentang 0–100
- Tidak boleh ada dua vendor dengan skor yang persis sama hingga desimal keempat (jika terjadi, ada kemungkinan bug kalkulasi)
- Vendor rank 1 harus memiliki skor lebih tinggi dari rank 2 (bukan sama atau lebih rendah)
- Jumlah row `hasil_vendor` harus sama dengan jumlah vendor yang dievaluasi

### 11.3 Jika validasi gagal

Jika validasi output gagal, Scoring Engine **tidak** menulis ke database. Ia melaporkan error ke Orchestrator beserta detail validasi mana yang gagal. Orchestrator mencatat error ini dan menandai evaluasi dengan status khusus untuk investigasi manual.

---

## 13. Aturan & Larangan

**Dilarang mengubah skor setelah dihasilkan** berdasarkan reasoning atau preferensi subjektif. Skor adalah output murni matematis — hanya bisa berubah jika data input atau konfigurasi berubah.

**Dilarang reasoning mempengaruhi ranking.** Urutan pemrosesan harus selalu: kalkulasi TOPSIS selesai → ranking terbentuk → reasoning dihasilkan berdasarkan ranking. Tidak boleh sebaliknya.

**Dilarang output kualitatif atau preferensi mempengaruhi skor TOPSIS.** Lapisan 2 dan 3 (section 10.1) bersifat adiktif — menambahkan informasi, bukan mengubah kalkulasi yang sudah selesai.

**Dilarang menggunakan nilai default tanpa mencatat flag.** Setiap kali nilai default digunakan karena data tidak tersedia, flag `data_tidak_lengkap` harus dicatat dan kriteria yang terdampak harus terdokumentasi dalam output.

**Dilarang menghapus vendor dari kalkulasi** karena alasan apapun — termasuk jika vendor tersebut memiliki banyak data null. Semua vendor yang masuk ke evaluasi harus mendapat skor, meskipun skornya rendah akibat banyak data yang tidak tersedia.

**Dilarang menyimpan output parsial ke database.** Penulisan `hasil_evaluasi` dan seluruh `hasil_vendor` harus dalam satu transaksi atomik.

---

## 14. Catatan untuk Dokumen Lanjutan

### Untuk AI-01 (Agent Orchestration)

Format data agregat yang dikirim Orchestrator ke Scoring Engine harus konsisten dengan pemetaan di section 6.1, ditambah output dari Qualitative Analyzer dan Preference Matcher. AI-01 perlu memastikan semua output agent tersedia sebelum Scoring Engine dipanggil.

### Untuk DB-01 (Data Model)

Tabel `hasil_evaluasi` perlu kolom tambahan: `preference_matching_result` (JSONB) dan `conflict_callout` (JSONB). Tabel `hasil_vendor` perlu kolom tambahan: `unique_offerings` (JSONB), `profil_kualitatif` (Text), dan `tingkat_kesesuaian_preferensi` (Enum, nullable). Tabel `evaluasi` perlu kolom `preferensi_perusahaan` (Text, nullable).

### Untuk SH-03 (Testing Strategy)

Scoring Engine tetap komponen paling mudah diuji karena TOPSIS deterministik. Test suite perlu diperluas untuk memverifikasi: output kualitatif tersimpan dengan benar, conflict callout dihasilkan saat kondisi terpenuhi, dan output mode netral vs opinionated berbeda sebagaimana mestinya.

### Untuk FE-03 (Page & User Flow)

Halaman P-05 perlu memuat tiga lapisan output: TOPSIS ranking (sudah ada), profil kualitatif per vendor (baru), dan rekomendasi berbasis preferensi dengan conflict callout (baru).

---

*Dokumen ini adalah living document — metodologi dan parameter kalkulasi dapat diperbarui berdasarkan hasil evaluasi performa sistem.*

---

**Riwayat Perubahan**

| Versi | Tanggal | Perubahan | Author |
|---|---|---|---|
| 1.0.0 | 2026-06-07 | Versi awal | — |
| 2.0.0 | 2026-06-11 | Tambah section 10 (Integrasi Output Kualitatif & Preferensi); perbarui input Scoring Engine (3.3) untuk output AI-06 dan AI-07; perbarui output (section 11) dengan field kualitatif dan preferensi; tambah aturan non-interferensi; renumber section | — |
