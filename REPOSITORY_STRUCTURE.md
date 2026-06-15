# Struktur Repository — AI Vendor Selection System

**Project:** AI Vendor Selection System  
**Dokumen:** Repository Structure  
**Versi:** 2.0.0  
**Tanggal:** 2026-06-12  
**Referensi:** ADR-031, ADR-032, FE-01 v2.0.0, SH-02 v3.0.0

---

Project ini menggunakan **2-repo** sesuai ADR-031: satu monorepo TypeScript untuk frontend dan BFF, satu repository terpisah untuk FastAPI agent service.

---

## Repository 1 — `vendor-ai`

Monorepo TypeScript yang dikelola dengan **pnpm workspaces**. Berisi frontend (Next.js), API Routes (BFF layer), shared types, konfigurasi Supabase, dan spesifikasi proyek.

```
vendor-ai/
│
├── apps/
│   │
│   ├── web/                          ← Next.js 14 (App Router) — Frontend
│   │   ├── app/                      ← Routing App Router
│   │   │   ├── (auth)/               ← Route group — semua halaman yang butuh auth
│   │   │   │   ├── dashboard/        ← P-02 Dashboard
│   │   │   │   ├── evaluasi/
│   │   │   │   │   ├── baru/         ← P-03 Buat Evaluasi (stepper 3 langkah)
│   │   │   │   │   └── [id]/
│   │   │   │   │       ├── proses/   ← P-04 AI Processing & Progress
│   │   │   │   │       └── hasil/    ← P-05 Hasil Evaluasi
│   │   │   │   ├── riwayat/          ← P-06 Riwayat Evaluasi
│   │   │   │   ├── approval/         ← P-07 Approval (Manager only)
│   │   │   │   └── settings/
│   │   │   │       └── kriteria/     ← P-08 Konfigurasi Bobot Kriteria (Manager only)
│   │   │   ├── login/                ← P-01 Halaman Login
│   │   │   └── layout.tsx            ← Root layout
│   │   │
│   │   ├── components/
│   │   │   ├── atomic/               ← Komponen dasar: StatusBadge, ScoreBar, RankBadge, dll.
│   │   │   ├── composite/            ← Komponen gabungan: VendorInputCard, EvaluasiRow, dll.
│   │   │   ├── layout/               ← AppShell, Sidebar, AIPanel
│   │   │   ├── feature/              ← Komponen domain: AgentProgressPanel, VendorRankingTable, dll.
│   │   │   └── charts/               ← CriteriaBarChart dan visualisasi lainnya
│   │   │
│   │   ├── hooks/                    ← Custom React hooks: useEvaluasi, useAgentProgress, useAIChat
│   │   │
│   │   ├── stores/                   ← Zustand global stores: authStore, chatStore, notificationStore
│   │   │
│   │   ├── lib/
│   │   │   ├── api/                  ← Base fetch wrapper dengan auth injection
│   │   │   ├── supabase/             ← Supabase client setup (browser + server)
│   │   │   ├── validations/          ← Zod schemas untuk form validation
│   │   │   └── constants/            ← Error messages, enums, konstanta aplikasi
│   │   │
│   │   ├── public/                   ← Static assets (icons, images)
│   │   │
│   │   ├── test/
│   │   │   └── handlers/             ← MSW mock handlers per domain (auth, evaluasi, vendor, dll.)
│   │   │
│   │   └── middleware.ts             ← Auth guard dan role-based redirect
│   │
│   └── api/                          ← Next.js 14 (App Router) — BFF / API Routes
│       └── app/
│           └── api/
│               └── v1/               ← Semua route handlers di sini
│                   ├── auth/         ← login, logout, refresh
│                   ├── users/        ← /me
│                   ├── evaluasi/     ← CRUD evaluasi, vendor, submit, approval
│                   ├── konfigurasi/  ← Bobot kriteria per kategori
│                   └── kategori/     ← Daftar kategori pengadaan
│
├── packages/
│   └── types/                        ← Shared TypeScript types — dipakai apps/web & apps/api
│                                     ← Berisi: API response types, entity types, enum definitions
│
├── supabase/                         ← Supabase CLI project root
│   ├── migrations/                   ← Semua migration SQL (13 file, urutan deterministik)
│   └── seed.sql                      ← Seed data konfigurasi kriteria default
│
├── docs/                             ← Seluruh dokumen spesifikasi proyek (30 spec + guides)
│   ├── SH-01_decision_log.md
│   ├── SH-02_deployment_runbook.md
│   ├── SH-03_testing_strategy.md
│   ├── SH-04_cost_usage_guide.md
│   ├── BE-01_system_architecture.md
│   ├── BE-02_api_contract.md
│   ├── BE-03_auth_security.md
│   ├── BE-04_integration_spec_fullstack.md
│   ├── FE-01_ui_architecture.md
│   ├── FE-02_component_library.md
│   ├── FE-03_page_and_user_flow.md
│   ├── FE-04_state_management.md
│   ├── FE-05_api_integration.md
│   ├── FE-06_testing_qa_frontend.md
│   ├── DB-01_data_model.md
│   ├── DB-02_migration_strategy.md
│   ├── DB-03_query_performance.md
│   ├── DB-04_backup_retention.md
│   ├── AI-01_agent_orchestration.md
│   ├── AI-02_prompt_library.md
│   ├── AI-03_scoring_engine.md
│   ├── AI-04_integration_spec.md
│   ├── AI-05_rag_specification.md
│   ├── AI-06_qualitative_analyzer_agent.md
│   ├── AI-07_preference_matcher_agent.md
│   ├── MILESTONE_PLAN.md
│   ├── GUIDE_FULLSTACK.md
│   ├── GUIDE_BACKEND_ENGINEER.md
│   ├── GUIDE_FRONTEND_ENGINEER.md
│   ├── GUIDE_DATABASE_ENGINEER.md
│   └── GUIDE_AI_ENGINEER.md
│
├── .github/
│   └── workflows/                    ← GitHub Actions CI/CD (type check, lint, build, test)
│
├── CODEOWNERS                        ← apps/web dan apps/api → Fullstack Engineer
├── FEATURE_STATUS.md                 ← Tracking status fitur lintas role
├── pnpm-workspace.yaml               ← Workspace config: apps/*, packages/*
└── package.json                      ← Root workspace scripts dan devDependencies
```

