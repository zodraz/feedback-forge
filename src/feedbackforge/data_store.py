"""
FeedbackForge Data Store
========================

In-memory data store for feedback items with query methods.
"""

import random
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from .models import FeedbackItem, SurveyResponse


class FeedbackDataStore:
    """Data store for feedback - can be populated from workflow results or mock data."""

    def __init__(self):
        self.feedback: List[FeedbackItem] = []
        self.analysis_results: Optional[Dict[str, Any]] = None
        self.alerts: List[Dict[str, Any]] = []

    def load_from_workflow_results(self, results: Dict[str, Any], surveys: List[SurveyResponse]) -> None:
        """Load data from workflow analysis results."""
        self.analysis_results = results
        for survey in surveys:
            topics_data = results.get("parallel_analysis", {}).get("topics", {})

            self.feedback.append(FeedbackItem(
                id=survey.id,
                text=survey.text,
                sentiment="negative" if survey.rating and survey.rating <= 2 else "positive" if survey.rating and survey.rating >= 4 else "neutral",
                sentiment_score=(survey.rating - 3) / 2 if survey.rating else 0,
                topics=list(topics_data.get("topic_distribution", {}).keys()) if topics_data else [],
                customer_segment=survey.customer_segment or "Unknown",
                customer_id=survey.customer_id or survey.id,
                customer_name=survey.customer_name or f"Customer {survey.id}",
                rating=survey.rating or 3,
                timestamp=datetime.fromisoformat(survey.timestamp) if survey.timestamp else datetime.now(),
                product_version=survey.product_version or "Unknown",
                platform=survey.platform,
            ))

    def load_mock_data(self) -> None:
        """Generate realistic mock feedback data."""
        platforms = ["iOS", "Android", "Web", "Desktop"]
        versions = ["2.0.3", "2.0.2", "2.0.1", "1.9.5"]

        enterprise_customers = [
            ("ENT001", "GlobalCorp Inc"), ("ENT002", "TechGiant Ltd"),
            ("ENT003", "Acme Corporation"), ("ENT004", "MegaSystems"), ("ENT005", "DataFlow Inc"),
        ]
        smb_customers = [
            ("SMB001", "TechStart"), ("SMB002", "GrowthCo"),
            ("SMB003", "InnovateLab"), ("SMB004", "SmallBiz Pro"), ("SMB005", "LocalTech"),
        ]
        individual_customers = [
            ("IND001", "John Smith"), ("IND002", "Jane Doe"),
            ("IND003", "Bob Wilson"), ("IND004", "Alice Brown"), ("IND005", "Charlie Davis"),
        ]
        all_customers = enterprise_customers + smb_customers + individual_customers

        feedback_id = 1
        now = datetime.now()

        # iOS crash spike (recent)
        for _ in range(47):
            customer = random.choice(all_customers)
            segment = "Enterprise" if customer[0].startswith("ENT") else ("SMB" if customer[0].startswith("SMB") else "Individual")
            self.feedback.append(FeedbackItem(
                id=f"FB{feedback_id:04d}",
                text=random.choice([
                    "App crashes every time I open settings on iOS.",
                    "iOS app crashed again. This is unacceptable!",
                    "Can't use the app on my iPhone - keeps crashing.",
                    "iOS 17 update broke the app completely.",
                ]),
                sentiment="negative", sentiment_score=-0.85,
                topics=["bugs", "mobile", "ios", "crash"],
                customer_segment=segment, customer_id=customer[0], customer_name=customer[1],
                rating=1, timestamp=now - timedelta(hours=random.randint(1, 72)),
                product_version="2.0.3", platform="iOS", is_urgent=True,
            ))
            feedback_id += 1

        # Pricing complaints (SMB)
        for _ in range(31):
            customer = random.choice(smb_customers)
            competitors = random.choice([["Competitor X"], ["Competitor Y"], ["Competitor X", "Competitor Z"]])
            self.feedback.append(FeedbackItem(
                id=f"FB{feedback_id:04d}",
                text=random.choice([
                    f"Pricing is too expensive for SMBs. {competitors[0]} offers better value.",
                    "Can't justify the cost for a small team. Need SMB pricing.",
                    f"Switching to {competitors[0]} - they have a startup plan.",
                ]),
                sentiment="negative", sentiment_score=-0.6,
                topics=["pricing", "competitive"],
                customer_segment="SMB", customer_id=customer[0], customer_name=customer[1],
                rating=2, timestamp=now - timedelta(days=random.randint(1, 30)),
                product_version=random.choice(versions), competitor_mentions=competitors,
            ))
            feedback_id += 1

        # Support complaints
        for _ in range(28):
            customer = random.choice(enterprise_customers + smb_customers)
            segment = "Enterprise" if customer[0].startswith("ENT") else "SMB"
            self.feedback.append(FeedbackItem(
                id=f"FB{feedback_id:04d}",
                text=random.choice([
                    "Support team takes too long to respond. Waited 3 days.",
                    "Still waiting for a response after 48 hours.",
                    "Enterprise support SLA not being met.",
                ]),
                sentiment="negative", sentiment_score=-0.5,
                topics=["support", "response_time"],
                customer_segment=segment, customer_id=customer[0], customer_name=customer[1],
                rating=2, timestamp=now - timedelta(days=random.randint(1, 30)),
                product_version=random.choice(versions),
            ))
            feedback_id += 1

        # Positive feedback
        positive_texts = [
            ("The product is amazing! Customer support was incredibly helpful.", ["support", "product"], 5),
            ("Love the new features! Much better than Company Y's offering.", ["features", "competitive"], 5),
            ("Excellent dashboard - exactly what we needed.", ["features", "usability"], 5),
            ("Integration was seamless, great documentation.", ["integration", "documentation"], 4),
        ]
        for _ in range(40):
            for text, topics, rating in positive_texts:
                customer = random.choice(all_customers)
                segment = "Enterprise" if customer[0].startswith("ENT") else ("SMB" if customer[0].startswith("SMB") else "Individual")
                self.feedback.append(FeedbackItem(
                    id=f"FB{feedback_id:04d}",
                    text=text, sentiment="positive", sentiment_score=0.8,
                    topics=topics, customer_segment=segment,
                    customer_id=customer[0], customer_name=customer[1],
                    rating=rating, timestamp=now - timedelta(days=random.randint(1, 30)),
                    product_version=random.choice(versions), platform=random.choice(platforms),
                ))
                feedback_id += 1

        # Checkout issues (recent outage simulation)
        for _ in range(23):
            customer = random.choice(enterprise_customers + smb_customers)
            segment = "Enterprise" if customer[0].startswith("ENT") else "SMB"
            self.feedback.append(FeedbackItem(
                id=f"FB{feedback_id:04d}",
                text=random.choice([
                    "Checkout not working! Can't complete my purchase.",
                    "Payment page returns error 500.",
                    "Credit card payment failing repeatedly.",
                ]),
                sentiment="negative", sentiment_score=-0.9,
                topics=["bugs", "checkout", "payment"],
                customer_segment=segment, customer_id=customer[0], customer_name=customer[1],
                rating=1, timestamp=now - timedelta(hours=random.randint(1, 4)),
                product_version="2.0.3", is_urgent=True,
            ))
            feedback_id += 1

    def get_weekly_summary(self) -> Dict[str, Any]:
        """Get summary statistics for the past week."""
        now = datetime.now()
        week_ago = now - timedelta(days=7)
        weekly = [f for f in self.feedback if f.timestamp >= week_ago]
        total = len(weekly)
        if total == 0:
            return {"total_responses": 0, "sentiment": {}, "top_issues": [], "urgent_count": 0}

        positive = len([f for f in weekly if f.sentiment == "positive"])
        negative = len([f for f in weekly if f.sentiment == "negative"])
        neutral = total - positive - negative

        topic_counts: Dict[str, int] = {}
        for f in weekly:
            for t in f.topics:
                topic_counts[t] = topic_counts.get(t, 0) + 1
        top_issues: List[tuple[str, int]] = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:5]

        return {
            "total_responses": total,
            "sentiment": {
                "positive_pct": round(positive / total * 100),
                "negative_pct": round(negative / total * 100),
                "neutral_pct": round(neutral / total * 100),
            },
            "top_issues": top_issues,
            "urgent_count": len([f for f in weekly if f.is_urgent]),
        }

    def get_issue_details(self, topic: str) -> Dict[str, Any]:
        """Get detailed analysis for a specific issue/topic."""
        now = datetime.now()
        week_ago = now - timedelta(days=7)
        relevant = [f for f in self.feedback if topic.lower() in [t.lower() for t in f.topics]]
        recent = [f for f in relevant if f.timestamp >= week_ago]

        if not recent:
            return {"topic": topic, "total_mentions": 0, "message": "No recent data for this topic"}

        negative_pct = round(len([f for f in recent if f.sentiment == "negative"]) / len(recent) * 100)
        versions: Dict[str, int] = {}
        platforms: Dict[str, int] = {}
        for f in recent:
            versions[f.product_version] = versions.get(f.product_version, 0) + 1
            if f.platform:
                platforms[f.platform] = platforms.get(f.platform, 0) + 1

        priority = "P0 - Critical" if len(recent) > 30 and negative_pct > 80 else \
                   "P1 - High" if len(recent) > 20 and negative_pct > 60 else \
                   "P2 - Medium" if len(recent) > 10 else "P3 - Low"

        return {
            "topic": topic, "total_mentions": len(recent), "negative_sentiment_pct": negative_pct,
            "affected_versions": versions, "affected_platforms": platforms,
            "sample_feedback": [f.text for f in recent[:3]], "priority": priority,
        }

    def get_competitor_analysis(self) -> Dict[str, Any]:
        """Get competitive intelligence from feedback."""
        now = datetime.now()
        month_ago = now - timedelta(days=30)
        recent = [f for f in self.feedback if f.timestamp >= month_ago]

        competitor_data: Dict[str, Dict[str, Any]] = {}
        for f in recent:
            for comp in f.competitor_mentions:
                if comp not in competitor_data:
                    competitor_data[comp] = {"mentions": 0, "reasons": {}}
                competitor_data[comp]["mentions"] += 1
                for t in f.topics:
                    if t != "competitive":
                        competitor_data[comp]["reasons"][t] = competitor_data[comp]["reasons"].get(t, 0) + 1

        competitors = [
            {"name": name, "mentions": data["mentions"],
             "win_reason": max(data["reasons"], key=data["reasons"].get) if data["reasons"] else "Unknown"}
            for name, data in sorted(competitor_data.items(), key=lambda x: x[1]["mentions"], reverse=True)
        ]

        churn_risks = [
            {"customer_id": f.customer_id, "customer_name": f.customer_name, "segment": f.customer_segment,
             "competitor": f.competitor_mentions[0] if f.competitor_mentions else "Unknown"}
            for f in recent if f.competitor_mentions and f.sentiment == "negative"
        ][:12]

        return {"competitors": competitors, "churn_risk_customers": churn_risks, "total_churn_risks": len(churn_risks)}

    def get_customer_context(self, customer_id: str) -> Dict[str, Any]:
        """Get context for a specific customer."""
        customer_feedback = sorted([f for f in self.feedback if f.customer_id == customer_id],
                                   key=lambda x: x.timestamp, reverse=True)
        if not customer_feedback:
            return {"error": f"No feedback found for {customer_id}"}

        recent = customer_feedback[:5]
        negative_count = len([f for f in recent if f.sentiment == "negative"])
        segment = recent[0].customer_segment

        return {
            "customer_id": customer_id, "customer_name": recent[0].customer_name, "segment": segment,
            "account_value": f"${random.randint(50, 150)}K ARR" if segment == "Enterprise" else f"${random.randint(5, 25)}K ARR",
            "escalation_risk": "HIGH" if negative_count >= 3 else "MEDIUM" if negative_count >= 1 else "LOW",
            "recent_feedback": [{"text": f.text, "sentiment": f.sentiment, "days_ago": (datetime.now() - f.timestamp).days} for f in recent],
        }

    def detect_anomalies(self) -> List[Dict[str, Any]]:
        """Detect unusual patterns in recent feedback."""
        now = datetime.now()
        two_hours_ago = now - timedelta(hours=2)
        recent = [f for f in self.feedback if f.timestamp >= two_hours_ago]

        topic_counts: Dict[str, int] = {}
        for f in recent:
            for t in f.topics:
                topic_counts[t] = topic_counts.get(t, 0) + 1

        anomalies: List[Dict[str, Any]] = []
        for topic, count in topic_counts.items():
            if count > 10:
                affected = [f for f in recent if topic in f.topics]
                anomalies.append({
                    "topic": topic, "count": count,
                    "severity": "CRITICAL" if count > 20 else "HIGH",
                    "affected_customers": len(affected),
                    "negative_pct": round(len([f for f in affected if f.sentiment == "negative"]) / len(affected) * 100),
                })
        return anomalies

    def set_alert(self, condition: str, threshold: float) -> Dict[str, Any]:
        """Set up an alert for monitoring."""
        alert = {"id": f"ALERT{len(self.alerts) + 1:03d}", "condition": condition, "threshold": threshold, "status": "active"}
        self.alerts.append(alert)
        return alert

    def get_surveys(self) -> List[SurveyResponse]:
        """Convert feedback items to SurveyResponse for workflow mode."""
        return [
            SurveyResponse(
                id=f.id,
                text=f.text,
                rating=f.rating,
                timestamp=f.timestamp.isoformat(),
                customer_segment=f.customer_segment,
                product_version=f.product_version,
                customer_id=f.customer_id,
                customer_name=f.customer_name,
                platform=f.platform,
            )
            for f in self.feedback
        ]


# Global data store - initialize with mock data
feedback_store = FeedbackDataStore()
feedback_store.load_mock_data()
