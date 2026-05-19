import discord
import time
import os
import sys
import threading
from http.server import SimpleHTTPRequestHandler, HTTPServer

# =====================================================================
# 🌍 UPTIME ROBOT VE RENDER PORT HATASI İÇİN ARKA PLAN WEB SUNUCUSU
# =====================================================================
def run_dummy_server():
    port = int(os.getenv("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    print(f"🌍 Uptime Web Sunucusu aktif edildi! Port: {port}")
    server.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()

# =====================================================================
# 🤖 DISCORD SELF-BOT MANTIĞI
# =====================================================================
class MySelfBot(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Render panelinden TARGET_ID verisini alıyoruz
        target_ids_str = os.getenv("TARGET_ID", "")
        
        self.hedef_kullanicilar = []
        if target_ids_str:
            try:
                self.hedef_kullanicilar = [int(x.strip()) for x in target_ids_str.split(",") if x.strip().isdigit()]
            except Exception as e:
                print(f"❌ TARGET_ID formatı hatalı! Hata: {e}")
        
        bildirim_str = os.getenv("SELF_BILDIRIM_KANALI")
        self.bildirim_kanal_id = int(bildirim_str) if (bildirim_str and bildirim_str.isdigit()) else None
        
        # Kullanıcıların son mesaj attığı zamanı saklar
        self.son_mesaj_zamanlari = {}
        
        # Sessizlik kriteri: 3 dakika = 180 saniye
        self.sessizlik_suresi = 180 

    async def on_ready(self):
        print("=========================================")
        print(f"🤖 [{self.user.name}] Giriş Başarılı!")
        print(f"🎯 Toplam {len(self.hedef_kullanicilar)} kullanıcı dinleniyor.")
        print(f"📢 Bildirim Kanalı ID: {self.bildirim_kanal_id}")
        print(f"⏱️ Beklenen Sessizlik: 3 Başlangıç/Sessizlik Süresi ({self.sessizlik_suresi} sn)")
        print("=========================================")
        
        if not self.hedef_kullanicilar or not self.bildirim_kanal_id:
            print("❌ HATA: TARGET_ID veya SELF_BILDIRIM_KANALI eksik ya da hatalı!")
            sys.exit(1)

    async def on_message(self, message):
        # Kendi hesabımızın mesajlarını es geçiyoruz
        if message.author.id == self.user.id:
            return

        # Mesajı atan kişi hedeflenen kullanıcılardan biriyse
        if message.author.id in self.hedef_kullanicilar:
            simdiki_zaman = time.time()
            kullanici_id = message.author.id
            
            # Kullanıcının son aktiflik zamanını kontrol et
            son_aktiflik = self.son_mesaj_zamanlari.get(kullanici_id, None)
            
            # 💡 MANTIK: 
            # Eğer son_aktiflik 'None' ise (yani kod çalıştığından beri İLK KEZ yazıyorsa)
            # VEYA şu anki zaman ile son mesajı arasında 3 dakikadan fazla (180 sn) süre geçmişse BİLDİRİM AT.
            if son_aktiflik is None or (simdiki_zaman - son_aktiflik >= self.sessizlik_suresi):
                bildirim_kanali = self.get_channel(self.bildirim_kanal_id)
                
                if bildirim_kanali:
                    sunucu_id = message.guild.id if message.guild else "@me"
                    mesaj_linki = f"https://discord.com/channels/{sunucu_id}/{message.channel.id}/{message.id}"
                    
                    bildirim_metni = (
                        f"@everyone\n"
                        f"**FERİŞTAHİNİ SİKTİĞİM MESAJ GÖNDERDİ XD**\n"
                        f"**Kullanıcı:** {message.author.name} (`{message.author.id}`)\n"
                        f"**Konum:** {message.guild.name if message.guild else 'Özel Mesaj'} / {message.channel}\n"
                        f"**Mesaj Bağlantısı:** {mesaj_linki}\n"
                        f"**Mesaj İçeriği:** {message.content}"
                    )
                    
                    await bildirim_kanali.send(bildirim_metni)
                    print(f"✅ [{message.author.name}] sessizlik sonrası yeni mesaj attı, bildirim gönderildi.")
            else:
                # Kullanıcı 3 dakikalık arayı doldurmadan yazmaya devam ediyorsa konsola log düşer ama Discord'a mesaj gitmez
                kalan_sure = int(self.sessizlik_suresi - (simdiki_zaman - son_aktiflik))
                print(f"⏳ [{message.author.name}] yazmaya devam ediyor, bildirim tetiklenmedi. Yeni bildirim için {kalan_sure} sn susmalı.")

            # Kullanıcı her mesaj gönderdiğinde kronometreyi sıfırlıyoruz
            self.son_mesaj_zamanlari[kullanici_id] = simdiki_zaman

# Render panelinden TOKEN verisini alıyoruz
TOKEN = os.getenv("SELF_TOKEN")

if not TOKEN:
    print("❌ HATA: SELF_TOKEN bulunamadı!")
    sys.exit(1)

client = MySelfBot()
client.run(TOKEN)
