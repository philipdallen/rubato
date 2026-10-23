# Literature review — W1 IR, score compression, pattern discovery (2026-08-23)

Pre-drafting evidence for the W-series tools and S-series specs. Complements
[prior-art-spike.md](prior-art-spike.md) (renderer/mockup component intel) and
[PRIOR_ART_REVIEW.md](../PRIOR_ART_REVIEW.md) (schema-era landscape + the
2026-08-25 appendix: DAW-native AI re-survey — the conductor role remains
unclaimed; trained renderers do score→expressive MIDI, no LLM-with-sanctions
prior art. Plus the 2026-09-21 appendix: container/rights/rejection-discipline
prior art — MPM is the nearest neighbour to the seed).
Conclusions here inform [design/w1-event-ir.md](design/w1-event-ir.md) and the
downstream scaffolds it gates.

## 1. Event-stream representations (informs W1)

- **MusicXML** is the fidelity ceiling: notation semantics (ties, tuplets,
  articulations, dynamics, notations) survive; it has an official compressed
  container (.mxl, zip/DEFLATE). Costs: heavy, presentation-oriented. Use as
  the import surface, not the internal model. [musicxml.com]
- **MEI** adds scholarly/editorial rigor (source variants, editorial
  interventions). Not needed for the W-series; a possible import surface
  later. [music-encoding.org, LoC fdd000502]
- **Humdrum/kern** is the analytic-compact line format (pitch/duration +
  analytic annotations). Useful as a validation/graph debug surface, not the
  canonical IR. [humdrum.org/rep/kern]
- **Partitura note arrays** (CPJKU, MIT-ish open): structured 2-D arrays of
  (onset, pitch, velocity, IDs) with beat maps — the closest existing
  in-memory model to what W1 needs. Reads MusicXML/MIDI/MEI/Humdrum. Strong
  candidate for W1's object model or at least its schema reference.
  [github.com/CPJKU/partitura, partitura.readthedocs.io]
- **Token encodings for LLM contexts** (S3/L1 prompt design): REMI/REMI+
  (Bar/Position + Pitch/Velocity/Duration; REMI+ adds multi-track + time
  signatures) via MidiTok's unified API; Compound Word; OctupleMIDI/MusicBERT
  (claims ~75% shorter than REMI). These are *prompt-time* concerns; W1's IR
  must not be a token format but must make tokenization cheap.
  [miditok.readthedocs.io, github.com/YatingMusic/remi, MusicBERT]

**W1 takeaways:** MusicXML (and .mxl) in, MIDI in as fallback; internal model
≈ structured note arrays with full maps (tempo/meter/key) preserved — closing
the old importer's flattening bug; token schemes are downstream export shapes
(S3), not the IR.

## 2. Score compression (informs S2)

- **.mxl** proves zip+DEFLATE is the baseline; it reduces file size, not
  token sequence length. The format's S2 must do more than zip.
- **Octuple/per-note columnar encodings** (MusicBERT, OctupleMIDI) merge
  attributes into single tokens — big token-length cuts, but editing an
  attribute requires re-tokenization. For S2's on-disk packing (columnar +
  delta + dictionary + entropy), that tradeoff is fine; for the IR it is not.
- **LZ78-style symbolic compressors** (LZMidi, arXiv 2503.17654) learn
  probabilities incrementally; more generation-model than container — treat
  as evidence that pattern-factored source forms compress well, not as a
  packing dependency.
- **Pitfall:** any MIDI/token intermediate between parser and packer loses
  notation semantics; S2 must pack from the W1 IR, not from a MIDI dump.

**S2 takeaways:** packing runs on the IR (not on MIDI); Octuple-style column
merging is the token-shape evidence; dictionaries/entropy are the actual
workhorses.

## 3. Pattern discovery (informs W3)

- **SIATEC / COSIATEC / SIATEC-C** (point-set geometric discovery; O(n³)
  baseline, efficient variant available): finds maximal repeated patterns;
  COSIATEC outputs pattern + translator sets used for compression-oriented
  evaluation. Reference implementation: Ostinato (pauldhein/ostinato).
  [SIATEC-C paper; Ostinato repo]
- **Rhythmic/metric complement:** RegularTimeInterval_Patterns_Discovery for
  the rhythm side W3's spec lists (ostinati, sequences).
- **Evaluation:** NCD-based compressor metrics (arXiv 2010.12325); Patterns
  UI (SMC 2024) for human review of discovered catalogs (feeds W5-class
  review).
- **Scale warning:** Beethoven 9 at 239k notes will need SIATEC-C or
  sampling; the corpus ratchet must climb before the Ninth's pattern pass.

**W3 takeaways:** adopt SIATEC(-C) via Ostinato rather than hand-rolling
pattern matching; budget compute for the Ninth; W3's output schema becomes
S2/S4's evidence list, ordered by measured frequency.

## 4. Alignment datasets (informs W4 + C3 budgets)

Note-level score↔performance alignments in **match-file format** (Widmer-style;
Foscarin et al., MEC 2022), parseable by Partitura:

