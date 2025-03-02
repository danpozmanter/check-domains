"""
Tests for the domain availability checker.

This module provides comprehensive tests for all functions in the
domain availability checker, using pytest fixtures and mocks
to isolate units and avoid actual network calls.
"""

import pytest
from unittest.mock import patch, mock_open, MagicMock, call
import os
import tempfile
import yaml
import check_domains


@pytest.fixture
def sample_config():
    """Fixture providing sample configuration data."""
    return """
    top_level_domains:
      - com
      - net
      - org
    """


@pytest.fixture
def sample_input():
    """Fixture providing sample input data."""
    return """
    example
    test

    sample
    """


def test_load_config_with_valid_file(sample_config):
    """Test loading config from a valid YAML file."""
    with patch("builtins.open", mock_open(read_data=sample_config)):
        result = check_domains.load_config("dummy_path.yaml")
        assert result == ["com", "net", "org"]


def test_load_config_with_missing_file():
    """Test loading config when file doesn't exist."""
    with patch("builtins.open", side_effect=FileNotFoundError):
        result = check_domains.load_config("nonexistent.yaml")
        assert result == []


def test_load_config_with_invalid_yaml():
    """Test loading config with invalid YAML content."""
    with patch("builtins.open", mock_open(read_data="invalid: yaml: content:")):
        with patch("yaml.safe_load", side_effect=yaml.YAMLError):
            with pytest.raises(yaml.YAMLError):
                check_domains.load_config("invalid.yaml")


def test_load_strings_with_valid_file(sample_input):
    """Test loading strings from a valid input file."""
    with patch("builtins.open", mock_open(read_data=sample_input)):
        result = check_domains.load_strings("dummy_input.txt")
        assert result == ["example", "test", "sample"]


def test_load_strings_with_missing_file():
    """Test loading strings when file doesn't exist."""
    with patch("builtins.open", side_effect=FileNotFoundError):
        result = check_domains.load_strings("nonexistent.txt")
        assert result == []


def test_check_domain_registered():
    """Test checking a registered domain."""
    with patch("whois.whois", return_value=MagicMock()):
        assert check_domains.check_domain("example.com") is True


def test_check_domain_unregistered():
    """Test checking an unregistered domain."""
    with patch("whois.whois", side_effect=Exception("Domain not found")):
        assert check_domains.check_domain("nonexistent-domain-12345.com") is False


def test_generate_domain_combinations():
    """Test generating domain combinations from base strings and TLDs."""
    bases = ["test", "example"]
    tlds = ["com", "net"]

    expected = [
        ("test.com", "test"),
        ("test.net", "test"),
        ("example.com", "example"),
        ("example.net", "example")
    ]

    result = check_domains.generate_domain_combinations(bases, tlds)
    assert sorted(result) == sorted(expected)


def test_find_available_domains():
    """Test finding available domains with a mock domain checker."""
    domains = [
        ("test.com", "test"),
        ("test.net", "test"),
        ("example.com", "example")
    ]

    # Mock check_domain to return False only for test.net (making it available)
    with patch("check_domains.check_domain",
               side_effect=lambda domain: False if domain == "test.net" else True):
        result = check_domains.find_available_domains(domains)
        assert result == ["test.net"]


def test_find_available_domains_with_callback():
    """Test finding available domains with status callback."""
    domains = [
        ("test.com", "test"),
        ("example.com", "example")
    ]

    callback_mock = MagicMock()

    # Mock check_domain to return False for all domains (unregistered)
    with patch("check_domains.check_domain", return_value=False):
        check_domains.find_available_domains(domains, callback_mock)

        # Expect the callback to be called with full domain names
        expected_calls = [call("test.com"), call("example.com")]
        for expected in expected_calls:
            assert expected in callback_mock.mock_calls


def test_print_status(capsys):
    """Test printing status updates."""
    check_domains.print_status("example")
    captured = capsys.readouterr()
    assert "Checking: example" in captured.out


def test_print_results_with_domains(capsys):
    """Test printing results when domains are available."""
    available = ["test.com", "example.org"]
    check_domains.print_results(available)

    captured = capsys.readouterr()
    assert "Available domains:" in captured.out
    assert "test.com" in captured.out
    assert "example.org" in captured.out


def test_print_results_no_domains(capsys):
    """Test printing results when no domains are available."""
    check_domains.print_results([])

    captured = capsys.readouterr()
    assert "No available domains found." in captured.out


def test_parse_arguments():
    """Test argument parsing with default config path."""
    with patch("argparse.ArgumentParser.parse_args",
               return_value=MagicMock(input_file="domains.txt", config="config.yaml")):
        args = check_domains.parse_arguments()
        assert args.input_file == "domains.txt"
        assert args.config == "config.yaml"


def test_main_function():
    """Test the main function with mocked dependencies."""
    with patch("check_domains.parse_arguments") as mock_parse_args, \
         patch("check_domains.load_config") as mock_load_config, \
         patch("check_domains.load_strings") as mock_load_strings, \
         patch("check_domains.generate_domain_combinations") as mock_gen_combinations, \
         patch("check_domains.find_available_domains") as mock_find_domains, \
         patch("check_domains.print_results") as mock_print_results:

        # Configure mocks
        mock_parse_args.return_value = MagicMock(input_file="domains.txt", config="config.yaml")
        mock_load_config.return_value = ["com", "org"]
        mock_load_strings.return_value = ["test", "example"]
        mock_gen_combinations.return_value = [("test.com", "test"), ("example.org", "example")]
        mock_find_domains.return_value = ["test.com"]

        # Run main function
        check_domains.main()

        # Verify all expected functions were called with correct args
        mock_parse_args.assert_called_once()
        mock_load_config.assert_called_once_with("config.yaml")
        mock_load_strings.assert_called_once_with("domains.txt")
        mock_gen_combinations.assert_called_once_with(["test", "example"], ["com", "org"])
        mock_find_domains.assert_called_once()
        mock_print_results.assert_called_once_with(["test.com"])


def test_integration_with_files():
    """Integration test using temp files."""
    # Create temp files for config and input
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as config_file:
        config_file.write("top_level_domains:\n  - com\n  - net")

    with tempfile.NamedTemporaryFile(mode='w', delete=False) as input_file:
        input_file.write("test\nexample")

    try:
        # Mock the domain checker and main functions
        with patch("check_domains.check_domain", return_value=False), \
             patch("check_domains.print_status"), \
             patch("sys.argv", ["check_domains.py", input_file.name, "--config", config_file.name]), \
             patch("check_domains.print_results") as mock_print:

            check_domains.main()

            # Verify results contain all expected domains
            called_args = mock_print.call_args[0][0]
            assert "test.com" in called_args
            assert "test.net" in called_args
            assert "example.com" in called_args
            assert "example.net" in called_args

    finally:
        # Clean up temp files
        os.unlink(config_file.name)
        os.unlink(input_file.name)


if __name__ == "__main__":
    pytest.main(["-v"])
