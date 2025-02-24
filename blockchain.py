# blockchain.py
import hashlib
import time
from typing import List, Dict, Set
from dataclasses import dataclass
from datetime import datetime
from enum import IntEnum

class CertificateLevel(IntEnum):
    LEVEL1 = 1
    LEVEL2 = 2
    LEVEL3 = 3

class NodePermissionLevel(IntEnum):
    LEVEL1_NODE = 1  # 可以驗證所有憑證
    LEVEL2_NODE = 2  # 可以驗證第二和第三級別的憑證
    LEVEL3_NODE = 3  # 只能驗證第三級別的憑證

# 憑證類型到權限等級的映射
CERT_TYPE_PERMISSIONS = {
    "LEVEL1": CertificateLevel.LEVEL1,
    "LEVEL2": CertificateLevel.LEVEL2, 
    "LEVEL3": CertificateLevel.LEVEL3, 
    "national_id": CertificateLevel.LEVEL1,
    "passport": CertificateLevel.LEVEL1,
    "driver_license": CertificateLevel.LEVEL2,
    "business_reg": CertificateLevel.LEVEL2,
    "birth_cert": CertificateLevel.LEVEL3,
    "marriage_cert": CertificateLevel.LEVEL3
}

@dataclass
class Certificate:
    id: str
    holder: str
    type: str
    issue_date: datetime
    expiry_date: datetime
    issuer: str
    metadata: Dict
    signature: str = ""

class AuthorityNode:
    def __init__(self, node_id: str, department: str, public_key: str, permission_level: NodePermissionLevel):
        self.node_id = node_id
        self.department = department
        self.public_key = public_key
        self.permission_level = permission_level
        self.is_active = True

    def can_verify_certificate(self, cert_type: str) -> bool:
        if cert_type not in CERT_TYPE_PERMISSIONS:
            return False
        return self.permission_level >= CERT_TYPE_PERMISSIONS[cert_type].value

class PoAConsensus:
    def __init__(self):
        self.authorities: Dict[str, AuthorityNode] = {}
        self.required_confirmations = 2
        
    def add_authority(self, authority: AuthorityNode):
        self.authorities[authority.node_id] = authority
    
    def remove_authority(self, node_id: str):
        if node_id in self.authorities:
            self.authorities[node_id].is_active = False
    
    def is_valid_authority(self, node_id: str) -> bool:
        return (node_id in self.authorities and 
                self.authorities[node_id].is_active)

class Block:
    def __init__(self, index: int, certificates: List[Certificate], 
                 timestamp: float, previous_hash: str, authority: str):
        self.index = index
        self.certificates = certificates
        self.timestamp = timestamp
        self.previous_hash = previous_hash
        self.authority = authority
        self.confirmations: Set[str] = set()
        self.hash = self.calculate_hash()
        
    def calculate_hash(self) -> str:
        block_string = (f"{self.index}{[cert.id for cert in self.certificates]}"
                       f"{self.timestamp}{self.previous_hash}{self.authority}")
        return hashlib.sha256(block_string.encode()).hexdigest()

