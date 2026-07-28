"""
Analytics Tracker Module

Tracks engagement metrics across all platforms.
Stores data in a local JSON file for analysis.
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import defaultdict


class AnalyticsTracker:
    """Tracks marketing engagement analytics."""

    def __init__(self, data_file: Optional[str] = None):
        self.data_file = data_file or os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "analytics_data.json",
        )
        self.events: List[Dict] = []
        self._load_data()

    def _load_data(self):
        """Load analytics data from file."""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, "r") as f:
                    data = json.load(f)
                    self.events = data.get("events", [])
        except Exception:
            self.events = []

    def _save_data(self):
        """Save analytics data to file."""
        try:
            data = {
                "events": self.events,
                "last_updated": datetime.now().isoformat(),
            }
            with open(self.data_file, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[Analytics] Save error: {e}")

    def track_event(
        self,
        platform: str,
        action: str,
        success: bool = True,
        metadata: Optional[Dict] = None,
    ):
        """Track a marketing event."""
        event = {
            "timestamp": datetime.now().isoformat(),
            "platform": platform,
            "action": action,
            "success": success,
            "metadata": metadata or {},
        }
        self.events.append(event)
        self._save_data()

    def get_summary(self, days: int = 7) -> Dict:
        """Get analytics summary for the last N days."""
        cutoff = datetime.now() - timedelta(days=days)
        recent_events = [
            e for e in self.events if datetime.fromisoformat(e["timestamp"]) > cutoff
        ]

        # Count by platform
        platform_counts: Dict[str, int] = defaultdict(int)
        action_counts: Dict[str, int] = defaultdict(int)
        success_count = 0
        failure_count = 0

        for event in recent_events:
            platform_counts[event["platform"]] += 1
            action_counts[event["action"]] += 1
            if event["success"]:
                success_count += 1
            else:
                failure_count += 1

        return {
            "period_days": days,
            "total_events": len(recent_events),
            "success_count": success_count,
            "failure_count": failure_count,
            "success_rate": success_count / max(len(recent_events), 1),
            "by_platform": dict(platform_counts),
            "by_action": dict(action_counts),
        }

    def get_daily_breakdown(self, days: int = 7) -> List[Dict]:
        """Get daily breakdown of events."""
        cutoff = datetime.now() - timedelta(days=days)
        daily: Dict[str, Dict] = defaultdict(
            lambda: {"total": 0, "success": 0, "failure": 0}
        )

        for event in self.events:
            event_date = datetime.fromisoformat(event["timestamp"]).strftime("%Y-%m-%d")
            if datetime.fromisoformat(event["timestamp"]) > cutoff:
                daily[event_date]["total"] += 1
                if event["success"]:
                    daily[event_date]["success"] += 1
                else:
                    daily[event_date]["failure"] += 1

        return [{"date": date, **counts} for date, counts in sorted(daily.items())]

    def get_platform_stats(self) -> Dict[str, Dict]:
        """Get detailed stats per platform."""
        platform_stats: Dict[str, Dict] = defaultdict(
            lambda: {
                "total": 0,
                "success": 0,
                "failure": 0,
                "actions": defaultdict(int),
            }
        )

        for event in self.events:
            platform = event["platform"]
            platform_stats[platform]["total"] += 1
            if event["success"]:
                platform_stats[platform]["success"] += 1
            else:
                platform_stats[platform]["failure"] += 1
            platform_stats[platform]["actions"][event["action"]] += 1

        # Convert defaultdicts to regular dicts
        return {
            platform: {
                "total": stats["total"],
                "success": stats["success"],
                "failure": stats["failure"],
                "success_rate": stats["success"] / max(stats["total"], 1),
                "actions": dict(stats["actions"]),
            }
            for platform, stats in platform_stats.items()
        }

    def export_report(self, format: str = "text") -> str:
        """Export analytics report."""
        summary = self.get_summary(days=7)
        platform_stats = self.get_platform_stats()

        if format == "text":
            lines = [
                "=" * 60,
                "MARKETING ANALYTICS REPORT",
                "=" * 60,
                f"Period: Last {summary['period_days']} days",
                f"Total Events: {summary['total_events']}",
                f"Success Rate: {summary['success_rate']:.1%}",
                "",
                "BY PLATFORM:",
            ]

            for platform, stats in platform_stats.items():
                lines.append(f"  {platform}:")
                lines.append(f"    Total: {stats['total']}")
                lines.append(f"    Success Rate: {stats['success_rate']:.1%}")
                lines.append(f"    Actions: {', '.join(stats['actions'].keys())}")

            lines.append("")
            lines.append("=" * 60)

            return "\n".join(lines)

        elif format == "json":
            return json.dumps(
                {
                    "summary": summary,
                    "platform_stats": platform_stats,
                },
                indent=2,
            )

        return ""
