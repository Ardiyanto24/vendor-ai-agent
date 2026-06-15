# Panduan Implementasi — AI Engineer

**Project:** AI Vendor Selection System  
**Role:** AI Engineer  
**Versi:** 2.0.0  
**Tanggal:** 2026-06-13  
**Referensi Utama:** AI-01, AI-02, AI-03, AI-04, AI-05, AI-06, AI-07, MILESTONE_PLAN v6.0.0

---

## Tentang Dokumen Ini

Panduan ini adalah panduan kerja operasional untuk AI Engineer — mencakup **satu repository**: `vendor-ai-agent` (FastAPI, Python). Dokumen ini menjelaskan apa yang perlu dibangun per fitur, pola implementasi yang konsisten, dan hal-hal kritis yang tidak boleh terlewat.

AI Engineer bertanggung jawab atas semua kecerdasan sistem: 7 sub-agent dengan LangGraph orchestration, TOPSIS scoring engine, RAG pipeline (indexing + retrieval), ekstraksi dokumen, dan AI chat streaming via SSE. **Tidak ada kode TypeScript di sini** — semua yang berhubungan dengan HTTP API untuk frontend, autentikasi user, dan CRUD ke Supabase adalah tanggung jawab track Fullstack di `vendor-ai/apps/api`.

Semua task mengacu ke spec resmi. Jika ada konflik antara panduan ini dan dokumen spec, dokumen spec yang berlaku.

---

## Prasyarat Sebelum Memulai

- Python 3.11+ dan `pip` atau `poetry` terinstall
- Repo `vendor-ai-agent` diinisialisasi (dikerjakan di F-00)
- Virtual environment aktif dengan semua dependencies dari `requirements.txt`: fastapi, uvicorn, langchain, langgraph, openai, google-generativeai, tavily-python, supabase, pdfplumber, numpy, scipy, pydantic
- Struktur folder dibuat: `agents/`, `scoring/`, `rag/`, `prompts/`, `tests/`
- File `.env.example` tersedia dengan semua variabel yang dibutuhkan
- `FEATURE_STATUS.md` ada di root `vendor-ai-agent`
- Branch `develop` dibuat dari `main` di repo `vendor-ai-agent`
- Service-to-service token sudah dikoordinasikan dengan track Fullstack

**Environment variables yang wajib ada sebelum F-00 selesai:**

| Variabel | Keterangan |
|---|---|
| `SUPABASE_URL` | URL Supabase project |
| `SUPABASE_SERVICE_ROLE_KEY` | Service role untuk read/write semua tabel |
| `OPENROUTER_API_KEY` | API key OpenRouter untuk LLM calls (DeepSeek-V4-Flash) |
| `GOOGLE_API_KEY` | API key Google untuk embedding (`text-embedding-004`) |
| `TAVILY_API_KEY` | API key Tavily untuk web search di Data Collector |
| `SERVICE_TOKEN` | Service-to-service token (sama dengan yang di apps/api) |
| `ALLOWED_ORIGINS` | CORS origins yang diizinkan (domain frontend) |
| `OPENROUTER_BASE_URL` | `https://openrouter.ai/api/v1` (bisa di-override untuk testing) |

---

## Konvensi Penting

**Prompt adalah file, bukan string:** Semua prompt LLM disimpan sebagai file `.md` di folder `prompts/`. Tidak boleh ada string prompt yang hardcode di kode Python. Saat agent berjalan, load prompt dari file menggunakan helper function.

**Output agent selalu JSON:** Semua agent menghasilkan output JSON terstruktur sesuai schema di AI-02. Output yang tidak sesuai schema dianggap gagal dan di-retry.

**Fallback, bukan crash:** Jika satu agent gagal (error, timeout, schema invalid setelah 3 retry), pipeline tetap lanjut dengan `None` untuk output agent tersebut. Scoring engine harus menangani `None` gracefully sesuai AI-03 section 7.

**Timeout 3 menit per agent:** Setiap agent memiliki timeout 3 menit. Gunakan `asyncio.wait_for` atau equivalent. Jika melewati timeout, agent dianggap gagal.

**Rate limiting update progress:** Tidak lebih dari satu write ke `agent_progress` setiap 3 detik untuk menghindari write burst ke Supabase Realtime (AI-01 section 6.2).

**FastAPI middleware service token:** Semua endpoint FastAPI kecuali `/health` dan `/v1/chat/stream` harus memerlukan header `X-Service-Token`. Middleware ini harus ada sejak F-00.

