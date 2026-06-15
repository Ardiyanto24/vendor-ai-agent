# SH-01 — Decision Log

**Project:** AI Vendor Selection System  
**Dokumen:** SH-01 — Decision Log  
**Versi:** 5.0.0  
**Tanggal:** 2026-06-13  
**Status:** Living Document  
**Author:** —  
**Direview oleh:** —

---

## Tentang Dokumen Ini

Decision Log adalah catatan permanen dari setiap keputusan teknis dan produk yang signifikan — beserta konteksnya, alternatif yang dipertimbangkan, alasan keputusan diambil, dan konsekuensi yang perlu disadari.

Dokumen ini ditulis untuk **orang yang bergabung belakangan** — engineer baru, stakeholder yang baru terlibat, atau tim sendiri enam bulan ke depan yang lupa mengapa sesuatu dirancang dengan cara tertentu. Tanpa catatan ini, keputusan yang sudah dipikirkan matang-matang berisiko diulang dari nol atau dibatalkan tanpa mempertimbangkan trade-off yang sudah dianalisa sebelumnya.

**Format setiap entri:**
- **Konteks** — situasi yang memunculkan kebutuhan keputusan ini
- **Keputusan** — apa yang diputuskan
- **Alternatif yang ditolak** — opsi lain yang dipertimbangkan dan mengapa tidak dipilih
- **Konsekuensi** — apa yang harus diterima sebagai trade-off dari keputusan ini
- **Dokumen terkait** — di mana keputusan ini berdampak

---

## Daftar Keputusan

| ID | Kategori | Judul | Tanggal |
|---|---|---|---|
| ADR-001 | Produk | Pendekatan UI-first dalam perancangan sistem | 2026-06-07 |
| ADR-002 | Produk | Dua role user untuk MVP | 2026-06-07 |
| ADR-003 | Produk | Layout 3-panel sebagai desain global | 2026-06-07 |
| ADR-004 | Produk | Core flow: evaluasi baru → processing → hasil | 2026-06-07 |
| ADR-005 | Produk | Batasan 10 vendor maksimum per evaluasi | 2026-06-07 |
| ADR-006 | Teknis | Next.js App Router sebagai framework frontend | 2026-06-07 |
| ADR-007 | Teknis | shadcn/ui sebagai UI component base | 2026-06-07 |
| ADR-008 | Teknis | Zustand + TanStack Query untuk state management | 2026-06-07 |
| ADR-009 | Teknis | Chart.js untuk visualisasi data scoring | 2026-06-07 |
| ADR-010 | Teknis | Arsitektur hybrid: Next.js + FastAPI | 2026-06-07 |
| ADR-011 | Teknis | Supabase sebagai platform database | 2026-06-07 |
| ADR-012 | Teknis | ~~Polyrepo: tiga repository terpisah~~ *(Superseded oleh ADR-031)* | 2026-06-07 |
| ADR-013 | Teknis | Vercel sebagai platform deployment frontend | 2026-06-07 |
| ADR-014 | Teknis | LangGraph sebagai framework agent orchestration | 2026-06-07 |
| ADR-015 | Teknis | ~~Claude Sonnet sebagai LLM utama~~ *(Superseded oleh ADR-033)* | 2026-06-07 |
| ADR-016 | Teknis | TOPSIS sebagai algoritma scoring | 2026-06-07 |
| ADR-017 | Teknis | Semi-relasional: JSON column untuk data dinamis | 2026-06-07 |
| ADR-018 | Teknis | UUID sebagai primary key di semua tabel | 2026-06-07 |
| ADR-019 | Teknis | Soft delete di semua tabel | 2026-06-07 |
| ADR-020 | Teknis | Supabase Realtime untuk progress agent | 2026-06-07 |
| ADR-021 | Teknis | SSE untuk AI chat streaming | 2026-06-07 |
| ADR-022 | Teknis | Tavily API untuk web search (free tier) | 2026-06-07 |
| ADR-023 | Produk | Integrasi ERP ditunda pasca-MVP | 2026-06-07 |
| ADR-024 | Produk | Verifikasi legalitas via web search, bukan API resmi | 2026-06-07 |
| ADR-025 | Teknis | Prompt disimpan sebagai file, bukan hardcoded | 2026-06-07 |
| ADR-026 | Teknis | Vitest + Playwright sebagai testing stack | 2026-06-07 |
| ADR-027 | Teknis | Supabase Pro tier minimum untuk production | 2026-06-07 |
| ADR-028 | Teknis | ~~OpenAI text-embedding-3-small sebagai embedding model untuk RAG~~ *(Superseded oleh ADR-034)* | 2026-06-11 |
| ADR-029 | Teknis | pgvector di Supabase sebagai vector store untuk RAG | 2026-06-11 |
| ADR-030 | Produk | Form preferensi opsional sebagai input Preference Matcher Agent | 2026-06-11 |
| ADR-031 | Teknis | 2-repo: monorepo TypeScript + repo terpisah FastAPI | 2026-06-12 |
| ADR-032 | Tim | ~~Empat role developer: Frontend, Backend, Database, dan AI Engineer~~ *(Superseded oleh ADR-036)* | 2026-06-12 |
| ADR-033 | Teknis | DeepSeek-V4-Flash via OpenRouter sebagai LLM utama | 2026-06-13 |
| ADR-034 | Teknis | Google Gemini text-embedding-004 sebagai embedding model untuk RAG | 2026-06-13 |
| ADR-035 | Dokumentasi | Namespace AI terpisah untuk dokumen spesifikasi AI Engineer | 2026-06-13 |
| ADR-036 | Tim | Dua track pengerjaan: Fullstack Engineer + AI Engineer (solo developer) | 2026-06-13 |

---

## Detail Keputusan

---

### ADR-001 — Pendekatan UI-first dalam perancangan sistem

**Tanggal:** 2026-06-07 | **Kategori:** Produk

**Konteks:**
Dalam merancang sistem yang melibatkan banyak komponen teknis (AI agent, scoring engine, database, API), ada dua pendekatan umum: mulai dari infrastruktur teknis (data model, API contract) lalu bangun UI di atasnya, atau mulai dari UI (apa yang dilihat dan dilakukan user) lalu turunkan kebutuhan teknis dari sana.

**Keputusan:**
Menggunakan pendekatan **UI-first (outside-in design)** — FE-03 (Page & User Flow) dikerjakan pertama, diikuti FE-02 (Component Library), sebelum mendefinisikan API contract dan data model.

**Alternatif yang ditolak:**

*Data model first:* Dimulai dari ERD, lalu API, lalu UI. Pendekatan ini umum di tim yang lebih nyaman dengan backend, tetapi berisiko menghasilkan UI yang mencerminkan struktur database, bukan kebutuhan user.

*API contract first:* Dimulai dari mendefinisikan endpoint, lalu diimplementasikan di kedua sisi. Baik untuk integrasi antar tim, tetapi sama berisikonya dengan data model first dalam mengabaikan perspektif user.

**Alasan memilih UI-first:**
UI mencerminkan kebutuhan nyata user. Dengan merancang UI terlebih dahulu, tim dipaksa berpikir dari perspektif procurement staff sebelum memikirkan implementasi teknis. Kebutuhan data dan API kemudian diturunkan dari UI — bukan sebaliknya.

**Konsekuensi:**
Dokumen frontend (FE-01 s/d FE-06) harus selesai sebelum BE-02 dan DB-01 bisa dikerjakan dengan akurat. Ini menciptakan ketergantungan urutan pengerjaan yang harus dijaga.

**Dokumen terkait:** FE-03, FE-02, FE-01, BE-02, DB-01

---

### ADR-002 — Dua role user untuk MVP

**Tanggal:** 2026-06-07 | **Kategori:** Produk

**Konteks:**
Sistem pengadaan di perusahaan nyata bisa memiliki banyak role — staf input, supervisor, manager, direktur, admin sistem, auditor. Mendefinisikan terlalu banyak role untuk MVP akan memperumit implementasi tanpa memberikan nilai yang proporsional.

**Keputusan:**
MVP hanya mendukung **dua role**: `staff` (procurement staff yang membuat evaluasi) dan `manager` (yang melakukan approval).

**Alternatif yang ditolak:**

*Satu role saja:* Semua user memiliki akses penuh. Ditolak karena approval flow — yang merupakan bagian kritis dari proses pengadaan — tidak bisa diimplementasikan dengan satu role.

*Tiga role (staff, manager, admin):* Menambahkan admin untuk konfigurasi sistem. Ditolak karena untuk MVP, fungsi admin (konfigurasi bobot kriteria) cukup dipegang manager.

**Alasan:**
Dua role mencerminkan struktur pengambilan keputusan yang paling mendasar dalam pengadaan: yang mengerjakan dan yang menyetujui. Ini cukup untuk mendemonstrasikan nilai sistem tanpa over-engineering.

**Konsekuensi:**
Tidak ada segregasi lebih lanjut dalam role staff (misalnya tidak bisa membatasi staff A hanya boleh akses kategori IT). Ini adalah trade-off yang diterima untuk MVP.

**Dokumen terkait:** FE-03, BE-06, DB-01

---

### ADR-003 — Layout 3-panel sebagai desain global

**Tanggal:** 2026-06-07 | **Kategori:** Produk

**Konteks:**
Aplikasi perlu mengintegrasikan dua fungsi utama yang berbeda sifatnya: menampilkan data terstruktur (evaluasi, vendor, skor) dan menyediakan antarmuka chat AI. Kedua fungsi ini perlu bisa diakses bersamaan tanpa perpindahan halaman.

**Keputusan:**
Menggunakan **layout 3-panel** yang konsisten di seluruh halaman: sidebar navigasi kiri (220px), panel konten utama (fleksibel), dan panel AI kanan (360px).

**Alternatif yang ditolak:**

*Full-width dengan panel AI slide-in:* AI panel muncul saat tombol diklik. Lebih bersih secara visual, tetapi membuat AI terasa sebagai fitur sekunder, bukan bagian inti alur kerja.

*Split 50-50 konten dan AI:* Terlalu banyak ruang untuk AI, terlalu sedikit untuk konten yang padat data.

*Tab-based antara konten dan AI:* User tidak bisa melihat keduanya bersamaan — menurunkan kegunaan AI panel secara signifikan.

**Alasan:**
Layout 3-panel adalah standar yang sudah familiar di tools AI modern (Cursor, Perplexity, Claude.ai). AI panel yang selalu hadir menegaskan bahwa AI adalah bagian inti dari alur kerja, bukan fitur tambahan. Panel kanan yang tetap memberikan akses AI kapan saja tanpa mengganggu fokus pada konten utama.

