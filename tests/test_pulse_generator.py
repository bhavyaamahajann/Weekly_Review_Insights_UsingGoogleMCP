import unittest
from unittest.mock import patch, MagicMock
import os
import sys
import json
from pydantic import ValidationError

# Add src and workspace to python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.analysis.pulse_generator import (
    generate_weekly_pulse,
    truncate_summary_to_word_cap,
    check_action_ideas_similarity,
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

class TestPulseGenerator(unittest.TestCase):

    def setUp(self):
        self.mock_themes = [
            {"label": "App Performance", "size": 100, "review_indices": [0, 1]},
            {"label": "Withdrawal Experience", "size": 50, "review_indices": [2, 3]},
            {"label": "Customer Support", "size": 30, "review_indices": [4, 5]}
        ]
        self.mock_quotes = [
            {"theme": "App Performance", "quote": "The app lags when loading stock charts.", "source_review_id": "abc1"},
            {"theme": "Withdrawal Experience", "quote": "Withdrawal is taking more than 3 days.", "source_review_id": "abc2"},
            {"theme": "Customer Support", "quote": "Support team takes forever to reply.", "source_review_id": "abc3"}
        ]
        os.environ["GROQ_API_KEY"] = "fake_key_for_testing"

    def test_truncate_summary_to_word_cap(self):
        # A summary with 10 words
        summary_short = "This is a simple short review of the application system."
        self.assertEqual(truncate_summary_to_word_cap(summary_short, 250), summary_short)

        # A summary with > 250 words
        long_sentence = "Word " * 260 + "."
        truncated = truncate_summary_to_word_cap(long_sentence, 250)
        self.assertTrue(len(truncated.split()) <= 250)

    def test_extract_json_from_response(self):
        valid_json_str = '{"weekly_summary": "Good app", "sentiment": {"positive": 50, "negative": 30, "neutral": 20}, "action_ideas": ["a", "b", "c"]}'
        data = extract_json_from_response(valid_json_str)
        self.assertEqual(data["weekly_summary"], "Good app")

        wrapped_json_str = f"Some markdown pre-amble:\n```json\n{valid_json_str}\n```\npost-amble."
        data_wrapped = extract_json_from_response(wrapped_json_str)
        self.assertEqual(data_wrapped["weekly_summary"], "Good app")

        with self.assertRaises(ValueError):
            extract_json_from_response("invalid json")

    @patch("src.analysis.pulse_generator.Groq")
    def test_generate_weekly_pulse_success(self, mock_groq_class):
        mock_client = MagicMock()
        mock_groq_class.return_value = mock_client
        
        valid_response_json = json.dumps({
            "weekly_summary": "Users generally report positive feedback regarding Groww's investment flow, but note performance issues and withdrawal delays.",
            "sentiment": {
                "positive": 60,
                "negative": 30,
                "neutral": 10
            },
            "action_ideas": [
                "Fix chart loading lag in options trading.",
                "Optimize withdrawal verification speeds.",
                "Provide ticketing details in support chat."
            ]
        })
        mock_client.chat.completions.create.return_value = MockChatCompletion(valid_response_json)

        # Run generator
        result = generate_weekly_pulse(self.mock_themes, self.mock_quotes, iso_week="2026-W23")
        
        self.assertEqual(result["sentiment"]["positive"], 60)
        self.assertEqual(len(result["action_ideas"]), 3)
        self.assertTrue(
            any("chart loading" in idea.lower() for idea in result["action_ideas"]) or
            "chart loading" in result["weekly_summary"].lower()
        )

    @patch("src.analysis.pulse_generator.Groq")
    def test_generate_weekly_pulse_auth_error(self, mock_groq_class):
        mock_client = MagicMock()
        mock_groq_class.return_value = mock_client
        
        import groq
        # Force authentication error
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_client.chat.completions.create.side_effect = groq.AuthenticationError(
            "Invalid API Key",
            response=mock_response,
            body={}
        )

        with self.assertRaises(PipelineAbortError):
            generate_weekly_pulse(self.mock_themes, self.mock_quotes)

    @patch("src.analysis.pulse_generator.Groq")
    def test_generate_weekly_pulse_fallback(self, mock_groq_class):
        mock_client = MagicMock()
        mock_groq_class.return_value = mock_client
        
        import groq
        
        # Mock rate limit 3 times on primary, success on fallback (4th call)
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_client.chat.completions.create.side_effect = [
            groq.RateLimitError("Rate limit exceeded", response=mock_response, body={}),
            groq.RateLimitError("Rate limit exceeded", response=mock_response, body={}),
            groq.RateLimitError("Rate limit exceeded", response=mock_response, body={}),
            MockChatCompletion(json.dumps({
                "weekly_summary": "Fallback success summary of user reviews.",
                "sentiment": {"positive": 50, "negative": 40, "neutral": 10},
                "action_ideas": [
                    "Fix chart loading lag in options trading.",
                    "Optimize withdrawal verification speeds.",
                    "Provide ticketing details in support chat."
                ]
            }))
        ]

        # Patch time.sleep to run quickly
        with patch("time.sleep"):
            result = generate_weekly_pulse(self.mock_themes, self.mock_quotes, iso_week="2026-W23")
            self.assertEqual(result["weekly_summary"], "Fallback success summary of user reviews.")
            
            # Verify it was called 4 times (3 for primary, 1 for fallback)
            self.assertEqual(mock_client.chat.completions.create.call_count, 4)
            # Check models called
            calls = mock_client.chat.completions.create.call_args_list
            self.assertEqual(calls[0][1]["model"], PRIMARY_MODEL)
            self.assertEqual(calls[3][1]["model"], FALLBACK_MODEL)

if __name__ == "__main__":
    unittest.main()
