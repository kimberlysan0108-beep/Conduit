import json, math, re
from pathlib import Path
from collections import Counter
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
import httpx

def tokens(s): return re.findall(r"[a-z0-9]+", s.lower())

class Retriever:
    """BM25 + vector cosine, reciprocal-rank fusion and transparent reranking.
    Offline vectors are TF-IDF, not semantic embeddings. Optional API embeddings.
    """
    def __init__(self, config=None):
        self.docs = json.loads(Path(__file__).with_name('documents.json').read_text())
        self.config = config
        self.corpus = [tokens(x['text']) for x in self.docs]
        self.vectorizer = TfidfVectorizer()
        self.vectors = self.vectorizer.fit_transform([d['text'] for d in self.docs])

    def search(self, query, k=3):
        n = len(self.docs); avg = sum(map(len, self.corpus))/n
        lexical=[]
        for doc in self.corpus:
            counts=Counter(doc); score=0.
            for term in tokens(query):
                df=sum(term in d for d in self.corpus)
                idf=math.log(1+(n-df+.5)/(df+.5))
                f=counts[term]
                score += idf*f*2.5/(f+1.5*(.25+.75*len(doc)/avg))
            lexical.append(score)
        mode='bm25+tfidf'
        if self.config and self.config.embedding_model:
            with httpx.Client(timeout=20) as client:
                r=client.post(self.config.llm_base_url+'/embeddings', headers={'Authorization':'Bearer '+self.config.llm_api_key},json={'model':self.config.embedding_model,'input':[query]+[d['text'] for d in self.docs]})
                r.raise_for_status()
            arr=np.array([x['embedding'] for x in sorted(r.json()['data'],key=lambda d:d['index'])])
            vector=(arr[1:]@arr[0]/(np.linalg.norm(arr[1:],axis=1)*np.linalg.norm(arr[0])+1e-12)).tolist()
            mode='bm25+api_embeddings'
        else:
            vector=(self.vectors@self.vectorizer.transform([query]).T).toarray().ravel().tolist()
        ranks=[sorted(range(n),key=lambda i:s[i],reverse=True) for s in [lexical,vector]]
        fused={i:sum(1/(60+r.index(i)+1) for r in ranks) for i in range(n)}
        # Exact title overlap is a small, deterministic reranking feature.
        for i,d in enumerate(self.docs): fused[i] += .001*len(set(tokens(query)) & set(tokens(d['title'])))
        return [{**self.docs[i], 'score':round(fused[i],6),'retrieval_mode':mode} for i in sorted(fused,key=fused.get,reverse=True)[:k]]
