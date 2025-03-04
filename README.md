# digital-id-revive

code by claude and gpt

這才弄兩個禮拜就demo，請OOP魔人手下留情

## 設計理念

原本的主軸是公鑰加密，後來延伸變成區塊鏈，覺得可以融合概念算成熟但石沉大海的——數位身分證。不過看完了新聞，一樣看不懂當初發生什麼事，扯的資安也不算是我現階段需要解決的問題，demo得出東西就好。架構上是半集權式的區塊鏈，不需要挖礦，也不會有gas問題、沒有token、只有憑證，固定n秒出塊一次，區塊是空的也照常出塊。主鏈是政府機關，其他驗證節點比較像是附和的角色。

1. 核心架構
   
  * 區塊鏈：使用權威證明(Proof of Authority, PoA)共識機制
   
  * 憑證管理：支援多級別的憑證發行和驗證
   
  * 權威節點：基於權限的分層節點系統

2. 主要技術

  * FastAPI web server
    
  * 自定義區塊鏈實現
    
  * sha256雜湊函數

  * RWD網頁

3. 主要功能

  * 憑證發行 — 根據不同部門和憑證類型進行發行、自動生成憑證uuid、設定憑證有效期

  * 憑證驗證 — 檢查憑證的有效性、驗證發行機構的權限、檢查憑證是否過期或已撤銷

  * 區塊管理 — 定期打包待處理的憑證、多節點確認區塊、維護區塊鏈的完整性和一致性

## 硬體

### 支援nfc的android手機

以android手機+chrome 89後推出的nfc api作為讀取/寫入載具，卡片照理來說應該要拿desfire或直接做jcop出來，但是我手上兩個都沒有，所以就拿mifare classic 4k出來頂一下。照理來說nfc api只能使用nfc標籤也就是ntag操作，但是後來發現普通的mifare classic卡，在格式化成NDEF格式後，也能對資料做讀寫。按照原本的文件應該要能做到此功能：
> 通訊時建立一次性安全通道傳遞資料，動態產生金鑰進行資料加密

但是classic卡只有儲存結構，不同於desfire類的應用檔案系統，所以只好把issue憑證的功能加密做在前端了，安全不是重點，demo有東西才是重點。

什麼? apple不支援chrome nfc api? ~~那就只能在demo的時候讓他們點區塊鏈瀏覽器了¯_(ツ)_/¯~~


### 卡片

卡面外觀不是重點，著重在感應的部分，將`示範卡片的內容`資料夾底下，相對的卡片json檔案以純文字的方式寫入卡片內，picture原本應該要能做到可以掃描卡片就出現大頭貼，但是卡片只有4k bytes 塞不下，所以只能寫檔名在叫前端去要圖片了。

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
|卡片號碼|密碼|內容|
|:-:|:-:|:-:|
|1|98765432|card1|
|2|87654321|card2|
|3|12345678|card3|
|4|99999999|card4|

certificate來自於前端的以下程式碼，內容是`card1`，密碼是`98765432`，使用固定種子，利用RSA具有隨機填充的特性，原本會做出每issue一次憑證就會重新生成並寫回卡片，這邊只有做到驗證而已，所以沒有真的寫回去。

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
### 目錄結構

```
.
│  blockchain.py
│  favicon.ico
│  main.py
│  validator_node.py
│  _run_app.cmd
│  _run_ngrok_app.cmd
│  _run_sub_node_1_1.cmd
│  _run_sub_node_1_2.cmd
│  _run_sub_node_2_1.cmd
│  _run_sub_node_2_2.cmd
│  _run_sub_node_3_1.cmd
│  _run_sub_node_3_2.cmd
│  _set_ngrok.cmd
│  _set_pip.cmd
│
├─python->python.7z解壓縮後的資料夾
├─static
│  │  blockscan.html
│  │  demobottom.jpg
│  │  dID.html
│  │  dID.js
│  │  flag.jpg
│  │  home.html
│  │  issue.html
│  │  ngrok.exe
│  │  _setngrok.cmd
│  │  示範1.png
│  │  示範2.png
│  │  示範3.png
│  └─ 示範4.png
│
└─示範卡片的內容
        1.json
        2.json
        3.json
        4.json
```

### 前端

