# digital-id-revive
code by claude and gpt
這才弄兩個禮拜就demo，請OOP魔人手下留情

## 設計理念

原本的主題是公鑰加密，後來延伸變成區塊鏈，覺得可以融合概念算成熟，但石沉大海的數位身分證。不過看完了新聞，一樣看不懂當初發生什麼事，扯的資安也不算是我現階段需要解決的問題，demo得出東西就好。

## 硬體

### 支援nfc的android手機

以android手機+chrome 89後推的nfc api作為讀取/寫入載具，卡片照理來說應該要拿desfire或直接做jcop出來，但是我手上兩個都沒有，所以就拿mifare classic 4k出來頂一下。照理來說nfc api只能使用nfc標籤也就是ntag操作，但是後來發現普通的mifare classic卡，在格式化成NDEF格式後，也能對資料做讀寫。按照原本的文件應該要能做到此功能
> 通訊時建立一次性安全通道傳遞資料，動態產生金鑰進行資料加密

但是classic卡只有儲存結構，不同於desfire類的應用檔案系統，所以只好把issue憑證的功能加密做在前端了，安全不是重點，demo有東西才是重點。

什麼? apple不支援chrome nfc api? ~~那就只能在demo的時候讓他們點區塊鏈瀏覽器了¯_(ツ)_/¯~~


### 卡片

外觀不是重點，著重在感應的部分，將以下基本資料用純文字的方式寫入卡片內，picture原本應該要能做到可以掃描卡片就出現大頭貼，但是4k bytes塞不下，所以只能寫檔名在叫前端去要圖片了。

```json
{
  "nation": "TAIWAN, REPUBLIC OF CHINA",
  "details": {
    "name": {
      "chinese": "陳小林",
      "english": "CHEN XIAO LING"
    },
    "date_of_birth": "1968/06/05",
    "sex": "女 F",
    "issuing_authority": "北市換發 Taipei City",
    "id_number": "A234567890",
    "date_of_issue": "2019/12/21",
    "date_of_expiry": "2020/04/20"
  },
  "picture": "示範1.png",
  "certificate": "hohLg4qHnFAvFT1k1FfeH642JaJ/dUs/RaU7jPex34Odfibhl1u8A5p/B01s1BpEfanrUjw37JR5fVKebpDG2g=="
}
```

certificate來自於前端的加密，內容是`card1`，密碼是`98765432`，使用固定種子，利用RSA具有隨機填充的特性

```javascript
function generateRSAKey(password) {
    const hashedPassword = hashPassword(password);
    const seed = forge.util.hexToBytes(hashedPassword);
    const prng = forge.random.createInstance();
    prng.seedFileSync = () => seed;
    const keypair = forge.pki.rsa.generateKeyPair({
        bits: 512,
        e: 0x10001,
        prng: prng
    });
    
    return keypair;
}
```

## 軟體

### 網路

我使用的網路不能設定Port Forwarding或DMZ，所以買了ngrok域名作穿透，

### 前端


### 後端
fastapi

### 採坑

#### onload不能自動要nfc權限
大坑，試了好久，一定要跟element互動後才可以跳權限出來

## 後記

教授: 如果今天是一個大project應該要直接寫一個app出來

我: ...

## 參考資料
1. https://ws.moi.gov.tw/001/Upload/OldFile/news_file/New%20eID%20%E6%96%B0%E8%BA%AB%E5%88%86%E8%AD%98%E5%88%A5%E8%AD%89%E6%87%B6%E4%BA%BA%E5%8C%85%E7%B0%A1%E5%A0%B1%E5%85%A7%E5%AE%B9.pdf