**Konsekuensi:**
Ruang layar lebih sempit di panel konten, terutama pada layar kecil. Desain responsif untuk tablet atau mobile memerlukan pertimbangan khusus yang tidak dicakup dalam MVP.

**Dokumen terkait:** FE-03, FE-02 (AppShell, Sidebar, AIPanel)

---

### ADR-004 — Core flow: evaluasi baru → processing → hasil

**Tanggal:** 2026-06-07 | **Kategori:** Produk

**Konteks:**
Ada tiga alur potensial yang bisa menjadi core flow aplikasi: (1) buat evaluasi → tunggu AI → lihat hasil, (2) cari vendor dari database → bandingkan → pilih, atau (3) upload dokumen → AI ekstrak → lihat hasil.

**Keputusan:**
**Alur (1)** — buat evaluasi baru, input vendor, tunggu AI memproses, lihat rekomendasi — menjadi core flow utama.

**Alternatif yang ditolak:**

*Cari dari database vendor:* Mengasumsikan adanya database vendor terpusat yang belum ada di MVP. Membutuhkan infrastruktur tambahan yang signifikan.

*Upload dokumen sebagai flow utama:* Bergantung pada kualitas dokumen penawaran yang tidak selalu konsisten. Lebih baik sebagai input alternatif dalam alur utama.

**Alasan:**
Alur (1) paling komprehensif dalam menunjukkan nilai AI sistem — user melihat seluruh proses dari input hingga rekomendasi yang dapat dijelaskan. Untuk portofolio, ini adalah alur yang paling "wow" saat didemonstrasikan. Upload dokumen tetap tersedia sebagai cara input vendor alternatif dalam alur yang sama.

**Konsekuensi:**
User harus menginput data vendor secara manual atau upload dokumen untuk setiap evaluasi. Tidak ada shortcut dari database vendor yang sudah ada.

**Dokumen terkait:** FE-03 section 7, BE-03

---

### ADR-005 — Batasan 10 vendor maksimum per evaluasi

**Tanggal:** 2026-06-07 | **Kategori:** Produk

**Konteks:**
Perlu mendefinisikan berapa banyak vendor yang bisa dievaluasi dalam satu proses evaluasi. Terlalu sedikit membatasi kegunaan, terlalu banyak membebani sistem dan mempersulit interpretasi hasil.

**Keputusan:**
Maksimum **10 vendor per evaluasi**, minimum **2 vendor**.

**Alternatif yang ditolak:**

*Tidak ada batasan:* Berisiko overload LLM dan database. Hasil dengan 20+ vendor juga sulit diinterpretasikan.

*Maksimum 5 vendor:* Terlalu restriktif untuk proses pengadaan yang kompetitif. Banyak RFP di dunia nyata memiliki lebih dari 5 peserta.

*Maksimum 20 vendor:* Setiap evaluasi dengan 20 vendor menghasilkan hingga 80 Tavily queries dan puluhan LLM calls — biaya dan waktu yang tidak sebanding dengan nilai tambahnya untuk MVP.

**Alasan:**
10 vendor adalah angka yang cukup untuk proses pengadaan yang kompetitif dan realistis, sekaligus dalam batas yang wajar untuk biaya API dan waktu processing. Evaluasi dengan 10 vendor tetap menghasilkan output yang bisa diinterpretasikan dengan jelas.

**Konsekuensi:**
Perusahaan dengan proses tender yang melibatkan lebih dari 10 vendor perlu melakukan pra-seleksi sebelum menggunakan sistem ini. Batasan ini dapat dilonggarkan di versi berikutnya berdasarkan data performa aktual.

**Dokumen terkait:** BE-02, BE-03, DB-01

---

### ADR-006 — Next.js App Router sebagai framework frontend

**Tanggal:** 2026-06-07 | **Kategori:** Teknis

**Konteks:**
Memilih framework frontend yang tepat untuk aplikasi ini yang memiliki karakteristik: butuh SSR untuk performa awal, butuh API routes untuk BFF layer, akan di-deploy ke Vercel, dan tim memiliki background TypeScript.

**Keputusan:**
**Next.js 14+ dengan App Router** sebagai framework frontend dan BFF (Backend for Frontend) layer.

**Alternatif yang ditolak:**

*Next.js dengan Pages Router:* Lebih familiar, tetapi Pages Router adalah pendekatan lama yang tidak mendapatkan fitur-fitur baru. App Router adalah arah resmi Next.js ke depan.

*Remix:* Filosofi yang bagus, tetapi ekosistem dan komunitas lebih kecil dari Next.js. Vercel native support juga lebih kuat untuk Next.js.

*Vite + React (tanpa Next.js):* Lebih ringan, tetapi tidak ada SSR dan API routes bawaan. Membutuhkan setup tambahan yang menambah kompleksitas.

**Alasan:**
Next.js App Router menyediakan SSR, API Routes, middleware, dan integrasi Vercel yang semuanya dibutuhkan sistem ini dalam satu framework. Server Components secara khusus menguntungkan untuk halaman yang berat data — mengurangi JavaScript yang dikirim ke browser.

**Konsekuensi:**
App Router memiliki learning curve lebih tinggi dari Pages Router, terutama dalam memahami server vs client component boundary. Tim perlu familiar dengan konsep ini sebelum mulai development.

**Dokumen terkait:** FE-01

---

### ADR-007 — shadcn/ui sebagai UI component base

**Tanggal:** 2026-06-07 | **Kategori:** Teknis

**Konteks:**
Membutuhkan UI component library yang menyediakan komponen-komponen dasar (button, input, table, dialog) agar tidak membangun dari scratch, sekaligus memberikan kontrol penuh untuk kustomisasi.

**Keputusan:**
**shadcn/ui** sebagai component base, dikombinasikan dengan Tailwind CSS.

**Alternatif yang ditolak:**

*MUI (Material UI):* Library dependency eksternal yang memiliki sistem styling sendiri (Emotion). Sulit dikombinasikan dengan Tailwind dan memberikan lock-in yang kuat ke design language Material Design.

*Ant Design:* Enterprise-ready dan lengkap, tetapi opinionated dalam styling dan sulit di-override untuk tampilan yang custom. Bundle size juga besar.

*Chakra UI:* Bagus, tetapi sama seperti MUI — dependency eksternal yang sulit dikombinasikan dengan Tailwind.

*Bangun dari scratch dengan Tailwind:* Terlalu lambat untuk MVP. Komponen dasar seperti dialog, select, dan table membutuhkan banyak waktu untuk dibangun dengan aksesibilitas yang benar.

**Alasan:**
shadcn/ui bukan dependency — komponen di-generate ke dalam project sehingga tim memiliki kontrol penuh atas kode. Tidak ada lock-in. Setiap komponen dapat dikustomisasi secara mendalam. Integrasi dengan Tailwind adalah native, bukan workaround.

**Konsekuensi:**
Update shadcn/ui tidak otomatis — jika ada perbaikan di komponen shadcn, tim perlu secara manual mengupdate komponen yang ada. Ini adalah trade-off dari pendekatan "copy, don't depend".

**Dokumen terkait:** FE-01, FE-02

---

### ADR-008 — Zustand + TanStack Query untuk state management

**Tanggal:** 2026-06-07 | **Kategori:** Teknis

**Konteks:**
Aplikasi memiliki dua jenis state yang berbeda: server state (data dari API yang perlu di-cache dan di-sync) dan client state (UI state yang tidak berasal dari server). Kedua jenis ini membutuhkan penanganan yang berbeda.

**Keputusan:**
**TanStack Query** untuk server state (caching, refetching, invalidasi) dan **Zustand** untuk global client state (sesi user, chat history, notifikasi).

**Alternatif yang ditolak:**

*Redux Toolkit untuk segalanya:* Terlalu verbose untuk skala project ini. Redux memaksa boilerplate yang signifikan untuk setiap slice of state.

*React Context + useReducer:* Cukup untuk project sederhana, tetapi tidak memiliki caching, deduplication request, dan background refetching yang disediakan TanStack Query untuk server state.

*Zustand untuk segalanya (termasuk server state):* Mencampur server state dan client state dalam satu store menciptakan dua sumber kebenaran dan sinkronisasi manual yang rentan bug.

*SWR sebagai alternatif TanStack Query:* Lebih sederhana dari TanStack Query, tetapi kurang fitur untuk use case kompleks seperti optimistic updates dan dependent queries yang mungkin dibutuhkan.

**Alasan:**
Pemisahan yang jelas antara server state (TanStack Query) dan client state (Zustand) mengikuti prinsip single source of truth. Setiap jenis data memiliki satu tempat yang jelas sebagai sumbernya.

**Konsekuensi:**
Tim perlu memahami perbedaan antara server state dan client state sebelum mulai development — keputusan "di mana menyimpan data ini" harus konsisten di seluruh codebase.

**Dokumen terkait:** FE-01, FE-04

---

### ADR-009 — Chart.js untuk visualisasi data scoring

**Tanggal:** 2026-06-07 | **Kategori:** Teknis

**Konteks:**
Halaman hasil evaluasi (P-05) membutuhkan visualisasi data scoring — bar chart horizontal per kriteria dan radar chart perbandingan vendor. Perlu memilih library yang tepat.

**Keputusan:**
**Chart.js** via `react-chartjs-2` wrapper.

**Alternatif yang ditolak:**

*Recharts:* Ringan dan React-native, tetapi kurang fleksibel untuk kustomisasi visual yang lebih dalam. Radar chart di Recharts juga kurang matang.

*Tremor:* Komponen chart siap pakai untuk dashboard, tetapi opinionated dalam styling dan sulit dikustomisasi untuk kebutuhan spesifik.

*D3.js:* Sangat powerful dan fleksibel, tetapi learning curve yang tinggi dan membutuhkan lebih banyak kode untuk chart yang relatif standar.

*Plotly:* Overkill untuk kebutuhan chart sederhana ini. Bundle size besar.

**Alasan:**
Chart.js adalah library yang mature, dokumentasinya lengkap, dan komunitas besar memudahkan troubleshooting. Fleksibel untuk bar chart dan radar chart yang dibutuhkan, dengan wrapper React yang baik.

**Konsekuensi:**
Chart.js bukan React-native — menggunakan imperative API yang dibungkus oleh react-chartjs-2. Ada sedikit overhead dalam setup registrasi komponen Chart.js yang perlu dipahami tim.

