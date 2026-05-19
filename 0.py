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
        
        # Kullanıcıların son mesaj zamanını tutar
        self.son_mesaj_zamanlari = {}
        # Kullanıcının şu an aktif bir konuşma içinde olup olmadığını tutar (True/False)
        self.aktif_konusmada_mi = {}
        
        # Konuşmanın bittiğini anlamak için gereken sessizlik süresi: 3 dakika (180 saniye)
        self.sessizlik_suresi = 180 

    async def on_ready(self):
        print("=========================================")
        print(f"🤖 [{self.user.name}] Giriş Başarılı!")
        print(f"🎯 Toplam {len(self.hedef_kullanicilar)} kullanıcı dinleniyor.")
        print(f"📢 Bildirim Kanalı ID: {self.bildirim_kanal_id}")
        print(f"⏱️ Sessizlik Kriteri: {self.sessizlik_suresi} sn (3 Dakika)")
        print("=========================================")
        
        if not self.hedef_kullanicilar or not self.bildirim_kanal_id:
            print("❌ HATA: TARGET_ID veya SELF_BILDIRIM_KANALI eksik ya da hatalı!")
            sys.exit(1)

    async def on_message(self, message):
        # Kendi mesajlarımızı eliyoruz
        if message.author.id == self.user.id:
            return

        # Mesaj listedeki hedeflerden birine mi ait?
        if message.author.id in self.hedef_kullanicilar:
            simdiki_zaman = time.time()
            kullanici_id = message.author.id
            
            # Kullanıcının geçmiş verilerini sözlükten çekiyoruz (Yoksa varsayılan atıyoruz)
            son_aktiflik = self.son_mesaj_zamanlari.get(kullanici_id, 0)
            konusma_durumu = self.aktif_konusmada_mi.get(kullanici_id, False)
            
            # Önce kontrol et: Kullanıcı en son mesajından sonra 3 dakika boyunca sustu mu?
            # Eğer 3 dakika sustuysa, önceki konuşma bitmiştir. Durumu sıfırla.
            if simdiki_zaman - son_aktiflik >= self.sessizlik_suresi:
                konusma_durumu = False
                self.aktif_konusmada_mi[kullanici_id] = False

            # 💡 ANA MANTIK ALANI:
            # Eğer kullanıcı şu an aktif bir konuşmada DEĞİLSE (Yeni konuşma başlatıyorsa)
            if konusma_durumu is False:
                bildirim_kanali = self.get_channel(self.bildirim_kanal_id)
                
                if bildirim_kanali:
                    sunucu_id = message.guild.id if message.guild else "@me"
                    mesaj_linki = f"https://discord.com/channels/{sunucu_id}/{message.channel.id}/{message.id}"
                    
                    bildirim_metni = (
                        f"@everyone\n"
                        f"🔔 **Hedef Kullanıcı Yeni Bir Konuşma Başlattı!**\n"
                        f"**Kullanıcı:** {message.author.name} (`{message.author.id}`)\n"
                        f"**Konum:** {message.guild.name if message.guild else 'Özel Mesaj'} / {message.channel}\n"
                        f"**Mesaj Bağlantısı:** {mesaj_linki}\n"
                        f"**İlk Mesaj:** {message.content}"
                    )
                    
                    await bildirim_kanali.send(bildirim_metni)
                    print(f"✅ [{message.author.name}] yeni konuşma başlattı. İlk bildirim gönderildi.")
                
                # Kullanıcı artık konuşma başlattığı için durumunu TRUE yapıyoruz.
                # Konuşması bitene kadar (3 dk susana kadar) bir daha bildirim gitmeyecek.
                self.aktif_konusmada_mi[kullanici_id] = True
            else:
                # Kullanıcı zaten aktif bir konuşmanın içinde yazmaya devam ediyor.
                # Konuşma devam ettiği için süre sınırlaması olmadan sessizce loglanır, bildirim atılmaz.
                print(f"💬 [{message.author.name}] konuşmaya devam ediyor. (Bildirim gönderilmedi)")

            # Kullanıcı her mesaj attığında son hareket saatini güncelliyoruz
            self.son_mesaj_zamanlari[kullanici_id] = simdiki_zaman

# Render panelinden TOKEN verisini alıyoruz
TOKEN = os.getenv("SELF_TOKEN")

if not TOKEN:
    print("❌ HATA: SELF_TOKEN bulunamadı!")
    sys.exit(1)

client = MySelfBot()
client.run(TOKEN)
