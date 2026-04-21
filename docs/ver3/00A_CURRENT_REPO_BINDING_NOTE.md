# 00A. Current Repo Binding Note
## authority-preserving mapping from the ver3 design tree to the active `htt_base` repo

---

## 0. purpose

`docs/ver3/*` 는 설계 authority pack이고, 현재 구현 repo는
`htt_base` 다. 이 문서는 ver3의 abstract module tree를 현재 repo path에
binding 한다.

이 문서는 authority order를 바꾸지 않는다.
충돌이 생기면 항상 `00_AUTHORITY_TREE.md` 와 그 위 문서가 우선이다.

---

## 1. binding rules

1. semantic SSOT는 `docs/ver3/*` 다.
2. 구현은 새 `src/lowell_bianchi/` tree를 만들지 않고 현재 repo에 이식한다.
3. fail-closed rule:
   - mapped path가 비어 있으면 fake fallback을 만들지 않는다.
   - unsupported family/backend는 explicit blocker 또는 no-claim으로 남긴다.
4. output/statistics/fitting은 `PR-10/PR-11` 전까지 authority를 열지 않는다.

---

## 2. module tree binding

| ver3 abstract module | current repo binding |
|---|---|
| `conventions.py` | `htt/src/common/conventions.py` |
| `registry.py` | `htt/bass/background/bianchi_types.py` |
| `geometry.py` | `htt/bass/background/geometry.py`, `htt/bass/background/weyl.py` |
| `background.py` | `htt/bass/background/{constraints,initial_conditions,evolution,rhs}.py` |
| `collision.py` | `htt/bass/collision/*` |
| `transport.py` | `htt/bass/transport/*`, tier-A note via `htt/bass/los/*` |
| `hierarchy.py` | `htt/bass/hierarchy/*`, `htt/bass/closure/*` |
| `visibility.py` | `htt/bass/recombination/*`, `htt/bass/collision/tilted_visibility.py` |
| `backends.py` | `htt/bass/los/*`, `htt/bass/perturbation/*`, selected `htt/bass/spectrum/*` |
| `output.py` | `htt/bass/forward/*`, `htt/bass/observational/*` |
| `validation.py` | `htt/bass/validation/*`, `htt/workspace/contracts/validation_registry.py`, `htt/scripts/* --check` |

---

## 3. PR-00 opened claim

- authority frozen only

Forbidden claims:
- ver3 fully implemented
- all-family runtime complete
- fitting/statistics ready

---

## 4. current packet scope

The first live implementation packet in this repo is:

- `PR-00` authority freeze
- `PR-01` invariant-basis tensor helper freeze

Everything above `PR-01` remains subject to the original ver3 dependency chain.