**Dokumen terkait:** FE-02 section 11

---

### ADR-010 — Arsitektur hybrid: Next.js + FastAPI

**Tanggal:** 2026-06-07 | **Kategori:** Teknis

**Konteks:**
Backend perlu menangani dua kelompok fungsi yang sangat berbeda karakteristiknya: operasi CRUD standar (evaluasi, vendor, auth) dan operasi AI yang berat (agent orchestration, scoring engine dengan numpy/scipy, LLM calls). Perlu memutuskan apakah satu atau dua service yang optimal.

**Keputusan:**
**Arsitektur hybrid**: Next.js API Routes untuk kelompok 1-2 (auth, CRUD), **FastAPI (Python)** untuk kelompok 3-5 (AI agent, scoring, chat streaming).

**Alternatif yang ditolak:**

*FastAPI saja (semua di Python):* Memaksakan semua fungsi dalam satu service Python. Feasible, tetapi kehilangan keunggulan Next.js sebagai BFF layer yang terintegrasi dengan frontend.

*Next.js API Routes saja (semua di TypeScript):* Semua logika AI dan scoring harus ditulis dalam TypeScript/JavaScript — kehilangan ekosistem Python yang kaya untuk ML/AI (numpy, scipy, LangGraph, Anthropic SDK Python).

*Tiga service terpisah (Next.js + Node BFF + Python):* Terlalu kompleks untuk MVP. Menambahkan service Node terpisah hanya untuk BFF tidak memberikan nilai tambah yang cukup.

**Alasan:**
Pemisahan yang alami: TypeScript untuk hal-hal web (routing, auth, CRUD) dan Python untuk hal-hal AI (agent, scoring). Setiap service dapat di-scale secara independen. Jika AI processing membutuhkan lebih banyak resource, hanya FastAPI yang perlu di-scale up.

**Konsekuensi:**
Dua codebase dengan dua bahasa yang perlu dikelola. Komunikasi internal Next.js → FastAPI melalui HTTP internal yang perlu dikonfigurasi dan dipantau. Developer perlu memahami kedua stack.

**Dokumen terkait:** BE-02, BE-01, FE-01

---

### ADR-011 — Supabase sebagai platform database

**Tanggal:** 2026-06-07 | **Kategori:** Teknis

**Konteks:**
Sistem membutuhkan: database relasional, file storage untuk dokumen upload, autentikasi, dan mekanisme real-time untuk broadcast progress agent. Bisa menggunakan service terpisah untuk masing-masing, atau satu platform yang menyediakan semuanya.

**Keputusan:**
**Supabase** sebagai platform tunggal yang menyediakan PostgreSQL, Storage, Auth, dan Realtime.

**Alternatif yang ditolak:**

*PostgreSQL mandiri + S3 + Auth0 + Pusher:* Kombinasi service terpisah yang masing-masing adalah solusi terbaik di kelasnya. Ditolak karena kompleksitas operasional yang tinggi untuk MVP — empat service berbeda yang perlu dikonfigurasi, dimonitor, dan ditagih terpisah.

*Firebase:* NoSQL — tidak cocok dengan kebutuhan data relasional sistem ini (evaluasi, vendor, hasil scoring memiliki relasi yang kompleks).

*PlanetScale (MySQL):* Database saja, tanpa storage, auth, atau realtime. Membutuhkan service tambahan.

**Alasan:**
Supabase menyediakan keempat kapabilitas yang dibutuhkan dalam satu platform dengan harga yang terjangkau. PostgreSQL sebagai database memberikan kemampuan relasional penuh. RLS di level database adalah lapisan keamanan yang kuat. Free tier cukup untuk development dan demo portofolio.

**Konsekuensi:**
Lock-in ke platform Supabase. Jika Supabase mengalami downtime, seluruh sistem (database, storage, auth, realtime) terdampak bersamaan. Migrasi ke platform lain di masa depan membutuhkan effort signifikan.

**Dokumen terkait:** DB-01, DB-02, BE-06

---

### ADR-012 — ~~Polyrepo: tiga repository terpisah~~ *(Superseded oleh ADR-031)*

**Tanggal:** 2026-06-07 | **Kategori:** Teknis | **Status:** Superseded — lihat ADR-031

**Catatan:** Keputusan ini digantikan oleh ADR-031 pada 2026-06-12. Entri ini dipertahankan untuk keperluan audit trail.

**Konteks:**
Project terdiri dari tiga komponen utama yang berbeda bahasa dan deployment target: Next.js frontend, Next.js API Routes (BFF), dan FastAPI service. Perlu memutuskan apakah disimpan dalam satu repo (monorepo) atau terpisah (polyrepo).

**Keputusan:**
**Polyrepo** — tiga repository terpisah: `vendor-ai-frontend`, `vendor-ai-backend`, `vendor-ai-agent`.

**Alternatif yang ditolak:**

*Monorepo dengan Turborepo/Nx:* Semua dalam satu repository. Lebih mudah untuk share types dan kode antar package. Ditolak karena kompleksitas setup monorepo yang tidak sebanding untuk skala MVP, terutama dengan Python dan TypeScript yang sulit di-share code-nya.

*Dua repo (frontend + backend):* Next.js frontend dan API Routes dalam satu repo, FastAPI terpisah. Opsi tengah yang masuk akal, tetapi tetap mencampur tanggung jawab frontend dan BFF dalam satu repo.

**Alasan:**
Perbedaan bahasa (TypeScript vs Python) membuat code sharing antar service tidak praktis. Batas tanggung jawab yang jelas per repository memudahkan ownership dan deployment yang independen. Frontend engineer tidak perlu clone kode Python untuk bekerja.

**Konsekuensi:**
Tidak ada type sharing otomatis antar service — kontrak API (BE-02) menjadi satu-satunya "kontrak" yang harus dijaga konsistensinya secara manual. Perubahan yang mempengaruhi beberapa service perlu di-coordinate antar repository.

**Dokumen terkait:** FE-01

---

### ADR-013 — Vercel sebagai platform deployment frontend

**Tanggal:** 2026-06-07 | **Kategori:** Teknis

**Konteks:**
Next.js frontend perlu di-deploy ke platform yang mendukung fitur-fitur spesifik Next.js (Server Components, API Routes, Edge functions) dengan minimal konfigurasi.

**Keputusan:**
**Vercel** sebagai platform deployment untuk Next.js frontend.

**Alternatif yang ditolak:**

*Railway:* Lebih fleksibel untuk host berbagai jenis service, tetapi tidak memiliki optimasi native untuk Next.js seperti yang dimiliki Vercel.

*AWS Amplify:* Mendukung Next.js, tetapi konfigurasi lebih kompleks dan tidak semua fitur Next.js didukung sepenuhnya.

*VPS mandiri (DigitalOcean, AWS EC2):* Kontrol penuh, tetapi membutuhkan konfigurasi server, SSL, dan CI/CD dari awal — overhead yang tidak perlu untuk MVP.

**Alasan:**
Vercel dibuat oleh tim yang sama dengan Next.js — integrasinya adalah yang terbaik. Preview deployment per PR, zero-configuration SSL, dan edge network global adalah fitur yang langsung tersedia tanpa setup tambahan.

**Konsekuensi:**
Lock-in ke Vercel. Biaya Vercel bisa meningkat signifikan pada skala traffic tinggi. Free tier cukup untuk development dan demo portofolio.

**Dokumen terkait:** FE-01

---

### ADR-014 — LangGraph sebagai framework agent orchestration

**Tanggal:** 2026-06-07 | **Kategori:** Teknis

**Konteks:**
Sistem membutuhkan framework untuk mengkoordinasikan lima AI agent yang berjalan paralel dengan dependency antar agent, state management, dan error handling.

**Keputusan:**
**LangGraph** sebagai framework orchestration agent.

**Alternatif yang ditolak:**

*CrewAI:* Lebih mudah setup untuk sistem multi-agent conversational. Ditolak karena kurang kontrol eksplisit atas alur eksekusi — untuk sistem yang harus dapat diaudit, alur yang terprediksi lebih penting dari kemudahan setup.

*AutoGen (Microsoft):* Lebih cocok untuk skenario agent yang saling berkomunikasi secara conversational. Sistem ini adalah pipeline terstruktur, bukan conversation.

*Implementasi custom tanpa framework:* Memberikan kontrol penuh tetapi membutuhkan effort signifikan untuk membangun state management, error handling, dan parallelism dari scratch.

**Alasan:**
LangGraph memodelkan alur agent sebagai directed graph yang eksplisit — dapat divisualisasikan, di-debug, dan di-audit. Kontrol eksplisit atas alur eksekusi sangat penting untuk sistem pengambilan keputusan yang hasilnya harus dapat dijelaskan.

**Konsekuensi:**
Learning curve LangGraph lebih tinggi dari CrewAI. Developer perlu memahami konsep graph state machine sebelum bisa berkontribusi pada kode orchestration.

**Dokumen terkait:** BE-03

---

### ADR-015 — ~~Claude Sonnet sebagai LLM utama~~ *(Superseded oleh ADR-033)*

**Tanggal:** 2026-06-07 | **Kategori:** Teknis | **Status:** Superseded — lihat ADR-033

**Catatan:** Keputusan ini digantikan oleh ADR-033 pada 2026-06-13. Entri ini dipertahankan untuk keperluan audit trail.

**Konteks:**
Sistem membutuhkan LLM yang dapat mengikuti instruksi secara konsisten, menghasilkan output JSON terstruktur yang reliable, dan memiliki kemampuan reasoning yang baik untuk analisa vendor.

**Keputusan:**
**Claude Sonnet** (via Anthropic API) sebagai LLM utama untuk semua agent evaluasi dan reasoning scoring. Claude Haiku sebagai kandidat untuk AI chat panel (keputusan final berdasarkan testing).

**Alternatif yang ditolak:**

*GPT-4o (OpenAI):* Performa sebanding, tetapi pengembang sistem memiliki latar belakang dan preferensi Anthropic. Keduanya feasible — ini adalah pilihan pragmatis.

*Gemini Pro (Google):* Masih relatif baru di ekosistem agent, dokumentasi dan SDK untuk agent use case kurang mature dibanding Anthropic dan OpenAI.

*Model open source (Llama, Mistral) self-hosted:* Tidak ada biaya API, tetapi membutuhkan infrastructure GPU yang biayanya jauh lebih tinggi untuk skala MVP. Kualitas output untuk instruction-following dan structured JSON juga masih di bawah model proprietary.

