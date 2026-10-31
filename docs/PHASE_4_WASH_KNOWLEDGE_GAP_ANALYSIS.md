# Phase 4 — Water, Sanitation & Hygiene Knowledge Gap Analysis

**Audit baseline:** repository `main` data inspected on 31 October 2026 (Jakarta time). This is a snapshot, not a live count. Re-run the audit after each collection cycle.

## Executive finding

The repository has a useful starting set of emergency-water and WASH source records, but it does not yet have a balanced, operationally useful Water & Sanitation knowledge base. Existing extracted tips are concentrated in drinking-water advisory communication. The most consequential technical areas—water source assessment, treatment limitations, water-quality testing, safe storage, and sanitation operations—are absent as reviewed knowledge records.

Do not interpret the presence of a source URL as complete evidence coverage. Some records are link directories or landing pages; some source text is only a short bibliographic description; and one UNHCR WASH entry explicitly says it is outdated and under revision.

## Snapshot inventory

| Repository asset | Snapshot | Interpretation |
|---|---:|---|
| All stored sources | 48 | Includes unrelated sources |
| Sources matching water/WASH/sanitation/hygiene search | 12 | Broad keyword match; includes adjacent food, shelter, and emergency-kit pages |
| Core water/WASH source records | 9 | Directly relevant records identified below |
| Existing water-category tips | 6 | All concern public advisory communication, not treatment or sanitation operations |
| Additional advisory communication tip | 1 | Spokesperson guidance, categorized as `other` |
| Candidate tips | 1 | Shelter-in-place candidate; not a WASH record |
| Approved tips | 0 | No published/approved tips in the inspected dataset |
| Recipes | 0 | Empty by design; no source-backed WASH recipe yet |
| Materials | 0 | Empty by design; no source-backed WASH materials record yet |

The seven advisory-related tips are still `needs_review`. Their existence does not mean the advice is approved for operational use.

## Existing core source inventory

| Source | What it can support | Limitation / next action |
|---|---|---|
| CDC — Preparing a Drinking Water Advisory | Advisory message design, public notices, accessible communication, translation, channels, contaminant-specific messaging | Strong communication source; not a water-treatment manual |
| CDC — Responding to WASH Emergency | A curated map of drinking-water advisories, bulk water, hygiene, cleanup, sanitation and wastewater resources | Primarily a link directory; follow and store the underlying technical documents before extracting operational claims |
| CDC — Planning & Training for WASH Emergency | Planning, training, environmental health, water security and response-resource discovery | Resource directory; underlying references need separate source records and evidence text |
| IFRC — Emergency WASH | Emergency WASH response domains, water-system rehabilitation, sanitation facilities, hygiene promotion and response capacity | Overview page; insufficient detail for step-by-step procedures or technical specifications |
| UNHCR — WASH in Emergencies | Humanitarian WASH assessment, coordination, access, indicators and inclusion | Page states it is outdated and under revision; treat as provisional discovery material, not current normative authority |
| Ready.gov — Water | Household emergency water needs, storage, and treatment topic discovery | US public preparedness guidance; capture the full current treatment/storage text and local applicability before turning it into tips |
| Des Moines Water Works — Emergency Water Preparedness | Household storage-container and preparedness considerations | Local utility guidance adapted from Ready.gov; secondary for this project and US-specific |
| WHO WPRO — Household Water Treatment and Safe Storage manual (2013) | Potentially detailed household treatment and safe-storage training | Repository currently stores catalogue metadata, not the manual's substantive text; obtain and archive the lawful document text before evidence extraction |
| WHO — Household water treatment and safe storage following emergencies and disasters (2002) | Emergency household water-treatment communication | Old publication; review currentness and retrieve the full document before relying on it |

Adjacent keyword matches include Ready.gov food safety, shelter, and emergency-kit pages. They may support cross-cutting preparedness, but should not be counted as core water-treatment or sanitation coverage.

## Topic coverage matrix

Status meanings: **Partial** = relevant source or indirect coverage exists, but the evidence is incomplete, indirect, outdated, or not yet converted into reviewed records. **Gap** = no adequate source-backed record identified in this snapshot. **Discovery only** = a source points toward the topic but does not itself provide enough stored evidence.

