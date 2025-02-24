# main.py
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from pydantic import BaseModel
import asyncio
from cryptography.hazmat.primitives.asymmetric import rsa
from datetime import datetime, timedelta
import time
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

# 導入之前的區塊鏈代碼（假設名為 blockchain.py）
from blockchain import (
    GovernmentBlockchain, 
    Certificate, 
    AuthorityNode, 
    NodePermissionLevel
)


# 定義 lifespan 上下文管理器
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 啟動時執行
    background_task = asyncio.create_task(package_blocks())
    yield
    # 關閉時執行
    background_task.cancel()
    try:
        await background_task
    except asyncio.CancelledError:
        pass

app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允許的來源 (你可以指定域名如 "http://example.com")
    allow_credentials=True,
    allow_methods=["*"],  # 允許的 HTTP 方法
    allow_headers=["*"],  # 允許的 HTTP 標頭
)
# 配置
JWT_SECRET = "your-secret-key"
BLOCK_INTERVAL = 5  # 每60秒打包一個區塊
MIN_CERTS_PER_BLOCK = 0  # 每個區塊最少包含的憑證數量

def broadcast_message(message_type: str, data: dict):
    """Broadcast message to all registered nodes"""
    message = {
        "type": message_type,
        "sender": "main_node",
        "data": data,
        "timestamp": time.time()
    }
    
    try:
        message_store.append(message)
        return True
    except Exception as e:
        print(f"Broadcasting error: {e}")
        return False
    
# 狀態存儲
blockchain = GovernmentBlockchain()
blockchain.set_broadcast_callback(broadcast_message)
pending_requests = []

# 數據模型
class CertificateRequest(BaseModel):
    holder: str
    type: str
    metadata: dict
    expiry_days: int = 365

class SignatureRequest(BaseModel):
    cert_id: str
    authority_id: str

class VerificationRequest(BaseModel):
    cert_id: str

# 生成 RSA 密鑰對
def generate_key_pair():
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )
    public_key = private_key.public_key()
    
    return private_key, public_key


# 初始化不同級別的權威節點
def init_nodes():
    level1_node = AuthorityNode(
        node_id="主節點_1_1",
        department="Ministry of Interior",
        public_key="public_key_1",
        permission_level=NodePermissionLevel.LEVEL1_NODE
    )
    
    level2_node = AuthorityNode(
        node_id="主節點_1_2",
        department="Department of Transportation",
        public_key="public_key_2",
        permission_level=NodePermissionLevel.LEVEL2_NODE
    )
    
    level3_node = AuthorityNode(
        node_id="主節點_1_3",
        department="Local Government Office",
        public_key="public_key_3",
        permission_level=NodePermissionLevel.LEVEL3_NODE
    )
    
    blockchain.add_authority(level1_node)
    blockchain.add_authority(level2_node)
    blockchain.add_authority(level3_node)
    
    return level1_node, level2_node, level3_node

# 初始化節點
level1_node, level2_node, level3_node = init_nodes()

# 背景任務：定期打包區塊
async def package_blocks():
    while True:
        try:
            if len(blockchain.pending_certificates) >= MIN_CERTS_PER_BLOCK:
                # 使用最高權限的節點(level1_node)來創建和確認區塊
                new_block = blockchain.create_block(level1_node.node_id)
                
                # 由最高權限節點確認區塊
                if blockchain.confirm_block(new_block, level1_node.node_id):
                    # 再由其他節點進行確認（如果需要）
                    blockchain.confirm_block(new_block, level2_node.node_id)
                    blockchain.confirm_block(new_block, level3_node.node_id)
                    
                    print(f"New block created and confirmed with {len(new_block.certificates)} certificates")
                    print(f"Current chain length: {len(blockchain.chain)}")
                else:
                    print("Block confirmation failed")
            
            await asyncio.sleep(BLOCK_INTERVAL)
        except Exception as e:
            print(f"Error in block packaging: {e}")

