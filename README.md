# digital-id-revive
code by claude and gpt
這才弄兩個禮拜就demo 請OOP魔人請手下留情

## 設計理念

原本的主題是公鑰加密，後來延伸變成區塊鏈，覺得可以融合概念算成熟的就是石沉大海的數位身分證。不過看完了新聞，一樣看不懂當初發生什麼事，扯的資安也不算是我現階段需要解決的問題，demo得出東西就好。

## 硬體


以android手機+chrome89後推的nfc api作為讀取載具，卡片照理來說應該要拿desfire或直接做jcop出來，但是我手上兩個都沒有，所以就拿mifare classic 4k出來頂一下。照理來說nfc api只能使用nfc標籤也就是ntag操作，但是後來發現普通的mifare classic卡可以直接格式化成NDEF格式後再


但但但apple不支援chrome nfc api，那就只能在demo的時候讓他們點區塊鏈瀏覽器了¯_(ツ)_/¯

## 軟體
ngrok作穿透
## 後記

教授: 如果今天是一個大project應該要直接寫一個app出來
我: ...

