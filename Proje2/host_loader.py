import sys
import serial
import time
import os

PORT = "COM6"
BAUD = 115200
DEFAULT_FILENAME = "output.mem"

def calculate_checksum(byte_data):
    checksum = 0
    for b in byte_data:
        checksum ^= b
    return checksum

def find_file(filename, search_path="."):
    print(f"Alt klasörlerde '{filename}' aranıyor...")
    for root, dirs, files in os.walk(search_path):
        if filename in files:
            return os.path.join(root, filename)
    return None

def send_program_to_fpga(file_path):
    try:
        print(f"[{PORT}] Portu açılıyor...")
        ser = serial.Serial(PORT, BAUD, timeout=1)
        time.sleep(2) # FPGA'in kendine gelmesi için bekleme
        
        # RAM imajı oluştur (Maksimum 4KB = 4096 byte)
        ram_image = bytearray(4096)
        max_written_byte = 0
        current_word_addr = 0

        # 1. Dosyayı Adres Etiketlerine Göre Oku
        with open(file_path, "r") as f:
            for line in f:
                line = line.strip()
                if not line: 
                    continue
                
                if line.startswith('@'):
                    # Word adresini hex olarak al (Örn: @0005 -> 5)
                    current_word_addr = int(line[1:], 16)
                    continue
                
                # 32-bit komutu al
                word_value = int(line, 16)
                byte_data = word_value.to_bytes(4, byteorder='little')
                
                # Word adresini Byte adresine çevir (Her word 4 byte yer kaplar)
                byte_addr = current_word_addr * 4
                
                # RAM sınır kontrolü
                if byte_addr + 4 <= len(ram_image):
                    ram_image[byte_addr:byte_addr+4] = byte_data
                    if byte_addr + 4 > max_written_byte:
                        max_written_byte = byte_addr + 4
                
                # Bir sonraki satırda @ yoksa ardışık yazmaya devam etsin diye adresi artır
                current_word_addr += 1
        
        # 2. Sadece veri olan kısma kadar paketle (4'er byte + 1 byte Checksum)
        packets = []
        for i in range(0, max_written_byte, 4):
            chunk = ram_image[i:i+4]
            checksum = calculate_checksum(chunk)
            packets.append(chunk + bytes([checksum]))

        print(f"Toplam {max_written_byte} byte veri bulundu.")
        print(f"{len(packets)} adet paket checksum ile fırlatılıyor...")
        
        # 3. Donanıma Kesintisiz Gönder
        for packet in packets:
            ser.write(packet)
            # Bekleme süresini azalttık (FSM timeout'a düşmesin diye)
            time.sleep(0.001) 
        
        ser.close()
        print("✅ Yükleme başarıyla tamamlandı!")
        
    except Exception as e:
        print("❌ Bağlantı hatası:", e)

if __name__ == "__main__":
    filename = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_FILENAME
    hedef_dosya = find_file(filename)
    
    if hedef_dosya:
        print(f"✅ Dosya bulundu: {hedef_dosya}")
        send_program_to_fpga(hedef_dosya)
    else:
        print(f"❌ HATA: '{filename}' bulunamadı.")