---

## F-00 — Environment Setup

**Tier:** 0 | **Estimasi:** 2–3 hari (paralel dengan track Fullstack)

### Yang Perlu Dibuat

#### 1. Inisialisasi FastAPI Project

Setup FastAPI dengan uvicorn, konfigurasi environment loading (`python-dotenv`), dan struktur folder dasar: `agents/`, `scoring/`, `rag/`, `prompts/`, `tests/`.

#### 2. GET /health

Health check endpoint. Memeriksa koneksi ke Supabase dan validitas API keys.

Yang diverifikasi: bisa query satu row dari Supabase, `OPENROUTER_API_KEY` valid (ping ringan ke OpenRouter), `GOOGLE_API_KEY` tersedia, `TAVILY_API_KEY` tersedia.

Response: `{ status: "ok", supabase: "ok", openrouter: "ok", google: "ok", tavily: "ok" }`

#### 3. Middleware Service Token

Implementasi middleware FastAPI yang mengecek header `X-Service-Token` di semua request. Endpoint yang dikecualikan: `/health` dan `/v1/chat/stream` (diakses langsung dari browser dengan JWT user).

Request tanpa token valid → 401 Unauthorized.

#### 4. Struktur Folder Prompts

Buat struktur folder `prompts/` sesuai AI-02 section 8.2 dengan file placeholder kosong:

```
vendor-ai-agent/prompts/
├── agents/
│   ├── data_collector/         (system.md, user_template.md)
│   ├── financial_analyzer/     (system.md, user_template.md)
│   ├── risk_assessor/          (system.md, user_template.md)
│   ├── performance_scorer/     (system.md, user_template.md)
│   ├── negotiation_assistant/  (system.md, user_template.md)
│   ├── qualitative_analyzer/   (system.md, user_template.md)
│   └── preference_matcher/     (system.md, user_template_neutral.md, user_template_opinionated.md)
├── chat_panel/                 (base_system.md, context_*.md per halaman)
├── ekstraksi_dokumen/          (system.md, user_template.md)
└── rag/                        (query_expansion.md)
```

#### 5. .env.example

Buat file `.env.example` di root `vendor-ai-agent` dengan semua variabel yang dibutuhkan beserta komentar penjelasannya.

### Kriteria Selesai F-00 [AI]

```
□ GET /health mengembalikan 200 dengan status semua dependency
□ Middleware memblokir request tanpa X-Service-Token (kecuali /health dan /v1/chat/stream)
□ Struktur folder prompts/ ada dengan placeholder file
□ requirements.txt berisi semua dependencies yang dibutuhkan
□ .env.example di root vendor-ai-agent terisi semua variabel
□ FEATURE_STATUS.md ada di root vendor-ai-agent
□ FastAPI bisa dijalankan lokal dengan uvicorn tanpa error
```

---

## F-07 — Upload Dokumen & Ekstraksi

**Tier:** 2 | **Prerequisite:** F-00 | **Estimasi:** 3–4 hari

### Yang Perlu Dibuat (FastAPI)

#### POST /v1/agent/ekstrak-dokumen

Dipanggil oleh Next.js (`apps/api`) setelah file berhasil di-upload ke Supabase Storage. Endpoint ini memicu dua pipeline yang berjalan paralel.

**Pipeline A — Ekstraksi field terstruktur:**
1. Unduh file dari Supabase Storage URL yang diterima di payload
2. Ekstrak teks: PDF menggunakan `pdfplumber`, Excel menggunakan `openpyxl` atau `pandas`
3. Kirim konten ke LLM dengan prompt dari `prompts/ekstraksi_dokumen/system.md` dan `user_template.md`
4. Parse output JSON: nama perusahaan, harga penawaran, kontak, spesifikasi, garansi, payment terms, dengan `confidence` per field
5. Update tabel `dokumen_upload`: set `hasil_ekstraksi`, `confidence_score`, `status_ekstraksi = 'done'`

**Pipeline B — RAG Indexing (berjalan paralel dengan Pipeline A):**
1. Dari teks yang sudah diekstrak, jalankan chunking hierarkis sesuai AI-05 section 7
2. Batch embed semua child chunks via Google Gemini `text-embedding-004` API (`GOOGLE_API_KEY`)
3. Bulk insert ke tabel `dokumen_chunk` (child + parent chunks, kolom `embedding vector(768)`)
4. Setelah selesai: update `indexing_rag_status = 'done'`, `chunk_count`

