from langchain_community.vectorstores import FAISS
from app.embeddings import get_embeddings

from app.agents.researcher import researcher
from app.agents.verifier import verifier
from app.agents.critic import critic



def load_retriever(index_path: str):
    embeddings = get_embeddings()

    db = FAISS.load_local(
        index_path,
        embeddings,
        allow_dangerous_deserialization=True
    )

    return db.as_retriever(search_kwargs={"k": 10})


def verify_claim_with_rag(claim: str, index_path: str):

    retriever = load_retriever(index_path)

    state = {
        "query": claim,
        "claim_type": "general"
    }

    # ---------- Research ----------
    state = researcher(state, retriever)

    # ---------- Verification ----------
    state = verifier(state)

    # ---------- Critic ----------
    # state = critic(state)
    
    return {
        "label": state.get("verdict"),
        "confidence": state.get("confidence"),
        "similarity": state.get("top_similarity"),
        "grounded": state.get("grounded"),
        "citations": state.get("citations"),
        "top_chunks": state.get("top_3_chunks")
        
    }