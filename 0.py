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
        
        # Son aktiflik (mesaj) zamanlarını tutan sözlük
        self.son_mesaj_zamanlari = {}
        
        # Sessizlik süresi: 3 dakika = 180 saniye
        self.sessizlik_suresi = 180 

    async def on_ready(self):
        print("=========================================")
        print(f"🤖 [{self.user.name}] Giriş Başarılı!")
        print(f"🎯 Toplam {len(self.hedef_kullanicilar)} kullanıcı dinleniyor.")
        print(f"📢 Bildirim Kanalı ID: {self.bildirim_kanal_id}")
        print(f"⏱️ Sessizlik Süresi: 3 dakika (180 sn)")
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
            
            # Bu kullanıcının daha önceki son mesaj zamanını al (Yoksa 0 kabul et)
            son_aktiflik = self.son_mesaj_zamanlari.get(kullanici_id, 0)
            
            # Kritik Değişiklik: Son mesajın üzerinden 3 dakikalık sessizlik geçmiş mi?
            if simdiki_zaman - son_aktiflik >= self.sessizlik_suresi:
                bildirim_kanali = self.get_channel(self.bildirim_kanal_id)
                
                if bildirim_kanali:
                    sunucu_id = message.guild.id if message.guild else "@me"
                    mesaj_linki = f"https://discord.com/channels/{sunucu_id}/{message.channel.id}/{message.id}"
                    
                    bildirim_metni = (
                        f"@everyone\n"
                        f" @everyone **FERİŞTAHİNİ SİKTİĞİM MESAJ GÖNDERDİ XD**\n"
                        f"**Kullanıcı:** {message.author.name} (`{message.author.id}`)\n"
                        f"**Konum:** {message.guild.name if message.guild else 'Özel Mesaj'} / {message.channel}\n"
                        f"**Mesaj Bağlantısı:** {mesaj_linki}\n"
                        f"**İlk Mesaj İçeriği:** {message.content}"
                    )
                    
                    await bildirim_kanali.send(bildirim_metni)
                    print(f"✅ [{message.author.name}] 3 dk sonra ilk kez yazdı, bildirim gönderildi.")
            else:
                # Kullanıcı henüz 3 dakika susmadığı için konuşmaya devam ediyor demektir
                kalan_sessizlik = int(self.sessizlik_suresi - (simdiki_zaman - son_aktiflik))
                print(f"⏳ [{message.author.name}] konuşmaya devam ediyor. Yeni bildirim tetiklenmesi için {kalan_sessizlik} sn sessiz kalmalı.")

            # Kişi her mesaj attığında son mesaj zamanını güncelliyoruz (Süre sıfırlanıyor)
            self.son_mesaj_zamanlari[kullanici_id] = simdiki_zaman

# Render panelinden TOKEN verisini alıyoruz
TOKEN = os.getenv("SELF_TOKEN")

if not TOKEN:
    print("❌ HATA: SELF_TOKEN bulunamadı!")
    sys.exit(1)

client = MySelfBot()
client.run(TOKEN)