HTML5、CSS3 (3D transformations)、Vanilla JavaScript、Web NFC API

| 圖片1 | 圖片2 | 圖片3 | 圖片4 |
|---|---|---|---|
| ![螢幕擷取畫面 2025-03-05 013720](https://github.com/user-attachments/assets/193c7535-1fa3-4234-9b66-554a234f4b8c) | ![螢幕擷取畫面 2025-03-05 013753](https://github.com/user-attachments/assets/742f539b-ee5a-435c-8b1c-e016fa6c56fb) | ![螢幕擷取畫面 2025-03-05 013800](https://github.com/user-attachments/assets/014b5603-1fa6-403e-a8ef-e5f8bd683082) | ![螢幕擷取畫面 2025-03-05 013739](https://github.com/user-attachments/assets/e86e41be-1863-435b-8820-2f5b65138cb8)|

### 後端

| 圖片1 | 圖片2 | 圖片3 |
|---|---|---|
| ![螢幕擷取畫面 2025-03-05 013623](https://github.com/user-attachments/assets/1e1dd9e6-6ddc-4f58-9d4d-f545cf27a7bb) | ![螢幕擷取畫面 2025-03-05 013620](https://github.com/user-attachments/assets/07486dc7-1e64-4637-a9af-f5d7cb591efb) | ![螢幕擷取畫面 2025-03-05 013617](https://github.com/user-attachments/assets/3ef1a23b-5c93-49d0-9b7e-5f9523b91ab0) |

我使用的網路不能設定Port Forwarding或DMZ，所以買了ngrok域名作穿透，域名應該會叫`https://xxx.ngrok.app/`。如果要在本地端測試，記得取代全部的網址為`http://127.0.0.1:8000`

#### api實現

使用fastapi、uvicorn套件

|api接口|方式|說明|回應格式
|:-:|:-:|:-:|:-:|
|`/certificate/issue`|POST|發行新憑證|json|
|`/api/certificate/{cert_id}`|GET|取得憑證資訊|json|
|`/chain/status`|GET|取得區塊鏈狀態|json|
|`/node/register`|POST|節點註冊|json|
|`/message/poll`|GET|抓取消息|json|
|`/node/heartbeat`|POST|確認節點上線狀態|json|

### 憑證申請等級

* LEVEL1：最高安全級別->像是房地產轉移

* LEVEL2：中等安全級別->像是申請戶口名簿

* LEVEL3：較低安全級別->像是實名制驗證

### 驗證節點等級

* LEVEL1_NODE：可以驗證所有級別的憑證->像是政府機關

* LEVEL2_NODE：可以驗證第二和第三級別的憑證->像是民間機構

* LEVEL3_NODE：只能驗證第三級別的憑證->像是個人節點

## 踩坑

* onload不能自動要nfc權限，真的大坑，試了好久，一定要跟element互動後(像是click)才可以跳權限出來

* demo 時一次卡了9個節點，後來發現直接被自己的heart beat攻擊(?)到癱瘓，只開3個節點有效解決

* CORS 問題，記得設定好


## 開始使用

1. 解壓縮 `python.7z` 此為可攜式python包，依賴已經在裡面了，無須`pip install`
2. 確保所有static底下的檔案的url都是正確的
3. `_set_ngrok.cmd` 如果要使用ngrok映射，必須先下載[ngrok.exe](https://ngrok.com/downloads/windows?tab=download)放在根目錄，填上token後，cmd打上`"ngrok.exe" http --url=xxx.ngrok.app 8000`啟動ngrok app，用免費的臨時網址也可以喔
4. `_run_app.cmd` 執行主區塊鏈
5. `_run_sub_node_1_1.cmd` 執行驗證子節點，`1_1`代表第一級第一個節點

## 後記

教授: 如果今天是一個大project應該要直接寫一個app出來

我: ...

## 參考資料
1. https://ws.moi.gov.tw/001/Upload/OldFile/news_file/New%20eID%20%E6%96%B0%E8%BA%AB%E5%88%86%E8%AD%98%E5%88%A5%E8%AD%89%E6%87%B6%E4%BA%BA%E5%8C%85%E7%B0%A1%E5%A0%B1%E5%85%A7%E5%AE%B9.pdf

## License
GPL-3.0 license.




