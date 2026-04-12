## ADDED Requirements

### Requirement: Expose MCP delta reindex tool for vault markdown
The system SHALL expose an MCP tool that scans the Obsidian vault for new, changed, and removed markdown files and updates embeddings only for the delta.

#### Scenario: Reindex changed markdown files
- **WHEN** `reindex_vault_delta` is invoked and markdown files have changed since last manifest snapshot
- **THEN** the system recomputes chunks/embeddings only for changed or new files and upserts them into the vector store

#### Scenario: Remove vectors for deleted markdown files
- **WHEN** `reindex_vault_delta` is invoked and previously indexed markdown files are now deleted
- **THEN** the system removes associated chunk vectors from the vector store

### Requirement: Maintain manifest for idempotent delta detection
The system SHALL persist a manifest of indexed markdown file fingerprints to support deterministic delta computation.

#### Scenario: No-op on unchanged vault state
- **WHEN** `reindex_vault_delta` is invoked and all markdown fingerprints match the manifest
- **THEN** the system performs no embedding regeneration and returns zero updated documents

#### Scenario: Recover manifest after restart
- **WHEN** the MCP process restarts
- **THEN** the system loads existing manifest state and continues delta detection without full reindex
