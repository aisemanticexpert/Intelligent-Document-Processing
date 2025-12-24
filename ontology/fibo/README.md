# FIBO - Financial Industry Business Ontology

This folder contains selected ontology files from the [FIBO (Financial Industry Business Ontology)](https://spec.edmcouncil.org/fibo/) project by EDM Council.

## Overview

FIBO defines the sets of things that are of interest in financial business applications and the ways that those things can relate to one another. FIBO can give meaning to any data (e.g., spreadsheets, relational databases, XML documents) that describe the business of finance.

## Downloaded Modules

| File | Description |
|------|-------------|
| `AboutFIBOProd.rdf` | Main FIBO production ontology loader |
| `FND-AllFND.rdf` | Foundations - core concepts (organizations, parties, places) |
| `FND-FormalOrganizations.rdf` | Formal organization definitions |
| `FND-Parties.rdf` | Party and agent definitions |
| `BE-AllBE.rdf` | Business Entities - legal entities and corporations |
| `BE-Corporations.rdf` | Corporation-specific definitions |
| `SEC-AllSEC.rdf` | Securities domain ontology |
| `FBC-AllFBC.rdf` | Financial Business and Commerce ontology |

## FIBO Domains

- **FND (Foundations)**: Core concepts required by other domains
- **BE (Business Entities)**: Legal entities, corporations, partnerships
- **FBC (Financial Business and Commerce)**: Financial products and services
- **SEC (Securities)**: Securities and related instruments
- **DER (Derivatives)**: Derivative instruments
- **LOAN (Loans)**: Loan products
- **IND (Indices and Indicators)**: Market indices and indicators

## Usage

These ontologies are used for semantic alignment with the Financial IDR Pipeline ontology (`financial_ontology.ttl`).

## License

Copyright (c) 2013-2025 EDM Council, Inc.
Copyright (c) 2013-2025 Object Management Group, Inc.

## Sources

- GitHub: https://github.com/edmcouncil/fibo
- Specification: https://spec.edmcouncil.org/fibo/
- Releases: https://github.com/edmcouncil/fibo/releases

## Contributor

Rajesh Gupta