**Alasan:**
Claude konsisten dalam mengikuti instruksi kompleks dan menghasilkan output JSON yang reliable — keduanya kritis untuk agent yang hasilnya dikonsumsi oleh scoring engine. Kemampuan instruction-following yang konsisten mengurangi kebutuhan prompt engineering yang rumit.

**Konsekuensi:**
Biaya API Anthropic. Ketergantungan pada ketersediaan layanan Anthropic. Jika Anthropic API mengalami downtime, seluruh proses evaluasi AI tidak bisa berjalan.

**Dokumen terkait:** BE-03, BE-04, BE-07

---

### ADR-016 — TOPSIS sebagai algoritma scoring

**Tanggal:** 2026-06-07 | **Kategori:** Teknis

**Konteks:**
Scoring engine perlu menghasilkan ranking vendor dari data multi-dimensi (lima kriteria dengan bobot berbeda). Perlu memilih metode MCDM (Multi-Criteria Decision Making) yang tepat.

**Keputusan:**
**TOPSIS** (Technique for Order Preference by Similarity to Ideal Solution) sebagai algoritma scoring.

**Alternatif yang ditolak:**

*AHP (Analytic Hierarchy Process):* Membutuhkan pairwise comparison matrix dari user — terlalu kompleks untuk pengalaman user yang baik di form pengadaan.

*Weighted Sum Model (WSM):* Sangat sederhana, tetapi tidak menangani trade-off dengan baik. Vendor yang sangat buruk di satu dimensi bisa tertutupi oleh nilai tinggi di dimensi lain.

*SAW (Simple Additive Weighting):* Mirip WSM, rentan terhadap unit scaling yang berbeda antar kriteria.

*Machine Learning ranking model:* Membutuhkan data training historis yang tidak tersedia untuk sistem baru.

**Alasan:**
TOPSIS menggabungkan yang terbaik dari kesederhanaan (bisa dijelaskan secara intuitif) dan keandalan matematis (berbasis jarak Euclidean). Cocok dengan background statistika tim. Deterministik dan reproducible — input sama selalu menghasilkan output sama.

**Konsekuensi:**
TOPSIS sensitif terhadap penambahan alternatif baru — ranking bisa berubah jika vendor ditambahkan ke evaluasi yang sudah ada. Oleh karena itu daftar vendor dikunci setelah evaluasi disubmit.

**Dokumen terkait:** BE-05

---

### ADR-017 — Semi-relasional: JSON column untuk data dinamis

**Tanggal:** 2026-06-07 | **Kategori:** Teknis

**Konteks:**
Beberapa data dalam sistem memiliki struktur yang dinamis dan bergantung pada konfigurasi — khususnya skor per kriteria (jumlah dan nama kriteria bisa berubah per kategori pengadaan).

**Keputusan:**
**Pendekatan semi-relasional**: sebagian besar data dalam tabel relasional ternormalisasi, data yang strukturnya dinamis (skor per kriteria, konfigurasi kriteria) disimpan sebagai JSONB column di PostgreSQL.

**Alternatif yang ditolak:**

*Relasional murni — tabel tersendiri per kriteria:* Membutuhkan perubahan skema setiap kali konfigurasi kriteria berubah. Tidak fleksibel untuk sistem yang konfigurasinya dapat diubah oleh manager.

*Semi-relasional tanpa JSONB (JSON biasa):* PostgreSQL JSON biasa tidak bisa di-index dan di-query seefisien JSONB. JSONB adalah pilihan yang jelas untuk PostgreSQL.

*Document database (MongoDB):* Fleksibel untuk data dinamis, tetapi kehilangan kemampuan relasional untuk data yang memang relasional (evaluasi, vendor, approval). Menggunakan dua database berbeda untuk satu sistem menambah kompleksitas.

**Alasan:**
JSONB di PostgreSQL memberikan fleksibilitas untuk data dinamis tanpa meninggalkan kemampuan relasional dan query yang kuat. PostgreSQL dapat melakukan query ke dalam JSONB menggunakan operator khusus, sehingga data di dalam JSONB tetap bisa di-filter dan di-index.

**Konsekuensi:**
JSONB column tidak memiliki schema enforcement di level database — validasi structure JSONB harus dilakukan di level aplikasi. Data di dalam JSONB juga lebih sulit di-migrate jika structure perlu berubah.

**Dokumen terkait:** DB-01

---

### ADR-018 — UUID sebagai primary key di semua tabel

**Tanggal:** 2026-06-07 | **Kategori:** Teknis

**Konteks:**
Perlu memilih format primary key yang konsisten di semua tabel — antara auto-increment integer atau UUID.

**Keputusan:**
**UUID** sebagai primary key di semua tabel.

**Alternatif yang ditolak:**

*Auto-increment integer:* Lebih kecil ukurannya (4 atau 8 bytes vs 16 bytes) dan lebih cepat untuk operasi index. Namun, ID yang berurutan memungkinkan enumeration attack — user bisa mencoba ID 1, 2, 3 untuk mengakses resource yang bukan miliknya.

*ULID (Universally Unique Lexicographically Sortable Identifier):* Keunggulan UUID dengan kemampuan sort berdasarkan waktu pembuatan. Menarik, tetapi belum menjadi standar di PostgreSQL dan Supabase secara native.

**Alasan:**
UUID tidak bisa ditebak — mencegah enumeration attack di mana user mencoba-coba ID untuk mengakses resource orang lain. Konsisten dengan standar Supabase Auth yang juga menggunakan UUID. Aman untuk diekspos di URL tanpa risiko keamanan.

**Konsekuensi:**
UUID lebih besar ukurannya (16 bytes) dan index UUID sedikit lebih lambat dari integer. Untuk skala MVP, perbedaan ini tidak signifikan.

**Dokumen terkait:** DB-01

---

### ADR-019 — Soft delete di semua tabel

**Tanggal:** 2026-06-07 | **Kategori:** Teknis

**Konteks:**
Saat user "menghapus" data (misalnya menghapus vendor dari evaluasi), perlu memutuskan apakah data dihapus permanen dari database atau hanya ditandai sebagai dihapus.

**Keputusan:**
**Soft delete** di semua tabel — data ditandai dengan `deleted_at` timestamp, tidak dihapus secara fisik.

**Alternatif yang ditolak:**

*Hard delete:* Data dihapus permanen. Lebih sederhana dari perspektif database (tidak perlu filter `deleted_at` di setiap query), tetapi kehilangan data yang mungkin dibutuhkan untuk audit atau recovery tidak disengaja.

*Hybrid (soft delete hanya untuk tabel tertentu):* Membingungkan — tim perlu mengingat tabel mana yang hard delete dan mana yang soft delete. Konsistensi lebih penting dari optimasi parsial.

**Alasan:**
Data pengadaan memiliki nilai audit — keputusan vendor yang pernah dibuat perlu bisa ditelusuri meskipun user sudah "menghapus" evaluasi tersebut. Soft delete juga memberikan safety net untuk recovery jika penghapusan tidak disengaja.

**Konsekuensi:**
Setiap query harus menyertakan filter `WHERE deleted_at IS NULL` secara konsisten. Jika lupa, query akan mengembalikan data yang sudah dihapus. Cleanup permanen membutuhkan proses terjadwal terpisah (lihat DB-04).

**Dokumen terkait:** DB-01, DB-04

---

### ADR-020 — Supabase Realtime untuk progress agent

**Tanggal:** 2026-06-07 | **Kategori:** Teknis

**Konteks:**
Halaman processing (P-04) perlu menampilkan progress agent secara real-time. Ada beberapa mekanisme yang bisa digunakan: polling, WebSocket custom, SSE, atau Supabase Realtime.

**Keputusan:**
**Supabase Realtime** — FastAPI menulis progress ke tabel `agent_progress`, Supabase broadcast perubahan ke frontend secara otomatis.

**Alternatif yang ditolak:**

*Polling setiap 3 detik:* Sederhana, tetapi mengirim request meskipun tidak ada perubahan — membuang bandwidth dan menambah beban server.

*WebSocket custom di FastAPI:* Memberikan kontrol penuh, tetapi membutuhkan implementasi WebSocket server, connection management, dan reconnection logic dari scratch.

*SSE dari FastAPI untuk progress:* SSE cocok untuk streaming teks, tetapi untuk data structured yang berubah-ubah (status per agent), Supabase Realtime yang sudah terintegrasi dengan database lebih natural.

**Alasan:**
Supabase Realtime sudah terintegrasi dengan database. FastAPI hanya perlu menulis ke tabel — broadcast ke semua client yang subscribe terjadi otomatis. Tidak perlu membangun infrastruktur WebSocket terpisah.

**Konsekuensi:**
Ketergantungan tambahan pada infrastruktur Supabase Realtime. Jika Supabase Realtime mengalami masalah, frontend tidak mendapat update progress — meskipun evaluasi tetap berjalan di backend.

**Dokumen terkait:** BE-02, FE-05, DB-01

---

### ADR-021 — SSE untuk AI chat streaming

**Tanggal:** 2026-06-07 | **Kategori:** Teknis

**Konteks:**
AI chat panel perlu menampilkan respons LLM secara streaming — token demi token saat dihasilkan. Perlu memilih mekanisme komunikasi yang tepat untuk streaming satu arah dari server ke browser.

**Keputusan:**
**Server-Sent Events (SSE)** dari FastAPI langsung ke browser untuk AI chat streaming.

**Alternatif yang ditolak:**

*WebSocket:* Dirancang untuk komunikasi dua arah. Overkill untuk streaming yang sifatnya satu arah (server → browser). Lebih kompleks untuk diimplementasikan dan di-proxy.

*Polling:* Tidak cocok untuk streaming teks — polling menciptakan jeda yang terlihat, bukan pengalaman streaming yang mulus.

*HTTP chunked response:* Serupa dengan SSE tetapi tanpa protokol standar. SSE lebih baik didukung oleh browser dan lebih mudah di-debug.

**Alasan:**
SSE adalah standar industri untuk streaming respons LLM (digunakan oleh OpenAI, Anthropic, dan hampir semua provider LLM). Komunikasi satu arah, lebih ringan dari WebSocket, dan didukung native oleh semua browser modern.

**Konsekuensi:**
SSE adalah koneksi HTTP yang long-lived — perlu dikelola dengan baik di sisi browser (menutup koneksi saat tidak dibutuhkan) untuk menghindari resource leak.

**Dokumen terkait:** BE-02, FE-05

---

### ADR-022 — Tavily API untuk web search (free tier)

