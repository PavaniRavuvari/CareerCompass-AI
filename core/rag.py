"""FAISS-backed retrieval over the bundled career guide, career profiles and learning resources.

Default embedding: TF-IDF + TruncatedSVD (offline, no key needed).
Set RAG_EMBEDDINGS=gemini to use Gemini embeddings instead.
"""
import os
import re

import faiss
import numpy as np
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer

from . import gemini
from .data import careers, guide, resources


def build_chunks():
    chunks = []
    for sec in re.split(r"\n(?=## )", guide()):
        if sec.strip():
            chunks.append({"source": "Career guide", "text": sec.strip()})
    for c in careers():
        chunks.append({"source": f"Career: {c['title']}", "text": f"{c['title']}: {c['description']} Key skills: {', '.join(c['skills'])}. "
                       f"Salary: {c.get('salary','')}. Outlook: {c.get('outlook','')}. Projects: {', '.join(c.get('projects', []))}."})
    for r in resources():
        chunks.append({"source": f"Resource: {r['title']}", "text": f"{r['title']} ({r['type']}, {r['level']}) teaches {', '.join(r['skills'])}. URL: {r['url']}"})
    return chunks


class RAGIndex:
    def __init__(self, use_gemini: bool | None = None):
        self.chunks = build_chunks()
        texts = [c["text"] for c in self.chunks]
        self.use_gemini = (os.getenv("RAG_EMBEDDINGS", "tfidf") == "gemini") if use_gemini is None else use_gemini
        if self.use_gemini:
            vecs = np.array(gemini.embed(texts), dtype="float32")
        else:
            self.tfidf = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), sublinear_tf=True)
            m = self.tfidf.fit_transform(texts)
            k = max(2, min(128, m.shape[1] - 1, m.shape[0] - 1))
            self.svd = TruncatedSVD(n_components=k, random_state=42)
            vecs = self.svd.fit_transform(m).astype("float32")
        faiss.normalize_L2(vecs)
        self.index = faiss.IndexFlatIP(vecs.shape[1])
        self.index.add(vecs)

    def _embed_query(self, q):
        if self.use_gemini:
            v = np.array(gemini.embed([q]), dtype="float32")
        else:
            v = self.svd.transform(self.tfidf.transform([q])).astype("float32")
        faiss.normalize_L2(v)
        return v

    def search(self, query: str, k: int = 4):
        scores, ids = self.index.search(self._embed_query(query), k)
        return [{**self.chunks[i], "score": float(s)} for s, i in zip(scores[0], ids[0]) if i >= 0]
