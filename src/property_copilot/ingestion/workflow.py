"""Coordinate the steps."""

from .source import SourceSteps
from .extraction import ExtractionSteps
from .boundaries import BoundariesSteps
from .assembly import AssemblySteps
from .metadata import MetadataSteps
from .validation import ValidationSteps
from property_copilot.config import find_project_root


class IngestionWorkflow(
    SourceSteps,
    ExtractionSteps,
    BoundariesSteps,
    AssemblySteps,
    MetadataSteps,
    ValidationSteps,
):
    """Replay reviewed steps with isolated instance state and inspectable results.

    Run steps in notebook order, or use run() for the complete workflow.
    Construction performs no file reads, writes, or service calls.
    """

    def __init__(self, root=None):
        self.ROOT = find_project_root(root)

    steps = (
        "step_1_locate_and_load_the_exact_source",
        "step_1_locate_and_load_the_exact_source_2",
        "step_1_locate_and_load_the_exact_source_3",
        "step_1_locate_and_load_the_exact_source_4",
        "step_1_locate_and_load_the_exact_source_5",
        "step_1_locate_and_load_the_exact_source_6",
        "step_4_extract_ordered_structural_blocks",
        "step_4c_tables_remain_in_place_with_nested_cell_paragraphs",
        "step_4d_footer_content_stays_outside_the_body",
        "step_4e_inspect_the_records",
        "step_4f_check_step_4_preservation",
        "step_4f_check_step_4_preservation_2",
        "step_5_identify_document_boundaries_and_structural_markers",
        "step_5b_assign_regions_using_explicit_delimiters",
        "step_5c_review_complete_spans_and_boundary_evidence",
        "step_5d_identify_candidate_structural_legal_markers",
        "step_5e_check_coverage_conservative_behavior_and_unchanged_records",
        "step_5e_check_coverage_conservative_behavior_and_unchanged_records_2",
        "step_6_assemble_the_simple_intermediate_representation",
        "step_6b_build_complete_document_descriptors_with_source_evidence",
        "step_6c_assemble_the_corpus_envelope",
        "step_6d_inspect_representative_assembled_records",
        "step_6e_check_assembly_integrity_and_json_compatibility",
        "step_7_separate_extracted_generated_structurally_interpreted_and_deferred_me",
        "step_7b_keep_package_properties_separate_from_legal_document_metadata",
        "step_7c_make_generated_interpreted_and_deferred_fields_explicit",
        "step_7d_actual_document_example_black_sea_coast_spatial_development_act",
        "step_7e_check_metadata_fidelity_and_category_separation",
        "step_8_validate_parsing_fidelity_and_persist_stage_1",
        "step_8c_validate_metadata_provenance_and_structural_evidence",
        "step_8d_report_ambiguity_and_show_source_previews",
        "step_8e_persist_and_reload_the_validated_representation",
        "final_stage_1_summary",
    )

    def run(self):
        """Run all steps and return this instance for result inspection."""
        for name in self.steps:
            getattr(self, name)()
        return self