| Dataset | Contents | Alignment | Relevance |
|---|---|---|---|
| **OFAI/vienna4x22_rematched** | 4 Mozart scores (MusicXML), 88 MIDI performances, 88 .match | note-level | Delta source already in use; per-phrase curves extend it |
| **Magaloff** (Flossmann/Goedecke/Widmer) | ~10h Chopin, 155 performances, 336,581 played notes | match files | Romantic-era budget anchor |
| **Batik-plays-Mozart** | 12 sonatas, ~102k played notes, harmony/phrase CSVs | match files (+ audio-adjusted branch) | Classical structure annotations — a gift for C2 seed authoring |
| **ASMD** (arXiv 2003.01958) | meta-framework normalizing many audio↔score datasets | varies | Multi-corpus expansion path for W2 |
| **BSED** (Zenodo; T-ISMIR) | 20 Beethoven orchestral excerpts, 5 synced versions each, ~4.8–5.7GB | note-level (CSV/MIDI derived) | Orchestral-era budgets; probe before the Ninth's interpretation event |

The holder `docs/delta-analysis-plan.md`'s dataset menu is validated by
literature: Vienna→Classical, Magaloff→Romantic, BSED→Orchestral; Baroque
remains a gap candidate via humdrum-data chorale corpora for score analysis.

## 5. LLMs as score readers / performers (informs C2/L1 prompt design)

- **Zero-shot symbolic analysis works** (arXiv 2507.12808): stock LLMs
  identify melodic motion, chords, rhythm from symbolic inputs — supports
  C2's analyze-IR→propose-seed loop.
- **ScoreSpeak (Cal Poly thesis)**: an agentic LLM with >80 score-editing
  tools, benchmarked on 752 precise-edit cases — evidence that tool-shaped
  structured output + validation loops are the right architecture for
  score manipulation (validates the L1 generate→validate→fix pattern).
- **CLaMP 2 (arXiv 2410.13267)**: multimodal MIR across text/symbolic —
  vocabulary for prompt design.
- **Tokenization survey** (arXiv 2408.15176): track-aware structured
  tokenization for polyphony; informs how C2/L1 chunk scores into LLM
  context windows.

**C2/L1 takeaways:** structured tool calls + validation > free-form text;
polyphony survives chunked context when tokens are track-aware (REMI+).

## 6. Tooling stack to borrow (locked-by-convention)

- **Partitura** — parsing/note arrays/beat maps (CPJKU, GPLv3)
- **Parangonar / Parangonada** — alignment engine / visual correction
  (sildater) — for W4/L4 alignment work
- **pyAMPACT** — score→audio descriptor linking — feeds L4 distillation
- **Ostinato** — SIATEC for W3
- **MidiTok** — token export for prompts (S3)
- **Verovio / musicxml2hum** — optional debug engraving (humdrum.org)

## What this settles for next steps

1. **W1 draft now has its reference model** — Partitura-style note arrays +
  full maps; MusicXML/.mxl import, MIDI fallback; token schemes pushed to
  S3-time exports. W1's open question (articulation detail) narrows to:
  preserve notations umbrella, design curve fields per delta devices.
2. **S2's evidence chain** is packed-IR, not packed-MIDI; Octuple is a
  token-shape precedent, not a packing dependency.
3. **W3's algorithm is chosen** — SIATEC(-C) via Ostinato; rhythm algorithms
  as complement; scale plan for the 239k-note Ninth.
4. **W4/L4 alignment men** — Partitura+Parangonar; match-file convention
  documented (MEC 2022).
5. **C2/L1 prompt design** — tool-shaped outputs + validation (ScoreSpeak
  evidence); REMI+/MidiTok for context chunking.

## Sources (key)

- MusicXML: musicxml.com/for-developers; W3 tutorial (notation-basics,
  compressed .mxl files); LoC MEI format family (fdd000502)
- Humdrum kern: humdrum.org/rep/kern; humdrum-data corpora
- Partitura: github.com/CPJKU/partitura; readthedocs tutorial
- REMI/REMI+; MidiTok tokenizations; MusicBERT/OctupleMIDI; tokenization
  survey arXiv 2408.15176
- LZMidi: arXiv 2503.17654; NCD evaluation arXiv 2010.12325
- SIATEC-C (Björklund); Ostinato (pauldhein/ostinato);
  RegularTimeInterval_Patterns_Discovery (MathysDaniel); Patterns UI SMC 2024
- Match-file format: Foscarin et al., "The Match File Format", MEC 2022
- Datasets: OFAI/vienna4x22_rematched (GitHub); Flossmann et al. Magaloff
  (JNMR 2010, T-ISMIR 317); Batik-plays-Mozart (ISMIR 2023, GitHub);
  ASMD (arXiv 2003.01958); BSED (Zenodo 17262629, T-ISMIR 343)
- LLM evidence: arXiv 2507.12808 (zero-shot analysis); ScoreSpeak
  (Cal Poly thesis, Nathan S. Lim); CLaMP 2 (arXiv 2410.13267)
- Tooling: Parangonar/Parangonada (sildater); pyAMPACT docs; Verovio
  (rism-digital/verovio); musicxml2hum (VHV)
