"""
Account pool manager for multi-account support and automatic switching.
Manages account persistence (accounts.json), quota tracking, and rotation policies.
"""
from __future__ import annotations

import json
import logging
import os
import time
import uuid
from dataclasses import asdict, dataclass, field
from datetime import date
from typing import Any, Dict, List, Optional

log = logging.getLogger("doubao2api.account_manager")


@dataclass
class Account:
    id: str
    name: str
    cookies: Dict[str, str] = field(default_factory=dict)
    status: str = "active"  # "active", "quota_exceeded", "disabled", "invalid"
    video_quota_exceeded: bool = False
    quota_reset_date: str = field(default_factory=lambda: date.today().isoformat())
    last_used: float = 0.0
    created_at: float = field(default_factory=time.time)

    def to_dict(self, mask_cookies: bool = False) -> Dict[str, Any]:
        data = asdict(self)
        if mask_cookies:
            # Mask sensitive cookies for safe display in UI/API
            masked = {}
            for k, v in self.cookies.items():
                if len(v) > 8:
                    masked[k] = v[:3] + "..." + v[-3:]
                else:
                    masked[k] = "***"
            data["cookies"] = masked
            data["has_sessionid"] = "sessionid" in self.cookies
        return data


class AccountManager:
    """Manages an account pool stored in accounts.json."""

    def __init__(
        self,
        storage_dir: Optional[str] = None,
        filepath: Optional[str] = None,
        strategy: str = "failover",  # "failover" | "round_robin"
    ):
        if filepath:
            self.filepath = filepath
        elif storage_dir:
            self.filepath = os.path.join(storage_dir, "accounts.json")
        else:
            base_dir = os.environ.get(
                "DOUBAO_BROWSER_DATA",
                os.path.join(os.path.expanduser("~"), ".doubao_browser"),
            )
            self.filepath = os.path.join(base_dir, "accounts.json")

        self.strategy = os.environ.get("DOUBAO_ACCOUNT_STRATEGY", strategy).lower()
        if self.strategy not in ("failover", "round_robin"):
            self.strategy = "failover"

        self.active_account_id: Optional[str] = None
        self.accounts: Dict[str, Account] = {}
        self._round_robin_index = 0

        self.load()

    def load(self) -> None:
        """Load accounts from JSON file."""
        if not os.path.exists(self.filepath):
            return

        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.strategy = data.get("strategy", self.strategy)
            self.active_account_id = data.get("active_account_id")

            self.accounts.clear()
            for item in data.get("accounts", []):
                acc = Account(
                    id=item.get("id", str(uuid.uuid4())[:8]),
                    name=item.get("name", "未命名账号"),
                    cookies=item.get("cookies", {}),
                    status=item.get("status", "active"),
                    video_quota_exceeded=item.get("video_quota_exceeded", False),
                    quota_reset_date=item.get("quota_reset_date", date.today().isoformat()),
                    last_used=item.get("last_used", 0.0),
                    created_at=item.get("created_at", time.time()),
                )
                self.accounts[acc.id] = acc

            self.reset_daily_quotas_if_needed()

            # Ensure valid active_account_id
            if self.accounts and (not self.active_account_id or self.active_account_id not in self.accounts):
                self.active_account_id = next(iter(self.accounts.keys()))

            log.info("Loaded %d accounts from %s (active=%s, strategy=%s)",
                     len(self.accounts), self.filepath, self.active_account_id, self.strategy)
        except Exception as e:
            log.error("Failed to load accounts from %s: %s", self.filepath, e)

    def save(self) -> None:
        """Save accounts to JSON file."""
        try:
            os.makedirs(os.path.dirname(os.path.abspath(self.filepath)), exist_ok=True)
            data = {
                "active_account_id": self.active_account_id,
                "strategy": self.strategy,
                "accounts": [asdict(acc) for acc in self.accounts.values()],
            }
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            log.error("Failed to save accounts to %s: %s", self.filepath, e)

    def reset_daily_quotas_if_needed(self) -> None:
        """Reset quota exceeded flags if a new day has arrived."""
        today_str = date.today().isoformat()
        changed = False
        for acc in self.accounts.values():
            if acc.quota_reset_date != today_str:
                if acc.video_quota_exceeded:
                    acc.video_quota_exceeded = False
                    if acc.status == "quota_exceeded":
                        acc.status = "active"
                    log.info("Auto-reset daily quota for account %s (%s)", acc.id, acc.name)
                    changed = True
                acc.quota_reset_date = today_str
                changed = True
        if changed:
            self.save()

    def add_or_update_account(
        self,
        name: str,
        cookies: Dict[str, str],
        account_id: Optional[str] = None,
    ) -> Account:
        """Add a new account or update an existing one."""
        self.reset_daily_quotas_if_needed()

        if account_id and account_id in self.accounts:
            acc = self.accounts[account_id]
            acc.name = name or acc.name
            if cookies:
                acc.cookies = cookies
                acc.status = "active"
                acc.video_quota_exceeded = False
        else:
            acc_id = account_id or f"acc_{uuid.uuid4().hex[:8]}"
            acc = Account(
                id=acc_id,
                name=name or f"账号-{len(self.accounts) + 1}",
                cookies=cookies,
                status="active",
            )
            self.accounts[acc.id] = acc

        if not self.active_account_id or self.active_account_id not in self.accounts:
            self.active_account_id = acc.id

        self.save()
        return acc

    def get_account(self, account_id: str) -> Optional[Account]:
        self.reset_daily_quotas_if_needed()
        return self.accounts.get(account_id)

    def get_active_account(self) -> Optional[Account]:
        self.reset_daily_quotas_if_needed()
        if not self.active_account_id:
            if self.accounts:
                self.active_account_id = next(iter(self.accounts.keys()))
            else:
                return None
        return self.accounts.get(self.active_account_id)

    def set_active_account(self, account_id: str) -> bool:
        """Set the active account."""
        if account_id in self.accounts:
            self.active_account_id = account_id
            self.accounts[account_id].last_used = time.time()
            self.save()
            return True
        return False

    def delete_account(self, account_id: str) -> bool:
        """Delete an account from the pool."""
        if account_id in self.accounts:
            del self.accounts[account_id]
            if self.active_account_id == account_id:
                self.active_account_id = next(iter(self.accounts.keys())) if self.accounts else None
            self.save()
            return True
        return False

    def rename_account(self, account_id: str, new_name: str) -> bool:
        """Rename an account."""
        if account_id in self.accounts and new_name.strip():
            self.accounts[account_id].name = new_name.strip()
            self.save()
            return True
        return False

    def update_account_status(self, account_id: str, status: str) -> bool:
        """Update status for an account ('active', 'invalid', etc.)."""
        if account_id in self.accounts:
            self.accounts[account_id].status = status
            self.save()
            return True
        return False

    def mark_quota_exceeded(self, account_id: Optional[str] = None, feature: str = "video") -> None:
        """Mark an account's quota as exceeded for today."""
        target_id = account_id or self.active_account_id
        if not target_id or target_id not in self.accounts:
            return

        acc = self.accounts[target_id]
        if feature == "video":
            acc.video_quota_exceeded = True
            acc.status = "quota_exceeded"
        acc.quota_reset_date = date.today().isoformat()
        log.warning("Account %s (%s) marked as quota exceeded for %s", acc.id, acc.name, feature)
        self.save()

    def reset_quota(self, account_id: str) -> bool:
        """Manually reset quota for an account."""
        if account_id in self.accounts:
            acc = self.accounts[account_id]
            acc.video_quota_exceeded = False
            if acc.status == "quota_exceeded":
                acc.status = "active"
            self.save()
            return True
        return False

    def has_alternative_accounts(self, feature: str = "video") -> bool:
        """Check if there are other healthy accounts available."""
        self.reset_daily_quotas_if_needed()
        available = [
            acc for acc in self.accounts.values()
            if acc.status == "active" and not (feature == "video" and acc.video_quota_exceeded)
            and acc.id != self.active_account_id
        ]
        return len(available) > 0

    def get_next_available_account(self, feature: str = "video") -> Optional[Account]:
        """Get next available account based on rotation strategy."""
        self.reset_daily_quotas_if_needed()
        if not self.accounts:
            return None

        # Filter available accounts
        available = [
            acc for acc in self.accounts.values()
            if acc.status == "active" and not (feature == "video" and acc.video_quota_exceeded)
        ]

        if not available:
            # If all are quota exceeded or disabled, return None
            return None

        # 1. Failover Strategy: stick with current active if it is still available
        if self.strategy == "failover":
            active = self.get_active_account()
            if active and active in available:
                return active
            # Active account is exhausted/unavailable: pick the first available alternative
            next_acc = available[0]
            self.set_active_account(next_acc.id)
            return next_acc

        # 2. Round-Robin Strategy: rotate through all available accounts
        self._round_robin_index = (self._round_robin_index + 1) % len(available)
        selected = available[self._round_robin_index]
        self.set_active_account(selected.id)
        return selected

    def list_accounts(self, mask_cookies: bool = True) -> List[Dict[str, Any]]:
        """List all accounts for API/UI."""
        self.reset_daily_quotas_if_needed()
        result = []
        for acc in self.accounts.values():
            d = acc.to_dict(mask_cookies=mask_cookies)
            d["is_active"] = (acc.id == self.active_account_id)
            result.append(d)
        return result
