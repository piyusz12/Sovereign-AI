"""
Tests — Task Router

Verifies that the task classifier and model router correctly
select the appropriate model for each task type.

Phase 6: Expanded with weighted scoring, routing policy, and hybrid classification.
Phase 7: Added coder-specific routing and code generation tests.
"""

import pytest
from backend.router.task_classifier import TaskClassifier
from backend.router.routing_policy import (
    RoutingPolicy,
    RoutingDecision,
    ClassificationSignal,
)
from backend.router.llm_classifier import LLMClassifier
from backend.api.schemas import TaskType, ModelName


@pytest.fixture
def classifier():
    return TaskClassifier()


@pytest.fixture
def policy():
    return RoutingPolicy()


@pytest.fixture
def llm_clf():
    return LLMClassifier()


class TestTaskClassifier:
    """Test the task classifier routes correctly."""

    def test_coding_classification(self, classifier):
        """Router selects coding model for code requests."""
        result = classifier.classify("Write Python code to calculate pump efficiency")
        assert result.task_type == TaskType.CODING
        assert result.model == ModelName.QWEN25_CODER_7B

    def test_vision_classification_with_image(self, classifier):
        """Router selects vision model when image is attached."""
        result = classifier.classify("What is this?", has_image=True)
        assert result.task_type == TaskType.VISION
        assert result.model == ModelName.QWEN3_VL_8B

    def test_vision_classification_keywords(self, classifier):
        """Router selects vision model for image-related queries."""
        result = classifier.classify("Identify the valve in this P&ID diagram")
        assert result.task_type == TaskType.VISION
        assert result.model == ModelName.QWEN3_VL_8B

    def test_document_reasoning_classification(self, classifier):
        """Router selects reasoning model for document analysis."""
        result = classifier.classify("Summarize this inspection report")
        assert result.task_type == TaskType.DOCUMENT_REASONING
        assert result.model == ModelName.QWEN3_14B

    def test_general_classification(self, classifier):
        """Router defaults to reasoning for ambiguous queries."""
        result = classifier.classify("Hello, how are you?")
        assert result.task_type == TaskType.GENERAL
        assert result.model == ModelName.QWEN3_14B

    def test_data_analysis_classification(self, classifier):
        """Router selects coder for data analysis tasks."""
        result = classifier.classify("Analyze this telemetry data and find anomalies in temperature readings")
        assert result.task_type == TaskType.DATA_ANALYSIS
        assert result.model == ModelName.QWEN25_CODER_7B

    def test_confidence_high_for_clear_tasks(self, classifier):
        """High confidence for clearly categorized tasks."""
        result = classifier.classify("Write Python code", has_image=False)
        assert result.confidence > 0.3

    def test_confidence_low_for_ambiguous(self, classifier):
        """Low confidence for ambiguous queries."""
        result = classifier.classify("Hello")
        assert result.confidence <= 0.5


class TestWeightedScoring:
    """Test that weighted scoring produces correct rankings."""

    def test_explicit_language_boosts_coding(self, classifier):
        """Explicit language mention (python) boosts coding score."""
        result = classifier.classify("I need python help")
        assert result.task_type == TaskType.CODING
        assert result.model == ModelName.QWEN25_CODER_7B

    def test_code_syntax_detected(self, classifier):
        """Code syntax in prompt triggers coding classification."""
        result = classifier.classify("Fix this: def foo(): import os")
        assert result.task_type == TaskType.CODING

    def test_strong_document_signal(self, classifier):
        """Document-heavy query routes to reasoning."""
        result = classifier.classify("Review the compliance audit report and summarize findings from the inspection")
        assert result.task_type == TaskType.DOCUMENT_REASONING
        assert result.model == ModelName.QWEN3_14B

    def test_engineering_visual(self, classifier):
        """Engineering diagram mention routes to vision."""
        result = classifier.classify("Show me the P&ID diagram for the cooling system")
        assert result.task_type == TaskType.VISION

    def test_data_processing_routes_to_coder(self, classifier):
        """Data processing tasks route to coder model."""
        result = classifier.classify("Process the CSV telemetry data and calculate average temperature")
        assert result.task_type in (TaskType.DATA_ANALYSIS, TaskType.CODING)
        assert result.model == ModelName.QWEN25_CODER_7B