**Koordinasi dua pipeline:** Status `dokumen_upload.status_ekstraksi = 'done'` hanya diset setelah **kedua pipeline** selesai. Jika Pipeline A berhasil tapi Pipeline B gagal: set `status_ekstraksi = 'done_partial'`.

Setiap pipeline memiliki retry 2x dengan exponential backoff untuk error transient.

**Confidence score < 0.7:** Field yang confidence-nya di bawah threshold ini tetap disimpan tetapi ditandai dalam metadata agar frontend bisa menampilkan indikator "perlu verifikasi".

### Kriteria Selesai F-07 [AI]

```
□ POST /v1/agent/ekstrak-dokumen mengembalikan 202 segera (async)
□ Teks berhasil diekstrak dari PDF dan Excel
□ Output LLM di-parse sebagai JSON terstruktur
□ hasil_ekstraksi dan confidence_score tersimpan di tabel dokumen_upload
□ Chunks RAG tersimpan di tabel dokumen_chunk (verifikasi count > 0)
□ Kegagalan Pipeline B menghasilkan status 'done_partial', tidak 'failed'
□ Field dengan confidence < 0.7 ditandai dalam metadata
```

---

## F-10 — AI Processing & Progress Real-time (P-04)

**Tier:** 3 | **Prerequisite:** F-07, Checkpoint Tier 1–2 | **Estimasi:** 8–12 hari (milestone terpanjang)

Baca AI-01 (Agent Orchestration) dan AI-02 (Prompt Library) secara menyeluruh sebelum mulai.

### Yang Perlu Dibuat (FastAPI)

#### 1. Setup LangGraph dengan 7 Node Agent

Buat graph LangGraph yang merepresentasikan dependency pipeline dari AI-01 section 5.1:

```
DC → FA/RA/PS paralel → NA/QA paralel → PM terakhir
```

Dependency yang lebih spesifik:
- DC, FA, RA berjalan paralel saat pipeline dimulai
- PS menunggu DC selesai (tetapi berjalan bersamaan dengan FA dan RA)
- NA dan QA berjalan paralel setelah PS selesai
- PM berjalan setelah NA dan QA keduanya selesai

Definisikan typed state LangGraph yang mengalir di antara node — berisi output semua agent yang sudah selesai dan metadata evaluasi.

#### 2. Orchestrator — Inisialisasi Progress

Sebelum agent satu pun berjalan, Orchestrator menulis 7 row ke `agent_progress` dengan status `idle`. Ini penting agar frontend bisa menampilkan semua agent segera saat P-04 dibuka.

Gunakan UPSERT dengan `ON CONFLICT (evaluasi_id, agent_key) DO UPDATE` agar idempotent.

#### 3. Tulis 5 Prompt Agent Pertama

Tulis prompt ke file sesuai format dan output JSON dari AI-02 section 5.1 s/d 5.5:

**DC Agent** — output JSON: `tahun_berdiri`, `ukuran_perusahaan`, `sertifikasi`, `berita_terkini`, `temuan_negatif`, `confidence_overall`. Gunakan Tavily API untuk web search (max 4 query per vendor) sebelum memanggil LLM.

**FA Agent** — output JSON: `skor_finansial`, `posisi_harga` (enum), `estimasi_tco`, `perbandingan_pasar_tersedia`, `catatan_finansial`.

**RA Agent** — output JSON: `skor_risiko` (0–100, di mana 100 = risiko sangat rendah), `level_risiko` (enum), `faktor_risiko`, `hal_yang_perlu_diklarifikasi`, `disclaimer`, `catatan_risiko`.

**PS Agent** — output JSON: `skor_performa`, `kesesuaian_spesifikasi` (enum), `kekuatan`, `kelemahan`, `skor_garansi_support`, `catatan_performa`.

**NA Agent** — output JSON: `vendor_rekomendasi_negosiasi`, `alasan_dipilih`, `poin_negosiasi` (array dengan `aspek`, `kondisi_saat_ini`, `target_negosiasi`, `alasan`, `prioritas`), `risiko_sebelum_kontrak`, `rekomendasi_naratif`.

#### 4. Implementasi 5 Agent Pertama

Pola yang sama untuk setiap agent:

