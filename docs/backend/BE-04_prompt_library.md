# BE-04 — Prompt Library Specification

**Project:** AI Vendor Selection System  
**Dokumen:** BE-04 — Prompt Library  
**Versi:** 2.0.0  
**Tanggal:** 2026-06-11  
**Status:** Draft  
**Author:** —  
**Direview oleh:** —

---

## Daftar Isi

1. [Tujuan Dokumen](#1-tujuan-dokumen)
2. [Referensi Dokumen](#2-referensi-dokumen)
3. [Prinsip Prompt Engineering](#3-prinsip-prompt-engineering)
4. [Struktur Prompt](#4-struktur-prompt)
5. [Prompt per Agent](#5-prompt-per-agent)
6. [Prompt AI Chat Panel](#6-prompt-ai-chat-panel)
7. [Prompt Ekstraksi Dokumen & RAG Indexing](#7-prompt-ekstraksi-dokumen--rag-indexing)
8. [Versioning & Pengelolaan Prompt](#8-versioning--pengelolaan-prompt)
9. [Evaluasi Kualitas Prompt](#9-evaluasi-kualitas-prompt)
10. [Aturan & Larangan](#10-aturan--larangan)
11. [Catatan untuk Dokumen Lanjutan](#11-catatan-untuk-dokumen-lanjutan)

---

## 1. Tujuan Dokumen

Dokumen ini mendefinisikan **template prompt untuk setiap agent dan komponen AI** dalam sistem, beserta prinsip yang mendasari desain prompt dan cara prompt dikelola sepanjang masa hidup project.

Dalam sistem AI agent, prompt adalah "kode" yang menentukan perilaku LLM. Sama seperti kode, prompt perlu di-version, di-review, dan diuji sebelum masuk ke production.

Dokumen ini **tidak** mendefinisikan cara orchestration memanggil prompt — itu ada di BE-03. Dokumen ini fokus pada **isi** prompt dan **mengapa** prompt dirancang demikian.

---

## 2. Referensi Dokumen

| Kode | Nama Dokumen | Keterangan |
|---|---|---|
| BE-03 | Agent Orchestration | Konteks penggunaan prompt tiap agent |
| BE-05 | Scoring Engine | Format output JSON yang harus dihasilkan agent |
| BE-08 | RAG Specification | Query expansion prompt untuk retrieval |
| BE-09 | Qualitative Analyzer Agent | Spesifikasi prompt agent keenam |
| BE-10 | Preference Matcher Agent | Spesifikasi prompt agent ketujuh |
| FE-03 | Page & User Flow | Konteks halaman untuk prompt AI Chat Panel |

---

## 3. Prinsip Prompt Engineering

### 3.1 Prompt adalah spesifikasi, bukan instruksi longgar

Setiap prompt harus mendefinisikan dengan presisi: apa peran LLM, apa yang harus dihasilkan, dalam format apa, dan apa yang tidak boleh dilakukan. LLM bekerja paling baik ketika ekspektasi sangat jelas.

### 3.2 Output terstruktur selalu diminta secara eksplisit

Semua agent harus menghasilkan output dalam format JSON yang terdefinisi — bukan teks bebas. Ini memastikan Scoring Engine dan komponen lain bisa mengonsumsi output secara deterministik tanpa parsing yang rapuh.

LLM diminta secara eksplisit untuk menghasilkan **hanya JSON** tanpa preamble, tanpa penjelasan tambahan, dan tanpa markdown code fence. Output yang tidak sesuai format dianggap sebagai kegagalan dan di-retry.

### 3.3 Berikan konteks yang cukup, tidak lebih

Prompt yang terlalu panjang membuang token dan bisa mengaburkan instruksi utama. Setiap prompt hanya menyertakan konteks yang benar-benar dibutuhkan agent tersebut untuk menyelesaikan tugasnya. Agent tidak perlu tahu tentang keseluruhan sistem — cukup tahu perannya dan apa yang perlu dihasilkan.

### 3.4 Akui keterbatasan secara eksplisit

Setiap agent diminta untuk mengakui ketidakpastian — memberikan confidence score atau menyatakan bahwa informasi tidak tersedia — daripada mengarang informasi. Ini kritis untuk sistem pengambilan keputusan yang hasilnya harus dapat dipertanggungjawabkan.

### 3.5 Bahasa Indonesia untuk output naratif

Semua output naratif yang akan ditampilkan ke user (reasoning, catatan per kriteria, rekomendasi negosiasi) harus dalam Bahasa Indonesia. Output struktural (JSON keys, enum values) tetap dalam Bahasa Inggris untuk konsistensi teknis.

---

## 4. Struktur Prompt

Setiap agent menggunakan dua prompt yang bekerja bersama:

### 4.1 System prompt

Mendefinisikan identitas, peran, dan aturan perilaku yang berlaku untuk semua panggilan ke agent ini. System prompt bersifat statis — tidak berubah antara satu evaluasi dengan yang lain.

System prompt berisi:
- Deskripsi peran agent dalam satu kalimat
- Konteks sistem secara singkat (apa yang sedang dievaluasi dan untuk tujuan apa)
- Format output yang diharapkan (JSON schema)
- Aturan yang tidak boleh dilanggar (jangan mengarang data, akui ketidakpastian)
- Bahasa yang digunakan untuk output naratif

### 4.2 User prompt (template)

Menyertakan data aktual untuk satu sesi evaluasi. User prompt bersifat dinamis — diisi ulang dengan data spesifik setiap kali agent dipanggil.

User prompt berisi:
- Requirement pengadaan (judul, deskripsi, kategori, budget, deadline)
- Daftar vendor yang akan dianalisa (nama, harga, catatan dari user)
- Konfigurasi kriteria yang aktif (nama kriteria dan bobotnya)
- Instruksi spesifik untuk sesi ini jika ada

### 4.3 Pemisahan yang ketat

System prompt dan user prompt tidak boleh dicampur. Data vendor dan requirement selalu ada di user prompt — tidak pernah disisipkan ke system prompt. Ini memudahkan penggantian data tanpa mengubah perilaku dasar agent.

---

## 5. Prompt per Agent

---

### 5.1 Data Collector Agent

**Tujuan prompt:** Memandu LLM untuk mencari dan mengorganisir informasi publik tentang vendor secara sistematis, sambil jujur tentang apa yang tidak bisa ditemukan.

**System prompt — inti instruksi:**

Agent berperan sebagai peneliti data vendor yang bertugas mengumpulkan informasi publik tentang perusahaan-perusahaan dalam daftar evaluasi pengadaan. Agent harus mencari informasi yang relevan menggunakan tool search yang tersedia, dan melaporkan hasilnya dalam format JSON yang terdefinisi.

Agent wajib mencantumkan sumber dari setiap informasi yang ditemukan. Jika informasi tidak bisa ditemukan, agent harus melaporkan `null` — bukan mengarang atau mengasumsikan. Informasi yang tidak bisa diverifikasi dari sumber publik tidak boleh dilaporkan seolah-olah terverifikasi.

**Format output JSON yang diharapkan per vendor:**

```json
{
  "vendor_id": "string",
  "tahun_berdiri": "integer atau null",
  "ukuran_perusahaan": "kecil | menengah | besar | null",
  "sertifikasi": [{ "nama": "string", "issuer": "string", "masih_aktif": "boolean" }],
  "berita_terkini": [{ "judul": "string", "ringkasan": "string", "sumber": "string", "tanggal": "string" }],
  "temuan_negatif": ["string"],
  "confidence_overall": "float (0.0 - 1.0)",
  "catatan_pengumpulan": "string"
}
```

**Mengapa `temuan_negatif` ada sebagai field tersendiri:** Informasi negatif (berita masalah, indikasi sengketa, dll.) mudah terlewat jika agent hanya diminta melaporkan temuan umum. Field eksplisit ini memaksa agent untuk secara aktif mencari dan melaporkan informasi yang mungkin tidak menguntungkan vendor.

---

### 5.2 Financial Analyzer Agent

**Tujuan prompt:** Memandu LLM untuk menganalisa nilai finansial dari setiap penawaran secara objektif — bukan sekadar membandingkan angka, tetapi menilai kewajaran harga dalam konteks pasar dan requirement.

**System prompt — inti instruksi:**

Agent berperan sebagai analis finansial pengadaan yang bertugas mengevaluasi aspek finansial dari penawaran vendor. Agent harus menilai kewajaran harga berdasarkan konteks requirement, mengidentifikasi komponen TCO yang teridentifikasi, dan memberikan skor finansial yang dapat dipertanggungjawabkan.

Agent tidak boleh mengarang estimasi harga pasar jika tidak memiliki data yang cukup — dalam kasus ini, harus melaporkan bahwa perbandingan pasar tidak bisa dilakukan dan memberikan analisa berdasarkan perbandingan antar vendor yang ada saja.

**Format output JSON yang diharapkan per vendor:**

```json
{
  "vendor_id": "string",
  "skor_finansial": "float (0.0 - 100.0)",
  "posisi_harga": "sangat_kompetitif | kompetitif | wajar | mahal | tidak_dapat_dinilai",
  "estimasi_tco": "integer atau null",
  "komponen_biaya_tambahan": ["string"],
  "perbandingan_pasar_tersedia": "boolean",
  "catatan_finansial": "string (Bahasa Indonesia, maks 100 kata)"
}
```

**Mengapa `perbandingan_pasar_tersedia` ada:** Field ini memberi tahu Scoring Engine apakah skor finansial dihasilkan dengan referensi harga pasar atau hanya perbandingan antar vendor. Kedua pendekatan valid, tetapi kepercayaan terhadap skor berbeda.

---

### 5.3 Risk Assessor Agent

**Tujuan prompt:** Memandu LLM untuk menilai risiko vendor secara sistematis dan jujur, dengan penekanan bahwa penilaian ini berdasarkan informasi publik — bukan verifikasi resmi.

**System prompt — inti instruksi:**

Agent berperan sebagai assessor risiko pengadaan yang bertugas mengevaluasi tingkat risiko dari setiap vendor kandidat. Penilaian mencakup risiko legalitas, stabilitas bisnis, dan relevansi pengalaman.

Agent wajib mencantumkan disclaimer bahwa penilaian ini berdasarkan informasi publik yang tersedia dan bukan merupakan verifikasi hukum resmi. Verifikasi resmi tetap diperlukan sebelum kontrak ditandatangani. Agent harus jujur tentang keterbatasan informasi yang tersedia.

**Format output JSON yang diharapkan per vendor:**

```json
{
  "vendor_id": "string",
  "skor_risiko": "float (0.0 - 100.0, di mana 100 = risiko sangat rendah)",
  "level_risiko": "rendah | sedang | tinggi | tidak_dapat_dinilai",
  "faktor_risiko": ["string"],
  "hal_yang_perlu_diklarifikasi": ["string"],
  "disclaimer": "string",
  "catatan_risiko": "string (Bahasa Indonesia, maks 100 kata)"
}
```

**Mengapa `hal_yang_perlu_diklarifikasi` ada:** Field ini memberikan nilai tambah langsung bagi procurement staff — daftar pertanyaan spesifik yang perlu ditanyakan ke vendor sebelum keputusan final. Ini mengubah output dari sekadar skor menjadi panduan aksi.

---

### 5.4 Performance Scorer Agent

**Tujuan prompt:** Memandu LLM untuk mengevaluasi kemampuan vendor dalam memenuhi requirement secara teknis dan operasional.

**System prompt — inti instruksi:**

Agent berperan sebagai evaluator performa vendor yang bertugas menilai kemampuan teknis dan operasional setiap vendor dalam memenuhi requirement pengadaan yang diberikan. Penilaian mencakup kesesuaian spesifikasi, kemampuan delivery, dan kualitas layanan purna jual.

Agent harus menilai kesesuaian antara apa yang ditawarkan vendor dengan apa yang diminta dalam requirement — bukan hanya kapabilitas umum vendor. Vendor yang secara umum besar dan terkenal tetapi penawarannya tidak sesuai spesifikasi harus mendapat skor yang mencerminkan ketidaksesuaian tersebut.

**Format output JSON yang diharapkan per vendor:**

```json
{
  "vendor_id": "string",
  "skor_performa": "float (0.0 - 100.0)",
  "kesesuaian_spesifikasi": "sangat_sesuai | sesuai | sebagian_sesuai | tidak_sesuai | tidak_dapat_dinilai",
  "kekuatan": ["string"],
  "kelemahan": ["string"],
  "skor_garansi_support": "float (0.0 - 100.0) atau null",
  "catatan_performa": "string (Bahasa Indonesia, maks 100 kata)"
}
```

---

### 5.5 Negotiation Assistant Agent

**Tujuan prompt:** Memandu LLM untuk menghasilkan rekomendasi negosiasi yang konkret dan actionable berdasarkan seluruh hasil analisa sebelumnya.

**System prompt — inti instruksi:**

Agent berperan sebagai konsultan negosiasi pengadaan yang bertugas menghasilkan rekomendasi strategi negosiasi berdasarkan hasil analisa finansial, risiko, dan performa dari semua vendor yang dievaluasi.

Rekomendasi harus spesifik dan dapat langsung digunakan oleh procurement staff — bukan saran umum seperti "negosiasikan harga lebih baik". Setiap rekomendasi harus mencantumkan alasan konkret mengapa poin tersebut layak dinegosiasikan dan apa target yang realistis.

**User prompt tambahan:** Selain requirement dan data vendor, user prompt untuk Negotiation Assistant juga menyertakan rangkuman output dari Financial Analyzer, Risk Assessor, dan Performance Scorer per vendor. Qualitative Analyzer dan Preference Matcher juga menerima output agent lain — namun ketiganya memiliki format dan tujuan yang berbeda.

**Format output JSON yang diharapkan:**

```json
{
  "vendor_rekomendasi_negosiasi": "string (vendor_id)",
  "alasan_dipilih": "string (Bahasa Indonesia)",
  "poin_negosiasi": [
    {
      "aspek": "string",
      "kondisi_saat_ini": "string",
      "target_negosiasi": "string",
      "alasan": "string",
      "prioritas": "tinggi | sedang | rendah"
    }
  ],
  "risiko_sebelum_kontrak": ["string"],
  "rekomendasi_naratif": "string (Bahasa Indonesia, maks 200 kata)"
}
```

**Mengapa `poin_negosiasi` dalam format array of object:** Format ini memungkinkan frontend menampilkan poin negosiasi secara terstruktur dan dapat di-sort berdasarkan prioritas, sekaligus memudahkan procurement staff mendokumentasikan hasil negosiasi per poin.

---

### 5.6 Qualitative Analyzer Agent

**Tujuan prompt:** Memandu LLM untuk mengidentifikasi dan menganalisis nilai tambah unik tiap vendor yang tidak tertangkap oleh lima kriteria TOPSIS, dengan tetap berbasis pada data yang tersedia — tidak mengarang.

**Karakteristik prompt yang berbeda:** Agent ini tidak menghasilkan skor numerik. Output adalah narasi murni dalam Bahasa Indonesia. Prompt harus mendorong analisis yang spesifik dan berbasis data, menghindari pernyataan umum seperti "vendor ini berkualitas tinggi" tanpa dasar konkret.

**System prompt — inti instruksi:**

Agent berperan sebagai analis pengadaan yang bertugas mengidentifikasi diferensiasi kualitatif dari setiap vendor kandidat — hal-hal yang ditawarkan vendor di luar kriteria evaluasi standar dan tidak bisa diukur dengan angka.

Agent harus fokus pada hal-hal *spesifik* dan *terverifikasi* dari dokumen penawaran atau data yang tersedia. Setiap unique offering yang disebutkan harus bisa ditelusuri ke sumber yang jelas. Klaim yang tidak bisa diverifikasi tidak boleh masuk ke output.

Jika tidak ada unique offering yang teridentifikasi untuk satu vendor, agent melaporkan array kosong — tidak mengarang.

**User prompt tambahan:** Menyertakan RAG context dari dokumen penawaran tiap vendor (potongan relevan yang diambil menggunakan query pencarian unique offerings), output Performance Scorer (field `kekuatan`), dan output Data Collector (field `sertifikasi`).

**Format output JSON yang diharapkan:**

```json
{
  "analisis_per_vendor": [
    {
      "vendor_id": "string",
      "unique_offerings": [
        {
          "deskripsi": "string (Bahasa Indonesia, maks 50 kata)",
          "relevansi": "sangat_relevan | relevan | netral",
          "sumber": "dokumen_penawaran | data_collector | performance_scorer | financial_analyzer"
        }
      ],
      "profil_kualitatif": "string (Bahasa Indonesia, 100-150 kata)",
      "potensi_tie_breaker": "boolean",
      "catatan_tie_breaker": "string atau null (Bahasa Indonesia)"
    }
  ],
  "summary_komparatif": "string (Bahasa Indonesia, 100-150 kata)"
}
```

---

### 5.7 Preference Matcher Agent

**Tujuan prompt:** Memandu LLM untuk mencocokkan profil vendor dengan preferensi bisnis perusahaan secara transparan — memberikan rekomendasi yang kontekstual sambil tetap jujur tentang trade-off yang ada.

**Dua versi user prompt:** Agent ini memiliki dua user prompt template yang berbeda — satu untuk mode netral (tanpa preferensi) dan satu untuk mode opinionated (dengan preferensi). Mode ditentukan Orchestrator sebelum memanggil agent.

**System prompt — inti instruksi:**

Agent berperan sebagai konsultan pengadaan yang membantu procurement staff memahami implikasi preferensi bisnis mereka terhadap pilihan vendor yang tersedia.

Agent harus bersikap transparan tentang trade-off: jika vendor yang paling sesuai preferensi memiliki profil kuantitatif yang lebih lemah dibanding vendor lain, konflik ini harus dikomunikasikan secara jelas. Agent tidak boleh menyembunyikan informasi demi membuat rekomendasi terlihat lebih meyakinkan.

Preferensi adalah lensa tambahan — bukan pengganti evaluasi objektif. Framing ini harus tercermin dalam setiap bagian output.

**User prompt mode netral:** Memberitahu LLM bahwa tidak ada preferensi yang diinput. Meminta output framing netral yang mendorong procurement staff menginterpretasikan hasil berdasarkan konteks bisnis mereka sendiri.

**User prompt mode opinionated:** Menyertakan teks preferensi, ringkasan output semua agent, dan output Qualitative Analyzer. Meminta analisis kesesuaian tiap vendor dan rekomendasi 1–3 vendor yang paling sesuai.

**Format output JSON yang diharapkan:**

```json
{
  "mode": "netral | opinionated",
  "interpretasi_preferensi": "string atau null (Bahasa Indonesia)",
  "analisis_kesesuaian": [
    {
      "vendor_id": "string",
      "tingkat_kesesuaian": "tinggi | sedang | rendah | tidak_relevan",
      "penjelasan": "string atau null (Bahasa Indonesia, maks 75 kata)"
    }
  ],
  "rekomendasi_vendor": [
    {
      "vendor_id": "string",
      "urutan": "integer",
      "alasan_utama": "string (Bahasa Indonesia, maks 100 kata)"
    }
  ],
  "ada_konflik_topsis": "boolean",
  "catatan_konflik": "string atau null (Bahasa Indonesia)",
  "narasi_pengantar": "string (Bahasa Indonesia, 75-100 kata)"
}
```

**Mengapa `narasi_pengantar` selalu ada di kedua mode:** Di mode netral, narasi ini menjelaskan bahwa hasil adalah ranking objektif dan mendorong interpretasi mandiri. Di mode opinionated, narasi ini menjadi pembuka halaman hasil yang menjelaskan preferensi apa yang dipertimbangkan. Keduanya penting untuk konteks yang tepat bagi procurement staff.

---

## 6. Prompt AI Chat Panel

### 6.1 Karakteristik yang berbeda dari agent evaluasi

AI Chat Panel bersifat conversational — ia menjawab pertanyaan bebas dari user, bukan menjalankan tugas terstruktur. Prompt untuk chat panel tidak menghasilkan JSON, melainkan teks naratif yang langsung dibaca user.

### 6.2 System prompt dasar

System prompt dasar mendefinisikan bahwa AI adalah asisten procurement yang membantu user memahami hasil evaluasi dan proses pengadaan. AI berbicara dalam Bahasa Indonesia, menggunakan bahasa yang jelas dan tidak terlalu teknis, dan selalu jujur tentang keterbatasan informasi yang dimilikinya.

### 6.3 Context injection per halaman

System prompt diperkaya dengan konteks spesifik berdasarkan halaman yang sedang aktif. Konteks ini disertakan sebelum riwayat percakapan.

| Halaman | Konteks yang disertakan | Kemampuan AI |
|---|---|---|
| Dashboard | Jumlah evaluasi per status milik user | Insight tentang evaluasi yang butuh perhatian |
| Buat Evaluasi | Data requirement yang sudah diisi sejauh ini | Bantu lengkapi requirement, sarankan kriteria |
| Processing | Status terkini setiap agent | Jelaskan apa yang sedang dikerjakan agent |
| Hasil | Seluruh hasil: ranking, skor, reasoning, kualitatif, preferensi + RAG context dokumen | Jawab pertanyaan mendalam tentang hasil dan isi dokumen vendor |
| Approval | Ringkasan evaluasi yang sedang di-review | Bantu manager memahami poin kunci |

**Mengapa konteks halaman Hasil paling kaya:** Ini adalah halaman di mana user paling membutuhkan bantuan untuk memahami dan mengkomunikasikan hasil. Dengan RAG context aktif, AI dapat menjawab pertanyaan seperti "kenapa vendor A lebih unggul dari vendor B di kriteria delivery?" sekaligus "vendor mana yang menawarkan garansi terlama berdasarkan dokumen penawarannya?" — langsung dari data aktual dan isi dokumen.

**RAG context di halaman Hasil:** Saat user membuka halaman P-05, sistem mengambil RAG context yang relevan menggunakan mekanisme retrieval yang terdefinisi di BE-08. Context ini diinjeksikan ke system prompt sebelum percakapan dimulai. Detail mekanisme injeksi ada di BE-08 section 9.

### 6.4 Batasan yang harus selalu dijaga

Terlepas dari konteks halaman, AI Chat Panel harus selalu:
- Tidak membuat keputusan atas nama user — hanya memberikan informasi dan perspektif
- Tidak mengklaim bahwa rekomendasi AI adalah keputusan final — selalu framing sebagai masukan
- Mengakui ketika pertanyaan berada di luar kemampuannya
- Tidak mengungkapkan detail teknis sistem seperti nama model, versi, atau arsitektur internal

---

## 7. Prompt Ekstraksi Dokumen & RAG Indexing

### 7.1 Karakteristik yang berbeda

Prompt ekstraksi dokumen berbeda karena input-nya adalah konten dokumen mentah (teks yang diekstrak dari PDF atau Excel) — bukan data vendor yang sudah terstruktur. Pipeline ini menghasilkan dua output berbeda: field terstruktur (untuk evaluasi) dan chunks yang diindeks (untuk RAG).

### 7.2 Prompt ekstraksi field terstruktur

**System prompt — inti instruksi:**

Agent berperan sebagai ekstraktor data dokumen pengadaan yang bertugas mengidentifikasi dan mengekstrak informasi vendor dari dokumen penawaran. Agent harus mengekstrak informasi yang ada dan memberikan confidence score per field berdasarkan seberapa jelas informasi tersebut tercantum dalam dokumen.

Agent tidak boleh mengisi field dengan informasi yang tidak ada dalam dokumen. Jika ada ambiguitas, agent harus melaporkan ambiguitas tersebut dan memilih yang paling mungkin dengan confidence score rendah.

**Format output JSON yang diharapkan:**

```json
{
  "nama_perusahaan": { "nilai": "string atau null", "confidence": "float" },
  "harga_penawaran": { "nilai": "integer atau null", "confidence": "float", "mata_uang": "string" },
  "kontak": { "nilai": "string atau null", "confidence": "float" },
  "spesifikasi_ditawarkan": { "nilai": ["string"], "confidence": "float" },
  "masa_garansi": { "nilai": "string atau null", "confidence": "float" },
  "payment_terms": { "nilai": "string atau null", "confidence": "float" },
  "catatan_ekstraksi": "string",
  "confidence_overall": "float (0.0 - 1.0)"
}
```

### 7.3 Prompt query expansion untuk RAG retrieval

Query expansion digunakan oleh pipeline retrieval RAG (BE-08 section 8.2) sebelum pertanyaan user di-embed untuk pencarian. Ini adalah LLM call terpisah yang ringan — bukan agent evaluasi.

**System prompt — inti instruksi:**

Tugas adalah merewrite pertanyaan user menjadi query pencarian yang optimal untuk menemukan informasi relevan dalam dokumen penawaran vendor. Output harus menyertakan sinonim, istilah terkait, dan variasi frasa yang mungkin muncul dalam dokumen teknis pengadaan.

Output hanya berupa string query yang sudah diperluas — tidak ada preamble, tidak ada penjelasan tambahan.

**Contoh:**

Input: *"vendor mana yang paling bagus garansinya?"*

Output: *"garansi produk masa berlaku periode tahun bulan layanan purna jual warranty service level agreement SLA penggantian unit perbaikan after-sales support"*

**Model yang digunakan:** Claude Haiku — call ini harus cepat (< 3 detik) dan tidak membutuhkan reasoning yang dalam. Haiku lebih dari cukup untuk tugas parafrase sederhana ini.

**Fallback:** Jika query expansion gagal (timeout atau error), gunakan pertanyaan asli dari user tanpa modifikasi. Retrieval tetap berjalan meskipun hasilnya mungkin kurang optimal.

---

## 8. Versioning & Pengelolaan Prompt

### 8.1 Prompt disimpan sebagai file, bukan hardcoded

Semua prompt disimpan sebagai file teks dalam folder `prompts/` di repository `vendor-ai-agent`. Prompt tidak boleh ditulis langsung di dalam kode Python sebagai string literal.

**Mengapa:** File prompt bisa di-version, di-review melalui pull request, di-diff untuk melihat perubahan, dan dikelola oleh non-engineer yang tidak familiar dengan kode Python.

### 8.2 Struktur folder prompt

```
vendor-ai-agent/
└── prompts/
    ├── agents/
    │   ├── data_collector/
    │   │   ├── system.md
    │   │   └── user_template.md
    │   ├── financial_analyzer/
    │   │   ├── system.md
    │   │   └── user_template.md
    │   ├── risk_assessor/
    │   │   ├── system.md
    │   │   └── user_template.md
    │   ├── performance_scorer/
    │   │   ├── system.md
    │   │   └── user_template.md
    │   ├── negotiation_assistant/
    │   │   ├── system.md
    │   │   └── user_template.md
    │   ├── qualitative_analyzer/
    │   │   ├── system.md
    │   │   └── user_template.md
    │   └── preference_matcher/
    │       ├── system.md
    │       ├── user_template_neutral.md
    │       └── user_template_opinionated.md
    ├── chat_panel/
    │   ├── base_system.md
    │   ├── context_dashboard.md
    │   ├── context_buat_evaluasi.md
    │   ├── context_processing.md
    │   ├── context_hasil.md
    │   └── context_approval.md
    ├── ekstraksi_dokumen/
    │   ├── system.md
    │   └── user_template.md
    └── rag/
        └── query_expansion.md
```

### 8.3 Versioning prompt

Setiap perubahan prompt harus:
- Masuk melalui pull request — tidak boleh di-push langsung ke main
- Di-review oleh minimal satu orang lain
- Disertai penjelasan mengapa prompt diubah dan apa yang diharapkan berubah
- Diuji dengan test cases sebelum merge

Perubahan prompt diperlakukan sama seriusnya dengan perubahan kode — dampaknya terhadap perilaku sistem bisa sama besarnya.

### 8.4 Changelog prompt

Setiap folder prompt menyertakan file `CHANGELOG.md` yang mencatat versi prompt (semantic versioning), tanggal perubahan, apa yang berubah, mengapa berubah, dan hasil evaluasi sebelum dan sesudah.

---

## 9. Evaluasi Kualitas Prompt

### 9.1 Mengapa prompt perlu dievaluasi

Mengubah prompt tanpa mengukur dampaknya adalah praktik berbahaya — perubahan kecil bisa mengubah output secara signifikan. Evaluasi kuantitatif memastikan perubahan benar-benar meningkatkan kualitas.

### 9.2 Test cases per agent

Setiap agent memiliki minimal **10 test case** yang mencakup:
- Kasus normal: vendor dengan data lengkap dan jelas
- Kasus edge: vendor dengan data sangat minim
- Kasus negatif: vendor dengan indikasi masalah yang perlu terdeteksi
- Kasus ambiguitas: data yang tidak jelas atau kontradiktif

### 9.3 Metric evaluasi

| Metric | Definisi | Target |
|---|---|---|
| Format compliance | Persentase output yang menghasilkan JSON valid sesuai schema | > 95% |
| Null rate | Persentase field yang di-null saat data sebenarnya tersedia | < 10% |
| Hallucination rate | Persentase output yang mengklaim informasi yang tidak ada di input | < 5% |
| Confidence calibration | Korelasi antara confidence score yang dilaporkan dan akurasi aktual | > 0.7 |

### 9.4 Kapan evaluasi dijalankan

- Sebelum setiap perubahan prompt di-merge ke main branch
- Secara berkala (bulanan) untuk mendeteksi degradasi akibat perubahan model LLM
- Setelah perubahan versi model LLM yang digunakan

---

## 10. Aturan & Larangan

**Dilarang menyertakan data vendor nyata dalam test case** yang masuk ke version control. Test case harus menggunakan data sintetis atau yang sudah dianonimisasi.

**Dilarang hardcode prompt di dalam kode Python.** Semua prompt harus ada dalam file di folder `prompts/`.

**Dilarang mengubah prompt di production** tanpa melalui pull request yang sudah di-review dan lulus evaluasi.

**Dilarang menginstruksikan LLM untuk mengabaikan keterbatasannya.** Prompt tidak boleh berisi instruksi seperti "asumsikan informasi yang tidak ada" atau "jika tidak yakin, pilih tanpa menyebutkan ketidakpastian".

**Dilarang prompt menyertakan informasi sensitif** seperti API key, credential, atau data personal user yang nyata.

**Output naratif harus selalu dalam Bahasa Indonesia** untuk semua field yang akan ditampilkan ke user.

---

## 11. Catatan untuk Dokumen Lanjutan

### Untuk BE-05 (Scoring Engine)

Format JSON output dari tiap agent adalah kontrak antara prompt dan scoring engine. BE-05 harus mengonsumsi data dalam format yang persis sama. Output Qualitative Analyzer dan Preference Matcher perlu diintegrasikan ke dalam reasoning naratif final di BE-05 section 9.

### Untuk SH-03 (Testing Strategy)

Test cases di section 9.2 perlu diintegrasikan ke pipeline CI. Qualitative Analyzer dan Preference Matcher perlu test cases tambahan yang berfokus pada kualitas narasi — apakah klaim spesifik dan terverifikasi, apakah konflik TOPSIS vs preferensi terdeteksi dengan benar.

### Untuk BE-03 (Agent Orchestration)

Orchestrator perlu menangani kasus di mana output agent tidak sesuai format JSON yang diharapkan, termasuk untuk dua agent baru. Preference Matcher memiliki dua user prompt template — Orchestrator yang menentukan template mana yang digunakan berdasarkan ada/tidaknya preferensi.

### Untuk BE-08 (RAG Specification)

Prompt query expansion (section 7.3) digunakan oleh pipeline retrieval RAG. Perubahan pada prompt ini berdampak pada kualitas retrieval dan harus melalui proses evaluasi yang sama dengan prompt agent lain.

---

*Dokumen ini adalah living document — prompt akan terus diiterasi berdasarkan hasil evaluasi dan feedback pengguna.*

---

**Riwayat Perubahan**

| Versi | Tanggal | Perubahan | Author |
|---|---|---|---|
| 1.0.0 | 2026-06-07 | Versi awal — lima agent | — |
| 2.0.0 | 2026-06-11 | Tambah prompt Qualitative Analyzer Agent (5.6) dan Preference Matcher Agent (5.7); perbarui context injection chat panel untuk RAG (6.3); perbarui section 7 dengan prompt query expansion RAG; perbarui struktur folder prompts | — |
