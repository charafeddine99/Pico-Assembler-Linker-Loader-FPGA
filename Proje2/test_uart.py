import serial
import time

PORT = "COM9"  # Aygıt yöneticisindeki portunu yaz
BAUD = 115200

try:
    print(f"{PORT} portu açılıyor...")
    ser = serial.Serial(PORT, BAUD, timeout=1)
    
    # KİLİT NOKTA: Port açıldıktan sonra donanımın resetten çıkmasını bekle
    print("Donanımın kendine gelmesi bekleniyor...")
    time.sleep(2) 
    print("Bağlantı Hazır! Cihaza veri gönderebilirsiniz.\n")
    
    while True:
        # Kullanıcıdan harf bekle
        char = input("Bir harf yazın ve Enter'a basın (Çıkmak için 'q'): ")
        
        if char == 'q':
            break
            
        if len(char) > 0:
            # Sadece ilk harfi binary formata çevirip gönder
            ser.write(char[0].encode())
            print(f"--> '{char[0]}' donanıma ateşlendi!")

    ser.close()
    print("Bağlantı kapatıldı.")
except Exception as e:
    print("Bağlantı hatası:", e)