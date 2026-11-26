# 3D Mini Game Physics & Loop Engine

Arka uç (backend) ve ön yüz (frontend) ayrımına sahip, oyun döngüsünü (game loop) ve fizik mantığını düzenli şekilde yönetmeyi hedefleyen mini 3B oyun motoru projesi.

## Proje Yapısı

```text
mini-game-physics-engine/
├── backend/     # Sunucu ve arka uç mantığı
├── frontend/    # Kullanıcı arayüzü ve sahne/oyun görünümü
├── .gitignore   # Git'e gönderilmeyecek dosya ve klasörler
└── README.md    # Proje açıklaması ve çalıştırma adımları
```

## Gereksinimler

* **Git** (sürüm kontrolü ve güncelleme gönderimi için)
* **Python** (arka uç bileşenlerini çalıştırmak için)
* **Node.js ve npm** (ön yüz paketleri veya web araçları kullanılıyorsa)

## Yerel Çalıştırma Adımları

### 1. Arka Uç (Backend)

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Paket kurulumundan sonra `backend` klasöründeki ana çalıştırma dosyasını kendi dosya adına göre çalıştırın.

### 2. Ön Yüz (Frontend)

```bash
cd frontend
npm install
npm run dev
```