**Tanggal:** 2026-06-07 | **Kategori:** Teknis

**Konteks:**
Data Collector Agent membutuhkan kemampuan web search untuk mengumpulkan informasi publik tentang vendor. Perlu memilih provider yang tepat dengan mempertimbangkan biaya untuk MVP portofolio.

**Keputusan:**
**Tavily API** dengan free tier (1.000 request/bulan).

**Alternatif yang ditolak:**

*SerpAPI:* Populer, mendukung Google Search, tetapi tidak ada free tier yang memadai untuk development.

*Brave Search API:* Privacy-focused dan lebih murah dari SerpAPI, tetapi kurang mature untuk AI agent use case dibanding Tavily.

*Selenium + web scraping:* Gratis, tetapi rapuh (sering rusak saat struktur halaman berubah), lambat, dan berisiko melanggar ToS website yang di-scrape.

*Tidak ada web search (hanya data dari user):* Mengurangi nilai Data Collector Agent secara signifikan — salah satu keunggulan sistem adalah kemampuan mengumpulkan data secara otomatis.

**Alasan:**
Tavily dirancang khusus untuk AI agent — output sudah terstruktur (judul, URL, snippet) tanpa perlu parsing HTML. Free tier 1.000 request/bulan cukup untuk development intensif dan demonstrasi portofolio.

**Konsekuensi:**
Free tier akan habis jika sistem digunakan untuk lebih dari ~25 evaluasi per bulan (dengan 10 vendor dan 4 query per vendor). Saat demo atau testing intensif, perlu monitoring penggunaan.

**Dokumen terkait:** BE-07

---

### ADR-023 — Integrasi ERP ditunda pasca-MVP

**Tanggal:** 2026-06-07 | **Kategori:** Produk

**Konteks:**
Sistem pengadaan yang mature idealnya terintegrasi dengan ERP/SAP perusahaan untuk mengambil data historis vendor (riwayat transaksi, rating evaluasi sebelumnya, complaint record). Namun ini menambah kompleksitas yang signifikan.

**Keputusan:**
**Integrasi ERP tidak ada di MVP** — semua data vendor diinput manual atau melalui upload dokumen.

**Alternatif yang ditolak:**

*Integrasi ERP di MVP:* Membutuhkan akses ke sistem ERP yang tidak tersedia untuk development portofolio. Selain itu, setiap perusahaan menggunakan ERP yang berbeda (SAP, Oracle, custom) sehingga integrasi harus generik atau dikonfigurasi per klien.

*Mock ERP data yang realistis:* Membuat data historis yang di-hardcode untuk demo. Ditolak karena misleading — menampilkan seolah-olah ada integrasi padahal tidak.

**Alasan:**
Nilai inti sistem — kemampuan AI menganalisa dan meranking vendor — dapat didemonstrasikan sepenuhnya tanpa integrasi ERP. Menunda integrasi ini menghemat effort yang signifikan untuk MVP tanpa mengurangi demonstrasi nilai utama.

**Konsekuensi:**
Sistem tidak bisa memanfaatkan data historis internal perusahaan — salah satu sumber sinyal paling valuable untuk evaluasi vendor. Ini adalah trade-off yang disadari dan terdokumentasi sebagai roadmap pasca-MVP.

**Dokumen terkait:** BE-07 section 10

---

### ADR-024 — Verifikasi legalitas via web search, bukan API resmi

**Tanggal:** 2026-06-07 | **Kategori:** Produk

**Konteks:**
Risk Assessor Agent perlu menilai aspek legalitas vendor. Idealnya menggunakan API resmi pemerintah (OSS, AHU Online) untuk verifikasi yang akurat. Namun akses ke API ini membutuhkan proses registrasi dan persetujuan yang panjang.

**Keputusan:**
Risk Assessor menggunakan **informasi dari web search** (via Tavily) untuk menilai risiko legalitas — bukan query ke API database pemerintah resmi.

**Alternatif yang ditolak:**

*Integrasi OSS API:* Verifikasi NIB dan izin usaha yang akurat. Ditolak karena proses registrasi panjang dan tidak feasible untuk MVP portofolio.

*Tidak menilai aspek legalitas:* Menghilangkan salah satu dimensi evaluasi yang penting. Ditolak karena risiko legalitas adalah pertimbangan nyata dalam pengadaan.

**Alasan:**
Web search memberikan indikasi risiko legalitas yang berguna (misalnya menemukan berita masalah hukum atau tidak adanya informasi publik sama sekali) meskipun bukan verifikasi resmi. Sistem secara eksplisit menyatakan keterbatasan ini dalam output Risk Assessor.

**Konsekuensi:**
Penilaian risiko legalitas bersifat indikatif, bukan definitif. Sistem harus selalu menyertakan disclaimer bahwa verifikasi resmi tetap diperlukan sebelum kontrak ditandatangani — ini sudah terdefinisi dalam prompt Risk Assessor (BE-04).

**Dokumen terkait:** BE-04, BE-07

---

### ADR-025 — Prompt disimpan sebagai file, bukan hardcoded

**Tanggal:** 2026-06-07 | **Kategori:** Teknis

**Konteks:**
Prompt untuk agent AI perlu dikelola dengan cara yang memungkinkan perubahan tanpa deployment kode, dapat di-review, dan memiliki version history yang jelas.

**Keputusan:**
Semua prompt disimpan sebagai **file `.md` dalam folder `prompts/`** di repository `vendor-ai-agent` — tidak ditulis sebagai string literal di dalam kode Python.

**Alternatif yang ditolak:**

*Hardcoded sebagai string di Python:* Paling mudah dari sisi implementasi. Ditolak karena perubahan prompt membutuhkan deployment kode, tidak bisa di-review secara terpisah dari kode, dan tidak ramah untuk non-engineer yang mungkin perlu mengoptimasi prompt.

*Database untuk menyimpan prompt:* Memungkinkan perubahan prompt tanpa deployment. Ditolak karena menambah kompleksitas (UI untuk edit prompt, versioning di database) yang tidak sebanding untuk MVP.

*External prompt management service (PromptLayer, LangSmith):* Tools khusus untuk pengelolaan prompt. Ditolak karena menambah dependency eksternal dan biaya untuk MVP.

**Alasan:**
File di Git memberikan semua yang dibutuhkan: version history, diff antar versi, code review melalui PR, dan kemampuan rollback. Tidak membutuhkan infrastruktur tambahan.

**Konsekuensi:**
Perubahan prompt tetap membutuhkan deployment (meskipun lebih sederhana dari deployment kode). Tidak ada hot-reload prompt tanpa restart service.

**Dokumen terkait:** BE-04

---

### ADR-026 — Vitest + Playwright sebagai testing stack

**Tanggal:** 2026-06-07 | **Kategori:** Teknis

**Konteks:**
Perlu memilih tooling testing untuk frontend yang mencakup unit test, integration test, dan E2E test.

**Keputusan:**
**Vitest** untuk unit dan integration test, **Playwright** untuk E2E test.

**Alternatif yang ditolak:**

*Jest + Cypress:* Kombinasi yang populer. Ditolak karena Vitest lebih cepat dari Jest untuk project Next.js (menggunakan Vite transformer yang sama), dan Playwright lebih reliable dari Cypress untuk multi-browser testing.

*Jest + Playwright:* Feasible, tetapi Vitest memberikan startup time yang lebih cepat dan watch mode yang lebih responsif untuk development experience yang lebih baik.

*Testing Library saja (tanpa E2E):* Tidak cukup untuk memvalidasi critical path end-to-end yang melibatkan navigasi multi-halaman.

**Alasan:**
Vitest dan Playwright adalah tools yang sedang menjadi standar baru di ekosistem frontend modern. Keduanya aktif dikembangkan dan memiliki komunitas yang berkembang pesat.

**Konsekuensi:**
Vitest memerlukan konfigurasi tambahan untuk Next.js App Router (khususnya untuk Server Components testing). Playwright E2E membutuhkan environment CI yang bisa menjalankan browser — perlu dikonfigurasi di GitHub Actions.

**Dokumen terkait:** FE-06

---

### ADR-027 — Supabase Pro tier minimum untuk production

**Tanggal:** 2026-06-07 | **Kategori:** Teknis

**Konteks:**
Supabase memiliki beberapa tier: Free, Pro, dan Team. Setiap tier memiliki perbedaan kapabilitas yang signifikan, terutama untuk backup dan recovery.

**Keputusan:**
**Supabase Pro tier** adalah minimum untuk deployment production.

**Alternatif yang ditolak:**

*Free tier untuk production:* Tidak menyediakan Point-in-time Recovery (PITR) — hanya backup harian. Untuk sistem pengadaan yang datanya sensitif, PITR adalah persyaratan minimal. Free tier juga memiliki batasan koneksi database yang rendah.

*Team tier dari awal:* Menyediakan lebih banyak fitur (SOC 2, dedicated support), tetapi biayanya jauh lebih tinggi dan belum diperlukan untuk MVP.

**Alasan:**
PITR memungkinkan recovery ke titik waktu tertentu — kritis jika data corruption baru terdeteksi beberapa jam setelah kejadian. Tanpa PITR, kehilangan data bisa mencapai 24 jam (satu siklus backup harian penuh).

**Konsekuensi:**
Biaya Supabase Pro (~$25/bulan) perlu diperhitungkan dalam total biaya operasional. Untuk development dan demo portofolio, Free tier tetap digunakan — Pro tier hanya saat deploy ke production yang nyata.

**Dokumen terkait:** DB-04

---

### ADR-028 — ~~OpenAI text-embedding-3-small sebagai embedding model untuk RAG~~ *(Superseded oleh ADR-034)*

**Tanggal:** 2026-06-11 | **Kategori:** Teknis | **Status:** Superseded — lihat ADR-034

**Catatan:** Keputusan ini digantikan oleh ADR-034 pada 2026-06-13. Entri ini dipertahankan untuk keperluan audit trail.

**Konteks:**
Sistem RAG membutuhkan model embedding untuk mengubah teks dokumen penawaran dan query user menjadi vektor numerik. Beberapa penyedia menawarkan embedding model dengan karakteristik berbeda.

**Keputusan:**
Menggunakan **OpenAI `text-embedding-3-small`** — menghasilkan vektor 1.536 dimensi dengan biaya ~$0.02 per 1 juta token.

**Alternatif yang ditolak:**

*OpenAI `text-embedding-3-large`:* Kualitas lebih tinggi (dimensi 3.072) tetapi biaya ~6.5x lebih mahal. Untuk dokumen pengadaan yang domainnya spesifik, `text-embedding-3-small` sudah lebih dari cukup.

