"""
Tests — Coding Module

Verifies code block extraction, system prompt selection,
and CodeGenerationResult handling.
"""

import pytest
from backend.router.coding import (
    CodeBlock,
    CodeGenerationResult,
    extract_code_blocks,
    extract_primary_code,
    get_system_prompt,
    CODING_SYSTEM_PROMPT,
    DATA_ANALYSIS_SYSTEM_PROMPT,
)


class TestExtractCodeBlocks:
    """Test code block extraction from LLM markdown output."""

    def test_single_python_block(self):
        """Extracts a single Python code block."""
        text = """Here is the code:

```python
def hello():
    print("Hello, World!")

hello()
```

This should work correctly."""

        blocks = extract_code_blocks(text)
        assert len(blocks) == 1
        assert blocks[0].language == "python"
        assert "def hello():" in blocks[0].code
        assert 'print("Hello, World!")' in blocks[0].code
        assert blocks[0].line_count == 4

    def test_multiple_blocks(self):
        """Extracts multiple code blocks from one response."""
        text = """First, create the utility:

```python
def add(a, b):
    return a + b
```

Then create the test:

```python
def test_add():
    assert add(1, 2) == 3
```
"""

        blocks = extract_code_blocks(text)
        assert len(blocks) == 2
        assert blocks[0].language == "python"
        assert blocks[1].language == "python"
        assert "def add" in blocks[0].code
        assert "def test_add" in blocks[1].code

    def test_no_code_blocks(self):
        """Returns empty list when no code blocks present."""
        text = "This is just plain text without any code blocks."
        blocks = extract_code_blocks(text)
        assert blocks == []

    def test_empty_input(self):
        """Returns empty list for empty input."""
        assert extract_code_blocks("") == []
        assert extract_code_blocks(None) == []  # type: ignore[arg-type]

    def test_no_language_specified(self):
        """Handles code blocks without language specifier."""
        text = """Some code:

```
x = 42
print(x)
```
"""
        blocks = extract_code_blocks(text)
        assert len(blocks) == 1
        assert blocks[0].language == "text"
        assert "x = 42" in blocks[0].code

    def test_different_languages(self):
        """Extracts blocks with different languages."""
        text = """Python version:

```python
print("hello")
```

JavaScript version:

```javascript
console.log("hello");
```
"""

        blocks = extract_code_blocks(text)
        assert len(blocks) == 2
        assert blocks[0].language == "python"
        assert blocks[1].language == "javascript"

    def test_empty_code_block_skipped(self):
        """Empty code blocks are skipped."""
        text = """Empty block:

```python
```

Real block:

```python
x = 1
```
"""
        blocks = extract_code_blocks(text)
        assert len(blocks) == 1
        assert blocks[0].code == "x = 1"

    def test_description_extraction(self):
        """Description is extracted from text before the code block."""
        text = """Here is a function to calculate pump efficiency:

```python
def pump_efficiency(flow_rate, power):
    return flow_rate / power * 100
```
"""
        blocks = extract_code_blocks(text)
        assert len(blocks) == 1
        assert "efficiency" in blocks[0].description.lower()

    def test_code_with_triple_backticks_content(self):
        """Handles code that doesn't have nested triple backticks."""
        text = '''```python
# This is a comment
data = {"key": "value"}
print(data)
```'''
        blocks = extract_code_blocks(text)
        assert len(blocks) == 1
        assert "data" in blocks[0].code


class TestExtractPrimaryCode:
    """Test primary code extraction."""

    def test_prefers_python(self):
        """Returns Python block when preferred."""
        text = """```bash
echo hello
```

```python
print("hello")
```
"""
        code = extract_primary_code(text, preferred_language="python")
        assert 'print("hello")' in code

    def test_falls_back_to_first(self):
        """Falls back to first block if preferred language not found."""
        text = """```javascript
console.log("hello");
```
"""
        code = extract_primary_code(text, preferred_language="python")
        assert "console.log" in code

    def test_empty_response(self):
        """Returns empty string if no blocks found."""
        code = extract_primary_code("No code here")
        assert code == ""


class TestGetSystemPrompt:
    """Test system prompt selection."""

    def test_coding_prompt(self):
        """Returns coding system prompt for coding tasks."""
        prompt = get_system_prompt("coding")
        assert prompt == CODING_SYSTEM_PROMPT
        assert "Python" in prompt

    def test_data_analysis_prompt(self):
        """Returns data analysis prompt for data tasks."""
        prompt = get_system_prompt("data_analysis")
        assert prompt == DATA_ANALYSIS_SYSTEM_PROMPT
        assert "pandas" in prompt

    def test_default_is_coding(self):
        """Default task type returns coding prompt."""
        prompt = get_system_prompt()
        assert prompt == CODING_SYSTEM_PROMPT


class TestCodeBlock:
    """Test CodeBlock dataclass."""

    def test_line_count_calculated(self):
        """Line count is auto-calculated from code."""
        block = CodeBlock(language="python", code="a = 1\nb = 2\nc = 3")
        assert block.line_count == 3

    def test_empty_code_line_count(self):
        """Empty code has zero line count."""
        block = CodeBlock(language="python", code="")
        assert block.line_count == 0


class TestCodeGenerationResult:
    """Test CodeGenerationResult dataclass."""

    def test_primary_code(self):
        """primary_code returns first block's code."""
        result = CodeGenerationResult(
            code_blocks=[
                CodeBlock(language="python", code="x = 1"),
                CodeBlock(language="python", code="y = 2"),
            ],
            raw_response="...",
            success=True,
        )
        assert result.primary_code == "x = 1"

    def test_primary_code_empty(self):
        """primary_code returns empty string when no blocks."""
        result = CodeGenerationResult(raw_response="no code", success=False)
        assert result.primary_code == ""

    def test_total_lines(self):
        """total_lines sums all blocks."""
        result = CodeGenerationResult(
            code_blocks=[
                CodeBlock(language="python", code="a = 1\nb = 2"),
                CodeBlock(language="python", code="c = 3"),
            ],
            raw_response="...",
            success=True,
        )
        assert result.total_lines == 3

    def test_to_dict(self):
        """to_dict produces serializable output."""
        result = CodeGenerationResult(
            code_blocks=[CodeBlock(language="python", code="x = 1")],
            raw_response="```python\nx = 1\n```",
            model_used="qwen2.5-coder:7b",
            success=True,
            duration_ms=150.0,
        )
        d = result.to_dict()
        assert d["success"] is True
        assert d["model_used"] == "qwen2.5-coder:7b"
        assert len(d["code_blocks"]) == 1
        assert d["code_blocks"][0]["language"] == "python"
        assert d["total_lines"] == 1
