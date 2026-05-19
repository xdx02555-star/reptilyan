import discord
import time
import os
import sys

class MySelfBot(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Render panelinden TARGET_ID verisini alıyoruz
        target_ids_str = os.getenv("TARGET_ID", "")
        
        # Gelen metni virgüllere göre bölüp sayısal ID listesine çeviriyoruz
        self.hedef_kullanicilar = []
        if target_ids_str:
            try:
                self.hedef_kullanicilar = [int(x.strip()) for x in target_ids_str.split(",") if x.strip().isdigit()]
            except Exception as e:
                print(f"❌ TARGET_ID formatı hatalı! Hata: {e}")
        
        # Render panelinden bildirim kanalını alıyoruz
        bildirim_str = os.getenv("SELF_BILDIRIM_KANALI")
        self.bildirim_kanal_id = int(bildirim_str) if (bildirim_str and bildirim_str.isdigit()) else None
        
        # Zamanlayıcı değişkenleri
        self.son_bildirim_zamanlari = {}
        self.cooldown_suresi = 600  # 10 dakika (saniye cinsinden)

    async def on_ready(self):
        print("=========================================")
        print(f"🤖 [{self.user.name}] Giriş Başarılı!")
        print(f"🎯 Toplam {len(self.hedef_kullanicilar)} kullanıcı dinleniyor.")
        print(f"📢 Bildirim Kanalı ID: {self.bildirim_kanal_id}")
        print("=========================================")
        
        if not self.hedef_kullanicilar or not self.bildirim_kanal_id:
            print("❌ HATA: TARGET_ID veya SELF_BILDIRIM_KANALI eksik ya da hatalı!")
            sys.exit(1)

    async def on_message(self, message):
        # Kendi mesajlarımızı es geçiyoruz
        if message.author.id == self.user.id:
            return

        # Mesaj listedeki hedeflerden birine mi ait?
        if message.author.id in self.hedef_kullanicilar:
            simdiki_zaman = time.time()
            kullanici_id = message.author.id
            
            son_zaman = self.son_bildirim_zamanlari.get(kullanici_id, 0)
            
            # 10 dakikalık sessizlik kontrolü
            if simdiki_zaman - son_zaman >= self.cooldown_suresi:
                bildirim_kanali = self.get_channel(self.bildirim_kanal_id)
                
                if bildirim_kanali:
                    sunucu_id = message.guild.id if message.guild else "@me"
                    mesaj_linki = f"https://discord.com/channels/{sunucu_id}/{message.channel.id}/{message.id}"
                    
                    bildirim_metni = (
                        f"🔔 **Hedef Kullanıcı Yeni Konuşma Başlattı!**\n"
                        f"**Kullanıcı:** {message.author.name} (`{message.author.id}`)\n"
                        f"**Konum:** {message.guild.name if message.guild else 'Özel Mesaj'} / {message.channel}\n"
                        f"**Mesaj Bağlantısı:** {mesaj_linki}\n"
                        f"**İlk Mesaj İçeriği:** {message.content}"
                    )
                    
                    await bildirim_kanali.send(bildirim_metni)
                    self.son_bildirim_zamanlari[kullanici_id] = simdiki_zaman
                    print(f"✅ [{message.author.name}] için bildirim kanala gönderildi.")
            else:
                kalan_sure = int(self.cooldown_suresi - (simdiki_zaman - son_zaman))
                print(f"⏳ [{message.author.name}] yazıyor ancak cooldown aktif. Kalan: {kalan_sure} sn.")

# Render panelinden TOKEN verisini alıyoruz
TOKEN = os.getenv("SELF_TOKEN")

if not TOKEN:
    print("❌ HATA: SELF_TOKEN bulunamadı!")
    sys.exit(1)

client = MySelfBot()
client.run(TOKEN)
