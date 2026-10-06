from .setup import SetupSteps
from .fixed import FixedSteps
from .structural import StructuralSteps
from .parent_child import ParentChildSteps
from .oversized import OversizedSteps
from .history import HistorySteps
from .metadata import MetadataSteps
from .comparison import ComparisonSteps
from .hybrid import HybridSteps
from property_copilot.config import find_project_root


class ChunkingExperiments(
    SetupSteps,
    FixedSteps,
    StructuralSteps,
    ParentChildSteps,
    OversizedSteps,
    HistorySteps,
    MetadataSteps,
    ComparisonSteps,
    HybridSteps,
):
    """Replay reviewed steps with isolated instance state and inspectable results.

    Run steps in notebook order, or use run() for the complete workflow.
    Construction performs no file reads, writes, or service calls.
    """

    def __init__(self, root=None):
        self.ROOT = find_project_root(root)

    steps = (
        "step_2_load_and_verify_the_stage_1_interface",
        "step_2_load_and_verify_the_stage_1_interface_2",
        "step_2a_inspect_the_inventory_and_preserved_evidence",
        "step_2b_build_reversible_document_views_not_chunks",
        "step_3_select_and_freeze_representative_content",
        "step_3b_explicit_source_window_selection",
        "step_3b_explicit_source_window_selection_2",
        "step_3c_freeze_the_manifest_and_full_document_inputs",
        "step_4a_demonstrate_source_inspection_leave_strategy_panels_empty",
        "step_4b_validate_setup_fidelity_and_display_edge_cases",
        "step_4c_preserve_the_approved_frozen_setup",
        "step_5a_load_the_approved_manifest_and_lock_the_experiment_inputs",
        "step_5b_strict_splitter_and_independent_boundary_checks",
        "step_5c_generate_all_nine_baselines_on_complete_document_inputs",
        "step_5d_evaluation_only_provision_ledger_never_used_by_the_splitter",
        "step_5e_corpus_level_and_sample_level_diagnostics",
        "step_5f_inspect_real_chunks_cut_points_overlap_and_source_maps",
        "step_5f_inspect_real_chunks_cut_points_overlap_and_source_maps_2",
        "step_5g_concrete_boundary_witnesses_and_interpretation",
        "step_5h_final_fidelity_checks_reproducible_report_and_approved_checkpoint",
        "step_6a_lock_inputs_and_document_the_conservative_policy",
        "step_6b_propose_boundary_decisions_do_not_generate_chunks_yet",
        "step_6c_inspect_uncertain_rejected_evidence_before_accepting_the_partition",
        "step_6d_generate_uncapped_structural_units_from_the_displayed_ledger",
        "step_6e_natural_sizes_residuals_annexes_provisions_and_uncertainty",
        "step_6f_same_source_visual_comparison_and_sample_diagnostics",
        "step_6g_corpus_comparison_and_observed_counterexamples",
        "step_6h_validate_conservative_behavior_and_save_a_separate_report",
        "step_6i_save_the_structural_report_and_approved_checkpoint",
        "step_7a_preserve_approved_artifacts_and_declare_evidenced_parent_candidates",
        "step_7b_relationship_identity_and_controlled_child_construction",
        "step_7c_validate_links_containment_ordering_full_coverage_and_provenance",
        "step_7d_parent_sizes_child_counts_and_context_expansion_diagnostics",
        "step_7e_identical_children_under_different_parents_controlled_comparison",
        "step_7f_complete_parents_and_ordered_children_on_the_frozen_samples",
        "step_7g_manual_child_parent_resolution_no_search",
        "step_7h_same_child_article_vs_section_vs_chapter_context",
        "step_7i_validate_relationship_failures_identity_and_reproducibility",
        "step_7j_save_relationship_results_and_stop_after_step_7",
        "step_8_oversized_unit_experiments_stop_here_for_review",
        "step_8a_boundary_aware_mechanics_and_their_costs",
        "step_8b_generate_experimental_children_while_retaining_every_complete_parent",
        "step_8c_matched_diagnostics_compare_methods_within_each_threshold_and_settin",
        "step_8d_representative_parents_children_and_cut_points",
        "step_8e_preservation_reproducibility_and_limits",
        "step_8f_review_observations_and_stop",
        "step_9_amendment_and_publication_history_investigation",
        "step_9a_original_versus_original_plus_annotations",
        "step_9b_how_much_text_is_annotated",
        "step_9c_boundary_witnesses_split_note_versus_separated_nearby_text",
        "step_9d_future_policy_hypotheses_no_policy_implemented",
        "step_9e_review_and_stop_after_step_9",
        "step_10_metadata_experiments_stop_here_for_review",
        "step_10a_source_field_inventory_and_selective_resolution",
        "step_10b_the_same_chunk_two_metadata_views",
        "step_10c_split_reasons_are_generated_evidence_source_fields_are_not",
        "step_10d_validate_references_and_source_fidelity",
        "step_10e_review_and_stop",
        "step_11_side_by_side_strategy_comparison_then_mentor_references",
        "step_11a_aligned_source_and_strategy_panels",
        "step_11b_independent_evidence_and_initial_reviewer_rubric",
        "step_11c_separate_read_only_mentor_evaluation_path",
        "step_11d_citation_and_literal_excerpt_alignment_evaluation_only",
        "step_11e_inspect_reference_excerpts_additions_and_source_context",
        "step_11f_validation_and_evaluation_isolation",
        "step_11g_evidence_table_and_stop_after_step_11",
        "step_12_hybrid_experiment_conclusions_and_stage_2_review",
        "step_12_hybrid_experiment_conclusions_and_stage_2_review_2",
        "step_12a_construct_the_hypothesis_from_existing_source_spans",
        "step_12b_inspect_the_same_frozen_samples_before_aggregate_diagnostics",
        "step_12c_improvements_regressions_and_the_shortlist_s_measured_costs",
        "step_12d_validate_the_composition_and_preservation_contract",
        "step_12e_what_is_supported_provisional_and_unresolved",
    )

    def run(self):
        """Run all steps and return this instance for result inspection."""
        for name in self.steps:
            getattr(self, name)()
        return self
