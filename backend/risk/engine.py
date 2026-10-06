from dataclasses import dataclass, asdict

@dataclass
class Risk:
    score: float
    expected_loss_cents: float
    factors: list[str]
    def json(self): return asdict(self)

def assess(amount, age_days, fraud, confidence, failures=0):
    # Heuristic ranking only: probability is NOT calibrated.
    score = .03 + min(amount / 100000, .35)
    factors = []
    for flag, weight, name in [(age_days < 7, .15, "new_account"), (fraud >= 50, .5, "fraud_flag"), (confidence < .8, .25, "low_model_confidence"), (failures > 0, .1, "tool_failures")]:
        if flag: score += weight; factors.append(name)
    score = min(score, 1.)
    return Risk(round(score, 4), round(score * amount, 2), factors)

def authority(plan, policy, risk, config):
    if not policy.allowed: return "DENY"
    if plan.action == "status": return "READ"
    if risk.score >= .5 or plan.amount_cents > config.confirm_limit_cents: return "HUMAN"
    if plan.action in {"cancel", "address"} or plan.amount_cents > config.auto_limit_cents: return "CONFIRM"
    return "AUTO"
