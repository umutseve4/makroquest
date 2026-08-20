# Mimari Kararlar

## Neden bu yığın?

| Karar | Gerekçe |
|---|---|
| FastAPI | Tip güvenli, hızlı, enflasyonum'dan tanıdık — öğrenme maliyeti sıfır |
| Neon Postgres + pgvector | Tek DB'de hem ilişkisel seri verisi hem embedding; free tier 100 CU-saat/ay yeterli |
| LangGraph | Ajan akışını (soru→retrieval→ipucu seviyesi) explicit graph olarak modellemek, kara kutu zincir yerine |
| Golden-set eval CI'da | Eval'siz RAG demo'su kanıt değildir; regresyonlar PR'da yakalanır |
| GitHub Actions ingestion | Cron'lu ücretsiz orkestrasyon v0; M3'te Step Functions'a taşınır |
| Docker | Ortam tekrarlanabilirliği + M3 AWS taşıma hazırlığı |

## Veri akışı

1. **Ingestion** (günlük cron): EVDS 3 API'den seriler + bülten metinleri → ham JSON → Postgres (`series`, `documents`).
2. **Embedding**: yeni `documents` chunk'lanır → embedding → `chunks(vector)`.
3. **Oyun**: vaka tanımı (YAML) → delil kartları `series`den; ipucu isteği → LangGraph ajanı → pgvector retrieval → **kaynaklı** cevap.
4. **Eval**: golden set (soru, beklenen kaynak, beklenen cevap özü) → retrieval hit-rate + citation doğruluğu → CI PASS/FAIL.

## Güvenlik / gizlilik

- API anahtarları (EVDS, LLM) yalnızca GitHub Secrets / ortam değişkeni; koda asla yazılmaz.
- Oyuncu verisi minimal: takma ad + skor. PII yok.

## Bilinen sınırlamalar

- v0'da ipucu ajanı tek dil (Türkçe) ve tek vaka.
- EVDS 3 beta — API kırılırsa ingestion'da şema doğrulama FAIL verir (sessiz bozulma yerine).
