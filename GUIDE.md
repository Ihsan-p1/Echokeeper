# 📖 EchoKeeper — Panduan Pengguna

EchoKeeper adalah bot Discord penerjemah yang mendukung **Vietnamese ��, English ��, Indonesian 🇮🇩** dan banyak bahasa lainnya.

---

## ⚡ Quick Start

| Yang mau lo lakukan | Command |
|---|---|
| Terjemahkan teks ke English | `!tl Hello, apa kabar?` |
| Terjemahkan ke bahasa tertentu | `!tl vi Halo semua!` |
| Set bahasa default kamu | `/lang id` |
| Aktifkan auto-translate untuk kamu | `/optin` |
| Translate pesan orang lain | React dengan 🌐 |

---

## 🗣️ Commands

### `!tl` — Translate Teks

```
!tl <teks>
!tl <kode_bahasa> <teks>
```

**Contoh:**
```
!tl Xin chào, hôm nay bạn thế nào?
!tl vi Halo, bagaimana kabarmu?
!tl id Hello, how are you today?
!tl en Xin chào mọi người
```

> Kalau tidak menyebut kode bahasa, bot translate ke bahasa default kamu (lihat `/lang`).

---

### `/tl` — Slash Command Translate

Ketik `/tl` di chat, lalu isi dua kolom:

- **text** → teks yang mau diterjemahkan
- **target** *(opsional)* → kode bahasa tujuan, default ke preferensi kamu

---

### `/lang` — Set Bahasa Default

```
/lang <kode>
```

**Contoh:**
```
/lang vi    → semua !tl kamu → Vietnamese
/lang id    → semua !tl kamu → Indonesian
/lang en    → semua !tl kamu → English
```

Setelah ini kamu cukup ketik `!tl <teks>` tanpa perlu tulis kode bahasa setiap kali.

---

### `/optin` — Aktifkan / Nonaktifkan Auto-Translate

Kalau **aktif**, setiap pesan kamu di channel auto-translate akan otomatis diterjemahkan.

```
/optin    → toggle ON / OFF
```

---

### `/myinfo` — Cek Pengaturan Kamu

```
/myinfo
```

Menampilkan bahasa default dan status auto-translate kamu saat ini.

---

### `/languages` — Daftar Bahasa

```
/languages
```

Menampilkan semua kode bahasa yang didukung.

---

### 🌐 Reaction Trigger

React emoji **🌐** ke **pesan siapapun** → bot otomatis terjemahkan pesan itu ke bahasa default **kamu**.

> Kamu harus sudah set `/lang` agar hasilnya sesuai.

---

## 🔧 Commands Khusus Admin

> Membutuhkan permission **Manage Channels**.

### `/setchannel` — Auto-Translate Channel

```
/setchannel <kode>
```

Semua pesan di channel ini akan otomatis diterjemahkan ke bahasa yang ditentukan.

**Contoh:**
```
/setchannel en    → semua pesan di channel ini → English
/setchannel vi    → semua pesan → Vietnamese
```

### `/removechannel` — Hapus Auto-Translate

```
/removechannel
```

Menonaktifkan auto-translate di channel saat ini.

---

## 🌍 Kode Bahasa yang Didukung

| Kode | Bahasa |
|------|--------|
| `en` | English |
| `id` | Indonesian |
| `vi` | Vietnamese |
| `ms` | Malay |
| `zh` | Chinese (Simplified) |
| `ja` | Japanese |
| `ko` | Korean |
| `ar` | Arabic |
| `fr` | French |
| `de` | German |
| `es` | Spanish |
| `pt` | Portuguese |
| `ru` | Russian |
| `hi` | Hindi |

---

## ⚠️ Tips & Batasan

**✅ Teks yang diterjemahkan dengan baik:**
- Kalimat lengkap dan formal
- Teks ≥ 5 kata
- Bahasa konsisten dalam satu pesan

**⚠️ Teks dengan kualitas kurang:**
- Singkatan informal (`gmn`, `btw`, `gak`, `bsok`)
- Bahasa campur dalam satu kalimat
- Teks sangat pendek (< 3 kata)
- Emoji atau link saja

**Batasan:**
- Maks **1000 karakter** per terjemahan
- Cooldown **3 detik** per user agar tidak spam

---

## ❓ FAQ

**Q: Bot tidak merespons `!tl`?**
A: Pastikan bot online dan punya permission **Send Messages** & **Embed Links** di channel.

**Q: Hasil terjemahan aneh untuk bahasa gaul?**
A: Bot menggunakan model akademik, kurang optimal untuk bahasa informal. Gunakan kalimat lengkap untuk hasil terbaik.

**Q: Bahasa sumber tidak terdeteksi dengan benar?**
A: Gunakan `/tl` dan isi kolom `target` secara manual, atau pastikan teks cukup panjang untuk dideteksi.

**Q: Slash command `/tl` tidak muncul?**
A: Tunggu 1–2 menit setelah bot masuk server, lalu coba ketik `/` lagi.

---

*Powered by Helsinki-NLP opus-mt · Open Source*
