from pymongo import MongoClient

MONGO_URI = (
    "mongodb+srv://aarshdhamsania:9106435150"
    "@cluster0.zshhqce.mongodb.net/esg_db"
    "?retryWrites=true&w=majority&appName=Cluster0"
)

client = MongoClient(MONGO_URI)
db = client.get_database()

db.claims.insert_one({
    "company": "Shell",
    "text": "Net-zero by 2050",
    "score": 0.81,
    "label": "greenwashing",
    "created_at": "2026-02-17"
})

db.claims.create_index("company")
db.claims.create_index("created_at")

print(db.list_collection_names())