class TestClassifyWithSignal:
    """Test classify_with_signal returns proper ClassificationSignal."""

    def test_signal_has_source(self, classifier):
        """Signal source is 'keyword'."""
        signal = classifier.classify_with_signal("Write python code")
        assert signal.source == "keyword"

    def test_signal_has_duration(self, classifier):
        """Signal includes timing information."""
        signal = classifier.classify_with_signal("Write python code")
        assert signal.duration_ms >= 0

    def test_signal_task_type_string(self, classifier):
        """Signal task_type is a string value."""
        signal = classifier.classify_with_signal("Write python code")
        assert isinstance(signal.task_type, str)
        assert signal.task_type == "coding"


class TestExplain:
    """Test the explain() method for pattern breakdown."""

    def test_explain_returns_breakdown(self, classifier):
        """explain() returns per-category scores."""
        result = classifier.explain("Write Python code to analyze data")
        assert "category_scores" in result
        assert "coding" in result["category_scores"]
        assert "vision" in result["category_scores"]
        assert "document_reasoning" in result["category_scores"]
        assert "data_analysis" in result["category_scores"]

    def test_explain_has_final_classification(self, classifier):
        """explain() includes the final classification."""
        result = classifier.explain("Summarize this inspection report")
        assert "final_classification" in result
        assert result["final_classification"]["task_type"] == "document_reasoning"

    def test_explain_shows_match_counts(self, classifier):
        """explain() shows matched pattern counts."""
        result = classifier.explain("Write Python code")
        coding_scores = result["category_scores"]["coding"]
        assert "matched_count" in coding_scores
        assert coding_scores["matched_count"] > 0

    def test_explain_includes_input(self, classifier):
        """explain() echoes the input text."""
        result = classifier.explain("Hello world")
        assert result["input"] == "Hello world"


class TestRoutingPolicy:
    """Test routing policy configuration."""

    def test_default_policy_values(self, policy):
        """Default policy has sensible defaults."""
        assert policy.llm_threshold == 0.6
        assert policy.default_category == "reasoning"
        assert policy.prefer_llm is False
        assert policy.llm_temperature == 0.1
        assert policy.llm_max_tokens == 256

    def test_custom_policy(self):
        """Custom policy overrides defaults."""
        custom = RoutingPolicy(
            llm_threshold=0.8,
            prefer_llm=True,
            default_category="coding",
        )
        assert custom.llm_threshold == 0.8
        assert custom.prefer_llm is True
        assert custom.default_category == "coding"


class TestRoutingDecision:
    """Test RoutingDecision dataclass."""

    def test_to_dict_minimal(self):
        """to_dict works with minimal decision."""
        decision = RoutingDecision(
            task_type="coding",
            model_category="coding",
            model_name="qwen2.5-coder-7b",
            confidence=0.9,
            reason="Test",
        )
        d = decision.to_dict()
        assert d["task_type"] == "coding"
        assert d["model_category"] == "coding"
        assert d["confidence"] == 0.9
        assert "keyword_signal" not in d
        assert "llm_signal" not in d

    def test_to_dict_with_signals(self):
        """to_dict includes signals when present."""
        kw = ClassificationSignal(
            source="keyword",
            task_type="coding",
            model="qwen2.5-coder-7b",
            confidence=0.8,
            reason="keywords",
            duration_ms=0.5,
        )
        decision = RoutingDecision(
            task_type="coding",
            model_category="coding",
            model_name="qwen2.5-coder-7b",
            confidence=0.8,
            reason="Test",
            keyword_signal=kw,
        )
        d = decision.to_dict()
        assert "keyword_signal" in d
        assert d["keyword_signal"]["source"] == "keyword"
        assert d["keyword_signal"]["confidence"] == 0.8


