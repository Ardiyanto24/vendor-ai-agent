# FE-02 — Component Library Specification

**Project:** AI Vendor Selection System  
**Dokumen:** FE-02 — Component Library  
**Versi:** 3.0.0  
**Tanggal:** 2026-06-11  
**Status:** Draft  
**Author:** —  
**Direview oleh:** —

---

## Daftar Isi

1. [Tujuan Dokumen](#1-tujuan-dokumen)
2. [Referensi Dokumen](#2-referensi-dokumen)
3. [Tech Stack](#3-tech-stack)
4. [Prinsip Komponen](#4-prinsip-komponen)
5. [Design Tokens](#5-design-tokens)
6. [Hierarki Komponen](#6-hierarki-komponen)
7. [Atomic Components](#7-atomic-components)
8. [Composite Components](#8-composite-components)
9. [Layout Components](#9-layout-components)
10. [Feature Components](#10-feature-components)
11. [Chart Components](#11-chart-components)
12. [Naming Convention](#12-naming-convention)
13. [Catatan untuk Dokumen Lanjutan](#13-catatan-untuk-dokumen-lanjutan)

---

## 1. Tujuan Dokumen

Dokumen ini mendefinisikan **apa saja komponen UI** yang dibutuhkan aplikasi AI Vendor Selection System, **mengapa komponen tersebut perlu ada**, dan **di halaman mana komponen tersebut digunakan**.

Dokumen ini menjadi kontrak antara desainer dan frontend engineer tentang unit-unit UI yang perlu dibangun. Komponen yang tidak terdaftar di sini tidak boleh dibuat tanpa pembaruan dokumen.

Dokumen ini **tidak** mendefinisikan cara implementasi kode — itu diserahkan sepenuhnya ke engineer saat development.

---

## 2. Referensi Dokumen

| Kode | Nama Dokumen | Keterangan |
|---|---|---|
| FE-01 | UI Architecture | Tech stack, folder structure, design system setup |
| FE-03 | Page & User Flow | Halaman yang menggunakan komponen ini |
| FE-04 | State Management | Bagaimana state dikelola di dalam komponen |
| FE-05 | API Integration | Pola data fetching yang relevan untuk komponen |

---

## 3. Tech Stack

Keputusan tech stack ini berlaku untuk seluruh komponen di dokumen ini.

| Kebutuhan | Pilihan | Alasan |
|---|---|---|
| Framework | Next.js 14+ (App Router) | SSR/SSG untuk performa, routing built-in, ekosistem terlengkap untuk React |
| Bahasa | TypeScript | Type safety mencegah bug runtime, dokumentasi kode yang lebih jelas |
| Styling | Tailwind CSS | Utility-first mempercepat development, konsistensi visual lebih mudah dijaga |
| UI Base | shadcn/ui | Komponen siap pakai yang fully customizable, tidak ada dependency lock-in karena kode di-copy ke project |
| Chart | Chart.js + react-chartjs-2 | Populer, dokumentasi lengkap, fleksibel untuk berbagai jenis visualisasi data |
| Icon | Lucide React | Konsisten dengan ecosystem shadcn/ui |
| Form | React Hook Form + Zod | Validasi deklaratif, performa tinggi, TypeScript-first |

**Mengapa shadcn/ui dipilih dibanding library lain:** shadcn/ui bukan dependency eksternal — komponen di-generate ke dalam project sehingga tim memiliki kendali penuh atas kode dan tidak terikat pada update library. Ini penting untuk proyek jangka panjang yang perlu kustomisasi mendalam.

---

## 4. Prinsip Komponen

### 4.1 Komponen menerima data, tidak mengambilnya sendiri

Komponen bersifat presentasional — mereka menampilkan data yang diterima via props. Pengambilan data dari API adalah tanggung jawab layer di atasnya (page atau container), bukan komponen itu sendiri.

**Pengecualian yang harus didokumentasikan eksplisit:** komponen yang karena alasan UX perlu fetch data secara mandiri (misalnya autocomplete yang membutuhkan search API).

### 4.2 Komponen tidak mengandung hardcoded string

Semua label, placeholder, dan pesan yang tampil ke user diterima via props atau konstanta terpusat — bukan ditulis langsung di dalam komponen. Ini memudahkan perubahan teks tanpa menyentuh logika komponen.

### 4.3 Pisahkan logic dari presentasi

Komponen yang mengandung logika bisnis (kalkulasi, transformasi data) harus memisahkan logika tersebut ke dalam hooks atau utilities terpisah. Komponen hanya bertanggung jawab atas tampilan.

---

## 5. Design Tokens

Design tokens adalah nilai-nilai visual yang menjadi fondasi konsistensi seluruh UI. Semua komponen wajib menggunakan tokens ini — tidak boleh ada nilai warna, ukuran, atau spasi yang ditulis langsung (hardcoded) di dalam komponen.

### 5.1 Warna

Dua kelompok warna utama:

**Warna brand** — digunakan untuk elemen interaktif utama (tombol, link, highlight aktif) dan accent AI panel.

**Warna status** — digunakan eksklusif untuk menampilkan status evaluasi. Setiap status memiliki satu warna yang konsisten di seluruh aplikasi sehingga user dapat mengenali status secara visual tanpa membaca teksnya.

| Status | Warna | Makna Visual |
|---|---|---|
| Draft | Abu-abu | Belum aktif, dalam penyusunan |
| Processing | Biru | Sedang berjalan, ada aktivitas |
| Selesai | Hijau | Berhasil selesai |
| Menunggu approval | Kuning/Amber | Butuh perhatian, ada aksi yang diperlukan |
| Approved | Hijau tua | Final dan disetujui |
| Butuh revisi | Merah | Ada masalah, perlu tindakan |

### 5.2 Tipografi

Lima level tipografi yang digunakan secara konsisten:

| Level | Digunakan untuk |
|---|---|
| Display | Judul halaman utama |
| Heading | Judul section dalam halaman |
| Subheading | Label kelompok atau sub-section |
| Body | Konten teks umum |
| Caption | Teks kecil: timestamp, label sekunder, keterangan |

### 5.3 Lebar panel

Tiga nilai lebar yang mendefinisikan layout 3-panel secara konsisten:
- Sidebar: lebar tetap
- Panel AI: lebar tetap
- Panel konten: mengisi sisa ruang yang tersedia

---

## 6. Hierarki Komponen

Komponen diorganisir dalam empat level hierarki. Setiap level memiliki tanggung jawab yang berbeda dan aturan ketergantungan yang ketat.

```
Atomic
  ↓ digunakan oleh
Composite
  ↓ digunakan oleh
Layout & Feature
  ↓ menyusun
Halaman (Pages)
```

**Atomic** — unit terkecil yang tidak bisa dipecah lagi. Tidak memiliki state internal yang kompleks. Contoh: Badge, Status indicator, Score bar.

**Composite** — gabungan beberapa atomic yang membentuk satu unit bermakna. Merepresentasikan satu objek domain. Contoh: Card evaluasi, Card vendor, Baris tabel.

**Layout** — komponen yang mengatur struktur global halaman. Tidak berubah antar halaman. Contoh: Shell 3-panel, Sidebar, Panel AI.

**Feature** — komponen besar yang spesifik ke satu fitur utama. Tidak reusable di luar konteks fiturnya. Contoh: Stepper buat evaluasi, Panel progress agent, Tabel ranking vendor.

---

## 7. Atomic Components

---

### StatusBadge

**Apa:** Label kecil berwarna yang menampilkan status evaluasi.

**Mengapa perlu:** Status muncul di hampir semua halaman dalam berbagai konteks. Dengan menjadikannya komponen tersendiri, warna dan label status dijamin konsisten di seluruh aplikasi.

**Digunakan di:** P-02, P-04, P-06, P-07

**Variant:** Satu variant per status evaluasi (enam total), ukuran normal dan kecil.

---

### ScoreBar

**Apa:** Indikator visual berupa bar horizontal yang menampilkan skor vendor di satu kriteria tertentu, beserta nama kriteria dan bobotnya.

**Mengapa perlu:** Skor numerik saja sulit dibaca cepat. Bar visual memungkinkan user membandingkan performa vendor antar kriteria dalam satu pandangan. Warna bar yang berubah berdasarkan nilai skor memberikan sinyal tambahan tanpa perlu membaca angka.

**Digunakan di:** P-05 (breakdown skor per kriteria di baris expandable)

**Variant:** Warna bar berubah berdasarkan rentang nilai (merah untuk skor rendah, kuning untuk sedang, biru untuk baik, hijau untuk sangat baik).

---

### AgentStatusIcon

**Apa:** Ikon kecil yang menampilkan kondisi satu sub-agent AI (belum mulai, sedang berjalan, selesai, error).

**Mengapa perlu:** Di halaman processing, lima agent berjalan bersamaan. User perlu membedakan status tiap agent secara cepat tanpa membaca teks. Ikon dengan warna dan animasi yang berbeda memungkinkan ini.

**Digunakan di:** P-04

**Variant:** Empat status (idle, running, done, error), masing-masing dengan ikon dan warna berbeda. Status running memiliki animasi berputar.

---

### RankBadge

**Apa:** Indikator posisi ranking vendor (1, 2, 3, dst.).

**Mengapa perlu:** Rank 1 adalah informasi paling penting di halaman hasil. Memberikannya visual yang berbeda (lebih menonjol, warna berbeda) membantu user langsung menemukan rekomendasi utama.

**Digunakan di:** P-05

**Variant:** Rank 1 dengan styling menonjol (background amber), rank 2–3 lebih subtle, rank 4 ke atas tampil sebagai teks polos.

---

## 8. Composite Components

---

### EvaluasiRow

**Apa:** Satu baris yang merepresentasikan satu evaluasi dalam daftar atau tabel, menampilkan informasi ringkas yang cukup untuk identifikasi dan navigasi cepat.

**Mengapa perlu:** Evaluasi muncul dalam daftar di beberapa halaman (Dashboard, Riwayat, Approval). Dengan satu komponen yang konsisten, tampilan dan informasi yang ditampilkan dijamin seragam.

**Digunakan di:** P-02, P-06, P-07

**Yang ditampilkan:** Judul evaluasi, kategori, jumlah vendor, StatusBadge, tanggal, dan vendor terpilih (jika ada).

---

### VendorInputCard

**Apa:** Card untuk memasukkan atau menampilkan data satu vendor kandidat dalam form pembuatan evaluasi.

**Mengapa perlu:** Vendor dapat diinput secara manual atau hasil ekstraksi AI dari dokumen. Komponen ini menangani kedua mode dengan tampilan yang sesuai konteks, termasuk state loading saat AI sedang mengekstrak.

**Digunakan di:** P-03 Step 2

**Variant:** Mode manual (form kosong), mode hasil ekstraksi AI (form pre-filled yang bisa diedit), mode loading (skeleton saat AI mengekstrak), mode error (jika ekstraksi gagal).

---

### CriteriaWeightInput

**Apa:** Satu baris input yang menangani bobot dan threshold minimum untuk satu kriteria evaluasi.

**Mengapa perlu:** Konfigurasi bobot melibatkan lima kriteria yang harus totalnya 100%. Komponen ini perlu memberi umpan balik visual langsung saat nilai tidak valid, tanpa menunggu user menekan tombol simpan.

**Digunakan di:** P-08

**Perilaku penting:** Menampilkan border merah jika total bobot keseluruhan belum 100%, memberikan umpan balik real-time.

---

### ApprovalCard

**Apa:** Card lengkap yang merangkum satu evaluasi beserta semua informasi yang dibutuhkan manager untuk mengambil keputusan, termasuk form approve/reject.

**Mengapa perlu:** Manager membutuhkan ringkasan padat dalam satu tampilan — tidak perlu membuka detail penuh untuk setiap evaluasi. Menggabungkan informasi dan form keputusan dalam satu card mempercepat alur approval.

**Digunakan di:** P-07

**Yang ditampilkan:** Judul evaluasi, pengaju, tanggal, rekomendasi AI beserta skor, ringkasan budget, form komentar, tombol approve dan reject.

---

## 9. Layout Components

---

### AppShell

**Apa:** Wrapper utama yang menyusun layout 3-panel untuk semua halaman kecuali Login.

**Mengapa perlu:** Layout 3-panel harus konsisten di seluruh aplikasi. AppShell memastikan Sidebar dan AIPanel selalu hadir dan posisinya tidak berubah, sementara konten utama di panel tengah berganti sesuai halaman aktif.

**Mengapa layout 3-panel ini dipilih:** Dijelaskan di FE-03 section 3.2.

---

### Sidebar

**Apa:** Panel navigasi tetap di sisi kiri yang menampilkan menu sesuai role user.

**Mengapa menu disesuaikan role:** Menampilkan menu yang tidak relevan hanya menambah kebisingan visual. Staff tidak perlu melihat menu Approval atau Settings yang tidak bisa mereka gunakan.

**Yang ditampilkan:** Logo, menu navigasi (disesuaikan role), informasi user yang login (nama, role), dan tombol logout.

---

### AIPanel

**Apa:** Panel percakapan AI di sisi kanan yang konteksnya berubah otomatis mengikuti halaman yang sedang aktif.

**Mengapa konteks menyesuaikan halaman:** Agar AI dapat langsung relevan tanpa user perlu menjelaskan konteks dari awal. Saat user membuka hasil evaluasi tertentu, AI sudah "tahu" evaluasi mana yang sedang dilihat dan dapat menjawab pertanyaan spesifik tentangnya.

**Yang ditampilkan:** Header panel dengan label konteks aktif, riwayat percakapan dalam sesi ini, dan input untuk mengetik pesan.

---

## 10. Feature Components

---

### EvaluasiStepper

**Apa:** Komponen multi-langkah yang memandu user melalui tiga tahap pembuatan evaluasi baru.

**Mengapa stepper:** Alasan pemilihan pola stepper dijelaskan di FE-03 P-03. Komponen ini bertanggung jawab atas navigasi antar langkah, validasi tiap langkah sebelum pindah, dan indikator posisi saat ini.

**Tiga langkah:** Requirement pengadaan, Tambah vendor, Konfirmasi.

**Digunakan di:** P-03

---

### AgentProgressPanel

**Apa:** Panel yang menampilkan status dan progress seluruh sub-agent AI secara real-time.

**Mengapa real-time visibility ini penting:** Dijelaskan di FE-03 P-04. Komponen ini mengonsumsi update real-time dari Supabase Realtime dan memperbarui tampilan secara otomatis.

**Yang ditampilkan:** Daftar tujuh sub-agent, masing-masing dengan AgentStatusIcon, progress bar, dan pesan terkini. Agent yang sedang menunggu dependency-nya selesai ditampilkan dalam state `waiting` yang berbeda dari `idle` — ini memberi user pemahaman bahwa urutan eksekusi memang disengaja, bukan stuck. Estimasi waktu selesai keseluruhan ditampilkan di bagian bawah panel.

**Digunakan di:** P-04

---

### RecommendationCard

**Apa:** Card hero yang menampilkan rekomendasi utama AI — vendor dengan skor tertinggi beserta skor total dan ringkasan reasoning.

**Mengapa ini komponen tersendiri:** Rekomendasi utama adalah informasi paling penting di seluruh aplikasi. Memisahkannya sebagai komponen tersendiri memastikan ia selalu mendapat visual treatment yang berbeda dari informasi lain — lebih besar, lebih menonjol, jelas sebagai focal point halaman.

**Digunakan di:** P-05

---

### VendorRankingTable

**Apa:** Tabel interaktif yang menampilkan perbandingan seluruh vendor yang dievaluasi, dengan kemampuan sort dan expand per baris untuk melihat breakdown skor detail dan profil kualitatif.

**Mengapa expand per baris:** Menampilkan semua detail semua vendor sekaligus akan membanjiri user dengan informasi. Dengan expand on demand, user dapat fokus pada vendor yang ingin ditelusuri lebih dalam.

**Yang ditampilkan di baris utama:** RankBadge, nama vendor, skor total, skor per kriteria (kolom), dan indikator `tingkat_kesesuaian_preferensi` berupa badge kecil jika evaluasi menggunakan preferensi.

**Yang ditampilkan saat baris di-expand:** ScoreBar per kriteria, catatan AI per kriteria, dan profil kualitatif vendor — unique offerings yang teridentifikasi beserta relevansinya.

**Mengapa indikator preferensi di baris utama:** Procurement staff yang membandingkan vendor perlu melihat dimensi preferensi tanpa harus meng-expand setiap baris. Badge kecil (`tinggi` / `sedang` / `rendah`) cukup untuk memberikan sinyal tanpa memenuhi kolom tabel.

**Digunakan di:** P-05

---

### AIReasoningPanel

**Apa:** Section yang menampilkan narasi reasoning lengkap dari AI dalam tiga bagian terstruktur.

**Mengapa reasoning perlu ditampilkan terpisah:** Angka skor saja tidak cukup untuk mengambil keputusan pengadaan yang melibatkan nilai besar. Narasi reasoning memberikan konteks yang bisa dikomunikasikan ke stakeholder dan membuat keputusan dapat diaudit.

**Tiga bagian:** Mengapa vendor terpilih direkomendasikan, kelemahan yang perlu diwaspadai, rekomendasi langkah negosiasi selanjutnya.

**Digunakan di:** P-05

---

### QualitativeProfileCard

**Apa:** Card yang menampilkan profil kualitatif satu vendor — unique offerings yang teridentifikasi dan narasi profil kualitatif keseluruhan.

**Mengapa komponen tersendiri:** Profil kualitatif adalah dimensi analisis yang sifatnya berbeda dari skor numerik — ia berisi deskripsi naratif tentang nilai tambah unik yang tidak bisa direduksi menjadi angka. Memisahkannya sebagai komponen tersendiri memastikan treatment visual yang tepat dan konsisten di seluruh konteks penggunaannya.

**Yang ditampilkan:** Narasi `profil_kualitatif`, diikuti daftar `unique_offerings` yang masing-masing menampilkan deskripsi dan badge relevansi (`sangat_relevan` / `relevan` / `netral`).

**Digunakan di:** P-05 (di dalam expand baris VendorRankingTable dan di Bagian 4 halaman hasil)

---

### QualitativeSummaryPanel

**Apa:** Section yang menampilkan summary komparatif kualitatif dari seluruh vendor dalam satu evaluasi — narasi tunggal yang membandingkan profil kualitatif semua vendor secara holistik.

**Mengapa summary komparatif perlu ada:** Procurement staff perlu melihat gambaran besar perbedaan kualitatif antar vendor sebelum masuk ke detail per vendor. Summary ini juga secara eksplisit menyebutkan potensi tie-breaking jika ada vendor dengan skor TOPSIS berdekatan.

**Digunakan di:** P-05 (Bagian 4)

---

### PreferenceRecommendationCard

**Apa:** Card yang menampilkan rekomendasi vendor berdasarkan preferensi perusahaan yang diinput, disertai reasoning per vendor yang direkomendasikan.

**Mengapa card terpisah dari RecommendationCard:** RecommendationCard menampilkan rekomendasi objektif berbasis TOPSIS. PreferenceRecommendationCard menampilkan rekomendasi kontekstual berbasis preferensi — keduanya bisa berbeda, dan perbedaan ini justru informatif. Memisahkannya memastikan user memahami bahwa ini adalah dua jenis rekomendasi yang berbeda sumbernya.

**Yang ditampilkan:** Per vendor yang direkomendasikan: urutan rekomendasi, nama vendor, dan narasi `alasan_utama` mengapa vendor ini sesuai preferensi.

**Digunakan di:** P-05 (Bagian 5 — hanya muncul jika evaluasi menggunakan preferensi)

---

### ConflictCallout

**Apa:** Komponen warning prominan yang ditampilkan saat vendor terbaik berdasarkan preferensi berbeda dari vendor terbaik berdasarkan TOPSIS.

**Mengapa ini komponen tersendiri:** Konflik antara preferensi dan metrik objektif adalah informasi yang sangat penting — procurement staff harus sadar bahwa memilih berdasarkan preferensi berarti ada trade-off terhadap dimensi kuantitatif. Komponen ini dirancang agar tidak bisa terlewat: warna peringatan, posisi prominan, dan tidak bisa di-dismiss selama halaman terbuka.

**Yang ditampilkan:** Penjelasan singkat tentang konflik — vendor mana yang terbaik di TOPSIS, vendor mana yang paling sesuai preferensi, dan narasi trade-off dari `catatan_konflik`.

**Digunakan di:** P-05 (Bagian 5 — hanya muncul jika `ada_konflik_topsis: true`)

---

### PreferenceInput

**Apa:** Textarea opsional untuk menginput preferensi bisnis perusahaan saat membuat evaluasi baru.

**Mengapa textarea bebas, bukan form terstruktur:** Preferensi bisnis terlalu bervariasi untuk distandarisasi dalam dropdown atau checkbox. Teks bebas memungkinkan staff mengekspresikan konteks bisnis yang spesifik dan nuanced — LLM lebih baik menginterpretasikan teks natural daripada pilihan yang kaku.

**Yang ditampilkan:** Label "Preferensi atau Prioritas Perusahaan (opsional)", textarea dengan counter karakter real-time (batas 1.000 karakter), dan placeholder teks yang memberikan contoh pengisian konkret.

**Digunakan di:** P-03 (Langkah 1)

---

## 11. Chart Components

Semua chart menggunakan Chart.js via react-chartjs-2.

**Mengapa Chart.js dipilih:** Alasan tercantum di section 3. Chart.js dipilih karena dokumentasinya yang lengkap, fleksibilitasnya untuk berbagai jenis visualisasi, dan popularitasnya yang memudahkan onboarding engineer baru.

---

### CriteriaBarChart

**Apa:** Bar chart horizontal yang memperlihatkan skor satu vendor di semua kriteria sekaligus.

**Mengapa horizontal:** Bar horizontal lebih mudah dibaca untuk perbandingan dengan label kategori panjang (nama kriteria) dibanding bar vertikal.

**Mengapa ada di expand baris tabel:** Grafik memberikan perbandingan visual yang lebih cepat dibaca dibanding angka-angka dalam kolom, terutama untuk user yang ingin memahami profil kekuatan dan kelemahan satu vendor secara holistik.

**Digunakan di:** P-05 (di dalam baris expandable VendorRankingTable)

---

### ScoreRadarChart

**Apa:** Radar chart yang membandingkan profil skor beberapa vendor secara visual dalam satu tampilan.

**Mengapa radar:** Radar chart ideal untuk membandingkan beberapa entitas di beberapa dimensi sekaligus — persis seperti kebutuhan membandingkan vendor di lima kriteria. Shape yang terbentuk langsung mencerminkan profil kekuatan dan kelemahan relatif antar vendor.

**Batasan:** Maksimum empat vendor ditampilkan bersamaan untuk menjaga keterbacaan.

**Digunakan di:** P-05 (sebagai alternatif view di VendorRankingTable)

---

## 12. Naming Convention

Konsistensi penamaan penting agar codebase mudah dinavigasi oleh semua anggota tim.

**Nama komponen:** PascalCase, mencerminkan apa yang direpresentasikan bukan bagaimana cara kerjanya. Contoh: `StatusBadge`, `VendorRankingTable`.

**Nama props handler:** Selalu diawali `on` diikuti kata kerja. Contoh: `onSubmit`, `onApprove`, `onRemove`.

**Nama props boolean:** Selalu diawali `is` atau `has`. Contoh: `isLoading`, `isSubmitting`, `hasError`.

**Nama props collection:** Selalu plural. Contoh: `vendors`, `agents`, `messages`.

---

## 13. Catatan untuk Dokumen Lanjutan

### Untuk FE-04 (State Management)

Komponen berikut memiliki kebutuhan state yang perlu dikelola di level yang lebih tinggi:
- AIPanel — riwayat percakapan perlu dapat diakses dari luar komponen dan di-reset saat evaluasi berganti
- AgentProgressPanel — update real-time perlu dikelola agar tidak terjadi memory leak saat komponen tidak aktif; kini mengelola 7 agent
- EvaluasiStepper — data yang sudah diisi di tiap langkah perlu tetap ada jika user navigasi bolak-balik, termasuk nilai PreferenceInput di Langkah 1
- ConflictCallout — state "sudah dibaca" tidak perlu disimpan — komponen selalu muncul jika konflik ada

### Untuk FE-05 (API Integration)

Komponen berikut memiliki kebutuhan data fetching khusus yang perlu didefinisikan polanya:
- AgentProgressPanel — subscribe ke Supabase Realtime channel (7 agent)
- AIPanel — membaca SSE stream dari FastAPI dengan RAG context aktif di halaman P-05
- VendorInputCard (mode upload) — polling status ekstraksi dokumen dan RAG indexing

### Untuk BE-02 (API Contract)

Endpoint hasil evaluasi perlu mengembalikan field baru: `summary_komparatif_kualitatif`, `preference_matching_result`, `conflict_callout`, dan per vendor: `unique_offerings`, `profil_kualitatif`, `tingkat_kesesuaian_preferensi`.

---

*Dokumen ini adalah living document — akan diperbarui saat komponen baru diidentifikasi selama proses development.*

---

**Riwayat Perubahan**

| Versi | Tanggal | Perubahan | Author |
|---|---|---|---|
| 1.0.0 | 2026-06-07 | Versi awal | — |
| 2.0.0 | 2026-06-07 | Revisi: fokus ke what & why, hapus semua TypeScript interface dan code snippet | — |
| 3.0.0 | 2026-06-11 | Update AgentProgressPanel ke 7 agent dengan state `waiting`; update VendorRankingTable dengan indikator preferensi dan kualitatif di expand; tambah 5 komponen baru: QualitativeProfileCard, QualitativeSummaryPanel, PreferenceRecommendationCard, ConflictCallout, PreferenceInput | — |
