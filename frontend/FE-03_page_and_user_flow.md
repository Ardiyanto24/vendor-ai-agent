# FE-03 — Page & User Flow Specification

**Project:** AI Vendor Selection System  
**Dokumen:** FE-03 — Page & User Flow  
**Versi:** 3.0.0  
**Tanggal:** 2026-06-11  
**Status:** Draft  
**Author:** —  
**Direview oleh:** —

---

## Daftar Isi

1. [Tujuan Dokumen](#1-tujuan-dokumen)
2. [Referensi Dokumen](#2-referensi-dokumen)
3. [Prinsip Desain](#3-prinsip-desain)
4. [User & Role](#4-user--role)
5. [Layout Global](#5-layout-global)
6. [Daftar Halaman](#6-daftar-halaman)
7. [Core User Flow](#7-core-user-flow)
8. [Halaman Detail](#8-halaman-detail)
9. [Status & State Evaluasi](#9-status--state-evaluasi)
10. [Navigasi & Routing](#10-navigasi--routing)
11. [Catatan untuk Dokumen Lanjutan](#11-catatan-untuk-dokumen-lanjutan)

---

## 1. Tujuan Dokumen

Dokumen ini mendefinisikan seluruh halaman, alur perpindahan antar halaman, dan konten utama tiap halaman untuk aplikasi AI Vendor Selection System.

Dokumen ini menjadi **sumber kebenaran utama** bagi frontend engineer dalam memahami apa yang perlu dibangun, bagi backend engineer dalam memahami data apa yang dibutuhkan tiap halaman, dan bagi database engineer dalam memahami entitas apa yang perlu tersedia.

Dokumen ini **tidak** mendefinisikan cara implementasi teknis — itu adalah tanggung jawab dokumen FE-01, FE-02, FE-04, dan FE-05.

---

## 2. Referensi Dokumen

| Kode | Nama Dokumen | Keterangan |
|---|---|---|
| FE-01 | UI Architecture | Tech stack, folder structure, routing strategy |
| FE-02 | Component Library | Komponen reusable yang dipakai di tiap halaman |
| FE-04 | State Management | Pengelolaan state global dan async |
| FE-05 | API Integration | Pola konsumsi API di sisi frontend |
| BE-02 | API Contract | Endpoint yang melayani tiap halaman |
| DB-01 | Data Model & ERD | Struktur data yang ditampilkan |

---

## 3. Prinsip Desain

Dokumen ini mengikuti pendekatan **UI-first / outside-in design** — UI dirancang lebih dulu sebelum backend dan database, karena UI mencerminkan kebutuhan nyata user dan memaksa tim berpikir dari perspektif pengguna, bukan dari perspektif sistem.

### 3.1 Prinsip utama

| Prinsip | Penjelasan |
|---|---|
| Clarity first | Setiap halaman memiliki satu tujuan utama yang jelas |
| Progressive disclosure | Informasi kompleks ditampilkan bertahap, tidak sekaligus |
| AI sebagai asisten | AI membantu user membuat keputusan, bukan menggantikannya |
| Explainable output | Setiap rekomendasi AI disertai justifikasi yang dapat dibaca manusia |
| Flexible input | User dapat menginput data secara manual, upload dokumen, atau kombinasi keduanya — mengakomodasi kenyataan bahwa proses procurement di lapangan tidak seragam |

### 3.2 Mengapa layout 3-panel

Aplikasi menggunakan layout 3-panel yang konsisten di seluruh halaman. Keputusan ini didasarkan pada tiga alasan:

Pertama, procurement staff perlu melihat data struktural (daftar vendor, skor) dan berkomunikasi dengan AI secara bersamaan tanpa berpindah halaman. Kedua, panel AI yang selalu hadir mengingatkan user bahwa AI adalah bagian inti dari alur kerja, bukan fitur tambahan. Ketiga, pola ini sudah familiar di kalangan tools AI modern sehingga mengurangi learning curve.

**Pembagian panel:**
- **Sidebar kiri** — navigasi tetap, tidak berubah antar halaman
- **Panel konten tengah** — konten utama yang berubah sesuai halaman aktif
- **Panel AI kanan** — chat dengan AI agent, konteksnya menyesuaikan halaman yang sedang dibuka

---

## 4. User & Role

MVP aplikasi ini memiliki dua role dengan tanggung jawab yang berbeda.

### 4.1 Procurement Staff

Role utama dengan frekuensi penggunaan tertinggi. Staff adalah orang yang menjalankan proses evaluasi dari awal hingga siap diserahkan ke atasan.

**Yang bisa dilakukan:**
- Membuat, mengedit, dan menghapus evaluasi yang masih berstatus draft
- Menambah dan menghapus vendor kandidat dalam evaluasi
- Memantau progress AI saat evaluasi diproses
- Melihat dan menganalisa hasil rekomendasi
- Mengirim hasil evaluasi ke manager untuk approval
- Berinteraksi dengan AI chat di semua halaman
- Melihat riwayat evaluasi miliknya sendiri

**Yang tidak bisa dilakukan:**
- Memberikan keputusan final (approve/reject)
- Mengubah konfigurasi bobot kriteria evaluasi
- Melihat evaluasi milik staff lain

### 4.2 Manager

Role approver yang bertindak sebagai pengambil keputusan final. Manager tidak selalu terlibat di awal proses, tetapi menjadi penentu di akhir.

**Yang bisa dilakukan (selain semua akses Staff):**
- Menerima dan mereview evaluasi yang dikirim staff
- Memberikan keputusan approve atau reject beserta komentar
- Melihat seluruh evaluasi dari semua staff
- Mengkonfigurasi bobot kriteria evaluasi per kategori pengadaan

---

## 5. Layout Global

### 5.1 Sidebar kiri

Sidebar selalu tampil di semua halaman kecuali Login. Sidebar berisi logo aplikasi, menu navigasi utama, dan informasi singkat user yang sedang login.

Menu navigasi ditampilkan sesuai role — menu Approval dan Settings hanya muncul untuk role Manager. Ini bukan sekadar pembatasan akses, tetapi juga membantu staff fokus pada alur kerjanya tanpa terganggu menu yang tidak relevan.

### 5.2 Panel AI kanan

Panel AI selalu tampil di semua halaman kecuali Login. Yang membedakan panel ini dari sekadar chatbot biasa adalah **konteks yang menyesuaikan halaman aktif secara otomatis**.

Saat user membuka halaman hasil evaluasi, AI sudah memiliki konteks tentang evaluasi tersebut dan dapat langsung menjawab pertanyaan seperti "kenapa vendor ini skornya rendah?" tanpa user perlu menjelaskan ulang. Konteks ini dikirim oleh sistem secara otomatis berdasarkan halaman dan evaluasi yang sedang dibuka.

---

## 6. Daftar Halaman

| Kode | Nama Halaman | Role yang Akses | Tujuan Singkat |
|---|---|---|---|
| P-01 | Login | Public | Titik masuk aplikasi, autentikasi user |
| P-02 | Dashboard | Semua | Gambaran cepat status semua evaluasi aktif |
| P-03 | Buat Evaluasi Baru | Staff, Manager | Input requirement dan daftar vendor kandidat |
| P-04 | Detail Evaluasi — Processing | Semua | Memantau progress AI saat evaluasi diproses |
| P-05 | Hasil Rekomendasi | Semua | Melihat dan menganalisa output rekomendasi AI |
| P-06 | Riwayat Evaluasi | Semua | Melihat semua evaluasi yang pernah dibuat |
| P-07 | Approval | Manager | Mereview dan memutuskan hasil evaluasi |
| P-08 | Settings — Konfigurasi Kriteria | Manager | Mengatur bobot kriteria evaluasi per kategori |

---

## 7. Core User Flow

### 7.1 Happy path — Procurement Staff

Ini adalah alur utama yang dirancang sebagai inti pengalaman pengguna. Semua keputusan desain UI berpusat pada kelancaran alur ini.

```
Login
  ↓
Dashboard — orientasi cepat, lihat apa yang perlu dikerjakan
  ↓
Buat Evaluasi Baru — input requirement dan tambah vendor
  ↓
Processing — pantau AI bekerja secara transparan
  ↓
Hasil Rekomendasi — analisa dan kirim ke manager
  ↓
Menunggu keputusan manager
```

Alur ini dipilih sebagai core flow karena paling mencerminkan nilai tambah sistem — user melihat secara langsung proses AI dari input hingga rekomendasi yang dapat dipertanggungjawabkan.

### 7.2 Approval flow — Manager

```
Terima notifikasi evaluasi siap direview
  ↓
Halaman Approval — baca ringkasan dan rekomendasi AI
  ↓
Putuskan: Approve atau Reject dengan komentar
  ↓
Notifikasi dikirim ke staff
```

### 7.3 Alur input vendor yang fleksibel

Di halaman Buat Evaluasi Baru, user dapat menambah vendor melalui tiga cara yang bisa dikombinasikan:

- **Input manual** — mengisi form satu per satu untuk tiap vendor
- **Upload dokumen** — mengunggah surat penawaran, AI mengekstrak data vendor secara otomatis
- **Kombinasi** — sebagian vendor diinput manual, sebagian dari upload dokumen

Fleksibilitas ini penting karena kenyataan di lapangan: tidak semua vendor mengirim penawaran dalam format yang sama, dan tidak semua staff memiliki data yang sudah terstruktur.

---

## 8. Halaman Detail

---

### P-01 Login

**Tujuan:** Memverifikasi identitas user sebelum masuk ke aplikasi.

**Mengapa halaman ini sederhana:** Login bukan bagian dari nilai utama aplikasi. Halaman ini sengaja dibuat minimal — hanya form email dan password — agar user bisa masuk secepat mungkin ke halaman yang sesungguhnya relevan bagi mereka.

**Yang ditampilkan:**
- Logo dan nama aplikasi
- Form login (email dan password)
- Link lupa password

**Perilaku penting:**
- Setelah login berhasil, user langsung diarahkan ke Dashboard
- Role user ditentukan dari response autentikasi dan menentukan menu apa yang tersedia di sidebar
- Jika login gagal, pesan error ditampilkan langsung di form tanpa redirect

**Data yang dibutuhkan:** Kredensial user, kembalian token dan informasi role

---

### P-02 Dashboard

**Tujuan:** Memberi procurement staff gambaran situasi secara cepat — evaluasi mana yang sedang berjalan, mana yang perlu perhatian, dan apa langkah selanjutnya.

**Mengapa dashboard sebagai halaman pertama:** Procurement staff jarang mengerjakan hanya satu evaluasi dalam satu waktu. Dashboard memberi mereka *situational awareness* tanpa harus mengingat di mana mereka terakhir berhenti.

**Yang ditampilkan:**
- Ringkasan jumlah evaluasi per status (aktif, sedang diproses, selesai, menunggu approval)
- Tombol aksi cepat untuk membuat evaluasi baru
- Daftar evaluasi terbaru dengan informasi ringkas: nama, jumlah vendor, status, dan tanggal
- Insight singkat dari AI berdasarkan kondisi evaluasi aktif user

**Perilaku penting:**
- Klik baris evaluasi membawa user ke halaman yang relevan berdasarkan status (processing ke P-04, selesai ke P-05)
- Untuk Manager, badge khusus ditampilkan jika ada evaluasi yang menunggu approval
- Status evaluasi yang sedang diproses diperbarui secara otomatis tanpa perlu refresh manual

**Data yang dibutuhkan:** Daftar evaluasi terbaru, ringkasan jumlah per status

---

### P-03 Buat Evaluasi Baru

**Tujuan:** Mengumpulkan semua informasi yang dibutuhkan AI untuk melakukan evaluasi — requirement pengadaan dan daftar vendor kandidat.

**Mengapa menggunakan stepper 3 langkah:** Informasi yang dibutuhkan cukup banyak dan bersifat hirarkis — requirement harus diisi dulu sebelum menambah vendor, dan konfirmasi dilakukan setelah semua data lengkap. Stepper mencegah user merasa overwhelmed sekaligus memastikan urutan pengisian yang benar.

**Tiga langkah:**

**Langkah 1 — Requirement pengadaan**

Yang diisi: judul evaluasi, kategori pengadaan, deskripsi kebutuhan, batas anggaran, deadline pengiriman, dan prioritas kriteria. Lampiran spesifikasi teknis dapat diupload sebagai konteks tambahan untuk AI.

Di bagian bawah langkah ini terdapat field **Preferensi atau Prioritas Perusahaan** yang bersifat opsional. Field ini adalah textarea bebas tempat staff mendeskripsikan prioritas bisnis yang relevan untuk pengadaan ini — seperti preferensi vendor lokal, urgensi waktu, atau komitmen jangka panjang yang tidak tercermin dalam bobot kriteria standar. Field ini dibatasi 1.000 karakter dan disertai placeholder dengan contoh pengisian.

Ketika preferensi diisi, sistem akan mengaktifkan Preference Matcher Agent (BE-10) yang menghasilkan rekomendasi vendor berbasis preferensi di halaman hasil. Ketika tidak diisi, sistem tetap berjalan penuh dalam mode netral.

Peran AI di langkah ini: membaca input yang sudah diisi dan memberikan saran kontekstual, misalnya menyarankan kriteria tambahan yang relevan untuk kategori pengadaan tertentu.

**Langkah 2 — Tambah vendor kandidat**

Yang diisi: daftar vendor yang akan dievaluasi, melalui input manual atau upload dokumen penawaran. Minimum 2 vendor, maksimum 10 vendor untuk MVP.

Saat user mengupload dokumen, AI mengekstrak informasi vendor secara otomatis dan menampilkan hasil ekstraksi untuk dikonfirmasi user sebelum disimpan. User tetap bisa mengedit hasil ekstraksi.

**Langkah 3 — Konfirmasi**

Ringkasan read-only dari semua data yang sudah diisi, termasuk estimasi waktu proses AI. User dapat kembali ke langkah sebelumnya atau langsung memulai evaluasi.

**Perilaku penting:**
- Setiap langkah divalidasi sebelum bisa lanjut ke langkah berikutnya
- Setelah submit, evaluasi otomatis masuk status processing dan user diarahkan ke P-04
- Evaluasi yang sudah disubmit tidak bisa diedit lagi

**Data yang dibutuhkan:** Daftar kategori pengadaan, konfigurasi kriteria per kategori

---

### P-04 Detail Evaluasi — Processing

**Tujuan:** Memberi user visibilitas transparan tentang apa yang sedang dikerjakan AI, sehingga proses tidak terasa seperti "kotak hitam".

**Mengapa transparansi ini penting:** Salah satu kekhawatiran utama pengguna terhadap sistem AI adalah ketidakpahaman tentang cara AI bekerja. Dengan menampilkan progress tiap sub-agent secara terpisah, user dapat melihat bahwa evaluasi dilakukan secara sistematis dan terstruktur — membangun kepercayaan terhadap hasilnya.

**Yang ditampilkan:**
- Daftar tujuh sub-agent beserta status dan progress masing-masing: Data Collector, Financial Analyzer, Risk Assessor, Performance Scorer, Negotiation Assistant, Qualitative Analyzer, dan Preference Matcher
- Pesan singkat dari tiap agent tentang apa yang sedang dikerjakan
- Estimasi waktu selesai
- Jumlah vendor yang sedang dianalisa

Tiga agent pertama (Data Collector, Financial Analyzer, Risk Assessor) berjalan paralel. Performance Scorer berjalan setelah Data Collector selesai. Negotiation Assistant dan Qualitative Analyzer berjalan paralel setelah Performance Scorer. Preference Matcher berjalan terakhir. Urutan eksekusi ini tercermin dalam tampilan — agent yang sedang menunggu ditampilkan dengan status berbeda dari yang sedang aktif berjalan.

**Perilaku penting:**
- Progress diperbarui secara real-time tanpa perlu refresh
- Jika salah satu agent mengalami masalah, ditampilkan sebagai peringatan tanpa menghentikan agent lain
- User boleh meninggalkan halaman — proses tetap berjalan di background
- Saat semua agent selesai, user otomatis diarahkan ke P-05
- Panel AI memberikan update naratif tentang temuan menarik selama proses berlangsung

**Data yang dibutuhkan:** Status dan progress real-time tiap sub-agent

---

### P-05 Hasil Rekomendasi

**Tujuan:** Menyajikan output evaluasi AI secara lengkap, jelas, dan dapat dipertanggungjawabkan sebagai basis pengambilan keputusan.

**Mengapa ini halaman terpenting:** Ini adalah "momen kebenaran" dari seluruh sistem. Jika halaman ini tidak meyakinkan, seluruh proses sebelumnya kehilangan nilai. Desainnya harus menjawab pertanyaan user: siapa vendor terbaik berdasarkan metrik, apa keunggulan unik masing-masing, dan — jika preferensi diisi — vendor mana yang paling sesuai dengan konteks bisnis perusahaan.

**Yang ditampilkan — lima bagian:**

**Bagian 1 — Narasi pengantar**
Teks pendek yang memberi framing hasil evaluasi. Isinya berbeda tergantung mode: jika tidak ada preferensi, narasi menyatakan bahwa ini adalah ranking objektif berbasis metrik terukur. Jika ada preferensi, narasi menyebutkan preferensi apa yang dipertimbangkan. Narasi ini dihasilkan oleh Preference Matcher Agent.

**Bagian 2 — Rekomendasi utama (TOPSIS)**
Vendor dengan skor TOPSIS tertinggi yang lolos threshold ditampilkan secara prominent beserta skor total dan ringkasan reasoning dalam dua kalimat. Di sinilah tombol "Kirim ke Manager untuk Approval" berada.

**Bagian 3 — Ranking semua vendor**
Tabel perbandingan seluruh vendor dengan skor total, skor per kriteria, dan indikator kesesuaian preferensi (jika ada). Baris dapat diperluas untuk melihat breakdown skor per kriteria, catatan AI per kriteria, dan profil kualitatif vendor tersebut. Kolom dapat diurutkan untuk eksplorasi mandiri.

**Bagian 4 — Profil kualitatif & perbandingan**
Narasi yang menguraikan nilai tambah unik tiap vendor di luar lima kriteria standar, diikuti summary komparatif antar semua vendor. Bagian ini dihasilkan oleh Qualitative Analyzer Agent. Jika dua atau lebih vendor memiliki skor TOPSIS yang berdekatan, bagian ini secara eksplisit menyoroti unique offerings mana yang bisa menjadi faktor pembeda.

**Bagian 5 — Rekomendasi berbasis preferensi** *(hanya ditampilkan jika preferensi diisi)*
Rekomendasi 1–3 vendor yang paling sesuai dengan preferensi yang dinyatakan, disertai reasoning per vendor. Jika ada konflik antara rekomendasi preferensi dan ranking TOPSIS, sebuah conflict callout ditampilkan secara prominan dengan warna peringatan — procurement staff tidak boleh melewatkan informasi ini.

**Bagian 6 — Reasoning AI**
Narasi penjelasan lengkap berbasis TOPSIS: mengapa vendor terpilih menang, kelemahan yang perlu diwaspadai, dan rekomendasi langkah negosiasi.

**Perilaku penting:**
- Halaman ini bersifat read-only — tidak ada editing hasil
- Panel AI aktif dengan RAG context — dapat menjawab pertanyaan mendalam tentang hasil evaluasi maupun isi dokumen penawaran vendor secara langsung
- Setelah dikirim ke manager, tombol berubah menjadi indikasi "sudah dikirim"
- Conflict callout (bagian 5) tidak bisa di-dismiss — selalu terlihat selama halaman terbuka

**Data yang dibutuhkan:** Ranking vendor, skor per kriteria, profil kualitatif, output preferensi (jika ada), conflict callout (jika ada), reasoning AI

---

### P-06 Riwayat Evaluasi

**Tujuan:** Menyediakan akses ke semua evaluasi yang pernah dibuat sebagai referensi dan dokumentasi.

**Mengapa riwayat ini penting:** Keputusan vendor yang baik dibangun di atas pembelajaran dari evaluasi sebelumnya. Riwayat memungkinkan staff membandingkan hasil antar waktu dan manager memiliki visibilitas penuh atas aktivitas pengadaan.

**Yang ditampilkan:**
- Tabel daftar evaluasi dengan kolom: nama, kategori, jumlah vendor, status, tanggal, dan vendor yang terpilih
- Filter berdasarkan status, kategori, dan rentang tanggal
- Pencarian berdasarkan nama evaluasi

**Perilaku penting:**
- Staff hanya melihat evaluasi miliknya sendiri
- Manager melihat evaluasi dari seluruh staff
- Klik baris membawa ke halaman detail yang relevan berdasarkan status

**Data yang dibutuhkan:** Daftar evaluasi dengan filter dan pagination

---

### P-07 Approval

**Tujuan:** Memberikan manager konteks yang cukup untuk mengambil keputusan final atas hasil evaluasi.

**Mengapa manager perlu halaman terpisah:** Manager tidak terlibat dalam proses pengisian data, sehingga mereka membutuhkan ringkasan yang padat dan langsung ke poin keputusan — berbeda dengan staff yang mengikuti proses dari awal.

**Yang ditampilkan:**
- Daftar evaluasi yang menunggu keputusan (tab utama)
- Per evaluasi: judul, nama staff pengaju, tanggal pengajuan, rekomendasi AI beserta skornya, dan ringkasan budget
- Tombol untuk melihat detail lengkap (membuka P-05)
- Form keputusan: approve atau reject dengan kolom komentar

**Perilaku penting:**
- Komentar bersifat opsional untuk approve, tetapi wajib untuk reject
- Setelah keputusan diambil, notifikasi dikirim ke staff
- Evaluasi yang di-reject kembali ke status "butuh revisi" dan dapat diperbaiki staff

**Data yang dibutuhkan:** Daftar evaluasi pending approval, detail evaluasi, hasil rekomendasi AI

---

### P-08 Settings — Konfigurasi Kriteria

**Tujuan:** Memberi manager kemampuan untuk menyesuaikan bobot kriteria evaluasi sesuai prioritas bisnis perusahaan per kategori pengadaan.

**Mengapa bobot bisa dikonfigurasi:** Prioritas kriteria tidak universal. Pengadaan IT hardware mungkin lebih mementingkan garansi dan support, sementara pengadaan jasa lebih mementingkan track record dan kecepatan delivery. Konfigurasi yang fleksibel membuat sistem relevan untuk berbagai jenis pengadaan.

**Yang ditampilkan:**
- Pilihan kategori pengadaan
- Tabel lima kriteria dengan field bobot (dalam persen) dan threshold minimum per kriteria
- Indikator total bobot yang diperbarui secara real-time saat user mengubah angka
- Tombol reset ke nilai default dan tombol simpan

**Perilaku penting:**
- Total bobot harus tepat 100% — tombol simpan tidak aktif selama kondisi ini belum terpenuhi
- Perubahan hanya berlaku untuk evaluasi yang dibuat setelah perubahan disimpan, tidak berlaku retroaktif
- Panel AI dapat menjelaskan implikasi perubahan bobot terhadap hasil evaluasi sebelum user menyimpan

**Data yang dibutuhkan:** Konfigurasi bobot kriteria per kategori, daftar kategori pengadaan

---

## 9. Status & State Evaluasi

Setiap evaluasi memiliki lifecycle yang terdefinisi. Memahami lifecycle ini penting karena status menentukan aksi apa yang tersedia, halaman mana yang bisa diakses, dan siapa yang bisa melakukan apa.

| Status | Makna | Siapa yang bisa akses |
|---|---|---|
| `draft` | Evaluasi sedang disusun, belum disubmit | Staff pemilik |
| `processing` | AI sedang menganalisa semua vendor | Staff pemilik |
| `selesai` | AI selesai, hasil tersedia, belum dikirim ke manager | Staff pemilik |
| `menunggu_approval` | Sudah dikirim ke manager, menunggu keputusan | Staff pemilik + semua Manager |
| `approved` | Manager menyetujui hasil evaluasi | Semua |
| `butuh_revisi` | Manager menolak, staff perlu merevisi | Staff pemilik + semua Manager |

**Alur transisi status:**

```
draft → processing → selesai → menunggu_approval → approved
                                                  ↘ butuh_revisi → menunggu_approval (ulang)
```

Status bersifat **searah** — evaluasi tidak bisa dikembalikan ke status sebelumnya kecuali melalui mekanisme reject yang sudah terdefinisi.

---

## 10. Navigasi & Routing

| Path | Halaman | Akses |
|---|---|---|
| `/login` | P-01 Login | Public |
| `/dashboard` | P-02 Dashboard | Semua role |
| `/evaluasi/baru` | P-03 Buat Evaluasi Baru | Staff, Manager |
| `/evaluasi/:id/proses` | P-04 Processing | Semua role |
| `/evaluasi/:id/hasil` | P-05 Hasil Rekomendasi | Semua role |
| `/riwayat` | P-06 Riwayat Evaluasi | Semua role |
| `/approval` | P-07 Approval | Manager only |
| `/settings/kriteria` | P-08 Settings | Manager only |

**Aturan redirect:**
- User yang belum login mengakses route apapun → diarahkan ke `/login`
- Staff mengakses route khusus Manager → diarahkan ke `/dashboard`
- Login berhasil → diarahkan ke `/dashboard`

---

## 11. Catatan untuk Dokumen Lanjutan

### Untuk FE-02 (Component Library)

Dari halaman-halaman di atas, komponen baru yang perlu ditambahkan:
- `PreferenceInput` — textarea dengan counter karakter dan placeholder (P-03 Langkah 1)
- `QualitativeProfileCard` — menampilkan profil kualitatif dan unique offerings per vendor (P-05 Bagian 4)
- `PreferenceRecommendationCard` — menampilkan rekomendasi berbasis preferensi (P-05 Bagian 5)
- `ConflictCallout` — warning prominan saat preferensi dan TOPSIS berkonflik (P-05 Bagian 5)
- Komponen `AgentProgressPanel` perlu diperbarui untuk menampilkan 7 agent

### Untuk BE-02 (API Contract)

Setiap halaman di dokumen ini memiliki kebutuhan data yang perlu diterjemahkan menjadi endpoint di BE-02. Endpoint hasil evaluasi perlu mengembalikan data kualitatif dan preferensi sebagai bagian dari response P-05.

### Untuk DB-01 (Data Model)

Entitas baru yang teridentifikasi dari kebutuhan halaman ini:
- Field `preferensi_perusahaan` di tabel `evaluasi` (untuk P-03)
- Kolom `unique_offerings`, `profil_kualitatif`, `tingkat_kesesuaian_preferensi` di `hasil_vendor` (untuk P-05)
- Kolom `preference_matching_result` dan `conflict_callout` di `hasil_evaluasi` (untuk P-05)

---

*Dokumen ini adalah living document — akan diperbarui seiring diskusi dengan tim dan feedback dari proses desain.*

---

**Riwayat Perubahan**

| Versi | Tanggal | Perubahan | Author |
|---|---|---|---|
| 1.0.0 | 2026-06-07 | Versi awal | — |
| 2.0.0 | 2026-06-07 | Revisi: fokus ke what & why, hapus detail implementasi | — |
| 3.0.0 | 2026-06-11 | P-03 Langkah 1: tambah field preferensi opsional; P-04: perbarui daftar agent dari 5 menjadi 7 beserta urutan eksekusi; P-05: tambah 3 bagian baru (narasi pengantar, profil kualitatif, rekomendasi preferensi + conflict callout) | — |