| Knowledge domain | Status | Evidence in repository | Gap to close |
|---|---|---|---|
| Emergency water preparedness and household demand | Partial | Ready.gov Water; emergency-kit sources; Des Moines Water Works | Validate current authoritative guidance and localize household/institutional needs without turning a single US figure into a universal standard |
| Water-source assessment and source protection | Gap | General WASH response/planning directories only | Add primary guidance for source inspection, catchment protection, flood impacts, and contamination pathways |
| Rainwater collection and use | Gap | No dedicated source-backed record identified | Add technical guidance on collection surfaces, first-flush considerations, storage, and risks; distinguish non-potable from potable use |
| Water treatment and disinfection | Partial / high risk | Ready.gov Water; WHO manual metadata; WHO emergency publication metadata; CDC advisory resources | Retrieve full current technical sources, document contaminant-specific limits, and require human review for every operational claim |
| Water-quality testing and interpretation | Gap | No adequate test-method or interpretation source text identified | Add official guidance on sampling, field tests, laboratory testing, indicator limits, and escalation; never infer potability from appearance/taste/odor |
| Safe household storage and handling | Partial | Ready.gov Water; Des Moines Water Works; WHO manual metadata | Retrieve complete evidence; cover container suitability, cleaning, covering, dispensing, recontamination, and storage limits |
| Bulk water transport and storage tanks | Discovery only | CDC WASH response page links to WHO tank/tanker cleaning and bulk-water guidance | Retrieve the linked WHO and public-health documents as independent source records |
| Hand hygiene and personal hygiene | Discovery only | CDC WASH response directory; IFRC overview; UNHCR WASH entry | Store and inspect primary technical guidance on handwashing facilities, water/soap availability, and emergency adaptations |
| Excreta, toilets, and fecal-sludge management | Discovery only / gap | CDC WASH response directory and IFRC overview mention sanitation; no detailed operational text | Add primary guidance for containment, safe emptying, transport, treatment, worker protection, and site-specific constraints |
| Wastewater and septic systems | Discovery only | CDC WASH response directory points to community wastewater and septic resources | Retrieve and store the underlying official technical guidance; distinguish household systems from municipal systems |
| Menstrual hygiene and accessible sanitation | Partial at overview level | IFRC emergency WASH overview mentions menstrual hygiene products; UNHCR WASH entry addresses inclusion | Add detailed, dignity-centered guidance on supplies, privacy, disposal, accessibility, and local context |
| Public-health advisories and risk communication | Partial; strongest current area | CDC advisory communications toolkit and seven unapproved communication tips | Human-review existing tips; add authoritative distinctions among boil-water, do-not-drink, and do-not-use advisories and local authority roles |
| Emergency WASH assessment, coordination, and monitoring | Partial | IFRC overview, UNHCR WASH entry, CDC planning/response directories | Add current operational assessment tools, indicators, coordination responsibilities, and local authority interfaces |

## Priority source-collection backlog

Prioritize retrieval of the actual technical documents, not just more broad landing pages.

### Priority 1 — close critical technical evidence gaps

1. WHO and national public-health guidance on household water treatment and safe storage, including current limitations and contaminant-specific warnings.
2. Official water-quality sampling, testing, and interpretation guidance, including when laboratory confirmation or authority notification is required.
3. Emergency sanitation guidance covering toilets, excreta containment, fecal sludge, wastewater, and worker safety.
4. Hand hygiene and hygiene-facility guidance for households, shelters, schools, and healthcare settings.

### Priority 2 — complete the household and community water chain

5. Water-source assessment and protection, including flood and industrial contamination risks.
6. Safe water collection, transport, bulk storage, tank/tanker cleaning, and point-of-use handling.
7. Rainwater harvesting and non-potable use boundaries.
8. Menstrual hygiene, accessible toilets, and inclusive WASH service design.

### Priority 3 — operationalize communication and coordination

9. Current official advisory categories, decision authority, and audience-specific messages.
10. Emergency WASH assessment indicators, coordination roles, and monitoring tools.

## Source acceptance checklist

Before adding a source to the evidence base, record:

- Canonical URL, publisher, title, document type, and retrieval date.
- Publication date and last-updated date where available.
- Jurisdiction, target population, climate/infrastructure assumptions, and intended use.
- Whether the stored text is the full relevant document, a partial extraction, or only a landing-page description.
- Authority tier and technical depth, assessed separately from recency.
- Exact passages that support each proposed claim.
- Known limitations, contraindications, uncertainty, and any required expert or authority referral.

A source can be authoritative yet outdated, jurisdiction-specific, or too shallow to support a procedure. A link directory is a discovery aid, not evidence for the technical steps listed on the linked pages.

## Data-development recommendations

1. Do not add synthetic recipes or materials to make the catalogues look populated.
2. Keep the existing seven advisory communication tips in `needs_review` until a human checks each claim against the source in context and confirms the stage classification.
3. Do not auto-approve water treatment, disinfection, testing, contamination, wastewater, sanitation, or hygiene procedures.
4. Create technical records only when the source text is available and each important field has traceable evidence.
5. Preserve the difference between source discovery, extracted candidate, reviewed record, and approved publication.
6. Keep source-specific units, thresholds, conditions, and jurisdiction intact; do not silently generalize them.

## Exit criteria for the WASH pilot

- All six pilot domains have a named source-coverage status and prioritized next action.
- Critical treatment, testing, and sanitation topics have current primary-source documents stored with substantive text.
- Candidate claims link to exact excerpts in stored sources.
- High-risk records receive human review and are not autonomously approved.
- Existing tests, data validators, and knowledge validators pass.
- Approved exports contain only records that passed the repository's review requirements.
- The remaining evidence gaps are documented before expanding the pilot to another civilization stage.

## Audit limitations

This analysis classifies the currently stored repository metadata, snippets, and available extracted text. It is not a full technical review of every linked PDF or external document. A topic marked Partial or Discovery only must not be treated as an operationally covered topic. Counts and statuses should be refreshed after source collection or data changes.