*Voyage AI `voyage-3-lite`:* Penyedia yang direkomendasikan Anthropic, performa kompetitif, biaya serupa. Ditolak karena OpenAI memiliki SDK yang lebih mature dan dokumentasi lebih lengkap — mengurangi waktu integrasi untuk MVP.

*Cohere `embed-v3`:* Performa kompetitif, ada free tier. Ditolak karena menambahkan satu provider lagi tanpa keunggulan signifikan dibanding OpenAI untuk use case ini.

*Self-hosted model (sentence-transformers):* Gratis setelah setup, tidak ada biaya per call. Ditolak karena memerlukan infrastruktur tambahan untuk hosting model yang tidak sesuai dengan prinsip minimal infrastruktur baru di MVP.

**Alasan memilih OpenAI:**
Keseimbangan terbaik antara kualitas, biaya, dan kemudahan integrasi. Biaya embedding sangat kecil (< 1% dari total biaya LLM per evaluasi) sehingga perbedaan harga antar penyedia tidak signifikan.

**Konsekuensi:**
Sistem kini bergantung pada dua provider AI: Anthropic untuk LLM dan OpenAI untuk embedding. Dua API key harus dikelola secara terpisah. Jika OpenAI mengalami downtime, RAG indexing tidak bisa berjalan — namun sistem tetap fungsional tanpa RAG (evaluasi tetap berjalan, chat menggunakan data terstruktur saja).

**Dokumen terkait:** BE-07, BE-08, SH-04

---

### ADR-029 — pgvector di Supabase sebagai vector store untuk RAG

**Tanggal:** 2026-06-11 | **Kategori:** Teknis

**Konteks:**
RAG membutuhkan vector store untuk menyimpan embedding chunk dokumen dan menjalankan similarity search saat retrieval. Ada pilihan antara dedicated vector database dan ekstensi PostgreSQL.

**Keputusan:**
Menggunakan **pgvector** — ekstensi PostgreSQL yang terintegrasi langsung di Supabase yang sudah digunakan sistem ini.

**Alternatif yang ditolak:**

*Qdrant (dedicated vector DB):* Performa lebih tinggi untuk skala besar, fitur filtering canggih. Ditolak karena memerlukan service baru yang harus di-deploy, di-monitor, dan dibayar terpisah — bertentangan dengan prinsip minimal infrastruktur baru.

*Pinecone:* Managed service, mudah di-setup. Ditolak karena biaya tambahan dan satu lagi vendor dependency tanpa keunggulan signifikan untuk skala MVP.

*Weaviate:* Open-source, bisa self-hosted. Sama seperti Qdrant — overhead infrastruktur tidak sebanding untuk skala MVP.

**Alasan memilih pgvector:**
Nol infrastruktur baru. Vector store hidup di Supabase yang sudah ada — tidak ada service tambahan, tidak ada biaya tambahan, tidak ada konfigurasi tambahan. RLS Supabase yang sudah dikonfigurasi untuk tabel lain langsung berlaku untuk tabel `dokumen_chunk`, memastikan isolasi data per evaluasi secara otomatis. Untuk skala MVP (maksimum 10 vendor × 50 halaman), pgvector lebih dari cukup secara performa.

**Konsekuensi:**
Di skala sangat besar (ribuan evaluasi dengan ratusan vendor), pgvector bisa menjadi bottleneck dibanding dedicated vector DB. Migrasi ke Qdrant atau Pinecone di masa depan memerlukan export data vector yang sudah tersimpan — feasible tetapi butuh upaya. Ini adalah trade-off yang diterima untuk MVP.

**Dokumen terkait:** BE-07, BE-08, DB-01, DB-02

---

### ADR-030 — Form preferensi opsional sebagai input Preference Matcher Agent

**Tanggal:** 2026-06-11 | **Kategori:** Produk

**Konteks:**
Scoring TOPSIS bersifat objektif dan netral. Namun perusahaan sering memiliki konteks bisnis (preferensi vendor lokal, urgensi timeline, komitmen strategis) yang tidak bisa direpresentasikan dalam bobot kriteria standar. Perlu mekanisme untuk mengekspresikan konteks ini tanpa merusak objektivitas TOPSIS.

**Keputusan:**
Menambahkan **textarea opsional** di P-03 Langkah 1 untuk menginput preferensi bisnis perusahaan dalam teks bebas (maks 1.000 karakter). Input ini menjadi trigger dan input untuk Preference Matcher Agent (BE-10) yang menghasilkan lapisan rekomendasi tambahan di atas TOPSIS.

**Alternatif yang ditolak:**

*Form terstruktur (dropdown, checkbox) untuk preferensi:* Lebih mudah diproses secara programatik, tetapi preferensi bisnis terlalu bervariasi untuk distandarisasi. Form kaku akan memaksa user mereduksi konteks yang nuanced menjadi pilihan yang tidak representatif.

*Memodifikasi bobot kriteria TOPSIS berdasarkan preferensi:* Cara yang lebih "bersih" secara teknis. Ditolak karena mengubah objektivitas kalkulasi — tidak bisa lagi dibedakan antara hasil murni TOPSIS dan hasil yang sudah dipengaruhi preferensi.

*Preferensi sebagai konfigurasi global per perusahaan:* Ditolak karena preferensi bersifat kontekstual — berbeda untuk setiap pengadaan. Konfigurasi global akan mengaplikasikan preferensi yang tidak relevan ke evaluasi yang berbeda.

*Tidak ada mekanisme preferensi sama sekali:* Ditolak karena mengurangi nilai sistem di konteks nyata. Procurement staff di perusahaan selalu memiliki pertimbangan strategis yang melampaui metrik standar.

**Alasan memilih textarea opsional:**
Teks bebas memungkinkan ekspresi konteks yang natural dan nuanced — LLM lebih baik menginterpretasikan teks natural dibanding mengisi kotak-kotak kaku. Opsionalitas memastikan sistem tetap sepenuhnya fungsional tanpa preferensi (mode netral), sehingga tidak ada user yang merasa terpaksa mengisi field yang tidak relevan untuk pengadaan tertentu.

**Konsekuensi:**
Kualitas rekomendasi berbasis preferensi bergantung pada kualitas input user — preferensi yang terlalu umum atau ambigu menghasilkan rekomendasi yang kurang tajam. Sistem perlu memberikan guidance yang baik (placeholder, contoh) untuk memandu user menulis preferensi yang actionable. Preference Matcher Agent harus transparan tentang konflik antara preferensi dan ranking TOPSIS.

**Dokumen terkait:** BE-10, FE-03, FE-02, DB-01

---

### ADR-031 — 2-repo: monorepo TypeScript + repo terpisah FastAPI

**Tanggal:** 2026-06-12 | **Kategori:** Teknis | **Menggantikan:** ADR-012

**Konteks:**
ADR-012 menetapkan polyrepo dengan tiga repository terpisah: `vendor-ai-frontend`, `vendor-ai-backend`, dan `vendor-ai-agent`. Setelah tim memulai perencanaan aktif, dua friction point muncul: koordinasi fitur lintas repo membutuhkan mekanisme FEATURE_STATUS.md manual di tiga tempat, dan tidak ada type sharing antar frontend dan backend Next.js — membuat kontrak API BE-02 rentan drift tanpa enforcement tooling.

**Keputusan:**
Mengadopsi struktur **2-repo**:
- `vendor-ai` — monorepo TypeScript yang menggabungkan Next.js frontend dan Next.js API Routes (BFF) dalam satu repository menggunakan pnpm workspaces. Berisi dua package: `apps/web` (frontend) dan `apps/api` (API Routes), dengan `packages/types` sebagai shared type definitions.
- `vendor-ai-agent` — repository terpisah untuk FastAPI (Python), tidak berubah dari ADR-012.

**Alternatif yang ditolak:**

*Tetap polyrepo (3 repo):* Mempertahankan ADR-012. Ditolak karena friction koordinasi fitur dan tidak adanya type enforcement antar FE dan BFF terbukti menjadi bottleneck nyata saat tim mulai merencanakan workflow development.

*Full monorepo (termasuk FastAPI):* Satu repository untuk semua service. Ditolak karena pnpm workspaces dan Turborepo hanya mendukung ekosistem JavaScript/TypeScript. FastAPI (Python) tidak bisa dikelola dalam workspace yang sama — memaksakan ini akan menghasilkan setup yang tidak natural dan sulit di-maintain.

*Dua repo tanpa workspace (Next.js monolith):* Menggabungkan frontend dan API Routes dalam satu Next.js project tanpa pembagian workspace. Opsi yang valid dan lebih sederhana, tetapi workspace memungkinkan pemisahan tanggung jawab yang lebih jelas dan memudahkan penambahan package bersama di masa depan.

**Alasan:**
Dengan menggabungkan `vendor-ai-frontend` dan `vendor-ai-backend` menjadi satu monorepo TypeScript, dua masalah utama ADR-012 teratasi sekaligus: koordinasi fitur FE+BE cukup dalam satu PR di satu repository, dan tipe data dapat di-share melalui `packages/types` sehingga perubahan response shape terdeteksi saat compile-time. Batas dengan FastAPI tetap terjaga secara alami karena perbedaan bahasa memang tidak memungkinkan code sharing yang bermakna.

**Konsekuensi:**
Frontend Engineer dan Backend Engineer (Next.js) kini bekerja di repository yang sama — perlu `CODEOWNERS` dan branch protection yang dikonfigurasi dengan baik untuk mencegah konflik. Database Engineer tidak memiliki repository Git tersendiri; migrasi database dikelola via Supabase CLI dengan file migration disimpan di `supabase/migrations/` dalam repo `vendor-ai`. Struktur branch develop berubah: dari `fe/develop` dan `be/develop` di repo terpisah menjadi dua branch yang sama dalam satu repo `vendor-ai` — logika koordinasi keduanya tetap sama.

**Nama repository yang berlaku:**

| Repository | Isi | Bahasa |
|---|---|---|
| `vendor-ai` | `apps/web` (Next.js frontend) + `apps/api` (Next.js API Routes) + `packages/types` | TypeScript |
| `vendor-ai-agent` | FastAPI service (AI, scoring, RAG) | Python |

**Dokumen terkait:** FE-01, SH-02, BE-01

---

### ADR-032 — ~~Empat role developer: Frontend, Backend, Database, dan AI Engineer~~ *(Superseded oleh ADR-036)*