```python
# Pseudocode pola agent
def run_agent(agent_key, payload, evaluasi_id):
    update_progress(evaluasi_id, agent_key, 'running', 0, "Memulai analisis...")
    
    prompt = load_prompt(f'prompts/agents/{agent_key}/system.md')
    user_template = load_prompt(f'prompts/agents/{agent_key}/user_template.md')
    user_content = fill_template(user_template, payload)
    
    # OpenAI SDK dengan base_url override ke OpenRouter
    client = OpenAI(
        base_url=os.environ["OPENROUTER_BASE_URL"],  # https://openrouter.ai/api/v1
        api_key=os.environ["OPENROUTER_API_KEY"]
    )
    
    for attempt in range(3):  # 2 retry = 3 total attempts
        try:
            update_progress(evaluasi_id, agent_key, 'running', 25, "Mengumpulkan data...")
            response = client.chat.completions.create(
                model='deepseek/deepseek-v4-flash',  # verifikasi model string di dashboard OpenRouter
                messages=[
                    {'role': 'system', 'content': prompt},
                    {'role': 'user', 'content': user_content}
                ],
                max_tokens=2000
            )
            
            output = parse_json_strict(response.choices[0].message.content)
            validate_schema(output, agent_key)  # raise jika tidak sesuai
            
            update_progress(evaluasi_id, agent_key, 'done', 100, "Selesai")
            return output
            
        except (JSONDecodeError, ValidationError, OpenAIError) as e:
            if attempt < 2:
                time.sleep(5 * (2 ** attempt))  # exponential backoff: 5s, 10s
                continue
            update_progress(evaluasi_id, agent_key, 'error', 0, str(e))
            return None  # pipeline tetap lanjut
```

Update progress di milestone bermakna (0%, 25%, 50%, 75%, 100%). Tidak lebih dari satu update per 3 detik. `pesan_terakhir` dalam Bahasa Indonesia dan deskriptif.

#### 5. Endpoint POST /v1/agent/evaluasi/:id/start

Dipanggil oleh track Fullstack (`apps/api`) setelah submit evaluasi.

Input: payload evaluasi lengkap termasuk `preferensi_perusahaan` (nullable).  
Proses: jalankan LangGraph pipeline sebagai background task.  
Response: 202 Accepted langsung.

**Circuit breaker:** Jika OpenRouter API gagal 3 kali berturut-turut, set semua agent yang belum selesai ke `error` dan hentikan pipeline.

### Kriteria Selesai F-10 [AI]

```
□ DC, FA, RA berjalan paralel (verifikasi dari timestamp log)
□ PS mulai setelah DC selesai (bukan setelah FA atau RA)
□ NA dan QA berjalan paralel setelah PS selesai
□ PM berjalan terakhir setelah NA DAN QA keduanya selesai
□ Progress tiap agent ter-update di tabel agent_progress
□ Satu agent gagal: evaluasi tetap selesai dengan flag di agent tersebut
□ Agent melewati 3 menit: dianggap gagal, pipeline lanjut
□ Semua prompt tersimpan sebagai file di folder prompts/ (tidak hardcoded)
□ Unit test semua 5 agent (DC, FA, RA, PS, NA) dengan LLM mock lulus
```

---

## F-11 — Hasil TOPSIS & Reasoning (P-05 Bagian 1–2–6)

**Tier:** 3 | **Prerequisite:** F-10 | **Estimasi:** 5–7 hari

Baca AI-03 (Scoring Engine) secara menyeluruh sebelum mulai.

### Yang Perlu Dibuat (FastAPI)

#### 1. Scoring Engine — 6 Tahap TOPSIS

Kode Python murni tanpa LLM. Gunakan `numpy` dan `scipy`.

**Tahap 1 — Normalisasi output agent ke skala 0–100:**

Petakan output agent ke 5 kriteria scoring sesuai AI-03 section 6.1:
- `harga_tco` ← `FA.skor_finansial`
- `kualitas_track_record` ← `PS.skor_performa`
- `kemampuan_delivery` ← `PS.kesesuaian_spesifikasi` (konversi enum → angka sesuai AI-03 section 6.3) + `PS.skor_garansi_support`
- `risiko_legalitas` ← `RA.skor_risiko`
- `support_aftersales` ← `PS.skor_garansi_support` + `DC.sertifikasi`

Jika agent gagal (output `None`), terapkan fallback sesuai AI-03 section 7.

**Tahap 2 — Decision matrix:** Matrix baris = vendor, kolom = 5 kriteria.

