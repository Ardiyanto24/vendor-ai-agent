# Feature Status — vendor-ai-agent

Tracking status pengerjaan per fitur untuk track AI Engineer.  
Hanya fitur yang menyentuh `vendor-ai-agent` yang tercantum di sini.

**Kapan kolom `AI` dinyatakan ✅:**
- FastAPI endpoint dan pipeline AI untuk fitur ini sudah berjalan di staging
- Unit test dengan LLM mock lulus
- Dikonfirmasi dari log staging bahwa pipeline berjalan sesuai dependency graph (AI-01)

**Status legend:** ✅ selesai · 🔄 in progress · ⏳ menunggu prerequisite · ❌ blocked

---

| Fitur | AI | Bergantung pada | Notes |
|---|---|---|---|
| F-00 Environment Setup | ✅ 2026-06-15 | — | GET /health, middleware, struktur folder prompts/ |
| F-07 Upload & Ekstraksi | — | F-00 | POST /v1/agent/ekstrak-dokumen — Pipeline A (ekstraksi) + Pipeline B (RAG indexing) |
| F-10 AI Processing | — | F-07 | POST /v1/agent/evaluasi/:id/start — 7 agent LangGraph |
| F-11 Hasil TOPSIS | — | F-10 | Scoring engine TOPSIS + GET /v1/scoring/evaluasi/:id/hasil |
| F-12 Profil Kualitatif | — | F-10, F-11 | Qualitative Analyzer Agent ditambah ke pipeline |
| F-13 Rekomendasi Preferensi | — | F-12 | Preference Matcher Agent — node terakhir LangGraph |
| F-14 AI Chat + RAG | — | F-07, F-11 | POST /v1/rag/query + POST /v1/chat/stream (SSE) |