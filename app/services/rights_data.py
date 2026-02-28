"""Known trademark / IP patterns for rights verification.

Extracted from rights_engine.py. Production would load from a database.
"""

# Known IP elements that must be blocked in style_only references
KNOWN_TRADEMARK_PATTERNS: list[str] = [
    # These are examples — the production registry would be much larger
    "mario", "luigi", "pokemon", "pikachu", "naruto", "sasuke",
    "goku", "vegeta", "spider-man", "spiderman", "batman", "superman",
    "iron man", "ironman", "captain america", "thor", "hulk",
    "mickey mouse", "disney", "marvel", "dc comics",
    "tanjiro", "nezuko", "demon slayer", "jujutsu kaisen",
    "one piece", "luffy", "zoro",
]