**Tahap 3 — Vector normalization:** `r_ij = x_ij / sqrt(sum(x_kj^2))`

**Tahap 4 — Weighted normalized matrix:** Kalikan dengan bobot dari konfigurasi (total bobot = 1.0).

**Tahap 5 — Solusi ideal:** A+ = max per kolom, A- = min per kolom.

**Tahap 6 — Skor final:** `D+ = ||v - A+||`, `D- = ||v - A-||`, `skor = D- / (D+ + D-)` × 100. Rank dari tertinggi ke terendah.

Input yang sama harus selalu menghasilkan output yang sama (deterministik).

#### 2. Threshold Minimum

Setelah skor TOPSIS dihitung, tandai vendor yang tidak memenuhi threshold minimum di satu atau lebih kriteria dengan `lolos_threshold = false`. Vendor tetap muncul di ranking dengan skor TOPSIS-nya.

#### 3. Reasoning Naratif via LLM

Setelah skor terbentuk (urutan ini penting — skor dulu, baru reasoning), panggil LLM untuk tiga field dalam Bahasa Indonesia:
- `reasoning_utama` — mengapa vendor rank 1 direkomendasikan
- `kelemahan_utama` — aspek yang perlu diwaspadai
- `rekomendasi_negosiasi` — ringkasan dari Negotiation Assistant

Input ke LLM: skor final, skor per kriteria, bobot, catatan agent, flag data tidak lengkap.

#### 4. Tulis ke Database — Satu Transaksi Atomik

Tabel `hasil_evaluasi`: satu row dengan semua field sesuai DB-01, termasuk `konfigurasi_snapshot`.  
Tabel `hasil_vendor`: satu row per vendor.  
Update `evaluasi.status = 'selesai'`.

Jika transaksi gagal: batalkan semua, status evaluasi tetap `processing`, log error.

Jalankan validasi sanity check sebelum menulis (AI-03 section 12): skor dalam 0–100, rank 1 > rank 2, tidak ada skor identik.

#### 5. GET /v1/scoring/evaluasi/:id/hasil

Kembalikan hasil evaluasi lengkap dari database. Dipanggil oleh track Fullstack (Next.js `apps/api`).

### Kriteria Selesai F-11 [AI]

```
□ Ranking vendor benar (diverifikasi manual dengan kalkulator TOPSIS independen)
□ Threshold diterapkan setelah TOPSIS (vendor tidak lolos: lolos_threshold=false)
□ Reasoning naratif dalam Bahasa Indonesia
□ Hasil ditulis dalam satu transaksi atomik
□ Unit test semua 6 tahap TOPSIS dengan nilai terverifikasi manual lulus
□ Skenario data tidak lengkap (agent gagal): fallback benar, tidak crash
□ Biaya token per evaluasi dicatat ke database
```

---

## F-12 — Profil Kualitatif (P-05 Bagian 3–4)

**Tier:** 3 | **Prerequisite:** F-10, F-11 | **Estimasi:** 3–4 hari

Baca AI-06 (Qualitative Analyzer Agent) secara menyeluruh sebelum mulai.

### Yang Perlu Dibuat (FastAPI)

#### 1. Tulis Prompt Qualitative Analyzer Agent

Buat `prompts/agents/qualitative_analyzer/system.md` dan `user_template.md`.

**System prompt** — inti: agent mengidentifikasi unique offerings yang spesifik dan terverifikasi dari dokumen penawaran. Tidak boleh mengarang. Tidak menghasilkan skor numerik.

**User template** — sertakan: RAG context dari dokumen penawaran (query "unique offerings layanan khusus diferensiasi"), output Performance Scorer field `kekuatan`, output Data Collector field `sertifikasi`.

Format output JSON sesuai AI-02 section 5.6:
```json
{
  "analisis_per_vendor": [
    {
      "vendor_id": "...",
      "unique_offerings": [{"deskripsi": "...", "relevansi": "...", "sumber": "..."}],
      "profil_kualitatif": "...",
      "potensi_tie_breaker": true,
      "catatan_tie_breaker": "..."
    }
  ],
  "summary_komparatif": "..."
}
```

#### 2. Implementasi Qualitative Analyzer Agent

Tambahkan QA sebagai node LangGraph yang berjalan paralel dengan NA setelah PS selesai.

Sebelum memanggil LLM, jalankan retrieval RAG untuk setiap vendor. Untuk F-12, jika `POST /v1/rag/query` belum tersedia, jalankan QA tanpa RAG context (degradasi yang diterima).

