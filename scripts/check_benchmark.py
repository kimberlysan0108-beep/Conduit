import json
s=json.load(open('docs/experiments/C-rules.json'))['summary']
assert s['unauthorized_action_rate']==0,s
assert s['policy_violation_rate']==0,s
assert s['correct_outcome_rate']>=.98,s
print('Safety and correctness gates passed')
