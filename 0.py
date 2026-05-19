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
        # Kütüphanenin sunucuları ve üyeleri hafızada tam tutması için ayarlar
        kwargs["chunk_guilds_at_startup"] = True
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
        
        # Kullanıcıların son mesaj zamanını tutar
        self.son_mesaj_zamanlari = {}
        # Kullanıcının şu an aktif bir konuşma içinde olup olmadığını tutar
        self.aktif_konusmada_mi = {}
        
        # Sessizlik kriteri: 3 dakika = 180 saniye
        self.sessizlik_suresi = 180 

    async def on_ready(self):
        print("=========================================")
        print(f"🤖 [{self.user.name}] Giriş Başarılı ve Önbellek Hazır!")
        print(f"🎯 Takip Edilen Kullanıcılar: {self.hedef_kullanicilar}")
        print(f"📢 Bildirim Kanalı ID: {self.bildirim_kanal_id}")
        print("=========================================")
        
        if not self.hedef_kullanicilar or not self.bildirim_kanal_id:
            print("❌ HATA: TARGET_ID veya SELF_BILDIRIM_KANALI eksik ya da hatalı!")
            sys.exit(1)

    # Ortak Kontrol Fonksiyonu (Hem yeni mesaj hem düzenleme için tek merkez)
    async def kontrol_et_ve_bildir(self, message):
        # Kendi mesajlarımızı eliyoruz
        if message.author.id == self.user.id:
            return

        # Mesaj listedeki hedeflerden birine mi ait?
        if message.author.id in self.hedef_kullanicilar:
            simdiki_zaman = time.time()
            kullanici_id = message.author.id
            
            son_aktiflik = self.son_mesaj_zamanlari.get(kullanici_id, 0)
            konusma_durumu = self.aktif_konusmada_mi.get(kullanici_id, False)
            
            # Eğer 3 dakika sustuysa konuşma bitmiştir, durumu sıfırla
            if simdiki_zaman - son_aktiflik >= self.sessizlik_suresi:
                konusma_durumu = False
                self.aktif_konusmada_mi[kullanici_id] = False

            # Yeni konuşma başlangıcı durumu
            if konusma_durumu is False:
                # Kanalı API üzerinden tazeleyerek çek (Önbellek sorununu çözer)
                try:
                    bildirim_kanali = self.get_channel(self.bildirim_kanal_id) or await self.fetch_channel(self.bildirim_kanal_id)
                except Exception:
                    bildirim_kanali = None
                
                if bildirim_kanali:
                    sunucu_id = message.guild.id if message.guild else "@me"
                    mesaj_linki = f"https://discord.com/channels/{sunucu_id}/{message.channel.id}/{message.id}"
                    
                    bildirim_metni = (
                        f"@everyone\n"
                        f"**MESAJ GÖNDERİ TÜREME OROSPU EVLADI XD**\n"
                        f"**Kullanıcı:** {message.author.name} (`{message.author.id}`)\n"
                        f"**Konum:** {message.guild.name if message.guild else 'Özel Mesaj'} / {message.channel}\n"
                        f"**Mesaj Bağlantısı:** {mesaj_linki}\n"
                        f"**İlk Mesaj:** {message.content}"
                    )
                    
                    await bildirim_kanali.send(bildirim_metni)
                    print(f"✅ [{message.author.name}] için bildirim başarıyla kanala iletildi.")
                
                self.aktif_konusmada_mi[kullanici_id] = True
            else:
                print(f"💬 [{message.author.name}] konuşmaya devam ediyor, sessizce loglandı.")

            # Kronometreyi her hareketle güncelle
            self.son_mesaj_zamanlari[kullanici_id] = simdiki_zaman

    # TETİKLEYİCİ 1: Yeni Mesaj Geldiğinde
    async def on_message(self, message):
        await self.kontrol_et_ve_bildir(message)

    # TETİKLEYİCİ 2: Mesaj Düzenlendiğinde (Gözden kaçmayı önler)
    async def on_message_edit(self, before, after):
        await self.kontrol_et_ve_bildir(after)

# Render panelinden TOKEN verisini alıyoruz
TOKEN = os.getenv("SELF_TOKEN")

if not TOKEN:
    print("❌ HATA: SELF_TOKEN bulunamadı!")
    sys.exit(1)

client = MySelfBot()
client.run(TOKEN)
