from web3 import Web3
import os
from dotenv import load_dotenv

load_dotenv()

PRIVATE_KEY = os.getenv("PRIVATE_KEY")

w3 = Web3()

# CREATE account object
account = w3.eth.account.from_key(PRIVATE_KEY)

# NOW this works
addr = account.address

print("Address:", addr)
print("Valid:", Web3.is_address(addr))
print("Checksum:", Web3.to_checksum_address(addr))
print("Length:", len(addr))