Fallback jika QA gagal: set `profil_kualitatif = null` dan `unique_offerings = []` per vendor. Pipeline tetap lanjut.

#### 3. Update Scoring Engine

Scoring Engine menerima output QA dan menyertakannya ke kolom `profil_kualitatif`, `unique_offerings` di `hasil_vendor`, dan `summary_komparatif_kualitatif` di `hasil_evaluasi`.

### Kriteria Selesai F-12 [AI]

```
□ QA berjalan paralel dengan NA setelah PS selesai (verifikasi timestamp log)
□ QA menghasilkan unique_offerings dan profil_kualitatif per vendor
□ Output QA tersimpan ke hasil_vendor dan hasil_evaluasi
□ Kegagalan QA: pipeline tetap selesai, kolom kualitatif null
□ Unit test QA dengan LLM mock lulus
```

---

## F-13 — Rekomendasi Preferensi & Conflict Callout (P-05 Bagian 5)

**Tier:** 3 | **Prerequisite:** F-08 (preferensi tersimpan di DB), F-12 | **Estimasi:** 3–4 hari

Baca AI-07 (Preference Matcher Agent) secara menyeluruh sebelum mulai.

### Yang Perlu Dibuat (FastAPI)

#### 1. Tulis Prompt Preference Matcher Agent

Buat tiga file:
- `prompts/agents/preference_matcher/system.md` — inti: agent mencocokkan profil vendor dengan preferensi bisnis secara transparan, jujur tentang trade-off. Preferensi adalah lensa tambahan, bukan pengganti evaluasi objektif.
- `prompts/agents/preference_matcher/user_template_neutral.md` — tidak ada preferensi; hasilkan framing netral.
- `prompts/agents/preference_matcher/user_template_opinionated.md` — sertakan: teks preferensi, rangkuman semua agent, output QA. Hasilkan rekomendasi 1–3 vendor.

Format output JSON sesuai AI-02 section 5.7 — termasuk `ada_konflik_topsis` (boolean) dan `catatan_konflik`.

#### 2. Implementasi Preference Matcher Agent

Node LangGraph terakhir — berjalan setelah QA selesai.

Logika pemilihan template: `preferensi_perusahaan is null` → gunakan neutral template. Tidak null → gunakan opinionated template.

Output PM ditulis ke:
- `preference_matching_result` (JSONB) di `hasil_evaluasi`
- `tingkat_kesesuaian_preferensi` per vendor di `hasil_vendor`
- `conflict_callout` di `hasil_evaluasi` (jika `ada_konflik_topsis = true`)

**PM tidak boleh mengubah skor TOPSIS** — ini adalah larangan tegas di AI-03 section 13 dan AI-01 section 11.

Format conflict callout:
```json
{
  "ada_konflik": true,
  "vendor_topsis_terbaik": "vendor_id",
  "vendor_preferensi_terbaik": "vendor_id",
  "narasi_konflik": "..."
}
```

Field `narasi_pengantar` dari output PM digunakan sebagai Bagian 1 P-05 — pastikan tersimpan dalam `preference_matching_result` JSONB.

### Kriteria Selesai F-13 [AI]

```
□ PM berjalan terakhir setelah NA dan QA keduanya selesai
□ Mode netral: PM menghasilkan output tanpa rekomendasi berbasis preferensi
□ Mode opinionated: PM menghasilkan rekomendasi 1–3 vendor
□ Konflik terdeteksi: vendor preferensi tinggi + TOPSIS rendah → conflict_callout terisi
□ PM tidak mengubah skor TOPSIS (verifikasi dari unit test)
□ preference_matching_result tersimpan sebagai JSONB
□ tingkat_kesesuaian_preferensi tersimpan per vendor
□ Unit test: mode netral vs opinionated output berbeda, konflik terdeteksi
```

---

## F-14 — AI Chat Panel + RAG

**Tier:** 3 | **Prerequisite:** F-07 (dokumen terindeks), F-11 | **Estimasi:** 3–4 hari

Baca AI-05 (RAG Specification) dan AI-02 section 6 secara menyeluruh sebelum mulai.

### Yang Perlu Dibuat (FastAPI)

#### 1. Tulis Prompt AI Chat Panel

