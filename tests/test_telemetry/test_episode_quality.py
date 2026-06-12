"""
Session-14 W2 — episode quality in the background telemetry processor.

Pins:
  * raw JSON agent blobs are parsed into clean human titles (root_cause /
    summary / title field extraction, markdown stripping, truncation);
  * "No significant anomalies detected" NON-EVENTS are never stored;
  * severity is normalized at write time to {info,warning,error,critical}
    (the LangGraph pipeline carries a 0-10 int that used to be stored as
    str(int) blobs like "10");
  * affected_services links only genuinely affected services (the old static
    six-service fallback produced the graph hairball);
  * the routine trend path calls the REAL ReasoningAgent.analyze_rca API
    (spec= pins the method name so a rename breaks this test).
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.agents.reasoning_agent import ReasoningAgent
from src.memory.episode_store import Episode
from src.telemetry.background_processor import (
    BackgroundTelemetryProcessor,
    _humanize_title,
    _is_non_event,
    _select_affected_services,
    normalize_severity,
)


# ── unit: title parsing ───────────────────────────────────────────────────────

class TestHumanizeTitle:

    def test_parses_root_cause_from_json_blob(self):
        raw = (
            '{"root_cause": "Neo4j connection pool exhaustion", '
            '"causal_chain": ["a", "b"], "confidence": 0.9}'
        )
        assert _humanize_title(raw) == "Neo4j connection pool exhaustion"

    def test_parses_summary_when_no_root_cause(self):
        raw = '{"summary": "High CPU on backend", "severity": "warning"}'
        assert _humanize_title(raw) == "High CPU on backend"

    def test_regex_fallback_on_truncated_json(self):
        # Truncated blob (not valid JSON) — the regex path must still extract.
        raw = '{"root_cause": "Disk pressure on loki", "causal_chain": ["fil'
        assert _humanize_title(raw) == "Disk pressure on loki"

    def test_plain_text_first_line(self):
        raw = "Memory leak in nextcloud sync worker\n\nDetails follow..."
        assert _humanize_title(raw) == "Memory leak in nextcloud sync worker"

    def test_markdown_and_fences_stripped(self):
        raw = '```json\n{"root_cause": "**Bad** `config` value"}\n```'
        assert _humanize_title(raw) == "Bad config value"

    def test_truncates_long_titles(self):
        raw = '{"root_cause": "' + "word " * 60 + '"}'
        title = _humanize_title(raw, max_len=100)
        assert len(title) <= 101  # 100 chars + ellipsis
        assert title.endswith("…")

    def test_fallback_on_empty_or_unparseable(self):
        assert _humanize_title("") == "Anomaly detected"
        assert _humanize_title(None) == "Anomaly detected"
        assert _humanize_title("{[[[", fallback="fb") == "fb"

    def test_no_raw_json_braces_leak_into_title(self):
        raw = '{"confidence": 0.5, "impact": {"services": []}}'
        title = _humanize_title(raw, fallback="Anomaly detected")
        assert "{" not in title and "}" not in title


# ── unit: severity normalization ─────────────────────────────────────────────

class TestNormalizeSeverity:

    def test_numeric_scale(self):
        # LangGraph annotate node scale: info=2 low=4 medium=6 high=8 critical=10
        assert normalize_severity(10) == "critical"
        assert normalize_severity(9) == "critical"
        assert normalize_severity(8) == "error"
        assert normalize_severity(7) == "error"
        assert normalize_severity(6) == "warning"
        assert normalize_severity(4) == "warning"
        assert normalize_severity(2) == "info"
        assert normalize_severity(0) == "info"

    def test_numeric_strings(self):
        assert normalize_severity("10") == "critical"
        assert normalize_severity("6") == "warning"

    def test_string_aliases(self):
        assert normalize_severity("critical") == "critical"
        assert normalize_severity("fatal") == "critical"
        assert normalize_severity("high") == "error"
        assert normalize_severity("error") == "error"
        assert normalize_severity("warning") == "warning"
        assert normalize_severity("medium") == "warning"
        assert normalize_severity("warn") == "warning"
        assert normalize_severity("low") == "info"
        assert normalize_severity("info") == "info"

    def test_garbage_and_none(self):
        assert normalize_severity(None) == "info"
        assert normalize_severity("") == "info"
        assert normalize_severity("garbage") == "info"
        assert normalize_severity(True) == "info"

    def test_always_in_closed_set(self):
        closed = {"info", "warning", "error", "critical"}
        for value in (0, 3, 5, 7, 10, "10", "high", None, "x", 3.5):
            assert normalize_severity(value) in closed


# ── unit: non-event detection + service selection ────────────────────────────

class TestNonEventAndServices:

    def test_non_event_markers(self):
        assert _is_non_event("No significant anomalies detected") is True
        assert _is_non_event("System healthy, all metrics nominal") is True
        assert _is_non_event("no anomalies detected in this window") is True
        assert _is_non_event(None, "", "No concerning patterns found") is True

    def test_real_events_are_not_non_events(self):
        assert _is_non_event("Neo4j connection pool exhausted") is False
        assert _is_non_event("High error rate in nextcloud logs") is False

    def test_select_keeps_only_mentioned_services(self):
        candidates = ["backend", "neo4j", "loki", "grafana", "prometheus", "frontend"]
        result = _select_affected_services(
            candidates, "RCA: Neo4j pool exhaustion impacting backend API"
        )
        assert sorted(result) == ["backend", "neo4j"]

    def test_select_small_unattributed_list_kept(self):
        result = _select_affected_services(["loki", "promtail"], "Generic anomaly text")
        assert sorted(result) == ["loki", "promtail"]

    def test_select_large_unattributed_list_dropped(self):
        candidates = ["backend", "neo4j", "loki", "grafana", "prometheus", "frontend"]
        assert _select_affected_services(candidates, "Generic anomaly text") == []

    def test_select_empty_candidates(self):
        assert _select_affected_services([], "anything") == []


# ── processor integration (mocked deps) ──────────────────────────────────────

def _make_processor(**overrides):
    kwargs = dict(
        fast_annotator=MagicMock(),
        reasoning_agent=MagicMock(),
        telemetry_collector=MagicMock(),
        episode_store=MagicMock(),
        neo4j_client=None,
        incident_graph=MagicMock(),
    )
    kwargs.update(overrides)
    processor = BackgroundTelemetryProcessor(**kwargs)
    processor.episode_store.find_similar_episodes = AsyncMock(return_value=[])
    processor.episode_store.store_episode = AsyncMock()
    processor.episode_store.update_episode = AsyncMock()
    return processor


def _empty_window():
    window = MagicMock()
    window.logs = []
    window.traces = []
    window.metrics = []
    return window


def _window_with_services(names):
    window = _empty_window()
    logs = []
    for name in names:
        log = MagicMock()
        log.labels = {"container_name": name}
        log.service = None
        logs.append(log)
    window.logs = logs
    return window


class TestStoreGraphResultQuality:

    @pytest.mark.asyncio
    async def test_non_event_is_not_stored(self):
        processor = _make_processor()
        graph_result = {
            "annotation": {"content": "No significant anomalies detected", "metadata": {}},
            "rca_result": None,
            "correlation_id": "corr-1",
            "severity": 2,
            "confidence": 0.9,
            "steps_completed": ["annotate"],
        }
        await processor._store_graph_result_as_episode(graph_result, _empty_window())
        processor.episode_store.store_episode.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_severity_int_normalized_and_title_humanized(self):
        processor = _make_processor()
        graph_result = {
            "annotation": {"content": "anomaly", "metadata": {"category": "error"}},
            "rca_result": {
                "content": '{"root_cause": "Neo4j pool exhaustion impacting backend", "confidence": 0.9}'
            },
            "correlation_id": "corr-2",
            "severity": 10,  # LangGraph int scale — used to be stored as "10"
            "confidence": 0.9,
            "steps_completed": ["annotate", "reasoning"],
        }
        await processor._store_graph_result_as_episode(
            graph_result, _window_with_services(["aiops-backend", "aiops-neo4j", "aiops-loki"])
        )

        processor.episode_store.store_episode.assert_awaited_once()
        episode: Episode = processor.episode_store.store_episode.await_args.args[0]
        assert episode.severity == "critical"
        assert episode.severity in {"info", "warning", "error", "critical"}
        assert episode.title.startswith("RCA: ")
        assert "Neo4j pool exhaustion" in episode.title
        assert "{" not in episode.title  # no raw JSON leak
        # Only the services the analysis actually names.
        assert sorted(episode.affected_services) == ["backend", "neo4j"]

    @pytest.mark.asyncio
    async def test_unattributed_hairball_gets_no_services(self):
        processor = _make_processor()
        graph_result = {
            "annotation": {"content": "Elevated error rate observed", "metadata": {}},
            "rca_result": None,
            "correlation_id": "corr-3",
            "severity": 6,
            "confidence": 0.6,
            "steps_completed": ["annotate"],
        }
        window = _window_with_services([
            "aiops-backend", "aiops-neo4j", "aiops-loki",
            "aiops-grafana", "aiops-prometheus", "aiops-frontend",
        ])
        await processor._store_graph_result_as_episode(graph_result, window)

        episode: Episode = processor.episode_store.store_episode.await_args.args[0]
        assert episode.affected_services == []  # not all six
        assert episode.severity == "warning"

    @pytest.mark.asyncio
    async def test_no_static_service_fallback(self):
        """Empty telemetry window -> no fabricated default service list."""
        processor = _make_processor()
        assert processor._extract_services_from_window(_empty_window()) == []


class TestRoutineTrendPath:

    def _recent_episode(self):
        return Episode(
            episode_id="ep-1",
            incident_id="inc-1",
            title="Backend latency spike",
            description="p95 latency exceeded threshold",
            severity="warning",
            category="performance",
            detected_at=datetime.utcnow(),
            affected_services=["backend"],
        )

    def _trend_agent(self, content):
        # spec=ReasoningAgent pins the REAL method name: if analyze_rca is
        # renamed, configuring/awaiting it here fails loudly.
        agent = MagicMock(spec=ReasoningAgent)
        response = MagicMock()
        response.content = content
        response.confidence = 0.8
        agent.analyze_rca = AsyncMock(return_value=response)
        return agent

    @pytest.mark.asyncio
    async def test_trend_path_uses_analyze_rca_and_humanizes_title(self):
        agent = self._trend_agent(
            '{"root_cause": "Recurring backend latency pattern", '
            '"reasoning": "three episodes share the same signature"}'
        )
        processor = _make_processor(reasoning_agent=agent)
        processor.episode_store.get_recent_episodes = AsyncMock(
            return_value=[self._recent_episode()]
        )

        await processor._routine_reasoning_analysis()

        agent.analyze_rca.assert_awaited_once()
        processor.episode_store.store_episode.assert_awaited_once()
        episode: Episode = processor.episode_store.store_episode.await_args.args[0]
        assert episode.title.startswith("Trend Analysis: ")
        assert "Recurring backend latency pattern" in episode.title
        assert "{" not in episode.title

    @pytest.mark.asyncio
    async def test_trend_non_event_not_stored(self):
        agent = self._trend_agent(
            "No recurring root causes were found; the system is healthy and "
            "all services are operating normally with stable metrics."
        )
        processor = _make_processor(reasoning_agent=agent)
        processor.episode_store.get_recent_episodes = AsyncMock(
            return_value=[self._recent_episode()]
        )

        await processor._routine_reasoning_analysis()

        agent.analyze_rca.assert_awaited_once()
        processor.episode_store.store_episode.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_reasoning_agent_has_no_analyze_incident(self):
        """Regression guard: the old (broken) call target must stay absent —
        if someone adds analyze_incident back, the trend path call site should
        be revisited deliberately."""
        assert not hasattr(ReasoningAgent, "analyze_incident")
        assert hasattr(ReasoningAgent, "analyze_rca")
