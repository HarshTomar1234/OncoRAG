"""Transform raw source records into KnowledgeObject dicts ready for Weaviate.

Field mappings here were verified against real API responses (not assumed)
during Phase 1 - notably: CIViC's Gene is reached through
molecularProfile.variants[].feature.featureInstance (a union), its NCBI id
field is `entrezId` not `ncbiId`; openFDA prescription labels use
`warnings_and_cautions` (OTC labels use `warnings` instead - both are
checked here since we can't predict which a given drug will have).
"""

from typing import Any, Iterable

from oncorag.ingestion.chunking import chunk_text, needs_chunking


def civic_evidence_to_objects(evidence: dict[str, Any]) -> list[dict[str, Any]]:
    """One CIViC evidence item yields an evidence_item object plus, for each
    distinct gene mentioned in its molecular profile, a gene object."""
    objects = []

    therapies = [t["name"] for t in evidence.get("therapies", [])]
    source = evidence.get("source") or {}
    description = evidence.get("description") or ""

    objects.append(
        {
            "object_type": "evidence_item",
            "content_text": description,
            "civic_id": str(evidence["id"]),
            "variant_name": evidence["molecularProfile"]["name"],
            "disease_name": evidence["disease"]["name"],
            "therapy_names": therapies,
            "evidence_type": evidence.get("evidenceType") or "",
            "evidence_level": evidence.get("evidenceLevel") or "",
            "evidence_direction": evidence.get("evidenceDirection") or "",
            "clinical_significance": evidence.get("significance") or "",
            "source_citation": source.get("citation") or "",
            "source_pmid": source.get("citationId") or "",
            "source_url": source.get("sourceUrl") or "",
        }
    )

    for variant in evidence["molecularProfile"].get("variants", []):
        feature = variant.get("feature") or {}
        feature_instance = feature.get("featureInstance") or {}
        entrez_id = feature_instance.get("entrezId")
        gene_name = feature.get("name")
        if not gene_name:
            continue
        objects.append(
            {
                "object_type": "gene",
                "content_text": feature.get("description") or gene_name,
                "gene_name": gene_name,
                "ncbi_id": str(entrez_id) if entrez_id is not None else "",
            }
        )

    return objects


def ctgov_study_to_objects(study: dict[str, Any]) -> list[dict[str, Any]]:
    """One ClinicalTrials.gov study yields a clinical_trial object plus, if its
    eligibility criteria are long, trial_eligibility_chunk objects that
    reference it (linked by nct_id; the actual Weaviate cross-reference is
    wired up at insert time once the parent has a UUID)."""
    ps = study["protocolSection"]
    ident = ps.get("identificationModule", {})
    status = ps.get("statusModule", {})
    conditions_mod = ps.get("conditionsModule", {})
    design = ps.get("designModule", {})
    arms = ps.get("armsInterventionsModule", {})
    eligibility = ps.get("eligibilityModule", {})
    locations_mod = ps.get("contactsLocationsModule", {})
    description_mod = ps.get("descriptionModule", {})

    nct_id = ident["nctId"]
    brief_summary = description_mod.get("briefSummary") or ""
    eligibility_criteria = eligibility.get("eligibilityCriteria") or ""
    interventions = [i.get("name", "") for i in arms.get("interventions", [])]
    locations = [
        loc.get("facility", "") for loc in locations_mod.get("locations", []) if loc.get("facility")
    ]

    objects = [
        {
            "object_type": "clinical_trial",
            "content_text": brief_summary,
            "nct_id": nct_id,
            "title": ident.get("briefTitle") or "",
            "conditions": conditions_mod.get("conditions", []),
            "interventions": interventions,
            "phase": ",".join(design.get("phases", [])),
            "overall_status": status.get("overallStatus") or "",
            "locations": locations,
            "last_update_date": (status.get("lastUpdatePostDateStruct") or {}).get("date", ""),
        }
    ]

    if needs_chunking(eligibility_criteria):
        for index, chunk in enumerate(chunk_text(eligibility_criteria)):
            objects.append(
                {
                    "object_type": "trial_eligibility_chunk",
                    "content_text": chunk,
                    "nct_id": nct_id,  # used to look up the parent UUID at insert time
                    "chunk_index": index,
                }
            )
    else:
        # Short enough to fold into the parent's own content instead of a
        # separate near-empty chunk collection entry.
        objects[0]["content_text"] = f"{brief_summary}\n\nEligibility: {eligibility_criteria}"

    return objects


def _first_or_empty(value: Any) -> str:
    if isinstance(value, list):
        return value[0] if value else ""
    return value or ""


def openfda_label_to_objects(label: dict[str, Any]) -> list[dict[str, Any]]:
    """One openFDA drug label yields a drug_label object plus, for long
    warnings/adverse-reactions text, drug_label_chunk objects."""
    openfda = label.get("openfda", {})
    drug_name = _first_or_empty(openfda.get("generic_name")) or _first_or_empty(
        openfda.get("brand_name")
    )
    if not drug_name:
        return []

    indications = _first_or_empty(label.get("indications_and_usage"))
    # Prescription labels use warnings_and_cautions; OTC labels use warnings.
    warnings = _first_or_empty(label.get("warnings_and_cautions")) or _first_or_empty(
        label.get("warnings")
    )
    adverse_reactions = _first_or_empty(label.get("adverse_reactions"))
    safety_text = "\n\n".join(t for t in (warnings, adverse_reactions) if t)

    objects = [
        {
            "object_type": "drug_label",
            "content_text": indications,
            "drug_name": drug_name,
            "manufacturer_name": _first_or_empty(openfda.get("manufacturer_name")),
            "mechanism_of_action": _first_or_empty(label.get("mechanism_of_action")),
        }
    ]

    if needs_chunking(safety_text):
        for index, chunk in enumerate(chunk_text(safety_text)):
            objects.append(
                {
                    "object_type": "drug_label_chunk",
                    "content_text": chunk,
                    "drug_name": drug_name,  # used to look up the parent UUID at insert time
                    "chunk_field_name": "safety",
                    "chunk_index": index,
                }
            )
    elif safety_text:
        objects[0]["content_text"] = f"{indications}\n\nSafety: {safety_text}"

    return objects


def dedupe_by_key(objects: Iterable[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    """Keep the first object seen for each value of `key` (drops falsy keys)."""
    seen = set()
    result = []
    for obj in objects:
        value = obj.get(key)
        if not value or value in seen:
            continue
        seen.add(value)
        result.append(obj)
    return result
