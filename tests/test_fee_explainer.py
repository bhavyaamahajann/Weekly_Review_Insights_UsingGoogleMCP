import unittest
from unittest.mock import patch, MagicMock
import os
import sys
import json
from pydantic import ValidationError

# Add src and workspace to python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.analysis.fee_explainer import (
    generate_fee_explainer,
    check_opinionated_language,
    extract_json_from_response,
    PRIMARY_MODEL,
    FALLBACK_MODEL
)
from src.utils.exceptions import PipelineAbortError

class MockMessage:
    def __init__(self, content):
        self.content = content

class MockChoice:
    def __init__(self, content):
        self.message = MockMessage(content)

class MockChatCompletion:
    def __init__(self, content):
        self.choices = [MockChoice(content)]

class TestFeeExplainer(unittest.TestCase):

    def setUp(self):
        os.environ["GROQ_API_KEY"] = "fake_key_for_testing"
        self.mock_sources = ["Groww Help Center", "SEBI Page"]

    def test_check_opinionated_language(self):
        neutral_bullets = [
            "Exit load is a fee charged on redemption.",
            "It is expressed as a percentage of the asset value.",
            "Holding periods are scheme-specific."
        ]
        has_op, _, _ = check_opinionated_language(neutral_bullets)
        self.assertFalse(has_op)

        opinionated_bullets = [
            "Exit load is a fee charged on redemption.",
            "You should avoid redeeming early to save cost.",
            "Holding periods are scheme-specific."
        ]
        has_op, idx, phrase = check_opinionated_language(opinionated_bullets)
        self.assertTrue(has_op)
        self.assertEqual(idx, 1)
        self.assertEqual(phrase, "you should")

    @patch("src.analysis.fee_explainer.Groq")
    def test_generate_fee_explainer_success(self, mock_groq_class):
        mock_client = MagicMock()
        mock_groq_class.return_value = mock_client
        
        valid_response_json = json.dumps({
            "scenario": "Mutual Fund Exit Load",
            "bullets": [
                "Exit load is a redemption fee charged by mutual funds.",
                "It applies if units are sold before a set holding period.",
                "The fee is deducted from the redemption proceeds."
            ],
            "sources": self.mock_sources,
            "last_checked": "June 2026"
        })
        mock_client.chat.completions.create.return_value = MockChatCompletion(valid_response_json)

        result = generate_fee_explainer(sources=self.mock_sources, iso_week="2026-W23")
        
        self.assertEqual(result["scenario"], "Mutual Fund Exit Load")
        self.assertEqual(len(result["bullets"]), 3)
        self.assertEqual(result["last_checked"], "June 2026")

    @patch("src.analysis.fee_explainer.Groq")
    def test_generate_fee_explainer_bullet_cap(self, mock_groq_class):
        mock_client = MagicMock()
        mock_groq_class.return_value = mock_client
        
        # Returns 8 bullets
        valid_response_json = json.dumps({
            "scenario": "Mutual Fund Exit Load",
            "bullets": [f"Bullet {i}" for i in range(1, 9)],
            "sources": self.mock_sources,
            "last_checked": "June 2026"
        })
        mock_client.chat.completions.create.return_value = MockChatCompletion(valid_response_json)

        result = generate_fee_explainer(sources=self.mock_sources, iso_week="2026-W23")
        
        # Verify it was capped to 6
        self.assertEqual(len(result["bullets"]), 6)

    @patch("src.analysis.fee_explainer.Groq")
    def test_generate_fee_explainer_opinion_retry_and_success(self, mock_groq_class):
        mock_client = MagicMock()
        mock_groq_class.return_value = mock_client
        
        opinion_response = json.dumps({
            "scenario": "Mutual Fund Exit Load",
            "bullets": [
                "Exit load is charged on early redemption.",
                "We recommend holding units for more than 1 year."
            ],
            "sources": self.mock_sources,
            "last_checked": "June 2026"
        })
        
        clean_response = json.dumps({
            "scenario": "Mutual Fund Exit Load",
            "bullets": [
                "Exit load is charged on early redemption.",
                "A holding period of 1 year is defined by the scheme."
            ],
            "sources": self.mock_sources,
            "last_checked": "June 2026"
        })
        
        # First call has opinion, second call (retry) is clean
        mock_client.chat.completions.create.side_effect = [
            MockChatCompletion(opinion_response),
            MockChatCompletion(clean_response)
        ]

        with patch("time.sleep"):
            result = generate_fee_explainer(sources=self.mock_sources, iso_week="2026-W23")
            self.assertEqual(mock_client.chat.completions.create.call_count, 2)
            self.assertIn("holding period of 1 year", result["bullets"][1])

    @patch("src.analysis.fee_explainer.Groq")
    def test_generate_fee_explainer_fallback(self, mock_groq_class):
        mock_client = MagicMock()
        mock_groq_class.return_value = mock_client
        
        import groq
        
        # Mock API failure 3 times on primary, success on fallback (4th call)
        mock_request = MagicMock()
        mock_client.chat.completions.create.side_effect = [
            groq.APIError("Internal Server Error", request=mock_request, body={}),
            groq.APIError("Internal Server Error", request=mock_request, body={}),
            groq.APIError("Internal Server Error", request=mock_request, body={}),
            MockChatCompletion(json.dumps({
                "scenario": "Mutual Fund Exit Load",
                "bullets": ["Factual bullet point."],
                "sources": self.mock_sources,
                "last_checked": "June 2026"
            }))
        ]

        with patch("time.sleep"):
            result = generate_fee_explainer(sources=self.mock_sources, iso_week="2026-W23")
            self.assertEqual(result["bullets"][0], "Factual bullet point.")
            self.assertEqual(mock_client.chat.completions.create.call_count, 4)
            
            # Check models called
            calls = mock_client.chat.completions.create.call_args_list
            self.assertEqual(calls[0][1]["model"], PRIMARY_MODEL)
            self.assertEqual(calls[3][1]["model"], FALLBACK_MODEL)

if __name__ == "__main__":
    unittest.main()
