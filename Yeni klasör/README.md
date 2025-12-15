# GMK AIR Motor Test Unit (Python Client)

Bu proje, drone motor/ESC/propeller testleri için PyQt6 tabanlı bir masaüstü istemcisidir. Seri port üzerinden gelen telemetriyi okur, canlı grafikler çizer, verileri CSV olarak kaydeder ve test segmentlerini özetler.

## Gereksinimler
- Python 3.10+
- Sistem kütüphaneleri: PyQt6 için platform bağımlı gereksinimler (macOS/Linux/Windows’ta ilgili Qt bağımlılıkları)

## Kurulum (sanal ortam önerilir)
```bash
python3 -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
```

## Çalıştırma
```bash
python -m app.main
```

## Paket Yapısı ve Amaçları
- `app/`: Uygulamanın giriş noktası ve bağımlılıkların bağlandığı yer (composition root). `main.py` burada.
- `presentation/`: Arayüz katmanı; PyQt6 widget’ları ve pencereleri. UI, domain veya veri katmanına doğrudan iş kuralı eklemez.
  - `presentation/windows/`: Ana pencere vb. üst seviye pencereler.
  - `presentation/widgets/`: Yeniden kullanılabilir widget’lar (grafik paneli, kontrol paneli, sol veri paneli, özet dialogu vb.).
- `domain/`: İş kuralları ve portlar. Harici sistemlere bağımlı olmayan saf kurallar. `ports.py` serial okuma için arayüz sağlar.
- `data/`: Domain portlarını uygulayan adaptörler. Örn. `serial_repository.py` seri porttan veriyi okur ve parse eder.
- `core/`: Ortak sabitler, basit yardımcılar (şu an `constants.py`).

Bu yapı, bağımlılıkları içe doğru yönlendirerek (UI → domain portu → data adaptörü) test edilebilirlik ve değişime açık/kapalı ayrımı sağlar.

## Temel Akış
1) Uygulama açılır, `MainWindow` oluşturulur.
2) Kullanıcı COM port seçer ve bağlanır (`SerialRepository` domain portunu uygular).
3) Gelen telemetri `SerialRepository` tarafından parse edilir, UI katmanına dikte edilir.
4) Grafik paneli canlı veriyi çizer; isteğe bağlı CSV ve PNG çıktıları alınır.
5) Test segmenti bittiğinde özet dialogu gösterilir.

## Test/Format
Projede otomatik test veya formatlayıcı tanımlı değil. Gerektiğinde `pytest` veya `ruff/black` eklenebilir.