**Tanggal:** 2026-06-12 | **Kategori:** Tim | **Status:** Superseded — lihat ADR-036

**Catatan:** Keputusan ini digantikan oleh ADR-036 pada 2026-06-13. Entri ini dipertahankan untuk keperluan audit trail.

**Konteks:**
Sejak awal, project ini dirancang dengan tiga role developer: Frontend Engineer, Backend Engineer, dan Database Engineer. Backend Engineer mencakup dua tanggung jawab sekaligus: Next.js API Routes (TypeScript, BFF layer) di repo `vendor-ai`, dan FastAPI service (Python, AI agent orchestration, scoring engine, RAG pipeline) di repo `vendor-ai-agent`. Dalam praktiknya, kedua tanggung jawab ini membutuhkan keahlian yang sangat berbeda — stack berbeda (TypeScript vs Python), pola pikir berbeda (REST API vs LLM/agent orchestration), dan deployment target berbeda (Vercel vs Railway/Fly.io). Dokumen panduan `GUIDE_BACKEND_ENGINEER.md` menjadi terlalu luas dan membingungkan karena menggabungkan dua persona yang tidak natural untuk dipegang satu orang.

**Keputusan:**
Mengadopsi **empat role developer**:
- **Frontend Engineer** — `apps/web` di repo `vendor-ai` (Next.js frontend, React, shadcn/ui)
- **Backend Engineer** — `apps/api` di repo `vendor-ai` (Next.js API Routes, BFF layer, TypeScript)
- **Database Engineer** — `supabase/migrations/` di repo `vendor-ai` (PostgreSQL, RLS, migration)
- **AI Engineer** — repo `vendor-ai-agent` sepenuhnya (FastAPI, LangGraph, TOPSIS, RAG, LLM prompt)

**Alternatif yang ditolak:**

*Tetap tiga role, Backend Engineer merangkap keduanya:* Dipertahankan dari rancangan awal. Ditolak karena menggabungkan dua stack yang tidak berkaitan (TypeScript BFF dan Python AI service) menciptakan beban kognitif yang tidak perlu dan menyulitkan onboarding engineer yang memiliki spesialisasi di salah satunya.

*Dua role (Full-stack + Database):* Menyederhanakan lebih jauh dengan menggabungkan FE dan BE. Ditolak karena frontend (React/shadcn/UI-first) dan backend BFF (API contract, auth, validasi) memiliki spesialisasi yang cukup besar untuk dipisahkan, terutama mengingat kompleksitas komponen UI yang sudah terdefinisi di FE-02.

*Lima role (pisahkan Scoring Engine dari AI Agent):* Memisahkan TOPSIS engine dari LangGraph orchestration. Ditolak karena scoring engine dan agent berada dalam satu repo Python yang sama dan saling bergantung erat — pemisahan ini akan menciptakan koordinasi overhead tanpa manfaat nyata di skala MVP.

**Alasan:**
Struktur 2-repo (ADR-031) sudah mencerminkan pemisahan alami antara TypeScript dan Python. Pemecahan Backend Engineer menjadi Backend Engineer (Next.js) dan AI Engineer (Python) mengikuti batas repo tersebut secara organik — setiap role kini memiliki satu repo atau satu workspace yang jelas sebagai territory kerjanya. Ini menghilangkan ambiguitas kepemilikan dokumen dan memudahkan onboarding karena panduan masing-masing role kini terfokus pada satu stack.

**Konsekuensi:**
Dokumen `GUIDE_BACKEND_ENGINEER.md` dipecah menjadi dua: konten FastAPI dipindah ke `GUIDE_AI_ENGINEER.md` baru, `GUIDE_BACKEND_ENGINEER.md` yang tersisa hanya mencakup Next.js API Routes. `MILESTONE_PLAN.md` dan `REPOSITORY_STRUCTURE.md` diperbarui untuk mencerminkan empat role. Dokumen spesifikasi `BE-03` hingga `BE-10` (kecuali `BE-06`) menjadi referensi utama AI Engineer; `BE-02` dan `BE-06` menjadi referensi utama Backend Engineer — prefix `BE-` dipertahankan karena perubahan kode dokumen akan memecah semua cross-reference yang sudah ada.

**Batas tanggung jawab yang jelas:**

| Role | Repository / Folder | Stack |
|---|---|---|
| Frontend Engineer | `vendor-ai/apps/web/` | TypeScript, Next.js, React, shadcn/ui |
| Backend Engineer | `vendor-ai/apps/api/` + `packages/types/` | TypeScript, Next.js API Routes |
| Database Engineer | `vendor-ai/supabase/migrations/` | SQL, Supabase CLI, PostgreSQL |
| AI Engineer | `vendor-ai-agent/` (seluruh repo) | Python, FastAPI, LangGraph, Claude API |

**Dokumen terkait:** GUIDE_AI_ENGINEER (baru), GUIDE_BACKEND_ENGINEER, MILESTONE_PLAN, REPOSITORY_STRUCTURE, SH-02, BE-01

---

### ADR-033 — DeepSeek-V4-Flash via OpenRouter sebagai LLM utama

**Tanggal:** 2026-06-13 | **Kategori:** Teknis | **Menggantikan:** ADR-015

**Konteks:**
ADR-015 menetapkan Claude Sonnet (via Anthropic API) sebagai LLM utama. Selama perencanaan implementasi, biaya API Anthropic diidentifikasi sebagai komponen biaya dominan — Claude Sonnet dikenakan ~$3/1M token input dan ~$15/1M token output. DeepSeek-V4-Flash tersedia via OpenRouter dengan biaya yang jauh lebih rendah, sementara kemampuan instruction-following dan structured JSON output-nya sudah terbukti kompetitif untuk use case agent pipeline.

**Keputusan:**
**DeepSeek-V4-Flash** diakses via **OpenRouter API** sebagai LLM utama untuk semua agent evaluasi dan AI chat panel. OpenRouter digunakan sebagai aggregator karena kompatibel dengan OpenAI SDK, menyederhanakan integrasi tanpa perlu ganti SDK.

**Alternatif yang ditolak:**

*Tetap Claude Sonnet (Anthropic API):* Kualitas output terbaik untuk instruction-following dan structured JSON. Ditolak karena biaya per evaluasi secara signifikan lebih tinggi — tidak optimal untuk proyek portofolio yang membutuhkan banyak iterasi testing.

*DeepSeek via API langsung (tanpa OpenRouter):* Menghindari lapisan relay OpenRouter. Ditolak karena OpenRouter memberikan fleksibilitas untuk berganti model tanpa mengubah kode — jika DeepSeek-V4-Flash tidak memuaskan saat testing, migrasi ke model lain cukup mengubah satu string konfigurasi.

*GPT-4o-mini via OpenRouter:* Alternatif murah dari OpenAI. Ditolak karena DeepSeek-V4-Flash menawarkan performa yang lebih kompetitif di harga yang lebih rendah berdasarkan benchmark reasoning dan instruction-following yang tersedia publik.

*Llama 3.3 70B via OpenRouter:* Open-source, tersedia di OpenRouter. Ditolak karena kualitas structured JSON output untuk pipeline agent masih di bawah model proprietary pada ukuran yang sama.

**Alasan:**
OpenRouter memungkinkan akses ke DeepSeek-V4-Flash menggunakan antarmuka kompatibel OpenAI — tidak ada perubahan arsitektur, hanya perubahan `base_url` dan model string. Biaya yang jauh lebih rendah memungkinkan testing dan iterasi yang lebih intensif tanpa kekhawatiran biaya API. Risiko utama — konsistensi structured JSON output — akan divalidasi saat testing awal implementasi agent.

**Konsekuensi:**
Sistem kini menggunakan OpenAI SDK (dengan `base_url` override ke OpenRouter) menggantikan Anthropic SDK — perubahan dependency di `vendor-ai-agent`. Semua referensi `ANTHROPIC_API_KEY` diganti ke `OPENROUTER_API_KEY`. Kualitas output JSON perlu divalidasi lebih teliti saat testing karena DeepSeek belum sehati-hati Claude dalam mengikuti format instruksi kompleks. Jika validasi gagal di beberapa agent, ada opsi untuk menggunakan model berbeda per agent via OpenRouter tanpa mengubah arsitektur.

**Dokumen terkait:** AI-01, AI-02, BE-07, SH-04

---

### ADR-034 — Google Gemini text-embedding-004 sebagai embedding model untuk RAG

**Tanggal:** 2026-06-13 | **Kategori:** Teknis | **Menggantikan:** ADR-028

**Konteks:**
ADR-028 menetapkan OpenAI `text-embedding-3-small` (dimensi 1.536) sebagai embedding model untuk RAG. Dengan beralihnya LLM ke OpenRouter (ADR-033), ketergantungan pada OpenAI API terpisah untuk embedding dievaluasi ulang. Google Gemini menyediakan `text-embedding-004` — model embedding yang stabil, berkualitas tinggi, dengan dimensi 768 (default), dan biaya yang kompetitif.

**Keputusan:**
**Google Gemini `text-embedding-004`** sebagai embedding model untuk RAG pipeline, menggantikan OpenAI `text-embedding-3-small`. Model menghasilkan vektor **768 dimensi**. Diakses via Google AI SDK (atau REST API) menggunakan `GOOGLE_API_KEY`.

**Alternatif yang ditolak:**

*Tetap OpenAI text-embedding-3-small (dimensi 1.536):* Kualitas baik dan sudah terbukti. Ditolak karena mempertahankan OpenAI sebagai dependency terpisah sementara LLM sudah dipindah ke OpenRouter — menambah satu API key lagi tanpa manfaat eksklusif.

*Google Gemini gemini-embedding-exp-03-07 (dimensi 3.072):* Eksperimental, dimensi lebih besar. Ditolak karena status eksperimental tidak cocok untuk production MVP — risiko breaking change lebih tinggi. Dimensi 3.072 juga meningkatkan storage dan compute biaya vector similarity search tanpa manfaat yang proporsional untuk skala MVP.

*Voyage AI voyage-3-lite:* Penyedia embedding yang direkomendasikan Anthropic, performa kompetitif. Ditolak karena menambah satu provider lagi — Google sudah terlibat di stack ini (Gemini). Konsolidasi provider lebih diutamakan.

*Self-hosted sentence-transformers:* Gratis setelah setup. Ditolak dengan alasan yang sama seperti ADR-028 — overhead infrastruktur tidak sebanding untuk MVP.

