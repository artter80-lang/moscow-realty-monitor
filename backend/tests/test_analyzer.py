import pytest

from app.analyzer.event_analyzer import AnalysisResult, EventAnalyzer

VALID_RESPONSE = {
    "category": "mortgage",
    "impact_score": -1,
    "price_direction": "down",
    "is_key_event": False,
    "reasoning": "Рост ставок по ипотеке снизит доступность жилья.",
}


def test_analysis_result_validates_impact():
    r = AnalysisResult(**{**VALID_RESPONSE, "impact_score": 99})
    assert r.impact_score == 2


def test_analysis_result_validates_category():
    r = AnalysisResult(**{**VALID_RESPONSE, "category": "unknown_cat"})
    assert r.category == "other"


def test_analysis_result_validates_direction():
    r = AnalysisResult(**{**VALID_RESPONSE, "price_direction": "sideways"})
    assert r.price_direction == "neutral"


@pytest.mark.asyncio
async def test_event_analyzer_returns_none_on_bad_json(mocker):
    mocker.patch(
        "app.analyzer.claude_client.ClaudeClient.analyze_event",
        return_value=None,
    )
    analyzer = EventAnalyzer()
    result = await analyzer.analyze("Тест", "Описание")
    assert result is None


@pytest.mark.asyncio
async def test_event_analyzer_returns_result_on_valid_response(mocker):
    mocker.patch(
        "app.analyzer.claude_client.ClaudeClient.analyze_event",
        return_value=VALID_RESPONSE,
    )
    analyzer = EventAnalyzer()
    result = await analyzer.analyze("Тест", "Описание")
    assert result is not None
    assert result.category == "mortgage"
    assert result.impact_score == -1
    assert result.price_direction == "down"
