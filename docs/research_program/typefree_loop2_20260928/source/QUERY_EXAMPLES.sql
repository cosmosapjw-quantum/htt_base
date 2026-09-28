-- sqlite3 THEORY_INHERITANCE.sqlite < QUERY_EXAMPLES.sql
-- Historical support status is not this loop's proof status.
SELECT classification, count(*) FROM original_items GROUP BY classification;
SELECT current_evidence, inheritance_action, count(*)
FROM normalized_claims GROUP BY current_evidence, inheritance_action;

-- Exact source-qualified candidate excerpts and successors.
SELECT p.anchor_id, p.proposed_id, p.title, p.source_path,
       n.inheritance_action, n.successor_ids_json
FROM proposals p JOIN normalized_claims n ON n.source_key=p.anchor_id
WHERE n.manual_review=1 ORDER BY p.anchor_id;

-- New statements, actual evidence level and per-claim decision.
SELECT claim_id, title, evidence_status, decision FROM loop_claims ORDER BY claim_id;
SELECT claim_id, statement, assumptions_json FROM loop_claims WHERE claim_id='TF-P2';

-- Search original catalog snippets; this query does not reprove them.
SELECT id, kind, title FROM text_search
WHERE text_search MATCH '"vorticity" OR "acceleration"' LIMIT 30;

-- Exact historical proof/source binding.
SELECT o.item_id,o.title,o.classification,s.path,s.git_blob,s.observed_commit,s.line
FROM original_items o JOIN occurrences s USING(item_id)
WHERE o.item_id='59dc094e5ed3ce17e01f2e2ecbdd2d1a';

-- Latest checkpoint inventory is separate from the older catalog baseline.
SELECT count(*) AS checkpoint_files FROM checkpoint_sources;
SELECT path,git_blob,review_scope FROM checkpoint_sources
WHERE path LIKE '%MES_GENERALIZED_TENSOR_R2%';

-- Same exact words, preserved historical version and finite review scope.
SELECT source_kind,source_key,historical_status,current_evidence,proof_obligations
FROM normalized_claims WHERE manual_review=1;
