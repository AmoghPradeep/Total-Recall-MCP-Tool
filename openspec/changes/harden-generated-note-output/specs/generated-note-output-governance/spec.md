## ADDED Requirements

### Requirement: Generated markdown notes SHALL avoid reserved vault roots
The system SHALL reserve internal vault roots such as `z.rawdata` for source storage and MUST NOT write generated markdown notes under reserved system directories.

#### Scenario: Reserved output root is rejected
- **WHEN** the model returns a `relativePath` rooted in `z.rawdata` or another reserved internal directory
- **THEN** the system MUST reject that destination and MUST write the note to the safe fallback output directory instead

#### Scenario: Directory hints exclude reserved roots
- **WHEN** the system prepares eligible directory hints for note generation
- **THEN** it MUST omit reserved internal directories from the hint list shown to the model

### Requirement: Generated notes SHALL use a canonical visible note structure
The system SHALL treat the markdown file name as the visible note title and MUST write normalized note bodies without a top-level H1 title heading.

#### Scenario: Successful note omits duplicate title heading
- **WHEN** a normalized note is generated successfully
- **THEN** the written markdown body MUST NOT begin with a top-level title heading that duplicates the file name

#### Scenario: Model-emitted title heading is removed
- **WHEN** the model returns note content that includes a leading top-level H1 title
- **THEN** the system MUST remove that title heading before writing the final markdown file

### Requirement: Generated notes SHALL contain one canonical sources section
The system SHALL own source-provenance rendering and MUST write at most one canonical `## Sources` section in each generated note.

#### Scenario: Duplicate provenance sections are consolidated
- **WHEN** the model returns a `Resources`, `Source`, or `Sources` section and the pipeline also has source metadata to attach
- **THEN** the system MUST remove the duplicate provenance sections and MUST write exactly one canonical `## Sources` section

#### Scenario: Sources section is appended when provenance exists
- **WHEN** the pipeline has one or more raw-source references for a generated note
- **THEN** the final note MUST include one canonical `## Sources` section containing those references

### Requirement: Generated note placement SHALL follow a bounded knowledge taxonomy
The system SHALL restrict generated note destinations to approved broad knowledge roots and MUST limit the destination hierarchy to at most three path segments.

#### Scenario: Broad approved destination is accepted
- **WHEN** the model returns a destination such as `Topics/Machine Learning/RAG`
- **THEN** the system MUST accept that destination if it is within the approved taxonomy and within the maximum hierarchy depth

#### Scenario: Overly specific or unapproved destination falls back
- **WHEN** the model returns a destination outside the approved taxonomy or deeper than three path segments
- **THEN** the system MUST reject that destination and MUST use the fallback output directory instead

### Requirement: Source provenance SHALL use aliased Obsidian wikilinks
The system SHALL render source provenance with aliased Obsidian wikilinks so the visible note body shows human-readable labels while the link target remains the exact raw asset path.

#### Scenario: Single raw source uses readable alias label
- **WHEN** a generated note has one raw source file
- **THEN** the canonical `## Sources` section MUST render an aliased Obsidian wikilink whose visible label is human-readable rather than the raw path text

#### Scenario: Multi-source note uses readable per-source labels
- **WHEN** a generated note has multiple raw source files such as page images
- **THEN** the canonical `## Sources` section MUST render readable aliased links for each source rather than exposing raw visible paths

### Requirement: Provenance SHALL reference stable vault-backed raw assets
The system SHALL build source provenance from raw assets staged inside the vault and MUST NOT expose transient local temp paths in generated notes or provenance-related prompt context.

#### Scenario: Audio provenance uses staged raw file
- **WHEN** the audio pipeline generates a normalized note
- **THEN** the source reference used for provenance MUST point to the staged raw audio file inside the vault instead of a temporary compressed file path

#### Scenario: Prompt context uses stable source reference
- **WHEN** the system provides source-reference context to the note-generation prompt
- **THEN** it MUST provide a stable vault-backed raw-source reference rather than a transient temp path
