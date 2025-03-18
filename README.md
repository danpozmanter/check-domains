# check-domains
Quickly check multiple variations of available domains.

[![Tests Passing](https://github.com/danpozmanter/check-domains/actions/workflows/test.yml/badge.svg)](https://github.com/danpozmanter/check-domains/actions)

## Usage

```
./run.sh example_domains.txt
```

## Test

```
./test.sh
```

## Config

```yaml
top_level_domains:
  - com
  - org
```

## Example File

```
google
pumpupthejam
```

This would check if google.com, google.org, pumpupthejam.com, pumpupthejam.org were available or registered.