class GovernmentBlockchain:
    def __init__(self):
        self.chain: List[Block] = []
        self.pending_certificates: List[Certificate] = []
        self.consensus = PoAConsensus()
        self.certificate_index: Dict[str, Certificate] = {}
        self.revoked_certificates: Set[str] = set()
        self.broadcast_callback = None  # 新增
        self.create_genesis_block()

    def set_broadcast_callback(self, callback):
        """設置廣播回調函數"""
        self.broadcast_callback = callback

    def create_genesis_block(self):
        genesis_block = Block(0, [], time.time(), "0", "genesis")
        self.chain.append(genesis_block)
    
    def add_authority(self, authority: AuthorityNode):
        self.consensus.add_authority(authority)

    
    def issue_certificate(self, certificate: Certificate, authority_id: str) -> bool:
        if not self.consensus.is_valid_authority(authority_id):
            return False
        
        authority = self.consensus.authorities[authority_id]
        if not authority.can_verify_certificate(certificate.type):
            return False
        
        self.pending_certificates.append(certificate)
        
        # 使用 callback 進行廣播
        if self.broadcast_callback:
            self.broadcast_callback("new_certificate", {
                "certificate": vars(certificate),
                "authority_id": authority_id
            }) #不知道為什麼ai都會在這邊強迫要用asyncio，不要理他們
        return True
    
    def _has_permission(self, authority: AuthorityNode, cert_type: str) -> bool:
        # 根據機關權限等級和憑證類型檢查權限
        permission_map = {
            "national_id": 5,
            "driver_license": 4,
            "business_reg": 4,
            "marriage_cert": 3,
            "birth_cert": 3,
            "LEVEL1": 5,
            "LEVEL2": 4,
            "LEVEL3": 3,
        }
        required_level = permission_map.get(cert_type, 1)
        return authority.permission_level >= required_level
    
    def create_block(self, authority_id: str) -> Block:
        if not self.consensus.is_valid_authority(authority_id):
            raise ValueError("Invalid authority")
        
        previous_block = self.chain[-1]
        new_block = Block(
            len(self.chain),
            self.pending_certificates.copy(),  # 使用複製的清單
            time.time(),
            previous_block.hash,
            authority_id
        )
        return new_block

    def confirm_block(self, block: Block, authority_id: str) -> bool:
        if not self.consensus.is_valid_authority(authority_id):
            return False
        
        if block.index != len(self.chain):
            return False
                
        if authority_id not in block.confirmations:
            block.confirmations.add(authority_id)
        
        if len(block.confirmations) >= 1:
            if self._add_block(block):
                self._update_certificate_index(block)
                self.pending_certificates = self.pending_certificates[len(block.certificates):]
                
                # 使用回調進行廣播
                if self.broadcast_callback:
                    self.broadcast_callback("new_block_proposal", {
                        "block": {
                            "index": block.index,
                            "hash": block.hash,
                            "previous_hash": block.previous_hash,
                            "timestamp": block.timestamp,
                            "authority": block.authority,
                            "certificates": [vars(cert) for cert in block.certificates]
                        }
                    })
                return True
        return False
    
    def _add_block(self, block: Block) -> bool:
        # 添加額外的驗證
        if block.index != len(self.chain):
            return False
        if block.previous_hash != self.chain[-1].hash:
            return False
        
        # 驗證區塊的雜湊值
        if block.hash != block.calculate_hash():
            return False
            
        self.chain.append(block)
        return True
    
    def _update_certificate_index(self, block: Block):
        for cert in block.certificates:
            self.certificate_index[cert.id] = cert
    
    def revoke_certificate(self, cert_id: str, authority_id: str) -> bool:
        if not self.consensus.is_valid_authority(authority_id):
            return False
        
        if cert_id in self.certificate_index:
            self.revoked_certificates.add(cert_id)
            return True
        return False
    
    def verify_certificate(self, cert_id: str) -> Dict:
        if cert_id not in self.certificate_index:
            return {"valid": False, "reason": "Certificate not found"}
        
        if cert_id in self.revoked_certificates:
            return {"valid": False, "reason": "Certificate revoked"}
        
        cert = self.certificate_index[cert_id]
        if cert.expiry_date < datetime.now():
            return {"valid": False, "reason": "Certificate expired"}
        
        return {
            "valid": True,
            "certificate": cert,
            "issuer": self.consensus.authorities[cert.issuer].department
        }

# 使用示例
if __name__ == "__main__":
    # 創建區塊鏈
    gov_chain = GovernmentBlockchain()
    
    # 添加權威節點（各政府部門）
    interior_ministry = AuthorityNode(
        "interior_001", 
        "Ministry of Interior", 
        "public_key_1", 
        5
    )
    transport_dept = AuthorityNode(
        "transport_001", 
        "Department of Transportation", 
        "public_key_2", 
        4
    )
    
    gov_chain.add_authority(interior_ministry)
    gov_chain.add_authority(transport_dept)
    
    # 建立新憑證
    new_cert = Certificate(
        id="DL123456789",
        holder="John Doe",
        type="driver_license",
        issue_date=datetime.now(),
        expiry_date=datetime.now().replace(year=datetime.now().year + 5),
        issuer="transport_001",
        metadata={"vehicle_class": "Type 2", "restrictions": "None"}
    )
    
    # 發行憑證
    gov_chain.issue_certificate(new_cert, "transport_001")
    
    # 創建並確認區塊
    new_block = gov_chain.create_block("transport_001")
    gov_chain.confirm_block(new_block, "transport_001")
    gov_chain.confirm_block(new_block, "interior_001")
    
    # 驗證憑證
    verification = gov_chain.verify_certificate("DL123456789")
    print(verification)