import hashlib
import json

def sha256_file(file_path):
    sha = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha.update(chunk)
    return sha.hexdigest()

def sha256_json(data):
    encoded = json.dumps(
        data,
        sort_keys=True,
        separators=(',', ':')  # 🔥 critical fix
    ).encode()
    return hashlib.sha256(encoded).hexdigest()
