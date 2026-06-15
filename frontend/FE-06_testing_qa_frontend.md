# FE-06 — Testing & QA Frontend Specification

**Project:** AI Vendor Selection System  
**Dokumen:** FE-06 — Testing & QA Frontend  
**Versi:** 1.0.0  
**Tanggal:** 2026-06-07  
**Status:** Draft  
**Author:** —  
**Direview oleh:** —

---

## Daftar Isi

1. [Tujuan Dokumen](#1-tujuan-dokumen)
2. [Referensi Dokumen](#2-referensi-dokumen)
3. [Prinsip Testing Frontend](#3-prinsip-testing-frontend)
4. [Tooling](#4-tooling)
5. [Unit Test Komponen](#5-unit-test-komponen)
6. [Integration Test](#6-integration-test)
7. [End-to-End Test](#7-end-to-end-test)
8. [Aksesibilitas](#8-aksesibilitas)
9. [Visual Regression Testing](#9-visual-regression-testing)
10. [Coverage Target](#10-coverage-target)
11. [Pipeline CI](#11-pipeline-ci)
12. [Aturan & Larangan](#12-aturan--larangan)
13. [Catatan untuk Dokumen Lanjutan](#13-catatan-untuk-dokumen-lanjutan)

---

## 1. Tujuan Dokumen

Dokumen ini mendefinisikan **strategi testing khusus untuk sisi frontend** — komponen apa yang diuji, alur mana yang perlu di-cover oleh E2E test, tooling apa yang digunakan, dan target coverage yang harus dicapai.

Dokumen ini menjawab pertanyaan: bagaimana memastikan komponen UI bekerja sesuai spesifikasi, bagaimana menangkap regresi sebelum sampai ke user, dan bagaimana testing diintegrasikan ke pipeline CI agar tidak ada kode bermasalah yang lolos ke production.

Dokumen ini **tidak** mendefinisikan testing untuk backend, agent, atau database — masing-masing tercakup dalam SH-03 (Testing Strategy keseluruhan sistem).

---

## 2. Referensi Dokumen

| Kode | Nama Dokumen | Keterangan |
|---|---|---|
| FE-01 | UI Architecture | Tech stack yang menentukan tooling testing |
| FE-02 | Component Library | Komponen yang menjadi unit test target |
| FE-03 | Page & User Flow | Alur yang menjadi E2E test target |
| FE-04 | State Management | State yang perlu diverifikasi dalam integration test |
| SH-03 | Testing Strategy | Strategi testing holistik seluruh sistem |

---

## 3. Prinsip Testing Frontend

### 3.1 Test perilaku, bukan implementasi

Test tidak boleh bergantung pada detail implementasi internal komponen — nama variabel internal, struktur state, atau class CSS. Test harus berinteraksi dengan komponen seperti yang dilakukan user: melalui teks yang terlihat, label, role ARIA, dan aksi yang dapat dilakukan.

**Mengapa:** Test yang bergantung pada implementasi internal akan rusak setiap kali kode di-refactor, meskipun perilaku komponen tidak berubah. Ini membuat refactoring menjadi mahal dan menghambat perbaikan kode.

### 3.2 Testing pyramid

Distribusi test mengikuti testing pyramid — banyak unit test, lebih sedikit integration test, dan sedikit E2E test yang mencakup critical path:

```
          /─────────\
         /  E2E (10%) \       Sedikit, lambat, mahal — hanya happy path
        /─────────────\
       / Integration   \      Lebih banyak — alur antar komponen
      /    (30%)        \
     /─────────────────\
    /   Unit Test (60%)  \    Banyak, cepat, murah — tiap komponen
   /─────────────────────\
```

### 3.3 Test harus deterministik

Test yang kadang lulus kadang gagal (flaky test) lebih berbahaya dari tidak ada test — ia membuang waktu investigasi dan melemahkan kepercayaan terhadap seluruh test suite. Flaky test harus diperbaiki atau dihapus, tidak dibiarkan.

### 3.4 Test sebagai dokumentasi hidup

Test yang ditulis dengan baik menjelaskan apa yang seharusnya dilakukan komponen dalam berbagai kondisi. Developer baru harus bisa memahami perilaku komponen dari membaca test-nya.

---

## 4. Tooling

| Kebutuhan | Tools | Alasan |
|---|---|---|
| Unit & Integration test | Vitest | Cepat, kompatibel dengan Vite/Next.js, API mirip Jest |
| Test renderer React | React Testing Library | Mendorong test berbasis perilaku, bukan implementasi |
| E2E test | Playwright | Multi-browser, reliable, built-in wait strategy yang baik |
| Aksesibilitas | jest-axe + Playwright axe | Deteksi otomatis violation WCAG |
| Visual regression | Playwright screenshot | Built-in di Playwright, tidak perlu service tambahan |
| Mock API | MSW (Mock Service Worker) | Intercept request di level network, bukan di kode |
| Coverage | Vitest coverage (v8) | Built-in, tidak perlu konfigurasi tambahan |

### 4.1 Mengapa Vitest, bukan Jest

Vitest memiliki performa yang jauh lebih baik untuk project Next.js karena menggunakan Vite sebagai transformer — startup time lebih cepat dan watch mode lebih responsif. API-nya kompatibel dengan Jest sehingga tidak ada learning curve bagi developer yang sudah familiar dengan Jest.

### 4.2 Mengapa MSW untuk mock API

MSW mengintercept request HTTP di level service worker (browser) atau di level node (test) — bukan dengan mocking fungsi fetch di kode. Ini berarti test berjalan melalui layer yang sama dengan production code, termasuk error handling dan header parsing. Mock yang lebih realistis menghasilkan test yang lebih dapat dipercaya.

---

## 5. Unit Test Komponen

Unit test memverifikasi bahwa setiap komponen berperilaku sesuai spesifikasi dalam isolasi — tanpa bergantung pada komponen lain atau API eksternal.

### 5.1 Komponen yang wajib memiliki unit test

Berdasarkan FE-02, komponen berikut wajib memiliki unit test karena memiliki logika kondisional yang signifikan atau digunakan di banyak tempat:

**Atomic components:**

`StatusBadge` — test bahwa setiap nilai status menghasilkan label dan warna yang benar. Enam variant harus ditest secara eksplisit.

`ScoreBar` — test bahwa nilai skor menghasilkan warna bar yang benar sesuai rentang (merah/kuning/biru/hijau), test bahwa label ditampilkan dengan benar, test bahwa nilai di luar rentang 0–100 ditangani dengan graceful.

`RankBadge` — test bahwa rank 1 mendapat styling berbeda dari rank lain, test bahwa rank besar (misalnya 10) ditampilkan dengan benar.

**Composite components:**

`CriteriaWeightInput` — test validasi: apakah field menampilkan indikator error saat `isInvalid` true, apakah callback `onChange` dipanggil dengan nilai yang benar saat input berubah.

`VendorInputCard` — test tiga mode (manual, extracted, loading), test bahwa tombol remove memanggil callback `onRemove`, test bahwa field yang ter-prefill dari ekstraksi dapat diedit.

`ApprovalCard` — test bahwa tombol reject memerlukan komentar sebelum bisa disubmit, test bahwa tombol disabled saat `isSubmitting` true, test bahwa kedua callback (`onApprove`, `onReject`) dipanggil dengan argumen yang benar.

**Feature components:**

`EvaluasiStepper` — test navigasi antar step (lanjut, kembali), test validasi per step (step 1 tidak bisa lanjut jika field wajib kosong), test bahwa step indicator menunjukkan posisi yang benar.

`CriteriaWeightInput` dalam konteks P-08 — test bahwa total bobot ditampilkan secara real-time, test bahwa tombol simpan disabled saat total bukan 100%.

### 5.2 Apa yang tidak perlu diunit test

- Komponen presentasional murni tanpa logika kondisional (hanya menampilkan data yang diterima via props)
- Styling dan warna secara spesifik (itu domain visual regression test)
- Komponen yang hanya membungkus komponen shadcn/ui tanpa logika tambahan

### 5.3 Pola penulisan unit test

Setiap unit test mengikuti pola AAA (Arrange, Act, Assert):
- **Arrange:** Setup komponen dengan props yang diperlukan menggunakan `render()`
- **Act:** Lakukan interaksi yang relevan (klik, input teks, dll.) menggunakan `userEvent`
- **Assert:** Verifikasi bahwa DOM menampilkan konten yang diharapkan menggunakan `screen.getBy*`

Query yang digunakan mengikuti prioritas React Testing Library: `getByRole` → `getByLabelText` → `getByText` → `getByTestId`. `getByTestId` hanya digunakan sebagai last resort.

---

## 6. Integration Test

Integration test memverifikasi bahwa beberapa komponen bekerja bersama dengan benar, termasuk interaksi dengan state management dan mock API.

### 6.1 Apa yang diuji

**Halaman Dashboard (P-02):**
- Test bahwa stat cards menampilkan angka yang benar dari data API yang di-mock
- Test bahwa klik baris evaluasi dengan status `processing` mengarahkan ke URL yang benar
- Test bahwa klik baris evaluasi dengan status `selesai` mengarahkan ke URL yang benar

**Form Buat Evaluasi (P-03):**
- Test alur lengkap pengisian tiga step dengan data valid
- Test bahwa step 1 tidak bisa dilanjutkan jika field wajib kosong
- Test bahwa vendor bisa ditambahkan dan dihapus di step 2
- Test bahwa step 3 menampilkan ringkasan data yang benar dari step 1 dan 2
- Test bahwa submit memanggil API yang benar dengan payload yang benar

**Halaman Hasil (P-05):**
- Test bahwa tabel ranking menampilkan vendor dalam urutan skor yang benar
- Test bahwa klik baris expand menampilkan detail breakdown skor
- Test bahwa tombol kirim approval disabled setelah diklik pertama kali

**Halaman Approval P-07 (khusus Manager):**
- Test bahwa tombol reject memerlukan komentar
- Test bahwa setelah approve, card evaluasi tersebut hilang dari daftar pending

**Halaman Settings P-08:**
- Test bahwa perubahan bobot memperbarui total secara real-time
- Test bahwa tombol simpan disabled saat total bukan 100%
- Test bahwa simpan berhasil memanggil API yang benar

### 6.2 Setup MSW untuk integration test

MSW dikonfigurasi untuk menyediakan handler per endpoint yang dibutuhkan setiap integration test. Handler mengembalikan data yang representatif — bukan data minimal — agar test mencerminkan kondisi production yang realistis.

Handler MSW disimpan dalam folder `test/handlers/` yang terorganisir per domain (evaluasi, auth, konfigurasi) dan dapat di-reuse antar test.

---

## 7. End-to-End Test

E2E test menggunakan Playwright untuk menjalankan browser sungguhan dan menguji alur pengguna secara menyeluruh dari login hingga output akhir.

### 7.1 Scope E2E test

E2E test hanya mencakup **critical path** — alur yang jika rusak akan langsung mempengaruhi fungsi utama aplikasi. Tidak setiap skenario diuji E2E karena E2E test lambat dan mahal untuk dijalankan.

### 7.2 Critical path yang wajib di-cover

**Happy path Staff:**
```
Login → Dashboard → Buat Evaluasi (isi form 3 step) →
Processing (tunggu selesai) → Hasil → Kirim ke Manager
```

**Happy path Manager — Approval:**
```
Login sebagai Manager → Halaman Approval →
Buka detail evaluasi → Approve dengan komentar
```

**Happy path Manager — Reject:**
```
Login sebagai Manager → Halaman Approval →
Reject dengan komentar → Verifikasi status berubah
```

**Konfigurasi bobot:**
```
Login sebagai Manager → Settings →
Ubah bobot kriteria → Simpan → Verifikasi perubahan tersimpan
```

### 7.3 Pendekatan mock di E2E test

E2E test berjalan terhadap aplikasi yang sudah di-deploy di environment testing — bukan localhost. Backend API di-mock menggunakan MSW di level service worker browser, sehingga tidak memerlukan database sungguhan untuk E2E test.

**Mengapa:** E2E test yang bergantung pada database sungguhan rentan terhadap kondisi data yang tidak terduga dan sulit di-reset. Mock yang deterministik menghasilkan test yang lebih stabil.

### 7.4 Strategi wait dan timing

Playwright memiliki built-in auto-wait yang menunggu elemen menjadi visible dan actionable sebelum berinteraksi. Tidak boleh ada `page.waitForTimeout()` dengan waktu hardcoded di test — ini adalah penyebab umum flaky test.

Untuk menunggu proses async seperti simulasi processing agent, test menggunakan `page.waitForSelector()` dengan selector spesifik yang muncul saat proses selesai.

### 7.5 Test isolation

Setiap E2E test berjalan dalam konteks browser yang fresh — tidak ada state yang dibawa dari test sebelumnya. Login dilakukan di awal setiap test atau menggunakan Playwright storageState untuk reuse session yang sudah di-setup sebelumnya.

---

## 8. Aksesibilitas

### 8.1 Mengapa aksesibilitas perlu di-test

Aplikasi enterprise yang baik harus dapat digunakan oleh semua karyawan, termasuk yang menggunakan screen reader atau navigasi keyboard. Selain itu, aksesibilitas yang baik juga meningkatkan kualitas HTML secara umum — yang berdampak positif pada SEO dan maintainability.

### 8.2 Automated accessibility testing

Setiap halaman utama diuji dengan `axe-core` yang diintegrasikan ke dalam Playwright E2E test. Test ini mendeteksi violation WCAG 2.1 level AA secara otomatis.

Violation yang terdeteksi menyebabkan test gagal — bukan hanya warning. Ini memastikan aksesibilitas diperlakukan sebagai persyaratan, bukan nice-to-have.

### 8.3 Manual checks yang tidak bisa di-otomasi

Beberapa aspek aksesibilitas tidak bisa dideteksi oleh tool otomatis dan perlu dicek secara manual:
- Navigasi keyboard: semua fungsi dapat diakses menggunakan Tab, Enter, dan arrow keys
- Urutan fokus yang logis saat navigasi keyboard
- Label yang bermakna bagi screen reader (bukan hanya "button" atau "link")
- Kontras warna yang cukup (axe-core membantu tapi tidak 100%)

Manual check dilakukan sekali per milestone rilis, bukan per commit.

### 8.4 Target aksesibilitas

- Zero violation WCAG 2.1 level AA yang terdeteksi oleh axe-core pada semua halaman utama
- Semua form dapat diisi menggunakan keyboard saja
- Semua konten penting memiliki teks alternatif atau label yang sesuai

---

## 9. Visual Regression Testing

### 9.1 Apa dan mengapa

Visual regression testing membandingkan screenshot komponen atau halaman dengan screenshot referensi yang sudah disetujui. Jika ada perbedaan visual yang tidak disengaja (misalnya styling berubah akibat update dependency), test akan mendeteksinya.

### 9.2 Scope visual regression

Visual regression test tidak diterapkan pada semua komponen — hanya pada komponen yang perubahan visualnya sulit terdeteksi oleh unit test:
- Layout 3-panel AppShell
- Halaman hasil evaluasi (P-05) — kompleks dan kritis
- StatusBadge dalam semua variantnya
- ScoreBar dalam semua rentang nilai

### 9.3 Workflow update screenshot

Saat perubahan visual disengaja (misalnya redesign komponen), screenshot referensi perlu diperbarui secara eksplisit. Pembaruan screenshot harus melalui review — tidak boleh di-commit tanpa persetujuan.

### 9.4 Batasan visual regression

Visual regression test sensitif terhadap perbedaan rendering antar sistem operasi dan browser. Untuk menghindari false positive, screenshot referensi di-generate dan dibandingkan dalam environment yang sama (Docker container dengan browser yang terdefinisi) — bukan di mesin developer lokal masing-masing.

---

## 10. Coverage Target

### 10.1 Target per lapisan test

| Lapisan | Target Coverage | Prioritas |
|---|---|---|
| Unit test — komponen dengan logika | > 80% statement coverage | Wajib |
| Unit test — komponen presentasional | Tidak ditargetkan | Opsional |
| Integration test — halaman utama | Semua halaman di P-01 s/d P-08 | Wajib |
| E2E test — critical path | Semua critical path di section 7.2 | Wajib |
| Aksesibilitas | Zero axe-core violation | Wajib |

### 10.2 Apa yang tidak diukur dengan coverage angka

Coverage persentase adalah indikator, bukan tujuan. Komponen yang memiliki 90% coverage tetapi test-nya hanya memverifikasi bahwa komponen dapat di-render tanpa crash — tanpa memverifikasi perilaku yang bermakna — tidak lebih baik dari 0% coverage yang jujur.

Yang lebih penting dari angka coverage adalah test yang memverifikasi skenario yang benar-benar penting bagi user.

### 10.3 Coverage yang dikecualikan

File berikut dikecualikan dari perhitungan coverage karena tidak berisi logika yang bisa di-test secara bermakna:
- File konfigurasi (next.config.js, tailwind.config.ts, dll.)
- Type definition files (.types.ts)
- Konstanta statis tanpa logika kondisional
- File index yang hanya re-export

---

## 11. Pipeline CI

### 11.1 Urutan eksekusi di CI

Setiap pull request menjalankan pipeline berikut secara berurutan. Tahap berikutnya hanya dijalankan jika tahap sebelumnya berhasil:

```
1. Type checking (tsc --noEmit)
        ↓
2. Linting (ESLint)
        ↓
3. Unit test + Integration test (Vitest)
        ↓
4. Coverage check (gagal jika di bawah target)
        ↓
5. Build (next build)
        ↓
6. E2E test (Playwright) — hanya di branch staging dan main
        ↓
7. Aksesibilitas check (axe via Playwright)
        ↓
8. Visual regression (Playwright screenshot diff)
```

### 11.2 Mengapa E2E hanya di staging dan main

E2E test membutuhkan waktu 5–15 menit untuk selesai — terlalu lama untuk dijalankan di setiap pull request. Unit test dan integration test sudah cukup untuk menangkap sebagian besar masalah. E2E dijalankan sebagai gate akhir sebelum merge ke staging dan production.

### 11.3 Parallelisasi

Unit test dan integration test dijalankan secara paralel di CI untuk mempersingkat waktu. Playwright E2E test dijalankan paralel di beberapa worker (maksimum 4 worker) untuk mempersingkat runtime.

### 11.4 Test report

Setiap run CI menghasilkan test report yang bisa diakses oleh seluruh tim:
- Vitest: HTML report dengan breakdown per file dan per test
- Playwright: HTML report dengan screenshot dan video recording untuk test yang gagal
- Coverage: badge yang ditampilkan di README repository

### 11.5 Kebijakan merge

Pull request tidak boleh di-merge jika:
- Ada test yang gagal
- Coverage turun di bawah target yang ditetapkan
- Ada axe-core violation baru yang diintroduksi
- Build gagal

---

## 12. Aturan & Larangan

**Dilarang menggunakan `page.waitForTimeout()` atau `sleep()` di test.** Ini adalah penyebab umum flaky test. Gunakan `waitForSelector`, `waitForResponse`, atau auto-wait bawaan Playwright.

**Dilarang query komponen menggunakan class CSS atau selector DOM yang rapuh.** Gunakan `getByRole`, `getByLabelText`, atau `getByText` — bukan `querySelector('.btn-primary')`.

**Dilarang meng-commit test yang gagal** dengan alasan "nanti diperbaiki". Test yang gagal harus diperbaiki atau dihapus sebelum merge.

**Dilarang skip test secara permanen** menggunakan `test.skip()` tanpa komentar yang menjelaskan mengapa dan kapan akan diperbaiki. Test yang di-skip lebih dari satu sprint harus dihapus atau diimplementasikan.

**Dilarang menulis test yang memverifikasi implementasi internal** seperti nama fungsi, struktur state internal Zustand, atau class CSS yang tidak berkaitan dengan perilaku yang terlihat user.

**Dilarang membiarkan flaky test** tanpa investigasi dan perbaikan dalam sprint yang sama ketika terdeteksi.

---

## 13. Catatan untuk Dokumen Lanjutan

### Untuk SH-03 (Testing Strategy)

FE-06 mendefinisikan testing khusus frontend. SH-03 perlu mengintegrasikan ini dengan strategi testing keseluruhan — termasuk bagaimana E2E test frontend berkoordinasi dengan integration test backend, dan bagaimana test suite dijalankan dalam urutan yang benar di CI/CD pipeline yang mencakup seluruh sistem.

### Untuk SH-02 (Deployment Runbook)

Pipeline CI di section 11 perlu dikonfigurasi di Vercel dan GitHub Actions. Runbook perlu mendokumentasikan cara setup environment variables untuk test (termasuk mock credentials), cara menjalankan Playwright dalam environment CI, dan cara membaca test report jika ada kegagalan.

### Untuk FE-02 (Component Library)

Komponen yang wajib memiliki unit test sudah terdefinisikan di section 5.1. Setiap komponen baru yang ditambahkan ke FE-02 di masa mendatang harus disertai keputusan eksplisit apakah komponen tersebut masuk ke daftar unit test wajib atau tidak.

---

*Dokumen ini adalah living document — strategi testing akan diperbarui seiring bertambahnya komponen dan alur baru.*

---

**Riwayat Perubahan**

| Versi | Tanggal | Perubahan | Author |
|---|---|---|---|
| 1.0.0 | 2026-06-07 | Versi awal | — |