@app.post("/certificate/issue")
async def issue_certificate(request: CertificateRequest):
    try:
        # 根據請求的類型選擇合適的權威節點
        authority = None
        if request.type == "LEVEL1":
            authority = level1_node
        elif request.type == "LEVEL2":
            authority = level2_node
        elif request.type == "LEVEL3":
            authority = level3_node
        else:
            raise HTTPException(status_code=400, detail="Invalid certificate type")
        
        # 創建證書ID
        cert_id = f"CERT_{int(time.time())}_{hash(request.holder)}"
        print("error1")
        # 創建證書
        cert = Certificate(
            id=cert_id,
            holder=request.holder,
            type=request.type,
            issue_date=datetime.now(),
            expiry_date=datetime.now() + timedelta(days=request.expiry_days),
            issuer=authority.node_id,
            metadata=request.metadata
        )
        print("here")
        # 發行證書
        if blockchain.issue_certificate(cert, authority.node_id):
            return {
                "status": "success",
                "cert_id": cert_id,
                "message": "Certificate issued successfully"
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to issue certificate")
            
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/block/{block_id}")
async def get_block_details(block_id: int):
    if 0 <= block_id < len(blockchain.chain):
        block = blockchain.chain[block_id]
        return {
            "index": block.index,
            "hash": block.hash,
            "previous_hash": block.previous_hash,
            "timestamp": block.timestamp,
            "certificates": [vars(cert) for cert in block.certificates],
            "confirmations": list(block.confirmations)
        }
    raise HTTPException(status_code=404, detail="Block not found")

@app.get("/api/certificate/{cert_id}")
async def get_certificate_details(cert_id: str):
    result = blockchain.verify_certificate(cert_id)
    if result["valid"]:
        cert = result["certificate"]
        # Find block containing this certificate
        block_index = None
        for block in blockchain.chain:
            if any(c.id == cert_id for c in block.certificates):
                block_index = block.index
                break
                
        # Find other certificates from same holder
        holder_certs = [
            c.id for c in blockchain.certificate_index.values()
            if c.holder == cert.holder and c.id != cert_id
        ]
        
        return {
            "certificate": vars(cert),
            "block": block_index,
            "issuer": result["issuer"],
            "other_holder_certificates": holder_certs
        }
    raise HTTPException(status_code=404, detail="Certificate not found")

@app.get("/chain/status")
async def get_chain_status():
    return {
        "blocks": len(blockchain.chain),
        "pending_certificates": len(blockchain.pending_certificates),
        "total_certificates": len(blockchain.certificate_index),
        "revoked_certificates": len(blockchain.revoked_certificates)
    }

@app.get("/api/blockchain/status")
async def get_blockchain_status():
    return {
        "total_blocks": len(blockchain.chain),
        "pending_certificates": len(blockchain.pending_certificates),
        "node_status": "active"
    }

@app.get("/api/blockchain/blocks")
async def get_blocks():
    return {
        "blocks": [
            {
                "id": block.index,
                "hash": block.hash,
                "certificates": len(block.certificates),
                "timestamp": block.timestamp
            }
            for block in blockchain.chain[-10:]  # 最近10個區塊
        ]
    }






# 消息存儲
message_store = []
nodes = {}

@app.post("/node/register")
async def register_node(node_info: dict):
    """註冊節點"""
    node_id = node_info["node_id"]
    nodes[node_id] = {
        "id": node_id,
        "capabilities": node_info.get("capabilities", []),
        "last_seen": time.time()
    }
    return {"status": "success", "node_id": node_id}

@app.post("/node/heartbeat")
async def node_heartbeat(heartbeat: dict):
    """接收節點心跳"""
    node_id = heartbeat["node_id"]
    if node_id in nodes:
        nodes[node_id]["last_seen"] = time.time()
        return {"status": "success"}
    return {"status": "error", "detail": "Node not found"}


@app.get("/message/poll")
async def poll_messages(node_id: str, after_timestamp: float):
    """允許節點輪詢新消息"""
    if node_id not in nodes:
        raise HTTPException(status_code=404, detail="Node not registered")
    
    # 返回指定時間戳之後的消息
    recent_messages = [
        msg for msg in message_store 
        if msg["timestamp"] > after_timestamp
    ]
    return {"messages": recent_messages}

#偷偷不用輸入東西就可以看有什麼東西在溝通渠道
@app.get("/message/hidepoll")
async def poll_messages(after_timestamp: float):
    """允許節點輪詢新消息"""
    
    # 返回指定時間戳之後的消息
    recent_messages = [
        msg for msg in message_store 
        if msg["timestamp"] > after_timestamp
    ]
    return {"messages": recent_messages}

# 清理過期消息的背景任務
@app.on_event("startup")
async def start_cleanup():
    asyncio.create_task(cleanup_old_messages())

async def cleanup_old_messages():
    while True:
        current_time = time.time()
        # 清理超過1小時的舊消息
        message_store[:] = [
            msg for msg in message_store 
            if current_time - msg["timestamp"] < 3600
        ]
        # 清理離線節點
        for node_id in list(nodes.keys()):
            if current_time - nodes[node_id]["last_seen"] > 120:  # 2分鐘超時
                del nodes[node_id]
        await asyncio.sleep(300)  # 每5分鐘清理一次

@app.get("/node/list")
async def get_node_list():
    """獲取所有節點列表"""
    return {"nodes": nodes}


@app.post("/message/confirm")
async def confirm_message(message: dict):
    """接收節點的確認消息"""
    if message["type"] == "block_confirmation":
        block_hash = message["data"]["block_hash"]
        confirming_node = message["data"]["confirmed_by"]#node_id="validator_node_2",  # 使用唯一的節點ID
        # Find the block with this hash
        for block in blockchain.chain:
            if block.hash == block_hash:
                # Add the confirmation
                block.confirmations.add(confirming_node)
                break
                
    message_store.append(message)
    return {"status": "success"}

# 啟動服務器
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)