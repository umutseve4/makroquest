# MakroQuest 🕵️📈

**Türkiye ekonomisi dedektiflik oyunu.** "TL neden değer kaybetti?" gibi gerçek ekonomik vakaları, gerçek verilerle (Dünya Bankası açık verileri) ve **kaynak gösteren** bir RAG ipucu ajanıyla çözersin.

> enflasyonum "fiyatlar **kaç** oldu?" sorusuna cevap verir; MakroQuest "**neden** oldu?" sorusunu oyunlaştırır.

## Canlı demo

🔗 **Demo:** https://makroquest.onrender.com — [Swagger UI](https://makroquest.onrender.com/docs) · [/health](https://makroquest.onrender.com/health)

> Not: Render free tier 15 dk hareketsizlikte uyur; ilk istek ~30-60 sn sürebilir.
> Canlı demo her hafta [live-smoke](.github/workflows/live-smoke.yml) workflow'u ile otomatik doğrulanır.

```bash
# Yerel çalıştırma (Docker):
docker build -t makroquest .
docker run -p 7860:7860 makroquest
# http://localhost:7860/docs  → Swagger UI
```

Hızlı tur:

```bash
curl localhost:7860/health
curl localhost:7860/case                          # vaka listesi
curl -X POST localhost:7860/case/kasim-2021/start # oturum aç
curl "localhost:7860/retrieve?q=doviz+kuru&k=3"   # kaynaklı retrieval
```

## Nasıl oynanır (MVP hedefi)

1. Bir **vaka** seç (ör. *"Kasım 2021: TL'ye ne oldu?"*).
2. Sana gerçek veri grafikleri ve delil kartları sunulur.
3. Takıldığında **RAG ipucu ajanına** sor — cevabı her zaman kaynak (bülten/seri) göstererek verir.
4. Doğru nedeni ve kanıt zincirini seç → puan ve rozet kazan, leaderboard'a gir.

## Mimari (hedef)

```
Dünya Bankası API ──▶ ingestion (GitHub Actions, günlük) ──▶ Neon Postgres + pgvector
                                                              │
                                        LangGraph ipucu ajanı (RAG, kaynaklı cevap)
                                                              │
                                        FastAPI backend ──▶ Render / HF Spaces
```

- **Veri:** Dünya Bankası Indicators API (anahtarsız), TÜİK Veri Portalı (faz 2)
- **Depolama:** Neon Postgres + pgvector (embedding'ler), oyuncu state için NoSQL (faz 2: DynamoDB)
- **AI:** LangGraph tabanlı ipucu ajanı; CI'da golden-set **RAG eval** (kaynak doğruluğu dahil)
- **Çalıştırma:** Docker (`MAKROQUEST_DATA_DIR` ile veri yolu); geliştirme GitHub Codespaces üzerinde — tamamen bulut, GPU'suz

## Durum

✅ **M1 tamamlandı — canlı demo yayında.** Yol haritası için [ROADMAP.md](ROADMAP.md).

| Aşama | Durum |
|---|---|
| M1 — Dikey dilim: 1 vaka + RAG ajanı + eval + canlı demo | ✅ tamamlandı |
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

MakroQuest bir eğitim/oyun projesidir; yatırım tavsiyesi değildir. Veriler Dünya Bankası ve TÜİK'in açık verilerinden alınır; hak sahipliği ilgili kurumlara aittir.