Buat file di `prompts/chat_panel/`:
- `base_system.md` — persona: asisten procurement yang berbicara Bahasa Indonesia, jujur tentang keterbatasan, tidak membuat keputusan atas nama user.
- `context_dashboard.md`, `context_processing.md`, `context_hasil.md`, `context_buat_evaluasi.md`, `context_approval.md` — konteks per halaman.

`context_hasil.md` adalah yang paling kaya — termasuk slot untuk RAG context.

Batasan yang wajib ada di `base_system.md` (AI-02 section 6.4): AI tidak membuat keputusan final, AI mengakui keterbatasan informasinya, AI tidak mengungkapkan detail teknis internal.

#### 2. POST /v1/rag/query (Endpoint Internal)

Dipanggil oleh chat endpoint dan oleh Qualitative Analyzer Agent.

Input: `{ evaluasiId, query, maxChunks?: int (default 5) }`

Proses hybrid search sesuai AI-05 section 8.2:
```
1. Query expansion via LLM (timeout 3 detik — fallback ke query asli jika gagal)
   Prompt: prompts/rag/query_expansion.md
   Gunakan model yang sama (DeepSeek-V4-Flash via OpenRouter) — call ringan

2. Embed expanded query via Google Gemini text-embedding-004 (GOOGLE_API_KEY)
   → menghasilkan vektor 768 dimensi

3. Vector similarity search di dokumen_chunk
   WHERE evaluasi_id = $evaluasiId
   ORDER BY embedding <=> $queryVector LIMIT 20  -- queryVector dimensi 768

4. Full-text search di dokumen_chunk
   WHERE evaluasi_id = $evaluasiId
   AND teks_chunk @@ plainto_tsquery('indonesian', $expandedQuery) LIMIT 20

5. Gabungkan dengan RRF (k=60): score = sum(1 / (60 + rank))
   Ambil top-5 child chunk

6. Ambil parent chunk untuk setiap child (deduplikasi per parent)

7. Return: parent chunks dengan metadata (vendor_id, halaman, posisi_section, nama_vendor)
```

Filter `evaluasi_id` **wajib selalu ada** — tidak boleh ada retrieval lintas evaluasi.

#### 3. POST /v1/chat/stream — SSE Endpoint

Satu-satunya FastAPI endpoint yang diakses langsung dari browser (bukan via Next.js).

**Auth:** Validasi JWT user (bukan service token).  
**Rate limiting:** 20 request per menit per user (BE-03 section 6.2).  
**Input:** `{ pesan, konteksHalaman, evaluasiId?, riwayatChat: [...] }` — riwayat maks 10 pesan.

Proses:
1. Jika `konteksHalaman = 'hasil'` dan `evaluasiId` ada: panggil `POST /v1/rag/query` untuk RAG context
2. Bangun system prompt: `base_system.md` + context halaman + RAG context
3. Panggil OpenRouter API dalam mode streaming (`stream=True` via OpenAI SDK)
4. Stream token ke client dalam format SSE: `{"type": "token", "content": "..."}`, `{"type": "done", "usage": {...}}`, `{"type": "error", "message": "..."}`

Response headers wajib: `Content-Type: text/event-stream`, `Cache-Control: no-cache`, `Connection: keep-alive`, `Access-Control-Allow-Origin: [origin frontend dari ALLOWED_ORIGINS]`

Kegagalan RAG tidak boleh memblokir chat — lanjutkan tanpa context dokumen.

#### 4. Tulis Prompt Query Expansion

Buat `prompts/rag/query_expansion.md` — instruksi untuk merewrite pertanyaan user menjadi query yang lebih kaya. Gunakan model yang sama (DeepSeek-V4-Flash via OpenRouter) — call ini ringan dan cepat.

### Kriteria Selesai F-14 [AI]

```
□ POST /v1/chat/stream: koneksi terbuka dan token muncul bertahap
□ Context halaman berbeda menghasilkan opening message AI yang berbeda
□ RAG retrieval mengembalikan chunks relevan dari dokumen yang sudah diindex
□ Kegagalan RAG tidak memblokir chat (fallback ke context tanpa dokumen)
□ Rate limit 20 request/menit per user berfungsi
□ CORS: hanya origin dari ALLOWED_ORIGINS yang diizinkan
□ Event 'done' menyertakan usage token
□ Unit test: SSE streaming format benar, RAG context disertakan saat halaman 'hasil'
```

---

## Checkpoint Final — Release Readiness

### Verifikasi Pipeline AI End-to-End

