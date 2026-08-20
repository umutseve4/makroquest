# MakroQuest 🕵️📈

**Türkiye ekonomisi dedektiflik oyunu.** "TL neden değer kaybetti?" gibi gerçek ekonomik vakaları, gerçek verilerle (TCMB EVDS, TÜİK) ve **kaynak gösteren** bir RAG ipucu ajanıyla çözersin.

> enflasyonum "fiyatlar **kaç** oldu?" sorusuna cevap verir; MakroQuest "**neden** oldu?" sorusunu oyunlaştırır.

## Nasıl oynanır (MVP hedefi)

1. Bir **vaka** seç (ör. *"Kasım 2021: TL'ye ne oldu?"*).
2. Sana gerçek veri grafikleri ve delil kartları sunulur.
3. Takıldığında **RAG ipucu ajanına** sor — cevabı her zaman kaynak (bülten/seri) göstererek verir.
4. Doğru nedeni ve kanıt zincirini seç → puan ve rozet kazan, leaderboard'a gir.

## Mimari (hedef)

```
EVDS 3 + TÜİK ──▶ ingestion (GitHub Actions, günlük) ──▶ Neon Postgres + pgvector
                                                              │
                                        LangGraph ipucu ajanı (RAG, kaynaklı cevap)
                                                              │
                                        FastAPI backend ──▶ HF Spaces / Render UI
```

- **Veri:** TCMB EVDS 3, TÜİK Veri Portalı
- **Depolama:** Neon Postgres + pgvector (embedding'ler), oyuncu state için NoSQL (faz 2: DynamoDB)
- **AI:** LangGraph tabanlı ipucu ajanı; CI'da golden-set **RAG eval** (kaynak doğruluğu dahil)
- **Çalıştırma:** Docker; geliştirme GitHub Codespaces üzerinde — tamamen bulut, GPU'suz

## Durum

🚧 **M1 geliştirme aşamasında.** Yol haritası için [ROADMAP.md](ROADMAP.md).

| Aşama | Durum |
|---|---|
| M1 — Dikey dilim: 1 vaka + RAG ajanı + eval | 🔨 devam ediyor |
| M2 — 5 vaka + puan/rozet/leaderboard | ⏳ planlandı |
| M3 — AWS taşıma (S3/Step Functions/DynamoDB) | ⏳ planlandı |

## Geliştirme

```bash
pip install -e ".[dev]"
pytest -q
```

## Lisans

MIT — bkz. [LICENSE](LICENSE).

## Sorumluluk reddi

MakroQuest bir eğitim/oyun projesidir; yatırım tavsiyesi değildir. Veriler TCMB EVDS ve TÜİK'in açık verilerinden alınır; hak sahipliği ilgili kurumlara aittir.
