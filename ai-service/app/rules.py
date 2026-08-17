# Guideline data used by the verification engine.
# These lists are intentionally small/illustrative for the MVP; the real
# PRGI guideline lists can be dropped in here or moved to the database once
# the schema/indexing step lands.

DISALLOWED_WORDS = {
    "police",
    "crime",
    "corruption",
    "cbi",
    "cid",
    "army",
    "vigilance",
    "intelligence",
    "raw",
    "nia",
    "ed",
}

# Words commonly prefixed/suffixed onto titles. Used both to detect "trivial"
# variations of an existing title (req 2) and to strip down to the "core"
# of a title before comparing (req 1b).
COMMON_AFFIXES = {
    "the",
    "india",
    "indian",
    "bharat",
    "hindustan",
    "samachar",
    "news",
    "times",
    "express",
    "herald",
    "tribune",
    "patrika",
    "gazette",
    "varta",
    "akhbar",
    "today",
    "daily",
    "weekly",
    "monthly",
}

# These descriptors occur in many publication titles. They remain available
# to the affix guideline checks above, but contribute only weakly to title
# similarity so a shared "daily" or "news" is not treated as distinctive.
GENERIC_PUBLICATION_TERMS = {
    "akhbar",
    "bulletin",
    "chronicle",
    "daily",
    "express",
    "gazette",
    "herald",
    "journal",
    "monthly",
    "news",
    "newspaper",
    "patrika",
    "post",
    "samachar",
    "times",
    "tribune",
    "varta",
    "weekly",
}

PERIODICITY_WORDS = {
    "daily",
    "weekly",
    "monthly",
    "fortnightly",
    "quarterly",
    "annual",
    "yearly",
    "biweekly",
}

# Transliterated regional-language words mapped to a canonical English
# meaning, so titles that mean the same thing in a different language can
# be caught (req 3d), e.g. "Daily Evening" vs "Pratidin Sandhya".
CROSS_LANGUAGE_EQUIVALENTS = {
    "samachar": "news",
    "khabar": "news",
    "varta": "news",
    "akhbar": "newspaper",
    "pratidin": "daily",
    "roz": "daily",
    "rozana": "daily",
    "saptahik": "weekly",
    "masik": "monthly",
    "sandhya": "evening",
    "sham": "evening",
    "shaam": "evening",
    "prabhat": "morning",
    "subah": "morning",
    "savera": "morning",
    "bharat": "india",
    "hindustan": "india",
    "desh": "nation",
    "rashtra": "nation",
    "patrika": "magazine",
    "prakash": "light",
    "jyoti": "light",
    "jyothi": "light",
}

# Thresholds (0-100 scale) tuned for the sample dataset; revisit once the
# real 160k-title corpus is loaded and we can validate against known
# accept/reject decisions.
SIMILARITY_DISPLAY_THRESHOLD = 40
SIMILARITY_REJECT_THRESHOLD = 85
TRIVIAL_AFFIX_MATCH_THRESHOLD = 88
COMBINATION_MATCH_THRESHOLD = 85
PERIODICITY_MATCH_THRESHOLD = 88
CROSS_LANGUAGE_MATCH_THRESHOLD = 85