**Alasan:**
`text-embedding-004` adalah model embedding Google yang paling stabil dan terdokumentasi dengan baik per pertengahan 2026. Dimensi 768 lebih efisien dari 1.536 (OpenAI) untuk storage vector dan kecepatan similarity search, tanpa penurunan kualitas retrieval yang signifikan untuk dokumen pengadaan berbahasa Indonesia dan Inggris. Konsolidasi ke Google sebagai provider embedding mengurangi jumlah API key yang harus dikelola.

**Konsekuensi:**
**Breaking change pada skema database:** Kolom `embedding` di tabel `dokumen_chunk` berubah dari `vector(1536)` menjadi `vector(768)`. Migration baru diperlukan — index HNSW yang ada harus di-drop dan dibuat ulang. Karena project belum memasuki fase implementasi, tidak ada data yang perlu di-migrate. Referensi `OPENAI_API_KEY` untuk embedding diganti ke `GOOGLE_API_KEY`. Sistem kini hanya bergantung pada dua provider: OpenRouter (LLM) dan Google (embedding) — lebih sederhana dari sebelumnya (Anthropic + OpenAI).

**Dokumen terkait:** BE-07, AI-04, DB-01, SH-04

---

### ADR-035 — Namespace AI terpisah untuk dokumen spesifikasi AI Engineer

**Tanggal:** 2026-06-13 | **Kategori:** Dokumentasi

**Konteks:**
Sejak ADR-032, dokumen spesifikasi yang dikerjakan AI Engineer (BE-03, BE-04, BE-05, BE-08, BE-09, BE-10) tetap menggunakan prefix `BE-` meski secara konten dan tanggung jawab mereka sepenuhnya milik AI Engineer di repo `vendor-ai-agent`. Keputusan saat itu mempertahankan prefix `BE-` untuk menghindari memecah cross-reference yang sudah ada. Namun menjelang fase implementasi, kebingungan muncul: engineer yang membuka folder `docs/` melihat deretan file `BE-` yang sebagian adalah tanggung jawab Backend Engineer (Next.js) dan sebagian lagi adalah tanggung jawab AI Engineer (FastAPI). Pemisahan namespace ini diperlukan agar setiap engineer langsung tahu dokumen mana yang relevan untuk pekerjaannya.

**Keputusan:**
Membuat **namespace `AI-`** khusus untuk dokumen spesifikasi yang menjadi tanggung jawab AI Engineer. Enam dokumen dipindah dari namespace `BE-` ke namespace `AI-` dengan penomoran ulang:

| Kode lama | Kode baru | Judul |
|---|---|---|
| BE-03 | AI-01 | Agent Orchestration |
| BE-04 | AI-02 | Prompt Library |
| BE-05 | AI-03 | Scoring Engine |
| BE-08 | AI-04 | RAG Specification |
| BE-09 | AI-05 | Qualitative Analyzer Agent |
| BE-10 | AI-06 | Preference Matcher Agent |

Namespace `BE-` yang tersisa hanya mencakup dokumen yang dikerjakan Backend Engineer (Next.js API Routes): BE-01 (Architecture, referensi bersama), BE-02 (API Contract), BE-06 (Auth & Security), BE-07 (Integration Spec).

**Alternatif yang ditolak:**

*Tetap prefix BE- dengan subdirektori:* Memindahkan file AI ke subfolder `docs/ai/`. Ditolak karena cara engineer menelusuri dokumen lebih sering via nama file daripada folder — prefix lebih efektif sebagai penanda cepat.

*Prefix berbeda (seperti AG- untuk Agent atau PY- untuk Python):* Ditolak karena `AI-` paling deskriptif dan langsung mencerminkan domain tanggung jawab, tanpa membutuhkan hafalan konvensi tambahan.

**Alasan:**
Namespace yang berbeda memberikan sinyal visual yang langsung dan tidak ambigu. Saat engineer membuka daftar dokumen, `AI-01` sampai `AI-06` jelas adalah domain AI Engineer, sementara `BE-01` sampai `BE-07` adalah domain Backend Engineer. Ini mengurangi cognitive overhead di awal setiap sesi kerja.

**Konsekuensi:**
Semua cross-reference ke BE-03, BE-04, BE-05, BE-08, BE-09, BE-10 di seluruh dokumen spesifikasi harus diperbarui ke kode baru. Ini menyentuh: BE-01, BE-02, BE-06, BE-07, DB-01, DB-02, DB-03, FE-04, FE-05, SH-03, SH-04, GUIDE_AI_ENGINEER, MILESTONE_PLAN, REPOSITORY_STRUCTURE. File lama dengan nama BE-03 s/d BE-10 dihapus dan diganti file baru dengan nama AI-01 s/d AI-06.

**Dokumen terkait:** BE-01, GUIDE_AI_ENGINEER, REPOSITORY_STRUCTURE

---

### ADR-036 — Dua track pengerjaan: Fullstack Engineer + AI Engineer (solo developer)

**Tanggal:** 2026-06-13 | **Kategori:** Tim | **Menggantikan:** ADR-032

**Konteks:**
ADR-032 mendefinisikan empat role developer: Frontend Engineer, Backend Engineer, Database Engineer, dan AI Engineer. Dalam kenyataannya, project ini dikerjakan oleh satu orang. Struktur empat role menciptakan dua friction point nyata: (1) milestone plan ditulis untuk paralel empat orang — tidak jelas mana yang dikerjakan duluan saat solo, dan (2) branching strategy dengan `fe/develop` dan `be/develop` sebagai branch terpisah adalah overhead tanpa manfaat untuk satu developer. Di sisi lain, AI Engineer memang bekerja di repo yang benar-benar berbeda (`vendor-ai-agent`), sehingga pemisahannya tetap relevan dan tidak perlu diubah.

**Keputusan:**
Mengadopsi **dua track pengerjaan**:
- **Track AI Engineer** — mengerjakan repo `vendor-ai-agent` secara eksklusif, dengan alur kerja dan branching yang tidak berubah dari sebelumnya.
- **Track Fullstack** — mengerjakan repo `vendor-ai` secara menyeluruh: database (migrations), backend (API Routes), dan frontend (React). Ketiga lapisan ini tetap dibedakan dengan tag `[DB]`, `[BE]`, `[FE]` di milestone dan checklist — bukan sebagai role terpisah, melainkan sebagai penanda lapisan teknis agar developer tahu sedang mengerjakan bagian mana.

Milestone plan ditulis ulang dari perspektif solo developer dengan urutan sequential per lapisan di dalam setiap fitur: DB → BE → FE.

**Alternatif yang ditolak:**

*Tetap empat role, abaikan bahwa ini solo:* Mempertahankan ADR-032 apa adanya. Ditolak karena milestone yang ditulis untuk paralel empat orang aktif menyebabkan kebingungan saat mengeksekusi sendirian — tidak jelas mana yang harus dimulai.

*Satu role tunggal tanpa pembedaan lapisan:* Menghilangkan semua tag `[DB]`, `[BE]`, `[FE]` dan menulis milestone sebagai satu aliran tanpa penanda lapisan. Ditolak karena penanda lapisan membantu developer mengetahui konteks teknis yang sedang dikerjakan — pola pikir yang berbeda diperlukan saat menulis migration SQL vs implementasi API vs membangun komponen React.

*Dua repo, dua role terpisah sepenuhnya:* Memisahkan jadwal AI Engineer dan Fullstack sepenuhnya. Tidak memungkinkan secara praktis karena ada fitur yang membutuhkan koordinasi keduanya (F-07, F-10, F-14).

**Alasan:**
Dua track mencerminkan realita struktural yang sudah ada: dua repo yang berbeda bahasa dan concern. Yang berubah hanya cara memandang repo `vendor-ai` — dari tiga role terpisah menjadi satu track Fullstack dengan pembedaan lapisan. Ini menyederhanakan branching, memperjelas urutan eksekusi solo, dan menghilangkan kebingungan "siapa yang mulai duluan" tanpa menghilangkan kejelasan "sedang mengerjakan lapisan apa."

**Konsekuensi:**
Branching strategy di `vendor-ai` disederhanakan dari dua develop branch (`fe/develop`, `be/develop`) menjadi satu `develop` branch. MILESTONE_PLAN ditulis ulang: estimasi durasi menjadi estimasi untuk satu orang sequential (lebih panjang dari estimasi paralel sebelumnya), paragraf "paralel empat developer" dihapus, urutan kerja per fitur menjadi DB → BE → FE. GUIDE_FRONTEND_ENGINEER, GUIDE_BACKEND_ENGINEER, dan GUIDE_DATABASE_ENGINEER tetap ada sebagai referensi teknis per lapisan — konten tidak berubah. GUIDE_FULLSTACK baru dibuat sebagai panduan operasional harian yang mengintegrasikan ketiga lapisan dalam urutan feature-based.

**Dokumen terkait:** SH-02, MILESTONE_PLAN, REPOSITORY_STRUCTURE, GUIDE_FULLSTACK (baru), BE-01

---

*Dokumen ini adalah living document — setiap keputusan signifikan baru yang diambil selama development harus ditambahkan ke log ini.*

---

**Riwayat Perubahan**

| Versi | Tanggal | Perubahan | Author |
|---|---|---|---|
| 1.0.0 | 2026-06-07 | Versi awal — 27 keputusan dari fase perancangan | — |
| 2.0.0 | 2026-06-11 | Tambah ADR-028 (OpenAI embedding model), ADR-029 (pgvector sebagai vector store), ADR-030 (form preferensi opsional) | — |
| 3.0.0 | 2026-06-12 | Tambah ADR-031 (adopsi 2-repo: monorepo TypeScript + repo terpisah FastAPI); tandai ADR-012 sebagai Superseded | — |
| 4.0.0 | 2026-06-12 | Tambah ADR-032 (empat role developer: pisah Backend Engineer menjadi Backend Engineer dan AI Engineer) | — |
| 5.0.0 | 2026-06-13 | Tambah ADR-033 (DeepSeek-V4-Flash via OpenRouter menggantikan Claude Sonnet); tambah ADR-034 (Google Gemini text-embedding-004 menggantikan OpenAI text-embedding-3-small); tandai ADR-015 dan ADR-028 sebagai Superseded | — |
| 6.0.0 | 2026-06-13 | Tambah ADR-035 (namespace AI terpisah: BE-03/04/05/08/09/10 → AI-01 s/d AI-06); tambah ADR-036 (dua track solo developer: Fullstack + AI Engineer, menggantikan ADR-032); tandai ADR-032 sebagai Superseded; perbarui referensi dokumen terkait di ADR-033 dan ADR-034 | — |
