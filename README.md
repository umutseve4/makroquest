<h1 align="center">MakroQuest</h1>

<p align="center">
  "TL neden değer kaybetti?" sorusunu bir dedektiflik vakası gibi çöz.<br>
  Gerçek Dünya Bankası verisi, delil kartları ve <b>her cevabında kaynak gösteren</b> bir ipucu ajanı.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/canl%C4%B1%20do%C4%9Frulama-haftal%C4%B1k-FF4D4F?style=flat-square" alt="haftalık canlı doğrulama">
  <img src="https://img.shields.io/badge/API%20anahtar%C4%B1-0-FF4D4F?style=flat-square" alt="0 API anahtarı">
  <img src="https://img.shields.io/badge/tamamlanan%20milestone-M1-FF4D4F?style=flat-square" alt="M1 tamamlandı">
</p>

<p align="center">
  <b><a href="https://makroquest.onrender.com">▶ Canlı demoyu aç</a></b><br>
  <sub><a href="https://makroquest.onrender.com/docs">Swagger UI</a> · <a href="https://makroquest.onrender.com/health">/health</a></sub>
</p>

---

## 30 saniyede ne oluyor?

```bash
curl localhost:7860/health
curl localhost:7860/case                          # vaka listesi
curl -X POST localhost:7860/case/kasim-2021/start # oturum aç
curl "localhost:7860/retrieve?q=doviz+kuru&k=3"   # kaynaklı retrieval
```

Yerel çalıştırma tek komut:

```bash
docker build -t makroquest .
docker run -p 7860:7860 makroquest
# http://localhost:7860/docs  → Swagger UI
```

## Nasıl oynanır

1. Bir **vaka** seç (ör. *"Kasım 2021: TL'ye ne oldu?"*).
2. Sana gerçek veri grafikleri ve delil kartları sunulur.
3. Takıldığında **RAG ipucu ajanına** sor — cevabı her zaman kaynak (bülten/seri) göstererek verir.
4. Doğru nedeni ve kanıt zincirini seç → puan ve rozet kazan, leaderboard'a gir.

> enflasyonum "fiyatlar **kaç** oldu?" sorusuna cevap verir; MakroQuest "**neden** oldu?" sorusunu oyunlaştırır.

## Mimari (hedef)

```
Dünya Bankası API ──▶ ingestion (GitHub Actions, günlük) ──▶ Neon Postgres + pgvector
                                                              │
                                        LangGraph ipucu ajanı (RAG, kaynaklı cevap)
                                                              │
                                        FastAPI backend ──▶ Render / HF Spaces
```

| Katman | Seçim |
|---|---|
| Veri | Dünya Bankası Indicators API (anahtarsız), TÜİK Veri Portalı (faz 2) |
| Depolama | Neon Postgres + pgvector (embedding'ler), oyuncu state için NoSQL (faz 2: DynamoDB) |
| AI | LangGraph tabanlı ipucu ajanı; CI'da golden-set **RAG eval** (kaynak doğruluğu dahil) |
| Çalıştırma | Docker (`MAKROQUEST_DATA_DIR` ile veri yolu); geliştirme GitHub Codespaces üzerinde — tamamen bulut, GPU'suz |

## Durum

| Aşama | Durum |
|---|---|
| M1 — Dikey dilim: 1 vaka + RAG ajanı + eval + canlı demo | ✅ tamamlandı |
| M2 — 5 vaka + puan/rozet/leaderboard | ⏳ planlandı |
| M3 — AWS taşıma (S3/Step Functions/DynamoDB) | ⏳ planlandı |

Yol haritası: [ROADMAP.md](ROADMAP.md).

## Sınırlar

- **Demo uyur.** Render free tier 15 dk hareketsizlikte uyur; ilk istek ~30–60 sn sürebilir. Kök URL (`/`) otomatik olarak `/docs`'a yönlenir.
- Canlı demo her hafta [live-smoke](.github/workflows/live-smoke.yml) workflow'u ile otomatik doğrulanır — sürekli erişilebilirlik iddia edilmez.
- Şu an **tek vaka** yayında; 5 vaka, puan, rozet ve leaderboard M2 kapsamındadır.
- MakroQuest bir eğitim/oyun projesidir; **yatırım tavsiyesi değildir.** Veriler Dünya Bankası ve TÜİK'in açık verilerinden alınır; hak sahipliği ilgili kurumlara aittir.

Geliştirme:

```bash
pip install -e ".[dev]"
pytest -q
```

---

MIT — bkz. [LICENSE](LICENSE).