---

## Repository 2 — `vendor-ai-agent`

Repository Python untuk FastAPI service. Berisi semua kecerdasan sistem: AI agent orchestration, TOPSIS scoring engine, RAG pipeline, dan SSE chat streaming.

```
vendor-ai-agent/
│
├── agents/                           ← Implementasi 7 sub-agent (LangGraph nodes)
│   ├── data_collector/               ← DC: web search via Tavily, profil publik vendor
│   ├── financial_analyzer/           ← FA: analisis harga, TCO, kewajaran penawaran
│   ├── risk_assessor/                ← RA: risiko legalitas dan stabilitas bisnis
│   ├── performance_scorer/           ← PS: kemampuan teknis, track record, delivery
│   ├── negotiation_assistant/        ← NA: strategi negosiasi dan posisi tawar
│   ├── qualitative_analyzer/         ← QA: nilai tambah unik, tie-breaker kualitatif
│   └── preference_matcher/           ← PM: pencocokan preferensi bisnis perusahaan
│
├── scoring/                          ← TOPSIS scoring engine
│                                     ← Normalisasi, pembobotan, ideal solution, ranking
│
├── rag/                              ← RAG pipeline
│   ├── indexing/                     ← Ekstraksi teks, chunking, embedding, simpan ke pgvector
│   └── retrieval/                    ← Hybrid search (vector + BM25), RRF reranking
│
├── prompts/                          ← Semua prompt LLM disimpan sebagai file .md
│   ├── agents/
│   │   ├── data_collector/           ← system.md, user_template.md
│   │   ├── financial_analyzer/       ← system.md, user_template.md
│   │   ├── risk_assessor/            ← system.md, user_template.md
│   │   ├── performance_scorer/       ← system.md, user_template.md
│   │   ├── negotiation_assistant/    ← system.md, user_template.md
│   │   ├── qualitative_analyzer/     ← system.md, user_template.md
│   │   └── preference_matcher/       ← system.md, user_template_neutral.md, user_template_opinionated.md
│   ├── chat_panel/                   ← base_system.md, context_*.md per halaman
│   ├── ekstraksi_dokumen/            ← system.md, user_template.md
│   └── rag/                          ← query_expansion.md
│
├── tests/                            ← Test suite FastAPI
│   ├── agents/                       ← Unit test per agent dengan LLM mock
│   ├── scoring/                      ← Unit test TOPSIS (6 tahap terverifikasi)
│   ├── rag/                          ← Test indexing dan retrieval
│   └── integration/                  ← End-to-end pipeline test
│
├── .github/
│   └── workflows/                    ← GitHub Actions CI/CD (pytest, lint)
│
├── FEATURE_STATUS.md                 ← Tracking status fitur (khusus FastAPI side)
├── requirements.txt                  ← Dependencies Python
└── .env.example                      ← Template environment variables
```

---

## Ringkasan Kepemilikan

| Folder / File | Dikerjakan oleh |
|---|---|
| `apps/web/` | Fullstack Engineer |
| `apps/api/` | Fullstack Engineer |
| `packages/types/` | Fullstack Engineer |
| `supabase/migrations/` | Fullstack Engineer |
| `supabase/seed.sql` | Fullstack Engineer |
| `CODEOWNERS`, `pnpm-workspace.yaml` | Fullstack Engineer (setup awal) |
| `FEATURE_STATUS.md` (vendor-ai) | Fullstack Engineer (diperbarui setiap fitur) |
| `vendor-ai-agent/agents/` | AI Engineer |
| `vendor-ai-agent/scoring/` | AI Engineer |
| `vendor-ai-agent/rag/` | AI Engineer |
| `vendor-ai-agent/prompts/` | AI Engineer |
| `vendor-ai-agent/tests/` | AI Engineer |
| `vendor-ai-agent/FEATURE_STATUS.md` | AI Engineer (diperbarui setiap fitur) |
| `docs/` | Fullstack + AI Engineer (read-only selama development) |

---

*Dokumen ini mencerminkan struktur repository sesuai ADR-031 (2-repo) dan pembagian track sesuai ADR-036 (Fullstack + AI Engineer). Perubahan struktural yang signifikan harus dicatat di SH-01 terlebih dahulu.*

---

**Riwayat Perubahan**

| Versi | Tanggal | Perubahan | Author |
|---|---|---|---|
| 1.0.0 | 2026-06-07 | Versi awal | — |
| 2.0.0 | 2026-06-12 | Adopsi ADR-032 (empat role): perbarui tabel kepemilikan | — |
| 3.0.0 | 2026-06-13 | Adopsi ADR-035 (namespace AI) dan ADR-036 (2 track solo developer): perbarui daftar file docs/ (BE-03→AI-01 s/d AI-07, BE-06→BE-03, BE-07 dipecah menjadi BE-04 dan AI-04, total 30 dokumen); perbarui tabel kepemilikan (4 role → Fullstack + AI Engineer); perbarui CODEOWNERS; perbarui kalimat penutup | — |
