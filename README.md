# 🔐 2FA Authenticator Hub (Server & cPanel Edition)

Aplikasi Web UI mandiri untuk mengelola dan menghasilkan kode verifikasi dua langkah (Two-Factor Authentication / 2FA) berbasis standar industri **TOTP RFC 6238** (100% identik dengan Google Authenticator, `2fa.live`, dan integrasi cepat ke `2fa.cn`).

Aplikasi ini didesain ringan, modern, aman, dan siap dijalankan di berbagai lingkungan: **Lokal (Windows/macOS/Linux)**, **cPanel Shared/Cloud Hosting (via Domain/Subdomain)**, serta **VPS / Cloud Server (Docker & Systemd)**.

---

## 🌟 Fitur Utama

- **Real-Time TOTP Code Generation**: Menghasilkan kode OTP 6 digit real-time dengan penghitung mundur (countdown) 30 detik.
- **Sinkron 100% dengan 2fa.cn**: Dilengkapi tombol **`🌐 2fa.cn`** di setiap akun; sekali klik, secret key langsung tersalin dan browser otomatis membuka `https://2fa.cn/`.
- **Generator Cepat**: Kolom uji instan untuk memeriksa kode OTP dari secret key tanpa perlu menyimpannya ke database.
- **Manajemen Akun Lengkap**: Tambah akun tunggal, impor massal (`Nama----SecretKey`), pencarian instan, edit nama/secret key, dan ekspor data backup JSON.
- **cPanel & Domain Ready**: Mendukung deployment langsung di cPanel Hosting via fitur *Setup Python App* (Phusion Passenger / WSGI) sehingga dapat diakses menggunakan domain sendiri (misal: `https://2fa.domainkamu.com`).
- **Proteksi Akses (HTTP Basic Auth)**: Fitur keamanan opsional saat server dipublikasikan ke internet umum, cukup dengan mengisi variabel lingkungan `AUTH_USER` dan `AUTH_PASS`.

---

## 📂 Struktur File

```text
├── server.py                 # Backend utama FastAPI (Host 0.0.0.0, Port 8799)
├── passenger_wsgi.py         # Entry point adapter WSGI untuk cPanel Phusion Passenger
├── .htaccess                 # Routing rule cPanel Passenger
├── requirements.txt          # Dependensi Python (fastapi, uvicorn, pydantic, a2wsgi)
├── run_2fa.bat               # Launcher 1-klik untuk Windows lokal
├── Dockerfile                # File build Docker container
├── docker-compose.yml        # Orchestration Docker Compose
├── 2fa-authenticator.service # Unit systemd daemon untuk Linux VPS
├── nginx.conf                # Konfigurasi reverse proxy Nginx + SSL
├── keys.example.json         # Contoh format data penyimpanan secret key
├── .gitignore                # Mencegah file privat (keys.json) terupload
└── templates/
    └── index.html            # Antarmuka Web responsif (Modern Dark-Mode)
```

---

## 🚀 Panduan Menjalankan

### 1. Menjalankan di Komputer Lokal

#### Windows (Paling Mudah):
Cukup klik ganda file:
👉 **`run_2fa.bat`**

Browser akan otomatis membuka `http://127.0.0.1:8799`.

#### Manual (Terminal / Command Prompt / Linux / Mac):
```bash
pip install -r requirements.txt
python server.py
```
Akses di browser: `http://127.0.0.1:8799`

---

### 2. Deployment di cPanel Hosting (Akses via Domain Sendiri)

Jika Anda memiliki cPanel Shared atau Cloud Hosting yang memiliki fitur **"Setup Python App"**:

1. **Buat Subdomain / Domain**:
   - Di cPanel, buka menu **Domains** atau **Subdomains**.
   - Buat subdomain, misalnya: `2fa.domainkamu.com`.
   - Catat direktori root-nya (misal: `public_html/2fa` atau `2fa`).
2. **Buat Python App**:
   - Di cPanel, buka menu **Setup Python App** (kategori *Software*).
   - Klik **Create Application**:
     - **Python version**: Pilih `3.10` atau `3.11`.
     - **Application root**: Isi nama folder Document Root tadi (misal: `2fa`).
     - **Application URL**: Pilih subdomain Anda (`2fa.domainkamu.com`).
     - **Application startup file**: Ketik `passenger_wsgi.py`.
     - **Application Entry point**: Ketik `application`.
   - Klik **Create**.
3. **Upload File**:
   - Masuk ke **File Manager** cPanel pada direktori Document Root tersebut.
   - Upload semua file dari repositori ini ke folder tersebut.
   - Rename file `keys.example.json` menjadi `keys.json` (atau buat file kosong `keys.json` berisi `[]`).
4. **Instalasi Modul**:
   - Kembali ke menu **Setup Python App**, pada bagian *Configuration files*, tambahkan `requirements.txt` lalu klik **Run Pip Install**.
5. **(Opsional) Aktifkan Proteksi Login**:
   - Pada bagian *Environment variables*, tambahkan:
     - `AUTH_USER` = `admin`
     - `AUTH_PASS` = `passwordrahasia123`
6. **Restart Aplikasi**:
   - Klik tombol **Restart**.
   - Buka `https://2fa.domainkamu.com` di browser.

---

### 3. Deployment di VPS / Server (Docker & Systemd)

#### Menggunakan Docker Compose (Direkomendasikan):
```bash
docker compose up -d --build
```
Aplikasi langsung berjalan di port `8799`.

#### Menggunakan Systemd (Linux Ubuntu / Debian):
```bash
sudo cp -r . /var/www/2fa_authenticator
cd /var/www/2fa_authenticator
pip install -r requirements.txt

sudo cp 2fa-authenticator.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now 2fa-authenticator
```

#### Menggunakan Domain + SSL Nginx:
Gunakan file `nginx.conf`:
```bash
sudo cp nginx.conf /etc/nginx/sites-available/2fa
sudo ln -s /etc/nginx/sites-available/2fa /etc/nginx/sites-enabled/
sudo certbot --nginx -d 2fa.domainkamu.com
sudo systemctl restart nginx
```

---

## 🔒 Catatan Keamanan

- File `keys.json` menyimpan secret key akun 2FA Anda dan telah dikecualikan secara otomatis melalui `.gitignore` agar tidak pernah terunggah ke repositori publik.
- Saat di-deploy ke internet terbuka, sangat disarankan untuk mengaktifkan HTTPS (SSL) dan variabel `AUTH_USER` & `AUTH_PASS`.

---

## ⚖️ Lisensi
Didistribusikan di bawah lisensi MIT. Bebas digunakan dan dimodifikasi untuk kebutuhan personal maupun organisasi.
