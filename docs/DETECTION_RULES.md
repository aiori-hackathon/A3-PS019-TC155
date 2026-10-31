# Detection rules

Privexis uses these five classes:

- C1: Personal identity — name, date of birth, gender, age.
- C2: Contact information — email address, phone number.
- C3: Government identifiers — Aadhaar, PAN, passport, voter ID, driving licence.
- C4: Financial information — bank account, IFSC, card number, UPI ID.
- C5: Location / address — postal address, PIN code, geographic coordinates.

Fields that match none are labelled `not personal data`. Rules match field names and use bounded sample values only for limited format context. A field may match multiple classes; all matches are retained. Confidence is a rule signal, not a probability.

Each finding records rule ID, rule-set version, source/table/column, class, confidence, and a summary that contains no sampled value. SQLite sources open in read-only mode. See `EVALUATION.md` for the manually labelled synthetic evaluation set and limitations.
