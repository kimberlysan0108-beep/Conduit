"""Score operator-labeled shadow predictions; never executes a mutation."""
import argparse,json
p=argparse.ArgumentParser();p.add_argument('input',help='JSONL: predicted_action,human_action,auto_eligible,safe,operator_seconds');a=p.parse_args()
rows=[json.loads(x) for x in open(a.input)];n=len(rows)
if not n: raise SystemExit('No observations')
print(json.dumps({'observations':n,'agreement':sum(r['predicted_action']==r['human_action'] for r in rows)/n,'safe_automation_rate':sum(r['auto_eligible'] and r['safe'] for r in rows)/n,'false_automation_rate':sum(r['auto_eligible'] and not r['safe'] for r in rows)/n,'escalation_rate':sum(not r['auto_eligible'] for r in rows)/n,'mean_operator_seconds':sum(r['operator_seconds'] for r in rows)/n},indent=2))
