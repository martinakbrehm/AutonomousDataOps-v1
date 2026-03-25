from sentence_transformers import SentenceTransformer
import faiss
import os
import pickle
import numpy as np


class VectorStore:
    def __init__(self, persist_dir=".vectordb", model_name="all-MiniLM-L6-v2"):
        os.makedirs(persist_dir, exist_ok=True)
        self.persist_dir = persist_dir
        self.model = SentenceTransformer(model_name)
        self.index_path = os.path.join(persist_dir, "faiss.index")
        self.meta_path = os.path.join(persist_dir, "meta.pkl")
        self.dim = self.model.get_sentence_embedding_dimension()
        if os.path.exists(self.index_path) and os.path.exists(self.meta_path):
            self.index = faiss.read_index(self.index_path)
            with open(self.meta_path, "rb") as f:
                self.meta = pickle.load(f)
        else:
            self.index = faiss.IndexFlatL2(self.dim)
            self.meta = []

    def add(self, texts, metadatas=None):
        if isinstance(texts, str):
            texts = [texts]
        embs = self.model.encode(texts, convert_to_numpy=True)
        self.index.add(embs.astype(np.float32))
        for i, t in enumerate(texts):
            md = metadatas[i] if metadatas and i < len(metadatas) else {"text": t}
            self.meta.append(md)
        self._save()

    def query(self, text, k=5):
        emb = self.model.encode([text], convert_to_numpy=True).astype(np.float32)
        if self.index.ntotal == 0:
            return []
        D, I = self.index.search(emb, k)
        results = []
        for idx in I[0]:
            if idx < len(self.meta):
                results.append(self.meta[idx])
        return results

    def _save(self):
        faiss.write_index(self.index, self.index_path)
        with open(self.meta_path, "wb") as f:
            pickle.dump(self.meta, f)
