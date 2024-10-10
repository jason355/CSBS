# Campus Slient Broadcasting System
---
## Overall
本系主要目的為透過Linebot、server、Android app，三部分實現無聲廣播。(Android app 請見: [App](https://github.com/jason355/CSBS-Yunan))
以下是本系統架構圖。
![image](https://github.com/user-attachments/assets/7fe78704-8096-4fec-bbbf-dc97974ea9ce)
發送者透過 Line 應用程式發送廣播訊息，此訊息將會從 Line 伺服器傳入至本系統之 Line Bot, 而此資料將會被存入資料庫。
Server 將會偵測新訊息並且傳送至指定Android App。

## 所需硬體與軟體
### 硬體
- 中央伺服器(或是可長時間運作之電腦)
- 接收端 (目前僅支援 Android 8.0 與 Android 11.0 且螢幕長寬比值約1.5之設備)
### 軟體 (安裝在中央伺服器)
- python 3.7以上
- MySQL (shell、workbench, server)
- Ngrok (供 Line Bot 使用)

## Line Bot
![image](https://github.com/user-attachments/assets/8ffae464-efbc-4df3-a43f-ff7832545b2d)

## Server
