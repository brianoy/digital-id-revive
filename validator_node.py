# validator_node.py
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import argparse
import random
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import httpx
import asyncio
import time
from pydantic import BaseModel

from blockchain import (
    GovernmentBlockchain, 
    AuthorityNode, 
    NodePermissionLevel,
    CERT_TYPE_PERMISSIONS
)
# 解析命令列參數
parser = argparse.ArgumentParser(description='Validator Node')
parser.add_argument('--permission-level', type=str, required=True,
                    help='Node permission level (e.g., LEVEL1_NODE)')
parser.add_argument('--node-name', type=str, required=True,
                    help='Node name ID')

args = parser.parse_args()

# 將字符串轉換為 NodePermissionLevel 枚舉
THIS_NODE_PR = getattr(NodePermissionLevel, args.permission_level)
NODE_NAME_ID = args.node_name

'''
THIS_NODE_PR = NodePermissionLevel.LEVEL1_NODE
NODE_NAME_ID = "數發部節點_1"
'''

class BlockchainMessage(BaseModel):
    type: str
    sender: str
    data: dict
    timestamp: float

class HTTPBlockchainNode:
    def __init__(self, node_id: str, relay_url: str, blockchain: GovernmentBlockchain,authority: NodePermissionLevel):
        self.node_id = node_id
        self.relay_url = relay_url.rstrip('/')
        self.blockchain = blockchain
        self.last_poll_time = time.time()
        self.active = False
        self.message_queue = asyncio.Queue()
        self.authority = authority  # Store the authority node reference

    def set_authority(self, authority: AuthorityNode):
        self.authority = authority

    async def start(self):
        """啟動節點"""
        try:
            # 只需註冊節點ID，不需要提供URL
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.relay_url}/node/register",
                    json={
                        "node_id": self.node_id,
                        "capabilities": ["validate", "propose"],
                        "last_seen": time.time()
                    }
                )
                if response.status_code == 200:
                    self.active = True
                    print(f"成功註冊到中繼服務器: {self.relay_url}")
                    
                    # 啟動消息輪詢和心跳
                    asyncio.create_task(self.poll_messages())
                    asyncio.create_task(self.send_heartbeat())
                    asyncio.create_task(self.process_message_queue())
                    return True
                else:
                    print(f"{self.relay_url}/node/register")
                    print(response.status_code)
                    print(f"註冊失敗: {response.text}")
                    return False
        except Exception as e:
            print(f"啟動錯誤: {e}")
            return False

    async def send_heartbeat(self):
        """定期發送心跳"""
        while self.active:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{self.relay_url}/node/heartbeat",
                        json={"node_id": self.node_id}
                    )
                    if response.status_code != 200:
                        print(f"心跳請求失敗: {response.text}")
            except Exception as e:
                print(f"心跳錯誤: {e}")
            await asyncio.sleep(30)

    async def poll_messages(self):
        """輪詢新消息"""
        while self.active:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"{self.relay_url}/message/poll",
                        params={
                            "node_id": self.node_id,
                            "after_timestamp": self.last_poll_time
                        }
                    )
                    if response.status_code == 200:
                        messages = response.json()["messages"]
                        for message in messages:
                            await self.message_queue.put(message)
                            self.last_poll_time = max(
                                self.last_poll_time,
                                message["timestamp"]
                            )
            except Exception as e:
                print(f"輪詢錯誤: {e}")
            await asyncio.sleep(5)

    async def process_message_queue(self):
        """處理消息隊列"""
        while self.active:
            try:
                message = await self.message_queue.get()
                await self.handle_message(message)
                self.message_queue.task_done()
            except Exception as e:
                print(f"消息處理錯誤: {e}")

    async def handle_message(self, message: dict):
        """處理接收到的消息"""
        try:
            if message["type"] == "new_block_proposal":
                block_data = message["data"]["block"]
                if self.verify_block(block_data):
                    await self.send_confirmation(
                        "block_confirmation",
                        {
                            "block_hash": block_data["hash"],
                            "confirmed_by": self.node_id
                        }
                    )
                    print(f"已確認區塊: {block_data['hash']}")

            elif message["type"] == "new_certificate":
                cert_data = message["data"]["certificate"]
                authority_id = message["data"]["authority_id"]
                if self.verify_certificate(cert_data, authority_id):
                    print(f"已驗證憑證: {cert_data['id']}")

        except Exception as e:
            print(f"消息處理錯誤: {e}")

    async def send_confirmation(self, message_type: str, data: dict):
        """發送確認消息"""
        try:
            message = {
                "type": message_type,
                "sender": self.node_id,
                "data": data,
                "timestamp": time.time()
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.relay_url}/message/confirm",
                    json=message
                )
                if response.status_code != 200:
                    print(f"確認消息發送失敗: {response.text}")
        except Exception as e:
            print(f"確認發送錯誤: {e}")

    def verify_block(self, block_data: dict) -> bool:
        """驗證區塊"""
        try:
            # 實作區塊驗證邏輯
            return True
        except Exception as e:
            print(f"區塊驗證錯誤: {e}")
            return False

    def verify_certificate(self, cert_data: dict, authority_id: str) -> bool:
        """驗證憑證"""
        try:
            if not self.authority:
                print("節點權限未設定")
                return False

            cert_type = cert_data.get("type")
            if not cert_type:
                print("沒有憑證錯誤")
                return False

            if cert_type not in CERT_TYPE_PERMISSIONS:
                print(f"未知的憑證類型錯誤: {cert_type}")
                return False

            # Get required permission level for this certificate type
            required_level = CERT_TYPE_PERMISSIONS[cert_type]

            # Check if node has sufficient permission
            has_permission = self.authority <= required_level #原本還有一個.permission_level
            # print(self.authority)
            # print(required_level)
            if not has_permission:
                print(f"驗證權限不足 Required: {required_level}, Node level: {self.authority}")
                return False

            return True

        except Exception as e:
            print(f"憑證驗證錯誤: {e}")
            return False

# FastAPI 應用程序
app = FastAPI()
blockchain = GovernmentBlockchain()
network_node = None

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    global network_node
    
    authority_node = AuthorityNode(
        node_id=NODE_NAME_ID,  # 使用唯一的節點ID
        department="gov_dep_2",
        public_key="1234562278",
        permission_level=THIS_NODE_PR #這邊老實說也意義不明ㄏㄏ
    )
    
    blockchain.add_authority(authority_node)
    
    network_node = HTTPBlockchainNode(
        node_id=authority_node.node_id,
        relay_url="https://xxxxxxx.ngrok.app",  # 主節點URL 記得要加s
        blockchain=blockchain,
        authority=THIS_NODE_PR
    )
    
    success = await network_node.start()
    if success:
        print("驗證節點已成功啟動")
    else:
        print("驗證節點啟動失敗")

@app.get("/status")
async def get_status():
    """獲取節點狀態"""
    return {
        "node_id": network_node.node_id if network_node else None,
        "active": network_node.active if network_node else False,
        "blockchain_height": len(blockchain.chain),
        "pending_certificates": len(blockchain.pending_certificates)
    }

if __name__ == "__main__":
    random_port = random.randint(8000, 9000)
    print(f"在port {random_port}上運作")
    print(f"Node 權限高度: {THIS_NODE_PR}")
    print(f"Node ID: {NODE_NAME_ID}")
    uvicorn.run("validator_node:app", host="0.0.0.0", port=random_port, reload=True)