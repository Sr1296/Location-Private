# OSINT Consent Dashboard v2 — Termux

Versi 2 otomatis meminta Geolocation API ketika landing page dibuka.
**Otomatis bukan berarti diam-diam:** browser/OS tetap harus memberikan izin.

## Instalasi Termux

```bash
pkg update
pkg install python unzip -y
cd ~/storage/downloads
unzip osint-consent-dashboard-v2.zip
cd osint-consent-dashboard-v2
python -m pip install -r requirements.txt
python app.py
```

Dashboard:
`http://127.0.0.1:5000`

## Pengujian dari perangkat lain

Untuk akses dari jaringan lokal, Flask harus di-bind ke `0.0.0.0`.
Edit baris terakhir `app.run(...)` menjadi:

```python
app.run(host="0.0.0.0", port=5000, debug=False)
```

Kemudian gunakan HTTPS untuk geolocation pada akses non-localhost. Jangan mengekspos dashboard ke internet tanpa autentikasi dan HTTPS.

## Catatan

- GPS hanya disimpan jika pengguna memberikan izin.
- Jika izin ditolak, server menyimpan kunjungan tanpa koordinat GPS.
- IP bukan lokasi GPS dan biasanya hanya memberikan perkiraan lokasi.
- Jangan gunakan sistem ini untuk memantau orang tanpa persetujuan atau dasar hukum.
