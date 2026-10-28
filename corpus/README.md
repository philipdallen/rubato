# Muse compression corpus — source registry

Reference corpus for the whole build: the analyzer (Phase 0), the compression
loop (Phase 3), conformance testing (Phase 2), and the end-to-end ratchet.
Every work is either public domain or owner-supplied; sources below are new
engravings/encodings of those works (see Licensing).

| Work | File(s) | Source | Format | Scale |
|---|---|---|---|---|
| Bach, *Jesu, meine Freude* BWV 227 (chorale movements) | `bach/bwv227.{1,3,7,11}.mxl` | music21 corpus (github.com/cuthbertLab/music21) | compressed MusicXML | ~280 notes, 4 voices each |
| Byrd, *Mass for Three Voices* (all 6 movements) | `byrd/{1-Kyrie..6-Agnus}.mid` | learnchoralmusic.co.uk (CPDL-derived) | MIDI | 3-voice polyphony |
| Schubert, *Death and the Maiden* D.810 (complete quartet) | `schubert/death-and-the-maiden.mxl` | OpenScore/StringQuartets (CC) | compressed MusicXML | 24,772 notes, 4 parts, ~1,445 bars |
| Beethoven, Symphony No. 5, mov. 1 (full orchestra) | `beethoven/beethoven-sym5-mov1.xml` | nyckmaia/maialib examples | MusicXML 3.1 | 13,675 notes, 12 parts, 431 dynamics |
| Beethoven, Symphony No. 9 (complete) | `beethoven/beethoven-sym9.xml` | nyckmaia/maialib examples | MusicXML | 239,459 notes, 52 parts, 11,931 dynamics |
| Allen, *Clinton St* (owner-supplied) | `allen/clinton-st.{musicxml,mid}` | owner's own MIDI, converted to MusicXML 4.0 (2026-10-21) | MIDI + MusicXML 4.0 | 2 parts; 212 notes (MusicXML) / 192 (MIDI); 13 bars, C major |

## Ladder

1. Bach chorale movements (small, homophonic, voice-leading)
2. Byrd mass movements (small, imitative polyphony)
3. Schubert finale (mid-scale chamber, dramatic structure)
4. Beethoven 5 mov. 1 (full orchestra, sonata form)
5. **Beethoven 9 complete** — the v1.0 conformance target. 239k notes.

## Quality notes (measured)

- Bach: SATB separated (mvt 3 is the SSATB fantasia — 5 parts, 377 notes;
  mvts 1/7/11: 4 parts, 279/307/190 notes); tempo marks only in mvts 1 & 3
  (7 & 11 carry none); **no dynamics** — chorales are typically unmarked;
  fine for pitch/rhythm/form tests.
- Byrd: MIDI only (no MusicXML found without a CAPTCHA wall — CPDL is behind
  Cloudflare). No dynamics. Tests the polyphonic-inference path.
- Schubert: OpenScore professional encoding, tempo marks; dynamics sparse.
- Beethoven 5 mov 1: 431 dynamic markings — the richest expressive layer.
- Beethoven 9: 11,931 dynamic markings, 52 staves including chorus/soloists.
- Clinton St (Allen): owner-supplied MIDI converted to MusicXML 4.0; 2 parts,
  no dynamics/hairpins; both the `.musicxml` and `.mid` carry pins. The
  MusicXML metronome mark is present, so its tempo map uses `<sound tempo>`
  values (a load warning, not an error).

## Licensing

The four composers (Bach, Byrd, Schubert, Beethoven) are long public domain
(d. 1623–1827); their sources are new encodings of public-domain works, freely
distributed by their hosts. Clinton St (Allen) is **not** public domain — it is
the owner's own work, supplied for this project. Record provenance in the `.ru`
manifest at compression time regardless — the format's own rule.
