# MakroQuest — Yol Haritası

İlke: **küçük çalışan dikey dilim > büyük spekülatif mimari.** Her milestone'un ölçülebilir kabul kriteri vardır; "tested + verified" olmadan tamamlandı sayılmaz.

## M1 — Dikey Dilim (hedef: ~2 hafta)

**Amaç:** 1 vaka uçtan uca oynanabilir + RAG ajanı kaynak gösteriyor + eval CI'da yeşil.

| # | İş | Kabul kriteri |
|---|---|---|
| M1.1 | Proje iskeleti: FastAPI app, pytest, ruff, CI | CI yeşil; `GET /health` 200 döner |
| M1.2 | Ingestion v0: EVDS'den 5 seri + 3-5 metin bülteni çek, Postgres'e yaz | Tekrar çalıştırılabilir (idempotent); satır sayıları loglanır; şema migration'lı |
| M1.3 | pgvector RAG: bülten chunk'ları + embedding + retrieval endpoint'i | `POST /ask` cevap + en az 1 kaynak referansı döner |
| M1.4 | LangGraph ipucu ajanı: soru → retrieval → kaynaklı cevap → ipucu seviyesi | Ajan asla kaynaksız iddia üretmez (yoksa "bilmiyorum" der) |
| M1.5 | Golden-set eval: 30 soru-cevap-kaynak üçlüsü; retrieval hit-rate + citation doğruluğu | Eval CI'da koşar; hit-rate ≥ %70 eşiği FAIL/PASS olarak raporlanır |
| M1.6 | Vaka #1: "Kasım 2021 — TL'ye ne oldu?" oynanabilir akış (API-level) | Vaka başlat → delil al → ipucu iste → cevap ver → skor döner; testli |
| M1.7 | Deploy: Docker image + HF Spaces/Render'da canlı demo | Public URL'de vaka #1 oynanabilir |

**M1 done tanımı:** Canlı URL'de vaka #1 oynanıyor, `/ask` kaynak gösteriyor, eval CI'da yeşil, README'de demo linki + ekran görüntüsü.

## M2 — Oyunlaştırma (~2 hafta)

- 5 vaka (senaryo formatı YAML/JSON şablonlaştırılır)
- Puan, rozet ("Faiz Şahini", "Enflasyon Avcısı"), leaderboard
- Oyuncu state için NoSQL katmanı
- Basit web UI (paylaşılabilir vaka sonucu kartı)

## M3 — AWS + DEA-C01 pratiği

- Ingestion → S3 + Lambda + Step Functions
- Oyuncu state → DynamoDB
- IaC (Terraform veya CDK) + maliyet korumaları (budget alarm)
- Amaç: DEA-C01 domain'lerinin (Ingestion %34, Storage %26, Ops %22, Security %18) canlı pratiği

## Bilinçli kapsam dışı (şimdilik)

- Çok oyunculu gerçek zamanlı mod
- Mobil uygulama
- LLM fine-tuning (önce eval kültürü)
