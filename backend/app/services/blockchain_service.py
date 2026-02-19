from web3 import Web3
import json
import os
from dotenv import load_dotenv
load_dotenv()

POLYGON_RPC = os.getenv("POLYGON_RPC")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS")

w3 = Web3(Web3.HTTPProvider(POLYGON_RPC))
account = w3.eth.account.from_key(PRIVATE_KEY)

with open("contract_abi.json") as f:
    abi = json.load(f)

contract = w3.eth.contract(
    address=Web3.to_checksum_address(CONTRACT_ADDRESS),
    abi=abi
)

def store_on_chain(
    document_id,
    pdf_hash,
    result_hash,
    company,
    score,
    risk_level
):
    nonce = w3.eth.get_transaction_count(account.address)

    txn = contract.functions.storeReport(
        document_id,
        pdf_hash,
        result_hash,
        company,
        score,
        risk_level
    ).build_transaction({
        "from": account.address,
    "nonce": nonce,
    "gas": 300000,
    "gasPrice": w3.eth.gas_price
    })

    signed_txn = w3.eth.account.sign_transaction(txn, PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)

    return tx_hash.hex()

def get_document_from_chain(document_id: str):
    result = contract.functions.getReport(document_id).call()

    return {
        "pdf_hash": result[0],
        "result_hash": result[1],
        "company": result[2],
        "score": result[3],
        "risk_level": result[4],
        "timestamp": result[5]
    }
