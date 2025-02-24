const demo = document.querySelector("#demo")
const card = demo.querySelector(".card")
const button = demo.querySelector(".card-container")
var ndef;

// 卡片翻面邏輯
function flipCard() {
  card.classList.toggle("facedown")
  const isFacedown = card.classList.contains("facedown")
  card.style.animationName = isFacedown
    ? "flip-to-back"
    : "flip-to-front"

  const shadow = demo.querySelector(".shadow")
  shadow.style.animationName = isFacedown
  ? "shadow-to-back"
  : "shadow-to-front"
  setAccessibility(card)
}

function setAccessibility(card) {
  const isFacedown = card.classList.contains("facedown")
  const front = card.querySelector(".front")
  const back = card.querySelector(".back")
  
  front.setAttribute("aria-hidden", isFacedown.toString())
  back.setAttribute("aria-hidden", (!isFacedown).toString())
}


function setupContent() {
  const front = demo.querySelector(".front")
  const back = demo.querySelector(".back")
  
  front.innerHTML = `
      <div class="id-card">
        <div class="nfc-container">
          <div class="wave"></div>
          <div class="phone"></div>
        </div>
        <div class="text">請靠近感應區域以進行 NFC 感應</div>
      </div>
  `
  
  back.innerHTML = ``
}

function update_front(content){
    const front = demo.querySelector(".front")
    front.innerHTML = content;
}

function read_normal(){
    let _ = `        
      <div class="id-card">
        <div class="nfc-container">
          <div class="wave"></div>
          <div class="phone"></div>
        </div>
        <div class="text">請靠近感應區域以進行 NFC 感應</div>
      </div>
    `
    update_front(_)
}

function read_fail(){
    let _ = ` 
    
    <div class="id-card">
        <div class="nfc-container">
            <div class="phone"></div>
            <div class="fail-icon">
                <span>!</span>
            </div>
        </div>
        <div class="text">感應到錯誤的卡片</div>    
    </div>
    `
    update_front(_)
    setTimeout(()=>{
        read_normal()
    },2300)
    
}

window.onload = () => {
    // Add the modal HTML to the document
    document.body.insertAdjacentHTML('beforeend', modalHTML);
    
    // Add the styles to the document
    const styleElement = document.createElement('style');
    styleElement.textContent = styleUpdate;
    document.head.appendChild(styleElement);
    
    setupContent(); // 初始化卡片
    //setupButton(); // 初始化按鈕event
    showNfcModal(); // 顯示 NFC 權限請求模態框
    
    if (/Chrome\/(\d+\.\d+.\d+.\d+)/.test(navigator.userAgent)) {
        if (89 > parseInt(RegExp.$1)) {
            console.log('Warning! Keep in mind this sample has been tested with Chrome ' + 89 + '.');
        }
    }
/*
    if (!("NDEFReader" in window)) {
        console.log("Web NFC is not available. Use Chrome on Android.");
    }*/
};

async function read_card() {
    if (!ndef) {
        ndef = new NDEFReader(); // 只初始化一次
    }
    await ndef.scan();
    //log("User clicked scan button");
    try {
        //log("> Scan started");

        ndef.addEventListener("readingerror", () => {
            read_fail()
            //log("Argh! Cannot read data from the NFC tag. Try another one?");
        });

        ndef.addEventListener("reading", ({ message, serialNumber }) => {
            // log(`> Serial Number: ${serialNumber}`);
            //log(`> Records: (${message.records[0].data})`);
            read_data_pros(message)

        });
    } 
    catch (e) {
        read_fail()
        // update_front(e);
    }
}

function showNfcModal() {
    const modal = document.getElementById('nfcModal');
    modal.style.display = 'flex';
    
    const confirmButton = document.getElementById('confirmNfc');
    confirmButton.addEventListener('click', async () => {
        modal.style.display = 'none';
        read_card();
        console.log("get confirm successfully")
    });
}


function read_data_pros(){
    try{
        const decoder = new TextDecoder();
        for (const record of event.message.records) {
            const text = decoder.decode(record.data)
            let json_read = JSON.parse(text)
            
            update_front(jsonToHtml(json_read))
        }
    }
    catch(e){
        read_fail()
        // update_front(e);
    }
}


// First add this CSS to your existing <style> section
const styleUpdate = `
.modal-overlay {
    display: none;
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0, 0, 0, 0.5);
    z-index: 1000;
    justify-content: center;
    align-items: center;
}

.modal-content {
    background-color: white;
    padding: 2rem;
    border-radius: 0.5rem;
    max-width: 80%;
    width: 400px;
    text-align: center;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.modal-buttons {
    margin-top: 1.5rem;
    display: flex;
    justify-content: center;
    gap: 1rem;
}

.modal-button {
    padding: 0.5rem 1.5rem;
    border: none;
    border-radius: 0.25rem;
    cursor: pointer;
    font-size: 1rem;
}

.modal-button.primary {
    background-color: #007bff;
    color: white;
}

.modal-button.primary:hover {
    background-color: #0056b3;
}
`;

// Add this HTML to your body
const modalHTML = `
<div class="modal-overlay" id="nfcModal">
    <div class="modal-content">
        <h3>NFC 權限請求</h3>
        <p>此網頁需要 NFC 通訊，請確認 NFC 權限以繼續使用。</p>
        <div class="modal-buttons">
            <button class="modal-button primary" id="confirmNfc">確定</button>
        </div>
    </div>
</div>
`;

function setupButton() {
    // button.addEventListener("click", () => {flipCard(card)})
    button.addEventListener("click", async () => {await read_card()})
}


function jsonToHtml(jsonObj) {
    return `
    <div class="id-card">
        <div class="header">
            <div class="title">
                <img class="flag" src="flag.jpg"> 中華民國國民身分證 TAIWAN,REPUBLIC OF CHINA     NATIONAL IDENTITY CARD
            </div>
        </div>
    <div class="h">
        <div class="v">

            <div class="name-section">
                <div class="name label">姓名 Name</div>
                <div class="value">${jsonObj.details.name.chinese}</div>
                <div class="value">${jsonObj.details.name.english}</div>
            </div>
            <br>
            <div class="h">
            <div class="v">
            <div class="info-section">
                <div class="label">出生日期 Date of Birth</div>
                <div class="value">${jsonObj.details.date_of_birth}</div>
            </div>

            <div class="info-section">
                <div class="label">性別 Sex</div>
                <div class="value">${jsonObj.details.sex}</div>
            </div>

            <div class="info-section">
                <div class="label">發證機關 Authority</div>
                <div class="value">${jsonObj.details.issuing_authority}</div>
            </div>
            </div>
            <div class="v">
            <div class="info-section">
                <div class="label">統一編號 ID No.</div>
                <div class="value">${jsonObj.details.id_number}</div>
            </div>

            <div class="info-section">
                <div class="label">發證日期 Date of Issue</div>
                <div class="value">${jsonObj.details.date_of_issue}</div>
            </div>

            <div class="info-section">
                <div class="label">有效期限 Date of Expiry</div>
                <div class="value">${jsonObj.details.date_of_expiry}</div>
            </div>
            </div>
        </div>
        </div>
        <img class="picture" src="${jsonObj.picture}">
    </div>
    </div>
    `;
}






