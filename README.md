score_pair

Scores how likely two customer records are the same person, from 0.0 to 1.0.

Run it

Needs Python 3.9 or newer. No libraries to install.

python run_pair.py R0007 R0058

Swap in any two record_id values from customer-records.csv. To run the tests: pip install pytest then python -m pytest.

How it works

The confidence is the weighted average of the fields that could be compared. If a field is blank on either side it is left out completely, so it counts neither for nor against.

name (phonetic): splits names into words so order and case don't matter. Each word pair scores the better of its spelling similarity and a rough sound key (so Swathi / Swati match). An initial like "S." scores 0.85 against any name starting with S.
email (edit distance): lowercase both, then 1 minus (Levenshtein distance / longer length).
phone: removes spaces, hyphens, +91 and a leading 0, then checks they are equal.
date of birth: reads the formats in the file (day first), then checks the dates are equal.
pin code, city: equal after trimming and ignoring case.
