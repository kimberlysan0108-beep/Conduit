import json, math
from pathlib import Path
from backend.policies.retrieval import Retriever
QUERIES=[('charged after cancellation refund',{'refund'}),('who approves high amount refund',{'authorization','refund'}),('stop subscription cancel',{'cancel'}),('shipping tracking address replacement',{'order'}),('credit exception approved account',{'credit'})]
def evaluate():
    rows=[];r=Retriever()
    for q,relevant in QUERIES:
        hits=[x['id'] for x in r.search(q,3)]
        gain=[int(x in relevant) for x in hits]
        dcg=sum(g/math.log2(i+2) for i,g in enumerate(gain)); ideal=sum(1/math.log2(i+2) for i in range(min(3,len(relevant))))
        rows.append({'query':q,'hits':hits,'recall_at_3':sum(gain)/len(relevant),'mrr':next((1/(i+1) for i,g in enumerate(gain) if g),0),'ndcg_at_3':dcg/ideal})
    return {'queries':len(rows),'metrics':{k:sum(x[k] for x in rows)/len(rows) for k in ['recall_at_3','mrr','ndcg_at_3']},'rows':rows}
if __name__=='__main__':
    result=evaluate();Path('docs/experiments/retrieval.json').write_text(json.dumps(result,indent=2));print(result['metrics'])