class TestLLMClassifier:
    """Test LLM classifier response parsing."""

    def test_parse_clean_json(self, llm_clf):
        """Parses clean JSON response."""
        raw = '{"task_type": "coding", "model": "qwen2.5-coder-7b", "confidence": 0.95, "reason": "Code request"}'
        signal = llm_clf._parse_response(raw, 100.0)
        assert signal is not None
        assert signal.task_type == "coding"
        assert signal.model == "qwen2.5-coder-7b"
        assert signal.confidence == 0.95
        assert signal.source == "llm"

    def test_parse_json_in_markdown(self, llm_clf):
        """Parses JSON wrapped in markdown code fences."""
        raw = '```json\n{"task_type": "vision", "model": "qwen3-vl-8b", "confidence": 0.9, "reason": "Image task"}\n```'
        signal = llm_clf._parse_response(raw, 50.0)
        assert signal is not None
        assert signal.task_type == "vision"
        assert signal.model == "qwen3-vl-8b"

    def test_parse_json_with_surrounding_text(self, llm_clf):
        """Parses JSON embedded in surrounding text."""
        raw = 'Here is my classification:\n{"task_type": "reasoning", "model": "qwen3-14b", "confidence": 0.85, "reason": "General question"}\nThat is my answer.'
        signal = llm_clf._parse_response(raw, 75.0)
        assert signal is not None
        assert signal.task_type == "reasoning"

    def test_parse_invalid_json(self, llm_clf):
        """Returns None for invalid JSON."""
        raw = "This is not valid JSON at all"
        signal = llm_clf._parse_response(raw, 100.0)
        assert signal is None

    def test_parse_invalid_task_type(self, llm_clf):
        """Returns None for invalid task_type."""
        raw = '{"task_type": "unknown_type", "model": "qwen3-14b", "confidence": 0.9, "reason": "test"}'
        signal = llm_clf._parse_response(raw, 100.0)
        assert signal is None

    def test_parse_invalid_model(self, llm_clf):
        """Returns None for invalid model."""
        raw = '{"task_type": "coding", "model": "gpt-4", "confidence": 0.9, "reason": "test"}'
        signal = llm_clf._parse_response(raw, 100.0)
        assert signal is None

    def test_parse_confidence_clamped(self, llm_clf):
        """Confidence is clamped to [0.0, 1.0]."""
        raw = '{"task_type": "coding", "model": "qwen2.5-coder-7b", "confidence": 5.0, "reason": "test"}'
        signal = llm_clf._parse_response(raw, 100.0)
        assert signal is not None
        assert signal.confidence == 1.0

    def test_parse_negative_confidence(self, llm_clf):
        """Negative confidence is clamped to 0.0."""
        raw = '{"task_type": "coding", "model": "qwen2.5-coder-7b", "confidence": -0.5, "reason": "test"}'
        signal = llm_clf._parse_response(raw, 100.0)
        assert signal is not None
        assert signal.confidence == 0.0


class TestCoderRouting:
    """Test that coding-specific inputs route correctly."""

    def test_explicit_python_request(self, classifier):
        """'Write Python code' routes to coder."""
        result = classifier.classify("Write Python code to read a CSV file")
        assert result.task_type == TaskType.CODING
        assert result.model == ModelName.QWEN25_CODER_7B

    def test_sql_query_routes_to_coder(self, classifier):
        """SQL queries route to coder model."""
        result = classifier.classify("Write SQL query to find all orders over $1000")
        assert result.task_type == TaskType.CODING

    def test_debug_request(self, classifier):
        """Debug requests route to coder."""
        result = classifier.classify("Debug this code: the function throws an error")
        assert result.task_type == TaskType.CODING

    def test_algorithm_request(self, classifier):
        """Algorithm requests route to coder."""
        result = classifier.classify("Implement a binary search algorithm")
        assert result.task_type == TaskType.CODING

    def test_pandas_data_analysis(self, classifier):
        """Pandas/data analysis routes to coder."""
        result = classifier.classify("Use pandas to analyze the sensor readings CSV")
        assert result.model == ModelName.QWEN25_CODER_7B

    def test_mixed_coding_vision_prefers_vision_with_image(self, classifier):
        """Image attachment overrides coding keywords."""
        result = classifier.classify("Write code to process this image", has_image=True)
        assert result.task_type == TaskType.VISION
        assert result.model == ModelName.QWEN3_VL_8B
