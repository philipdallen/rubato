# Clinton St — vision note (DRAFT for the owner's edit)

*Status: draft. Final wording is the owner's call (issue #443 "Fenced").*

Clinton St is the first finished piece in the Rubato format: a 13-bar tune in
C major, Long Meter Double, carried end to end through the pipeline rather than
described by it.

What the artifact shows:

- **The format closes.** The tune encodes to a 1,608-byte `.ru` container
  (`artifacts/clinton-st/clinton-st.ru`) and decodes back note-for-note:
  recall 1.0, precision 1.0 against the source MusicXML (196 pitched notes + 16 rests, 2 parts). Nothing is lost and
  nothing is invented between source and container.
- **The pipeline runs on a real tune.** Source MusicXML → IR → `.ru` → decode →
  audio, using only the repo's own tools. The render is the sine stand-in path
  (`tools/muse_play`); the sample tier (`tools/muse_sample`, VSCO 2 CE) needs
  CDN read access, which this run could not obtain (see the blocker on #443).
- **It is the owner's own work.** The tune is by Philip D. Allen; the encoding
  is `ai_involvement: none` in the manifest — a human tune in a machine format,
  which is the point.

Where this goes next: the same page, staged on the CDN alongside a
sample-rendered audio take, is the outreach artifact for the Avid follow-up.
