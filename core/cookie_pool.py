"""
Cookie Pool Manager — Loads and manages N distinct Google session cookie sets.

Each cookie set is identified by a numeric index (1-6) and loaded from
environment variables with the pattern: HIVE_{index}___Secure-1PSID, etc.

Cookie #1 is designated as the "Leader" — used for MoE synthesis.
Cookies #2-N are "Workers" — used for parallel generation.
"""

import os
import sys


# The three cookies required for a valid Gemini web session
REQUIRED_KEYS = ["__Secure-1PSID", "__Secure-1PSIDTS", "__Secure-1PSIDCC"]
MAX_SLOTS = 6


class CookiePool:
    """Manages a pool of Google session cookies extracted from .env"""

    def __init__(self, env_path=".env"):
        self._cookies = {}  # {slot_index: {cookie_name: cookie_value}}
        self._env_path = env_path
        self._load()

    def _load(self):
        """Parse .env file and load all HIVE_{N}_* cookie sets."""
        if not os.path.exists(self._env_path):
            print(f"\u274c [COOKIE POOL] .env not found at {self._env_path}")
            return

        raw = {}
        with open(self._env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue

                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().strip('"').strip("'")

                # Parse HIVE_{N}___Secure-1PSID pattern
                if key.startswith("HIVE_"):
                    parts = key.split("_", 2)  # ['HIVE', '1', '__Secure-1PSID']
                    if len(parts) >= 3:
                        try:
                            slot = int(parts[1])
                        except ValueError:
                            continue
                        cookie_name = parts[2]
                        # Reconstruct cookie name (the split ate one underscore)
                        # HIVE_1___Secure-1PSID → slot=1, cookie=__Secure-1PSID
                        if slot not in raw:
                            raw[slot] = {}
                        raw[slot][cookie_name] = value

        # Validate: only keep slots with all required cookies and non-placeholder values
        for slot in sorted(raw.keys()):
            if slot < 1 or slot > MAX_SLOTS:
                continue
            cookies = raw[slot]
            if all(
                k in cookies and cookies[k] and not cookies[k].startswith("your_")
                for k in REQUIRED_KEYS
            ):
                self._cookies[slot] = cookies
                print(
                    f"    \U0001f36a [POOL] Slot {slot} loaded "
                    f"(PSID: ...{cookies['__Secure-1PSID'][-8:]})"
                )
            else:
                missing = [k for k in REQUIRED_KEYS if k not in cookies or not cookies[k]]
                if missing:
                    print(
                        f"    \u26a0\ufe0f  [POOL] Slot {slot} skipped — "
                        f"missing: {', '.join(missing)}"
                    )

    def get_all(self):
        """Returns dict of all valid cookie sets {slot: {cookies}}."""
        return dict(self._cookies)

    def get_leader(self):
        """Returns the leader cookie set (slot 1). Used for MoE synthesis."""
        return self._cookies.get(1)

    def get_workers(self):
        """Returns worker cookie sets (slots 2-N). Used for parallel generation."""
        return {k: v for k, v in self._cookies.items() if k != 1}

    def get_slot(self, slot_id):
        """Returns a specific cookie set by slot index."""
        return self._cookies.get(slot_id)

    def worker_count(self):
        """Number of worker slots (excluding leader)."""
        return len(self.get_workers())

    def total_count(self):
        """Total number of valid cookie sets (leader + workers)."""
        return len(self._cookies)

    def slot_ids(self):
        """Returns sorted list of all valid slot IDs."""
        return sorted(self._cookies.keys())

    def worker_ids(self):
        """Returns sorted list of worker slot IDs (excluding leader)."""
        return sorted(k for k in self._cookies.keys() if k != 1)

    def summary(self):
        """Human-readable summary of the cookie pool state."""
        total = self.total_count()
        workers = self.worker_count()
        leader = "\u2705" if self.get_leader() else "\u274c"
        return (
            f"Cookie Pool: {total} slots loaded | "
            f"Leader: {leader} | Workers: {workers} | "
            f"Slots: {self.slot_ids()}"
        )


if __name__ == "__main__":
    pool = CookiePool()
    print(f"\n{pool.summary()}")
    if pool.total_count() == 0:
        print("\n\u274c No cookies loaded. Copy .env.example to .env and fill in your cookies.")
        sys.exit(1)
