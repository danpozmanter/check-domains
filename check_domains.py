"""
Domain availability checker that searches for unregistered domains.

This module takes a list of base strings and checks their availability
across multiple top-level domains defined in a configuration file.
"""

import yaml
import whois
import argparse
from typing import List, Tuple


def load_config(config_file: str) -> List[str]:
    """
    Load top-level domains from a YAML configuration file.

    Args:
        config_file: Path to the YAML configuration file

    Returns:
        List of top-level domains
    """
    try:
        with open(config_file, 'r') as file:
            config = yaml.safe_load(file)
        return config.get('top_level_domains', [])
    except FileNotFoundError:
        return []


def load_strings(input_file: str) -> List[str]:
    """
    Load base strings from an input file.

    Args:
        input_file: Path to the input file containing base strings

    Returns:
        List of non-empty strings from the file
    """
    try:
        with open(input_file, 'r') as file:
            return [line.strip() for line in file if line.strip()]
    except FileNotFoundError:
        return []


def check_domain(domain: str) -> bool:
    """
    Check if a domain is registered.

    Args:
        domain: Domain name to check

    Returns:
        True if domain is registered, False otherwise
    """
    try:
        whois.whois(domain)
        return True  # Domain is registered
    except Exception:
        return False  # Domain is not registered or error occurred


def generate_domain_combinations(base_strings: List[str], tlds: List[str]) -> List[Tuple[str, str]]:
    """
    Generate all combinations of base strings and TLDs.

    Args:
        base_strings: List of base string names
        tlds: List of top-level domains

    Returns:
        List of tuples containing (full domain name, base string)
    """
    return [(f"{base}.{tld}", base) for base in base_strings for tld in tlds]


def find_available_domains(domain_combinations: List[Tuple[str, str]],
                           status_callback=None) -> List[str]:
    """
    Find available domains from a list of domain combinations.

    Args:
        domain_combinations: List of (domain, base) tuples
        status_callback: Optional callback function to report status

    Returns:
        List of available domain names
    """
    available_domains = []

    for domain, base in domain_combinations:
        if status_callback:
            status_callback(domain)

        if not check_domain(domain):
            available_domains.append(domain)

    return available_domains


def print_status(base: str) -> None:
    """
    Print status update for the current base string being checked.

    Args:
        base: The base string currently being checked
    """
    print(f"Checking: {base}")


def print_results(available_domains: List[str]) -> None:
    """
    Print the list of available domains.

    Args:
        available_domains: List of available domain names
    """
    if available_domains:
        print("Available domains:")
        print("\n".join(available_domains))
    else:
        print("No available domains found.")


def parse_arguments() -> argparse.Namespace:
    """
    Parse command line arguments.

    Returns:
        Parsed command line arguments
    """
    parser = argparse.ArgumentParser(description="Check for available domain names")
    parser.add_argument('input_file', help='File containing list of base strings')
    parser.add_argument('--config', default="config.yaml",
                        help='Configuration file path (default: config.yaml)')
    return parser.parse_args()


def main() -> None:
    """
    Main function to orchestrate the domain availability checking process.
    """
    args = parse_arguments()

    # Load configuration and input
    tlds = load_config(args.config)
    base_strings = load_strings(args.input_file)

    # Generate combinations and find available domains
    domain_combinations = generate_domain_combinations(base_strings, tlds)
    available_domains = find_available_domains(domain_combinations, print_status)

    # Output results
    print_results(available_domains)


if __name__ == "__main__":
    main()
