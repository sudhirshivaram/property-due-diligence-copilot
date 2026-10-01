# Stage 2 — Chunking Strategy Research and Experiments

## 1. Purpose and grounding

Create `notebooks/02_chunking_experiments.ipynb` as a guided, reproducible comparison of fixed-length, structural, parent-child, and subsequently hybrid chunking.

The sole corpus-building input will be `data/processed/01_parsed_docx_structure.json`. No implementation or file changes have been made.

Repository inspection established:

- Stage 1 validation reports **PASS** across **21 documents**.
- The artifact contains **30,670 full-text blocks**, with candidate markers for Parts, Chapters, Sections, Articles, § provisions, and Annexes.
- **297 unclassified full-text headings** remain unresolved. Marker candidates are evidence, not an established legal hierarchy.
- Metadata values retain their original text and source locations.
- Mentor `corpus/chunks.jsonl`, inside the source archive, contains **94 chunks covering 19 documents**. Its builder uses separate Markdown excerpts; sample chunks include English summaries and generated context prefixes. No `chunks.json` was found in that archive.
- The broader project plan has older stage numbering. This notebook will follow the user’s current Stage 2 definition.

Success means producing inspectable chunks, reproducible comparisons, and evidence-backed recommendations for further validation. It does **not** mean selecting production parameters or establishing retrieval performance.

## 2. Step-by-step notebook sequence

### Step 1 — Explain the strategies and experiment boundaries

Introduce the distinction between:

| Strategy | Main question |
|---|---|
| Fixed-length | What happens when length determines boundaries? |
| Structural | What happens when evidenced legal units determine boundaries? |
| Parent-child | Can small units remain connected to useful larger context? |
| Hybrid | Which observed failures justify combining these approaches? |

Explain that parent-child organization is a relationship model: its children still need a splitting method. It is not mutually exclusive with structural or fixed-length splitting.

