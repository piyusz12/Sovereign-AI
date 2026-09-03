"""
Tests — Task Router

Verifies that the task classifier and model router correctly
select the appropriate model for each task type.
"""

import pytest
from backend.router.task_classifier import TaskClassifier
from backend.api.schemas import TaskType, ModelName


@pytest.fixture
def classifier():
    return TaskClassifier()


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
