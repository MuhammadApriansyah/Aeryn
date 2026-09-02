# 📊 Integration Map — 83 High-Value Files → Active Routers

## Status: ACTIVE (already imported by routers)

These modules are already wired in, just need verification:

| Module | Router | Status |
|--------|--------|--------|
| safety.secrets_runtime | admin, auth, plugins | ✅ Active |
| safety.soc2_compliance | admin | ✅ Active |
| safety.safety_engine | chat, dashboard | ✅ Active |
| safety.enhanced_sandbox | phase4 | ✅ Active |
| safety.enhanced_guardrails | phase4 | ✅ Active |
| safety.owasp_security | phase4, tools | ✅ Active |
| memory.vault | chat, dashboard, shared | ✅ Active |
| memory.hybrid_search | chat, dashboard, shared | ✅ Active |
| memory.social_memory | chat, dashboard | ✅ Active |
| memory.enhanced_memory | phase4 | ✅ Active |
| memory.entity_resolution | phase4, tools | ✅ Active |
| memory.memory_decay | phase4, tools | ✅ Active |
| memory.temporal_memory | phase4 | ✅ Active |
| reasoning.proactive_engine | phase4, tools | ✅ Active |
| reasoning.proactive_v2 | phase4 | ✅ Active |
| reasoning.long_horizon | phase4, tools | ✅ Active |
| reasoning.dream_synthesis | phase4 | ✅ Active |
| reasoning.constitutional_ai | phase4 | ✅ Active |
| reasoning.self_improvement | phase4 | ✅ Active |
| reasoning.emotional_intelligence | phase4 | ✅ Active |
| reasoning.context_manager | tools | ✅ Active |
| reasoning.reasoning_style | chat | ✅ Active |
| database.shared_db | phase4, shared | ✅ Active |
| database.vector_db | phase4 | ✅ Active |
| database.semantic_indexer | dashboard, notifications, tools | ✅ Active |
| self_improvement.engine | chat, main | ✅ Active |
| platform.plugin_system | phase4, plugins | ✅ Active |
| platform.plugin_marketplace | plugins | ✅ Active |
| platform.workspace_manager | workspaces | ✅ Active |
| platform.tool_runtime | tools | ✅ Active |
| platform.auto_task | phase4, tools | ✅ Active |
| platform.background_queue | main, tools | ✅ Active |
| platform.multi_agent | phase4 | ✅ Active |
| platform.adaptive_gateway | main | ✅ Active |
| platform.agent_daemon | main | ✅ Active |
| platform.capability_bridge | main | ✅ Active |
| platform.plugin_registry | chat, main | ✅ Active |
| platform.realtime | dashboard, main | ✅ Active |
| platform.performance | dashboard, main, phase4 | ✅ Active |
| platform.notification_system | dashboard, notifications | ✅ Active |
| utils.performance | dashboard, main, phase4 | ✅ Active |
| utils.error_recovery | chat, dashboard, main, notifications | ✅ Active |
| utils.patch_sqlite | ALL routers | ✅ Active |
| utils.logger | admin, auth, chat, dashboard, main, shared | ✅ Active |
| utils.llm_client | chat, dashboard, main, phase4 | ✅ Active |
| utils.data_encryption | admin, auth, phase4 | ✅ Active |
| utils.persona_engine | chat, dashboard | ✅ Active |
| utils.adapters | chat | ✅ Active |
| auth.auth | admin, auth, main, phase4, workspaces | ✅ Active |
| auth.rate_limiter | admin, auth, chat, main | ✅ Active |
| auth.api_keys | auth, dashboard | ✅ Active |
| auth.email_verification | admin, auth | ✅ Active |
| auth.sso_manager | admin, auth | ✅ Active |
| billing.billing | admin, auth | ✅ Active |
| billing.usage_metering | admin, auth, tools | ✅ Active |
| observability.tracer | chat, main | ✅ Active |
| connectors.vault_connector | main | ✅ Active |
| orchestration.crew_orchestrator | main | ✅ Active |
| workflow.phase_workflow | main | ✅ Active |
| adaptive | phase4 | ✅ Active |
| engine | engine | ✅ Active |

## Status: DEAD (never imported)

These modules need integration or removal:

| Module | Potential Router | Action |
|--------|------------------|--------|
| safety.guardian | chat | Wire to validate input |
| safety.guardian_enhanced | chat | Wire to validate input |
| safety.guardrails | chat | Wire to validate input |
| safety.critic_pass | chat | Wire to critique responses |
| safety.critic_refine | chat | Wire to refine responses |
| safety.injection_sweep | phase4 | Wire to scan |
| safety.production_guard | chat | Wire to validate |
| safety.research_guard | chat | Wire to verify |
| safety.security_hardening | phase4 | Wire to harden |
| safety.security_kernel | phase4 | Wire to secure |
| safety.shadow_mode | phase4 | Wire to shadow |
| safety.verification_gate | chat | Wire to verify |
| safety.verifier | chat | wire to verify |
| memory.core_memory | chat | wire to memory |
| memory.enhanced_memory | chat | wire to memory |
| memory.episodic_memory | chat | wire to memory |
| memory.graph | chat | wire to graph |
| memory.graph_memory | chat | wire to graph |
| memory.memory_consolidation | phase4 | wire to consolidate |
| memory.memory_curator | phase4 | wire to curate |
| memory.memory_indexer | phase4 | wire to index |
| memory.memory_learning | phase4 | wire to learn |
| memory.semantic_recall | phase4 | wire to recall |
| memory.session_history | chat | wire to history |
| memory.supersession | phase4 | wire to supersede |
| reasoning.cerewet_mode | chat | wire to commitments |
| reasoning.context_specialization | chat | wire to context |
| database.neon_connector | phase4 | wire to neon |
| database.neon_db | phase4 | wire to neon |
| database.semantic_search | phase4 | wire to search |
| agents.division_1_creative.master_agent | phase4 | wire to agents |
| agents.division_2_psych.master_agent | phase4 | wire to agents |
| agents.division_3_reasoning.master_agent | phase4 | wire to agents |
| agents.division_4_gov.master_agent | phase4 | wire to agents |
| agents.division_5_infra.master_agent | phase4 | wire to agents |
| agents.division_2_psych.sub_agents_real | phase4 | wire to agents |
| agents.division_4_gov.sub_agents_real | phase4 | wire to agents |
| agents.division_1_creative.sub_agent_pov.agent | phase4 | wire to agents |
| agents.division_1_creative.sub_agent_style.agent | phase4 | wire to agents |
| agents.division_3_reasoning.sub_agent_mcts.agent | phase4 | wire to agents |
| agents.division_3_reasoning.sub_agent_fol.agent | phase4 | wire to agents |
| agents.division_3_reasoning.sub_agent_critique.agent | phase4 | wire to agents |
| agents.division_3_reasoning.sub_agent_graph.agent | phase4 | wire to agents |
| agents.division_5_infra.sub_agent_sync.agent | phase4 | wire to agents |
| agents.division_5_infra.sub_agent_validator.agent | phase4 | wire to agents |
| agents.division_3_reasoning.middleware | phase4 | wire to agents |
| mcp.server | phase4 | wire to mcp |
| mcp.client | phase4 | wire to mcp |
| hermes.hermes_brain | chat | wire to hermes |
| hermes.hermes_hands | chat | wire to hermes |
| hermes.hermes_reflex | chat | wire to hermes |
| hermes_plugin.loader | chat | wire to hermes |
| hermes_plugin.hermes_bridge_init | chat | wire to hermes |
| fullstack.engine | phase4 | wire to fullstack |
| fullstack.planner | phase4 | wire to fullstack |
| fullstack.backend | phase4 | wire to fullstack |
| fullstack.frontend | phase4 | wire to fullstack |
| fullstack.database | phase4 | wire to fullstack |
| fullstack.deploy | phase4 | wire to fullstack |
| fullstack.api_gen | phase4 | wire to fullstack |
| fullstack.test_gen | phase4 | wire to fullstack |
| fullstack.cli.main | phase4 | wire to fullstack |
| fullstack.migration.manager | phase4 | wire to fullstack |
| fullstack.templates.base | phase4 | wire to fullstack |
| fullstack.templates.react_fastify | phase4 | wire to fullstack |
| fullstack.templates.vue_fastify | phase4 | wire to fullstack |
| cost.model_router | phase4 | wire to cost |
| cost.token_monitor | phase4 | wire to cost |
| platform.browser_automation | phase4 | wire to browser |
| platform.browser_vector | phase4 | wire to browser |
| platform.calendar_integration | phase4 | wire to calendar |
| platform.cloud_sync | phase4 | wire to cloud |
| platform.discord_bot | phase4 | wire to discord |
| platform.email_agent | phase4 | wire to email |
| platform.github_integration | phase4 | wire to github |
| platform.gitlab_integration | phase4 | wire to gitlab |
| platform.graphql_api | phase4 | wire to graphql |
| platform.jira_integration | phase4 | wire to jira |
| platform.linear_integration | phase4 | wire to linear |
| platform.mcp_production | phase4 | wire to mcp |
| platform.mcp_server | phase4 | wire to mcp |
| platform.multi_agent_rooms | phase4 | wire to rooms |
| platform.multi_region | phase4 | wire to region |
| platform.multi_tenant | phase4 | wire to tenant |
| platform.notification_system | dashboard, notifications | wire to notify |
| platform.orchestrator | phase4 | wire to orchestrate |
| platform.plugin_docs | phase4 | wire to docs |
| platform.realtime_rust | phase4 | wire to realtime |
| platform.skill_crystallization | phase4 | wire to skills |
| platform.skill_forge | phase4 | wire to skills |
| platform.sub_agent_runner | phase4 | wire to agents |
| platform.task_executor | phase4 | wire to tasks |
| platform.telegram_bot | admin, phase4 | wire to telegram |
| platform.tool_bridge | phase4 | wire to tools |
| platform.tool_governance | phase4 | wire to tools |
| platform.webhook_system | phase4 | wire to webhooks |
| platform.websocket_rust | phase4 | wire to websocket |
| platform.websocket_server | phase4 | wire to websocket |
| platform.workspace_manager | workspaces | wire to workspaces |
| personal.context | chat | wire to personal |
| personal.personalization | chat | wire to personal |
| personal.proactive_engine | chat | wire to proactive |
| security.memory_guard | phase4 | wire to security |
| security.prompt_injection | phase4 | wire to security |
| security.tool_permissions | phase4 | wire to security |
| security.dashboard.compliance | phase4 | wire to compliance |
| security.dashboard.security_dashboard | phase4 | wire to dashboard |
| sandbox.detector | phase4 | wire to sandbox |
| sandbox.fallback | phase4 | wire to sandbox |
| sandbox.level0_basic | phase4 | wire to sandbox |
| sandbox.level1_namespace | phase4 | wire to sandbox |
| sandbox.level2_bubblewrap | phase4 | wire to sandbox |
| sandbox.level3_full | phase4 | wire to sandbox |
| utils.basic_tools | phase4 | wire to utils |
| utils.bica_alignment | phase4 | wire to utils |
| utils.cache | phase4 | wire to utils |
| utils.cog_mem_lifecycle | phase4 | wire to utils |
| utils.config | phase4 | wire to utils |
| utils.context_pruner | phase4 | wire to utils |
| utils.dynamic_router | phase4 | wire to utils |
| utils.dynamic_schema | phase4 | wire to utils |
| utils.embedding_bridge | phase4 | wire to utils |
| utils.error_handling | phase4 | wire to utils |
| utils.event_bus | phase4 | wire to utils |
| utils.fallback_router | phase4 | wire to utils |
| utils.guardrails | phase4 | wire to utils |
| utils.image_tools | phase4 | wire to utils |
| utils.latent_value | phase4 | wire to utils |
| utils.llm_client | chat, dashboard, main, phase4 | wire to utils |
| utils.memory_pool | phase4 | wire to utils |
| utils.memory_vault_bridge | phase4 | wire to utils |
| utils.meta_evolution | phase4 | wire to utils |
| utils.model_client | phase4 | wire to utils |
| utils.multimodal | phase4 | wire to utils |
| utils.persona_engine | chat, dashboard | wire to utils |
| utils.reconsideration_guard | phase4 | wire to utils |
| utils.sla_monitoring | phase4 | wire to utils |
| utils.structured_output | phase4 | wire to utils |
| utils.swarm_convergence | phase4 | wire to utils |
| utils.tool_schema | phase4 | wire to utils |
| utils.tui_monitor | phase4 | wire to utils |
| utils.workflow_dag | phase4 | wire to utils |
| wizard.interactive | phase4 | wire to wizard |
| working_tests.generator | phase4 | wire to tests |
| websocket_template.generator | phase4 | wire to websocket |
| template_preview.preview | phase4 | wire to preview |
| template_inheritance.base | phase4 | wire to template |
| smart_seeder.generator | phase4 | wire to seeder |
| success_anim.animator | phase4 | wire to anim |
| preview.viewer | phase4 | wire to preview |
| diff_preview.viewer | phase4 | wire to diff |
| custom_generators.registry | phase4 | wire to custom |
| custom_template.editor | phase4 | wire to custom |
| undo.manager | phase4 | wire to undo |
| auto_rollback.manager | phase4 | wire to rollback |
| env_management.manager | phase4 | wire to env |
| error_solver.solver | phase4 | wire to solver |
| debug_mode.debugger | phase4 | wire to debug |
| deploy_dashboard.dashboard | phase4 | wire to deploy |
| diff_preview.viewer | phase4 | wire to diff |
| distributed_tracing.tracer | phase4 | wire to trace |
| headless_mode.runner | phase4 | wire to headless |
| help.helper | phase4 | wire to help |
| gallery.examples | phase4 | wire to gallery |
| oneclick.generator | phase4 | wire to oneclick |
| proactive.warnings | phase4 | wire to proactive |
| progress.indicator | phase4 | wire to progress |
| rate_limiting.limiter | phase4 | wire to rate |
| success_anim.animator | phase4 | wire to anim |
| smart_seeder.generator | phase4 | wire to seeder |
| template_preview.preview | phase4 | wire to preview |
| template_inheritance.base | phase4 | wire to template |
| undo.manager | phase4 | wire to undo |
| auto_rollback.manager | phase4 | wire to rollback |
| env_management.manager | phase4 | wire to env |
| error_solver.solver | phase4 | wire to solver |
| debug_mode.debugger | phase4 | wire to debug |
| deploy_dashboard.dashboard | phase4 | wire to deploy |
| diff_preview.viewer | phase4 | wire to diff |
| distributed_tracing.tracer | phase4 | wire to trace |
| headless_mode.runner | phase4 | wire to headless |
| help.helper | phase4 | wire to help |
| gallery.examples | phase4 | wire to gallery |
| oneclick.generator | phase4 | wire to oneclick |
| proactive.warnings | phase4 | wire to proactive |
| progress.indicator | phase4 | wire to progress |
| rate_limiting.limiter | phase4 | wire to rate |