Use official documentation as conceptual references, without adding framework dependencies. LangChain distinguishes length-based, text-structure, and document-structure splitting; LlamaIndex documents explicit relationships between hierarchical chunks. These describe mechanisms, not optimal parameters for this corpus. [LangChain splitter documentation](https://docs.langchain.com/oss/python/integrations/splitters), [LlamaIndex hierarchical parser documentation](https://docs.llamaindex.ai/en/v0.10.22/api_reference/node_parsers/hierarchical/).

Every experiment will use the same teaching template:

1. **What** is being tested?
2. **Why** might it help this corpus?
3. **How** are boundaries or relationships constructed?
4. Which intermediate output should be inspected?
5. Which design choices and trade-offs matter?
6. Which observations favor or disfavor it?
7. What remains unproven?

### Step 2 — Load and verify the Stage 1 interface

Load the existing JSON without reparsing the DOCX.

Display:

- Schema version, artifact fingerprint, original DOCX fingerprint, and validation status.
- Document inventory and full-text block counts.
- Structural-marker counts and unresolved warnings.
- One document descriptor and representative annotated blocks.

Check required fields, unique IDs, document membership, ordered positions, and the recorded validation result. Stop with a clear error for unsupported or inconsistent input.

Build experimental text streams separately for each document’s `full_text` region:

- Preserve `raw_text` exactly.
- Insert a documented newline between blocks and track it as an added separator.
- Maintain reversible mappings from stream offsets to block IDs and character offsets.
- Identify delimiter-only full-text markers through Stage 1 evidence; record them separately rather than treating them as legal text.
- Retain publication history, navigation, unclassified content, and empty-block evidence.
- Exclude `reference_rules`, front matter, and metadata tables from chunk payloads; retain their existing records separately.

Use Python Unicode character counts for the initial experiments. They are reproducible, require no model choice, and preserve exact source offsets. Do not label them tokens or estimate Bulgarian tokens using an English character/token ratio.

### Step 3 — Select and freeze representative content

Start with the following actual corpus locations. Positions refer to Stage 1 body positions; the notebook will store full block IDs and reviewed span boundaries.

| Example | Actual starting point | Why inspect it? |
|---|---|---|
| Normal Article | Document 1, ЗУТ, Чл. 1, positions 61–62 | Multi-paragraph provision with an inline amendment note |
| Short neighboring Articles | Document 1, Чл. 2 and Чл. 2а, starting at 63–64 | Tiny units, Cyrillic suffixes, and accidental merging |
| Nested structure | Document 1, Chapter III / Section I / Чл. 10, starting at 110–114 | Heading labels and titles occupy separate blocks |
| Long Article | Document 2, Наредба № 3, Чл. 7, starting at 2779 | Preliminary candidate span is about 18,724 characters before added separators; verify its endpoint before use |
| § provisions | Document 1, additional and transitional/final provision regions | Repeated numbering, amendment sections, and misleading global § identifiers |
| Annex | Document 2, Приложение № 1, starting at 2848 | Forms and numbered content that should not be treated automatically as Articles |
| Very long paragraph | Document 11, EU regulation, position 25737, 3,600 characters | A single paragraph can exceed a candidate chunk size |
| Publication history | Document 1, position 56, 4,077 characters | History alone can dominate or exceed a chunk |
| EU Article | Document 11, an evidenced `Член` heading and its body | Different heading and Article conventions |
| Weakly structured text | Document 16 or 21, plus an unclassified heading | Tests behavior where Article-based hierarchy is inappropriate |

For § examples, inspect the enclosing headings explicitly to distinguish additional provisions from transitional/final provisions; do not classify every § identically.

The notebook will:

- Inventory candidate unit and paragraph lengths across all documents.
- Show the median, upper percentiles, and longest candidates.
- Add a median-sized Article if the initial normal example is atypical.
- Review surrounding blocks before confirming each sample.
- Freeze a sample manifest containing source spans, selection rationale, and unresolved boundary questions.

Run strategies on the **same complete source documents** containing these samples, then display chunks intersecting each selected span. This avoids giving fixed-length chunking artificial advantages by restarting its windows at handpicked Article boundaries. Show any text extending outside the selected sample.

### Step 4 — Create shared inspection displays

Use small Python helpers and notebook HTML displays, with no new UI framework.

For every strategy, show:

- Configuration and sample ID.
- Chunk ordinal and reproducible chunk ID.
- Document title and document ID.
- Character count.
- Beginning and end previews.
- Expandable full text.
- Source block spans and character offsets.
- Evidenced structural context and uncertainty.
- Actual overlap with adjacent chunks.
- Whether a reviewed Article, § provision, Annex, or paragraph was split.
- Whether a chunk combines multiple legal units.

Provide a source-text panel alongside the outputs. Highlight cut points and overlaps without modifying stored text. Keep generated context labels visually separate from verbatim source text.

For parent-child outputs, show a relationship table and the complete selected parent beside its ordered children.

### Step 5 — Fixed-length baseline

**What and how:** Slice each document stream into exact character windows.

Test:

| Parameter | Initial candidates |
|---|---|
| Chunk length | 1,000; 2,000; 4,000 characters |
| Overlap | 0%; 10%; 20% of chunk length |

These nine configurations are experimental probes. The range exposes both ordinary provisions and observed 3,600–4,077-character paragraphs to different splitting conditions; it is not a production recommendation.

Use stride `length − overlap`, stop after covering the document end, and never cross document boundaries. Keep strict slicing distinct from boundary-aware fallback experiments.

**Inspect:** Broken words, detached Article labels, incomplete lists, separated exceptions, overlapping history text, and chunks mixing unrelated provisions.

**Advantages:** Simple, deterministic, predictable maximum size, and a useful control.

**Disadvantages:** Ignores legal boundaries; overlap adds duplication without guaranteeing missing context is restored.

**Favor it if:** Most inspected passages remain understandable across several sizes, with limited fragmentation and duplication.

**Disfavor it if:** Even larger windows repeatedly separate conditions from exceptions, detach citations, or combine unrelated provisions.

### Step 6 — Document-aware structural baseline

**What:** Construct provisional units using Stage 1 evidence, without imposing a size limit initially.

**How:**

- Inspect Part, Chapter, Section, Article, §, and Annex candidates alongside neighboring text.
- Associate separate heading labels and titles only where their adjacency and content support that interpretation.
- End units at the next supported boundary of the appropriate scope.
- Reset structural context at document boundaries and evidenced transitions.
- Preserve content before the first provision and between units as explicit residual spans.
- Retain ambiguous sections as unclassified spans with warnings.
- Do not infer hierarchy solely from Word heading levels or split at inline legal citations.
- Use source positions to distinguish repeated Article/§ labels in different amendment sections.

Display the proposed boundary ledger before chunk generation: label, source location, proposed role, evidence, and uncertainty. Apply explicit reviewed overrides to representative samples; keep unreviewed corpus-wide statistics labeled provisional.

**Inspect:** Complete provisions, heading attachment, Annex boundaries, unusually small or large chunks, unclassified content, and false marker detections.

**Advantages:** Potentially preserves legal units and readable citations.

**Disadvantages:** Uneven sizes, short isolated provisions, oversized units, and sensitivity to ambiguous source structure.

**Favor it if:** Reviewed boundaries consistently preserve complete rules and their qualifications.

**Disfavor it if:** Ambiguity requires extensive correction or large units contain many separable topics.

### Step 7 — Parent-child alternatives

Compare the following relationships rather than assuming an Article is always the parent:

| Parent | Children | Experiment purpose |
|---|---|---|
| Article or § provision | Fixed-length subspans | Test focused pieces with complete-provision context |
| Evidenced Section or Chapter | Contained legal units; split oversized children when necessary | Test whether neighboring provisions add useful context |
| Annex or evidenced Annex subsection | Contiguous paragraph groups or fixed-length subspans | Accommodate forms and non-Article structure |
| Reviewed unclassified span | Contiguous smaller spans | Preserve context without inventing a legal role |

For controlled comparisons, reuse the fixed-length configurations inside parents. Report when two alternatives yield identical child spans so that differences are attributed to parent choice.

Explain the future mechanics without implementing them:

- **Parent:** A preserved source span representing larger context.
- **Child:** A smaller, traceable span within that parent.
- **Future embedding/search target:** Child text.
- **Future match:** A child and its parent link.
- **Possible LLM context:** The linked parent, subject to a later context-budget policy.

Manually select a child ID to display its parent. This is relationship inspection, not a search or retrieval experiment.

Measure parent size, child count, and parent-to-child expansion ratio. Show that a Chapter parent can be far too large even when children are well sized. Do not silently truncate it or assume the entire parent will eventually fit.

**Favor it if:** Parent expansion restores a missing definition, condition, or exception with modest additional context.

**Disfavor it if:** Parents add mostly unrelated material, remain incomplete, or create excessive context expansion.

### Step 8 — Oversized-unit experiments

Keep the uncapped structural baseline visible so fallback splitting cannot hide its weaknesses.

Test structural-size triggers of **2,000, 4,000, and 8,000 characters**. These span observed paragraph sizes and long Article candidates. Display the percentage and types of units affected by each trigger.

For affected units, compare:

1. Exact fixed-length child windows.
2. Boundary-aware child splitting: preserve whole source paragraphs where possible; within an oversized paragraph, prefer whitespace cuts and use exact character cuts only when necessary.

Use child targets of 1,000 and 2,000 characters, with 0% and 10% overlap. Record actual overlap after boundary adjustment.

Preserve the complete parent and all source mappings. Children must not cross parent boundaries, omit text, or loop when overlap is requested. Mark every fallback reason visibly.

Inspect Articles, § provisions, Annexes, history paragraphs, and long prose separately. Favor thresholds that reduce fragmentation while keeping manageable child sizes; record trade-offs rather than choosing the threshold with the smallest chunks.

### Step 9 — Amendment and publication-history investigation

Compare two non-destructive experimental representations:

- Original text, unchanged.
- Original text, unchanged, plus separately annotated history spans.

Annotations will retain verbatim history text, block offsets, proposed scope, and uncertainty. They are not verified effective-date or legal-status assertions.

Display examples of document-level publication lists and inline amendment notes. Measure their character share and inspect whether chunk boundaries detach them from the affected provision.

Discuss all three future possibilities:

| Future policy | Benefit | Cost or unresolved issue |
|---|---|---|
| Keep in searchable text | Preserves legal context directly | Repeated dates and publication references may dilute topical focus |
| Metadata only | Could reduce textual noise | Requires reliable attribution and a separate approved text transformation |
| Both | Preserves context and supports metadata access | Duplicates information and adds annotation complexity |

The metadata-only policy remains a **design hypothesis** here. No history text will be removed, masked, or rewritten. Retrieval-noise conclusions will remain qualitative until a separately approved retrieval stage.

### Step 10 — Metadata experiments

Use an experimental document registry plus chunk references rather than copying every document field onto every chunk.

| Category | Experimental contents | Intended use |
|---|---|---|
| A. Document-level | Bulgarian title, English subtitle, jurisdiction, URL, official reference, version date, accessed date, note, source evidence | Document identification, provenance, potential future filtering |
| B. Structural | Evidenced labels, scope, heading locations, uncertainty, boundary evidence | Context, citation construction, boundary debugging |
| C. Chunk-generated | ID, strategy, configuration ID, ordinal, character count, source spans, overlaps, split reasons | Reproducibility, comparison, traceability |
| D. Parent-child | Parent ID, child order, relationship type, parent source span | Context lookup and containment validation |
| E. Provenance/citation | Document reference, block IDs, offsets, DOCX/artifact fingerprints, resolvable source URL and legal labels | Source verification and readable citations |

Specific choices:

- Resolve titles and citation fields through the document registry for display.
- Demonstrate a selective joined view containing jurisdiction and raw version date as possible future filter fields.
- Retain English titles for display; do not automatically prepend them to chunk text.
- Keep access dates, long notes, official-reference strings, and parser provenance at document/run level unless a demonstrated need justifies duplication.
- Preserve dates verbatim; do not equate version date with effective date.
- Do not import reference-only topic, city, district, `in_force`, or page values.
- Use source locations, not invented physical page numbers.

Display the same chunk with minimal metadata and a selectively enriched view, explaining which added fields help inspection. This remains a notebook experiment contract, not a production schema or public API.

### Step 11 — Side-by-side comparison and mentor references

Show the same source span above three aligned panels: fixed-length chunks, structural chunks, and parent-plus-children.

Use separate quantitative and qualitative evidence:

| Criterion | Evidence |
|---|---|
| Source preservation | Exact span reconstruction and coverage |
| Boundary quality | Reviewed provisions cut internally; chunks combining provisions |
| Size | Distribution, extremes, and fraction above each experimental threshold |
| Duplication | Repeated source-character coverage caused by overlap |
| Context | Manual checks for definitions, conditions, exceptions, and cross-references |
| Parent expansion | Parent/child size ratio and added unrelated material |
| Metadata usefulness | Whether source, legal unit, and uncertainty can be identified |
| Long-unit handling | Complete parent retained; ordered children cover its text |
| Retrieval precision potential | Qualitative focus judgment only |

Distinguish overlap duplication from intentional parent/child containment and from repeated text already present in the source.

Use a simple reviewer rubric—pass, concern, fail, or uncertain—with a source-backed explanation. Do not collapse everything into a weighted winner score.

Only after the independent strategy comparison, load mentor references through a separate read-only path:

- Map documents using reviewed titles and source URLs.
- Align provisions using citation labels and source excerpts.
- Label exact, partial, ambiguous, and unmatched correspondences.
- Separate added English summaries and generated prefixes from source-text comparisons.
- Compare rule coverage, boundary choices, context completeness, and citation usefulness.
- Treat unmapped references as unresolved, not proof that our corpus is missing content.

Do not compare IDs, timestamps, total chunk counts, `embedding_text`, or implementation-specific metadata for equality. Do not treat 94 curated reference chunks as exhaustive full-text ground truth. Never feed them into our chunk builders.

### Step 12 — Hybrid experiment, conclusions, and review

Place this section after the three independent strategies and their observation tables.

Require recorded observations before running it; otherwise display “hybrid hypothesis pending review.”

Test the proposed combination only if the evidence supports it:

1. Preserve evidenced meaningful units below the experimental threshold.
2. Retain oversized units as parents.
3. Apply the tested controlled splitting method to their children.
4. Preserve uncertain spans without assigning invented legal ancestry.

Tie every hybrid rule to a specific observed failure and compare it against the relevant baseline on identical source spans. Report regressions as well as improvements.

Finish with:

- Observations supporting each strategy.
- Counterexamples and unresolved ambiguities.
- A provisional shortlist of configurations.
- Whether the hybrid warrants further testing.
- Questions reserved for later token-budget and retrieval evaluation.

No final production strategy, size, parent policy, or metadata schema will be declared.

## 3. Validation and acceptance

The future implementation will include focused notebook assertions and small synthetic edge cases:

- Every selected source character is accounted for; overlap is explicitly measurable.
- Source slices reconstruct exactly, including Cyrillic, punctuation, and history notes.
- No chunk crosses document boundaries; no child crosses its parent.
- Parent links resolve, contain their children, and form no cycles.
- IDs are reproducible for unchanged source, configuration, and spans.
- Repeated § labels, Cyrillic Article suffixes, inline citations, detached heading titles, and ambiguous markers behave visibly and conservatively.
- Empty input, final short chunks, exact-size units, and oversized unbroken text terminate correctly.
- Reference material cannot enter corpus-building functions.
- Changing a sample selection or parameter cannot reuse stale comparison results.
- Restart-and-run-all reproduces deterministic outputs, with the observation-dependent hybrid section explicitly skipped when not yet reviewed.
- Stage 1 and the source archive remain unchanged.

Legal meaning and boundary correctness require manual inspection; passing preservation checks will not be presented as legal validation.

## 4. Implementation boundaries and defaults

- Implement only after approval.
- Remain notebook-first, using Python’s standard library and existing notebook display capabilities.
- No new production modules, public APIs, framework dependencies, or production metadata schema.
- Keep original text immutable and experimental annotations separate.
- Run detailed sample inspection first; then generate compact corpus-wide diagnostics.
- Keep private outputs local. The committed notebook will have outputs cleared, following repository convention; optional executed copies and experiment reports belong in a separate ignored Stage 2 output directory.
- Leave embeddings, vector databases, retrieval execution, reranking, generation, LLM integration, and agents entirely outside Stage 2.
- Treat thresholds, overlap, parent selection, ambiguous boundaries, and history placement as experimental questions with recorded evidence—not assumptions disguised as final decisions.
