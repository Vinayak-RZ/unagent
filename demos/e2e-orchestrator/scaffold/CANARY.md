# Canary checklist

> simulation != production

- shadow the candidate function on the same traffic
- compare outcome vector: failure, cost, latency, variance, policy
- promote only if intervals and safety gates pass; else ABSTAIN/demote
- simulation != production