```
□ Submit evaluasi dengan 3 vendor → semua 7 agent selesai → hasil TOPSIS tersedia
□ Agent DC berhasil menggunakan Tavily API (verifikasi dari log: ada web search call)
□ Output semua agent valid JSON sesuai schema (verifikasi dari test cases AI-02 section 9)
□ Evaluasi dengan 1 agent gagal: evaluasi tetap selesai dengan flag ada_data_tidak_lengkap
□ Scoring TOPSIS menghasilkan ranking yang masuk akal untuk data input yang diketahui
□ Reasoning naratif dalam Bahasa Indonesia dan spesifik terhadap vendor (bukan generik)
```

### Verifikasi Biaya dan Monitoring

```
□ Spending alert OpenRouter API terkonfigurasi
□ Spending alert Tavily API terkonfigurasi
□ Spending alert Google Gemini Embedding API terkonfigurasi
□ Token usage per evaluasi dicatat ke database
```

### Checklist Final [AI]

```
□ Prompt evaluation metric: format compliance >95%, hallucination <5% (dari 10 test case)
□ Semua prompt tersimpan sebagai file (tidak ada hardcode di Python)
□ Unit test semua 7 agent dengan LLM mock lulus
□ Unit test scoring engine semua 6 tahap TOPSIS dengan nilai terverifikasi lulus
□ FastAPI berjalan di belakang reverse proxy dengan TLS termination di production
□ Pipeline CI vendor-ai-agent hijau (pytest, lint)
```

---

## Referensi Cepat — FastAPI Endpoints per Fitur

| Fitur | FastAPI Endpoint | Dipanggil oleh |
|---|---|---|
| F-00 | GET /health | Tim (verifikasi setup) |
| F-07 | POST /v1/agent/ekstrak-dokumen | Fullstack (apps/api) |
| F-10 | POST /v1/agent/evaluasi/:id/start | Fullstack (apps/api) |
| F-11 | GET /v1/scoring/evaluasi/:id/hasil | Fullstack (apps/api) |
| F-14 | POST /v1/rag/query | Internal (chat + QA agent) |
| F-14 | POST /v1/chat/stream | Browser (langsung, bukan via Next.js) |

---

## Referensi Cepat — Dokumen Spec per Domain

| Domain | Dokumen Spec |
|---|---|
| Agent orchestration & dependency graph | AI-01 |
| Semua prompt & output schema | AI-02 |
| TOPSIS scoring engine | AI-03 |
| Integrasi Tavily, OpenRouter, Google Gemini | AI-04 |
| RAG pipeline (chunking, embedding, hybrid search) | AI-05 |
| Qualitative Analyzer Agent | AI-06 |
| Preference Matcher Agent | AI-07 |
| API contract (endpoint shape yang dipanggil dari Next.js) | BE-02 |
| Auth & Security (rate limiting, JWT) | BE-03 |

---

*Dokumen ini adalah panduan kerja operasional yang harus selalu sinkron dengan spesifikasi di AI-01 s/d AI-07. Jika ada perubahan spec, panduan ini perlu diperbarui sebelum task implementasi dimulai.*

---

**Riwayat Perubahan**

| Versi | Tanggal | Perubahan | Author |
|---|---|---|---|
| 1.0.0 | 2026-06-12 | Versi awal — dibuat dari pemecahan GUIDE_BACKEND_ENGINEER v3.0.0 sesuai ADR-032 (4 role developer) | — |
| 2.0.0 | 2026-06-13 | Ganti LLM dari Anthropic SDK (claude-sonnet-4-6) ke OpenAI SDK + OpenRouter (deepseek/deepseek-v4-flash); ganti embedding dari OpenAI text-embedding-3-small ke Google Gemini text-embedding-004; perbarui env vars, health check, dependencies, pseudocode agent, Pipeline B RAG, RAG query endpoint, SSE chat endpoint, checklist monitoring, dan referensi dokumen | — |
| 3.0.0 | 2026-06-13 | Adopsi ADR-035 (namespace AI) dan ADR-036 (2 track solo developer): perbarui header Referensi Utama (BE-03/04/05/07/08/09/10 → AI-01/02/03/04/05/06/07); perbarui semua referensi inline di konvensi, F-00, F-07, F-10, F-11, F-12, F-13, F-14; ganti "Backend Engineer" → "track Fullstack" di semua konteks; perbarui tabel endpoint dan tabel referensi cepat dokumen; tambah BE-03 (Auth & Security) di tabel referensi; perbarui kalimat penutup | — |
