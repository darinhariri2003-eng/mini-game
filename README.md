# 3D Mini Game Physics & Loop Engine

Arka uç (backend) ve ön yüz (frontend) ayrımına sahip, oyun döngüsünü (game loop) ve fizik mantığını düzenli bir mimari içinde yönetmeyi amaçlayan mini 3B oyun motoru projesi.

## Proje Yapısı

```text
mini-game-physics-engine/
├── backend/     # Oyun döngüsü, fizik/sunucu mantığı ve arka uç bileşenleri
├── frontend/    # Sahne, arayüz ve istemci tarafı dosyaları
├── .gitignore   # Git'e gönderilmeyecek dosya ve klasörler
└── README.md    # Proje açıklaması ve çalıştırma adımları
```

## Gereksinimler

* **Git** (sürüm kontrolü ve güncelleme gönderimi için)
* **Python** (arka uç bileşenlerini ve yerel sunucuyu çalıştırmak için)

## Yerel Çalıştırma Adımları

### 1. Arka Uç (Backend)

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

*(Projede ayrı bir bağımlılık listesi yoksa veya sanal ortam kullanılmıyorsa kurulum adımını atlayabilirsiniz).* Ardından `backend` klasöründeki ana Python dosyasını çalıştırın:

```bash
python main.py
```

*(Ana dosyanın adı farklıysa kendi dosya adınıza göre güncelleyin).*

### 2. Ön Yüz (Frontend)

Ön yüz dosyalarını tarayıcıda açmak veya yerel sunucu üzerinden çalıştırmak için `frontend` klasörüne geçin:

```bash
cd frontend
python -m http.server 8000
```

Ardından tarayıcıdan `http://localhost:8000` adresine giderek arayüzü ve sahneyi görüntüleyebilirsiniz (veya `index.html` varsa doğrudan tarayıcıda açabilirsiniz).

## Geliştirme Durumu

Projenin temel klasör yapısı oluşturuldu ve `README.md` dokümantasyonu ile birlikte GitHub'daki `main` dalına aktarıldı. Fizik hesaplamaları, oyun döngüsü ve arayüz entegrasyonu üzerinde geliştirmeler sürdürülmektedir.