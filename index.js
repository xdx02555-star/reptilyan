const express = require('express');
const axios = require("axios");

const app = express();
const PORT = process.env.PORT || 3000;

app.get("/", (req, res) => {
  res.send("Multi-Token Bot Render üzerinde 400ms hızla aktif!");
});

app.listen(PORT, () => {
  console.log(`Sunucu ${PORT} portunda dinleniyor.`);
});

// --- AYARLAR (Environment Variables) ---
const rawTokens = process.env.TOKENS ? process.env.TOKENS.split(",") : [];
const message = process.env.MESSAGE;
const channels = [
  "1467580268075421789",
  "1465058037088784447",
  "1465052769743405128"
];

let currentIndex = 0;
let tokenIndex = 0;

if (rawTokens.length === 0 || !message) {
    console.error("HATA: Render panelinde TOKENS veya MESSAGE bulunamadı!");
} else {
    console.log(`${rawTokens.length} adet token yüklendi. 400ms hızla başlıyor...`);
    // Hız 400ms olarak güncellendi
    setInterval(handleCycle, 400);
}

async function handleCycle() {
  if (rawTokens.length === 0) return;

  const currentChannelId = channels[currentIndex];
  const currentToken = rawTokens[tokenIndex].trim();

  try {
    await axios.post(`https://discord.com/api/v9/channels/${currentChannelId}/messages`, {
      content: message
    }, {
      headers: {
        "Authorization": currentToken,
        "Content-Type": "application/json"
      }
    });
    
    console.log(`✅ Gönderildi: Kanal ${currentChannelId} | Token: ...${currentToken.slice(-4)}`);
  } catch (err) {
    // 429 hatası çok sık gelirse hızı biraz düşürmen gerekebilir
    console.error(`❌ Hata: ${err.response?.status || "Bağlantı"} (Token Index: ${tokenIndex})`);
  }

  currentIndex = (currentIndex + 1) % channels.length;
  tokenIndex = (tokenIndex + 1) % rawTokens.length;
}
