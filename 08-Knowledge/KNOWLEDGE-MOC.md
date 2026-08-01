---
type: moc
topic: knowledge
created: 2026-07-30
updated: 2026-07-30
tags: [moc, knowledge, navigation]
---

# Knowledge MOC

Navigation hub for the HermesForge knowledge base.

## Insights by Connection Type

```dataview
TABLE rows.file.name AS "Insights", length(rows) AS "Count"
FROM "08-Knowledge/Insights"
WHERE type = "insight"
GROUP BY connection_type
SORT length(rows) DESC
```

## Insights by Actionability

```dataview
TABLE actionability, connection_type, sources
FROM "08-Knowledge/Insights"
WHERE type = "insight"
SORT actionability DESC, file.name ASC
```

## Murphy Book by Concept Type

```dataview
TABLE length(rows) AS "Notes"
FROM "08-Knowledge/Trading-Systems/technical-analysis-financial-markets-murphy"
WHERE type = "atomic-note"
GROUP BY concept_type
SORT length(rows) DESC
```

## Murphy Book by Topic

```dataview
TABLE length(rows) AS "Notes", rows.concept_type AS "Types"
FROM "08-Knowledge/Trading-Systems/technical-analysis-financial-markets-murphy"
WHERE type = "atomic-note"
GROUP BY topic
SORT length(rows) DESC
```

## Skills

```dataview
TABLE file.name
FROM "08-Knowledge/Skills"
SORT file.name ASC
```

## Related
- [[STRATEGIES-MOC]]
- [[GRAPH-INVENTORY-AND-ONTOLOGY]]
