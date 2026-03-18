"""
Example: Create Zendesk Tickets from FeedbackForge
===================================================

This script creates sample Zendesk tickets based on FeedbackForge scenarios.

Usage:
    # Create all tickets (14 total)
    python examples/create_zendesk_tickets.py --all --yes

    # Create specific ticket set
    python examples/create_zendesk_tickets.py --set=critical --yes
    python examples/create_zendesk_tickets.py --set=features --yes
    python examples/create_zendesk_tickets.py --set=performance --yes

    # Create a specific number of tickets
    python examples/create_zendesk_tickets.py --count=5 --yes

    # Interactive mode (default)
    python examples/create_zendesk_tickets.py
"""

import asyncio
import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from feedbackforge.mcp_server import create_zendesk_ticket


def get_all_tickets():
    """Get all available ticket templates."""
    return [
        # CRITICAL ISSUES
        {
            "subject": "[FeedbackForge] iOS App Crash - High Volume",
            "description": """**Issue**: Multiple customers reporting iOS app crashes when opening settings

**Severity**: Critical
**Affected Users**: 47 reports in last 72 hours
**Platform**: iOS 17+
**App Version**: 2.0.3

**Customer Impact**:
- Enterprise customers: 12
- SMB customers: 23
- Individual users: 12

**Sentiment**: Highly negative (-0.85 avg)

**Sample Feedback**:
- "App crashes every time I open settings on iOS"
- "iOS app crashed again. This is unacceptable!"
- "Can't use the app on my iPhone - keeps crashing"

**Recommended Action**:
- Immediate investigation required
- Rollback to v2.0.2 if fix not available within 24h
- Proactive communication to affected customers

**Source**: FeedbackForge Anomaly Detection
**Detected**: {datetime.now().strftime('%Y-%m-%d %H:%M')}
""",
            "priority": "urgent",
            "type": "incident",
            "tags": ["feedbackforge", "ios", "crash", "high-volume", "p0"]
        },
        {
            "subject": "[FeedbackForge] Pricing Concerns from SMB Segment",
            "description": """**Issue**: SMB customers expressing pricing concerns and considering competitors

**Severity**: High
**Affected Segment**: SMB (31 mentions in last 30 days)
**Churn Risk**: Medium-High

**Competitor Mentions**:
- Competitor X: 18 mentions
- Competitor Y: 8 mentions
- Competitor Z: 5 mentions

**Common Themes**:
- "Pricing is too expensive for SMBs"
- "Need SMB-specific pricing tier"
- "Considering switch to Competitor X - better value"

**Recommended Actions**:
1. Review SMB pricing strategy
2. Create startup/SMB pricing tier
3. Proactive outreach to at-risk customers
4. Competitive analysis vs Competitor X

**Business Impact**:
- Potential churn: 12-15 SMB accounts
- Estimated ARR at risk: $180K-$250K

**Source**: FeedbackForge Competitive Intelligence
**Detected**: {datetime.now().strftime('%Y-%m-%d %H:%M')}
""",
            "priority": "high",
            "type": "problem",
            "tags": ["feedbackforge", "pricing", "smb", "churn-risk", "competitive"]
        },
        {
            "subject": "[FeedbackForge] Support Response Time SLA Breach",
            "description": """**Issue**: Enterprise customers complaining about slow support response times

**Severity**: High
**Affected Segment**: Enterprise + SMB
**Volume**: 28 complaints in last 30 days

**SLA Breach Details**:
- Enterprise SLA: 4 hours
- Actual response time: 48-72 hours
- Breach rate: ~70%

**Customer Sentiment**: Negative (-0.5 avg)

**Sample Feedback**:
- "Support team takes too long to respond. Waited 3 days."
- "Still waiting for a response after 48 hours"
- "Enterprise support SLA not being met"

**Impact**:
- Customer satisfaction declining
- Renewal risk for Q2 enterprise accounts
- Potential escalation to executives

**Recommended Actions**:
1. Audit support ticket queue and staffing
2. Implement escalation protocol for enterprise tickets
3. Review and update SLA targets
4. Proactive communication to affected customers

**Source**: FeedbackForge Topic Analysis
**Detected**: {datetime.now().strftime('%Y-%m-%d %H:%M')}
""",
            "priority": "high",
            "type": "problem",
            "tags": ["feedbackforge", "support", "sla", "enterprise"]
        },
        {
            "subject": "[FeedbackForge] Checkout Payment Processing Spike",
            "description": """**Issue**: Sudden spike in checkout/payment errors

**Severity**: Critical
**Detection Time**: Last 4 hours
**Volume**: 23 reports

**Error Symptoms**:
- Payment page returns error 500
- Credit card processing failing
- Unable to complete purchase

**Customer Segments**:
- Enterprise: 8 reports
- SMB: 15 reports

**Business Impact**:
- Direct revenue loss
- Potential lost sales
- Customer frustration at purchase point

**Recommended Actions**:
1. IMMEDIATE: Check payment gateway status
2. Review recent payment processing changes
3. Enable fallback payment processor if available
4. Monitor error rates continuously

**Priority**: P0 - Revenue impacting
**Source**: FeedbackForge Anomaly Detection
**Detected**: {datetime.now().strftime('%Y-%m-%d %H:%M')}
""",
            "priority": "urgent",
            "type": "incident",
            "tags": ["feedbackforge", "payment", "checkout", "revenue-impact", "p0"],
            "category": "critical"
        },
        # REGIONAL & MOBILE ISSUES
        {
            "subject": "[FeedbackForge] Android App Login Issues - Regional",
            "description": f"""**Issue**: Android users in APAC region experiencing login failures

**Severity**: High
**Affected Region**: APAC (Japan, Singapore, Australia)
**Volume**: 18 reports in last 12 hours
**Platform**: Android 13+
**App Version**: 2.0.3

**Error Pattern**:
- "Authentication failed" error
- Timeout on login screen
- Works fine on WiFi, fails on mobile data

**Customer Segments**:
- Enterprise: 6 reports
- SMB: 9 reports
- Individual: 3 reports

**Potential Root Cause**:
- Regional API gateway issue
- CDN routing problem
- Firebase authentication latency

**Recommended Actions**:
1. Check APAC infrastructure status
2. Review regional API logs
3. Enable debug logging for APAC users
4. Consider fallback authentication method

**Source**: FeedbackForge Regional Analysis
**Detected**: {datetime.now().strftime('%Y-%m-%d %H:%M')}
""",
            "priority": "high",
            "type": "incident",
            "tags": ["feedbackforge", "android", "login", "apac", "regional"],
            "category": "critical"
        },
        # FEATURE REQUESTS
        {
            "subject": "[FeedbackForge] Feature Request: Dark Mode - High Demand",
            "description": f"""**Request**: Users requesting dark mode feature

**Priority**: Medium-High
**Demand**: 52 mentions in last 60 days
**Sentiment**: Positive requests with some frustration

**Customer Segments**:
- Enterprise: 15 requests
- SMB: 22 requests
- Individual: 15 requests

**Common Feedback**:
- "Please add dark mode - eye strain at night"
- "Every modern app has dark mode now"
- "Dark mode would make this perfect"

**Competitive Analysis**:
- Competitor X: Has dark mode
- Competitor Y: Has dark mode + auto-switching
- Industry standard: Expected feature

**Business Impact**:
- Frequent feature request
- Potential differentiator
- Improves accessibility
- Modern UX expectation

**Recommended Actions**:
1. Prioritize in product roadmap (Q2)
2. Design system support for theming
3. Include auto-switching (system preference)
4. Beta test with power users

**Source**: FeedbackForge Feature Analysis
**Detected**: {datetime.now().strftime('%Y-%m-%d %H:%M')}
""",
            "priority": "normal",
            "type": "task",
            "tags": ["feedbackforge", "feature-request", "dark-mode", "ux"],
            "category": "features"
        },
        {
            "subject": "[FeedbackForge] Mobile App Offline Mode Needed",
            "description": f"""**Request**: Users need offline mode for mobile apps

**Priority**: High
**Demand**: 31 requests in last 45 days
**User Profile**: Field workers, travelers, rural areas

**Use Cases**:
- Field sales reps (no connectivity)
- Remote workers (spotty internet)
- International travel (airplane mode)
- Rural areas (poor network)

**Customer Feedback**:
- "Can't use app on flights - need offline mode"
- "Field workers need offline data entry"
- "Competitors have offline sync"
- "Lost work when connection dropped"

**Requested Capabilities**:
1. View cached data offline
2. Create/edit records offline
3. Sync when back online
4. Conflict resolution UI
5. Offline indicator

**Technical Considerations**:
- Local database (SQLite/Realm)
- Sync protocol design
- Conflict resolution strategy
- Storage limitations
- Security (encrypted local storage)

**Competitive Analysis**:
- Competitor X: Full offline mode with sync
- Competitor Y: Read-only offline mode
- Industry trend: Expected for mobile apps

**Business Impact**:
- Expanding to field workers segment
- Competitive requirement
- Improved reliability perception

**Source**: FeedbackForge Feature Requests
**Detected**: {datetime.now().strftime('%Y-%m-%d %H:%M')}
""",
            "priority": "high",
            "type": "task",
            "tags": ["feedbackforge", "mobile", "offline", "feature-request"],
            "category": "features"
        },
        {
            "subject": "[FeedbackForge] Integration Request: Salesforce Connector",
            "description": f"""**Request**: Native Salesforce integration

**Priority**: High
**Demand**: 19 requests from enterprise customers
**Business Impact**: Deal blocker for 3 prospects

**Requested Capabilities**:
1. Bi-directional sync with Salesforce
2. Map custom fields
3. Real-time updates
4. Lead/Contact sync
5. Activity logging
6. Custom object support

**Customer Use Cases**:
- Sync customer feedback to Salesforce leads
- Track sales pipeline with feedback data
- Automated lead scoring based on feedback
- Customer success team visibility
- Executive reporting in Salesforce

**Current Workaround**:
- Manual CSV exports
- Zapier integration (limited)
- API integration (requires dev team)

**Competitive Analysis**:
- Competitor X: Native Salesforce app
- Competitor Y: Salesforce integration (limited)
- Market expectation: Standard for B2B SaaS

**Technical Requirements**:
- Salesforce App Exchange listing
- OAuth authentication
- Webhook support
- Custom object API
- Bulk API for large syncs

**Business Value**:
- Win 3 pending deals ($450K ARR)
- Retention for existing Salesforce customers
- Competitive requirement
- Enterprise market expansion

**Recommended Actions**:
1. Prioritize for Q2 roadmap
2. Salesforce partnership discussion
3. Hire Salesforce integration specialist
4. Beta program with key customers

**Source**: FeedbackForge Integration Requests
**Detected**: {datetime.now().strftime('%Y-%m-%d %H:%M')}
""",
            "priority": "urgent",
            "type": "task",
            "tags": ["feedbackforge", "integration", "salesforce", "enterprise", "feature-request"],
            "category": "features"
        },
        # PERFORMANCE ISSUES
        {
            "subject": "[FeedbackForge] Data Export Performance Issues",
            "description": f"""**Issue**: Users reporting slow data export functionality

**Severity**: Medium
**Volume**: 14 complaints in last 2 weeks
**Affected Feature**: CSV/Excel export

**Performance Metrics**:
- Small exports (<1000 rows): OK
- Medium exports (1K-10K rows): Slow (30-60s)
- Large exports (>10K rows): Timeout or fail

**Customer Impact**:
- Enterprise customers most affected (large datasets)
- Blocking monthly reporting workflows
- Work-arounds: Multiple small exports (tedious)

**Technical Details**:
- Exports run synchronously on web server
- No progress indicator
- Browser timeout after 60 seconds

**Recommended Solutions**:
1. **Short-term**: Increase timeout, add progress bar
2. **Long-term**: Background job processing with email notification
3. **Alternative**: Streaming export implementation

**Customer Feedback**:
- "Export keeps timing out for our monthly report"
- "Need to export in batches - very frustrating"
- "Other tools export 50K rows instantly"

**Source**: FeedbackForge Performance Analysis
**Detected**: {datetime.now().strftime('%Y-%m-%d %H:%M')}
""",
            "priority": "normal",
            "type": "problem",
            "tags": ["feedbackforge", "performance", "export", "enterprise"],
            "category": "performance"
        },
        {
            "subject": "[FeedbackForge] API Rate Limits Too Restrictive",
            "description": f"""**Issue**: Developers complaining about API rate limits

**Severity**: Medium-High
**Affected**: API integration customers
**Volume**: 9 complaints (all Enterprise/SMB developers)

**Current Limits**:
- 100 requests/minute per API key
- 10,000 requests/day

**Customer Feedback**:
- "Hit rate limit during normal operations"
- "Need higher limits for data sync"
- "Competitors offer 500/min"
- "Causing sync delays and failed jobs"

**Affected Use Cases**:
- Real-time data synchronization
- Bulk data imports
- Webhook processing
- Scheduled batch jobs

**Competitive Comparison**:
- Competitor X: 500 req/min, 50K/day
- Competitor Y: 1000 req/min, 100K/day
- Industry standard: 200-500 req/min

**Business Impact**:
- Blocking enterprise integrations
- Developer frustration
- Potential churn risk
- Competitive disadvantage

**Recommended Actions**:
1. Review and increase base limits (200/min, 25K/day)
2. Implement tiered rate limits by plan
3. Add rate limit headers to API responses
4. Document rate limit best practices
5. Offer rate limit increase for enterprise plans

**Source**: FeedbackForge API Usage Analysis
**Detected**: {datetime.now().strftime('%Y-%m-%d %H:%M')}
""",
            "priority": "high",
            "type": "problem",
            "tags": ["feedbackforge", "api", "rate-limits", "enterprise", "developers"],
            "category": "performance"
        },
        {
            "subject": "[FeedbackForge] Desktop App Memory Leak - Windows",
            "description": f"""**Issue**: Desktop application memory leak on Windows

**Severity**: Medium-High
**Platform**: Windows 10/11
**App Version**: 2.0.3 Desktop
**Volume**: 7 reports from enterprise users

**Symptoms**:
- Memory usage grows over time (starts 200MB, grows to 2GB+)
- Application becomes slow after 4-6 hours
- Eventually freezes or crashes
- Requires restart to fix

**Affected Workflows**:
- Users who keep app open all day
- Heavy dashboard usage
- Real-time data monitoring

**Customer Segments**:
- Enterprise: 6 reports (critical workflow)
- SMB: 1 report

**Reproduction**:
- Open desktop app
- Navigate between dashboards
- Leave running for 6+ hours
- Monitor Task Manager memory usage

**Potential Causes**:
- Event listeners not cleaned up
- Cached data not released
- WebView memory accumulation
- Image/chart rendering leak

**Recommended Actions**:
1. Memory profiling session (Chrome DevTools)
2. Check for event listener leaks
3. Review data caching strategy
4. Add memory usage monitoring
5. Implement periodic memory cleanup

**Customer Impact**: High for all-day users

**Source**: FeedbackForge Bug Reports
**Detected**: {datetime.now().strftime('%Y-%m-%d %H:%M')}
""",
            "priority": "high",
            "type": "problem",
            "tags": ["feedbackforge", "desktop", "windows", "memory-leak", "performance"],
            "category": "performance"
        },
        # ACCESSIBILITY & UX
        {
            "subject": "[FeedbackForge] Accessibility Issues for Screen Readers",
            "description": f"""**Issue**: Web application not fully accessible with screen readers

**Severity**: High (Legal/Compliance)
**Affected**: Users with visual impairments
**Standards**: WCAG 2.1 AA compliance gaps

**Reported Issues**:
- Missing ARIA labels on buttons
- Keyboard navigation broken in modals
- Form errors not announced
- Focus management issues
- Low contrast in some areas

**Customer Feedback**:
- "Can't use with JAWS screen reader"
- "Keyboard shortcuts don't work"
- "Accessibility team flagged issues"

**Compliance Risk**:
- ADA compliance requirements
- Enterprise procurement blocker
- Potential legal liability
- VPAT (Voluntary Product Accessibility Template) gaps

**Affected Features**:
- Dashboard navigation
- Form submissions
- Modal dialogs
- Data tables
- Chart interactions

**Recommended Actions**:
1. **Immediate**: Accessibility audit (WCAG 2.1 AA)
2. Add ARIA labels and roles
3. Fix keyboard navigation
4. Improve focus management
5. Color contrast fixes
6. Test with screen readers (JAWS, NVDA, VoiceOver)
7. Update VPAT documentation

**Business Impact**:
- Enterprise requirement
- Government sector blocker
- Legal compliance
- Inclusive design

**Source**: FeedbackForge Accessibility Analysis
**Detected**: {datetime.now().strftime('%Y-%m-%d %H:%M')}
""",
            "priority": "urgent",
            "type": "problem",
            "tags": ["feedbackforge", "accessibility", "wcag", "compliance", "a11y"],
            "category": "accessibility"
        },
        {
            "subject": "[FeedbackForge] Email Notifications Not Received",
            "description": f"""**Issue**: Users not receiving email notifications

**Severity**: Medium
**Volume**: 12 reports in last week
**Affected**: All customer segments

**Symptoms**:
- Notification settings enabled but no emails received
- Intermittent - some emails arrive, others don't
- Worse for Gmail users (8 out of 12 reports)

**Notification Types Affected**:
- Alert notifications
- Daily digest emails
- Password reset emails
- Invitation emails

**Technical Investigation**:
- Email delivery service: SendGrid
- Recent delivery rate: 92% (down from 98%)
- Bounce rate: 3%
- Spam complaints: 0.5%

**Potential Causes**:
1. Gmail deliverability issues
2. SPF/DKIM configuration
3. Sender reputation
4. Email template content
5. Rate limiting

**Customer Workarounds**:
- Check spam folder (sometimes works)
- Use in-app notifications instead
- Contact support for manual triggers

**Recommended Actions**:
1. Review SendGrid deliverability dashboard
2. Check SPF/DKIM/DMARC records
3. Review email content for spam triggers
4. Implement email verification/warmup
5. Add email delivery status page
6. Provide in-app notification fallback

**Source**: FeedbackForge Infrastructure Monitoring
**Detected**: {datetime.now().strftime('%Y-%m-%d %H:%M')}
""",
            "priority": "normal",
            "type": "problem",
            "tags": ["feedbackforge", "email", "notifications", "deliverability"],
            "category": "infrastructure"
        },
        # POSITIVE FEEDBACK
        {
            "subject": "[FeedbackForge] Positive Feedback: Onboarding Experience",
            "description": f"""**Feedback Type**: Positive Recognition

**Topic**: Excellent onboarding experience
**Volume**: 23 positive mentions in last 30 days
**Sentiment**: Very positive (+0.85 avg)

**What Users Love**:
- "Best onboarding flow I've seen"
- "Interactive tutorial made setup easy"
- "Got up and running in 5 minutes"
- "Clear guidance, no confusion"

**Key Strengths**:
- Step-by-step interactive tutorial
- Contextual help tooltips
- Progress indicator
- Sample data for testing

**Customer Segments**:
- Individual users: 18 mentions (love it!)
- SMB: 4 mentions (very helpful)
- Enterprise: 1 mention

**Competitive Advantage**:
- Significantly better than Competitor X
- On par with industry leaders

**Recommendations**:
1. Use as case study in marketing materials
2. Create video showcasing onboarding flow
3. Collect testimonials for website
4. Consider extending approach to other features

**Source**: FeedbackForge Sentiment Analysis
**Detected**: {datetime.now().strftime('%Y-%m-%d %H:%M')}
""",
            "priority": "low",
            "type": "task",
            "tags": ["feedbackforge", "positive", "onboarding", "marketing"],
            "category": "positive"
        }
    ]


async def create_tickets(tickets_to_create):
    """Create tickets in Zendesk."""
    created_tickets = []

    for idx, ticket_args in enumerate(tickets_to_create, 1):
        print(f"\n[{idx}/{len(tickets_to_create)}] Creating: {ticket_args['subject']}")
        print(f"   Priority: {ticket_args['priority'].upper()}")
        print(f"   Type: {ticket_args['type']}")

        try:
            result = await create_zendesk_ticket(ticket_args)
            result_text = result[0].text
            data = json.loads(result_text)

            if data.get("success"):
                print(f"   ✅ Created Ticket #{data['ticket_id']}")
                print(f"   🔗 URL: {data['ticket_url']}")
                created_tickets.append(data)
            else:
                print(f"   ❌ Error: {data.get('error')}")

        except Exception as e:
            print(f"   ❌ Exception: {e}")

        # Rate limiting - be nice to Zendesk API
        if idx < len(tickets_to_create):
            await asyncio.sleep(1)

    print(f"\n{'='*60}")
    print(f"Summary: Created {len(created_tickets)}/{len(tickets_to_create)} tickets")
    print(f"{'='*60}\n")

    if created_tickets:
        print("Created Tickets:")
        for ticket in created_tickets:
            print(f"  • #{ticket['ticket_id']}: {ticket['subject']}")
            print(f"    {ticket['ticket_url']}\n")


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Create Zendesk tickets from FeedbackForge scenarios",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --all --yes              # Create all 14 tickets
  %(prog)s --set=critical --yes     # Create only critical tickets (6)
  %(prog)s --set=features --yes     # Create feature request tickets (3)
  %(prog)s --set=performance --yes  # Create performance tickets (3)
  %(prog)s --count=5 --yes          # Create first 5 tickets
  %(prog)s                          # Interactive mode with prompts
        """
    )

    parser.add_argument("--all", action="store_true", help="Create all tickets (14 total)")
    parser.add_argument("--set", choices=["critical", "features", "performance", "accessibility", "infrastructure", "positive"],
                        help="Create specific ticket set")
    parser.add_argument("--count", type=int, help="Create first N tickets")
    parser.add_argument("--yes", "-y", action="store_true", help="Skip confirmation prompt")

    args = parser.parse_args()

    # Check credentials
    if not os.environ.get("ZENDESK_SUBDOMAIN"):
        print("❌ Error: ZENDESK_SUBDOMAIN not set")
        print("   Please set: export ZENDESK_SUBDOMAIN=yourcompany")
        return

    if not os.environ.get("ZENDESK_EMAIL"):
        print("❌ Error: ZENDESK_EMAIL not set")
        print("   Please set: export ZENDESK_EMAIL=your@email.com")
        return

    if not os.environ.get("ZENDESK_API_TOKEN"):
        print("❌ Error: ZENDESK_API_TOKEN not set")
        print("   Please set: export ZENDESK_API_TOKEN=your_token")
        return

    # Get all available tickets
    all_tickets = get_all_tickets()

    # Filter tickets based on arguments
    if args.set:
        tickets_to_create = [t for t in all_tickets if t.get("category") == args.set]
        selection_desc = f"{args.set} tickets"
    elif args.count:
        tickets_to_create = all_tickets[:args.count]
        selection_desc = f"first {args.count} tickets"
    elif args.all:
        tickets_to_create = all_tickets
        selection_desc = "all tickets"
    else:
        # Interactive mode - show menu
        print("\nFeedbackForge → Zendesk Ticket Creator")
        print("="*60)
        print("\nAvailable ticket sets:")
        print("  1. All tickets (14)")
        print("  2. Critical issues only (6)")
        print("  3. Feature requests only (3)")
        print("  4. Performance issues only (3)")
        print("  5. Accessibility & infrastructure (2)")
        print("  6. First 5 tickets")
        print("  7. Custom count")
        print("  0. Cancel")

        try:
            choice = input("\nSelect option (0-7): ").strip()

            if choice == "0":
                print("Cancelled.")
                return
            elif choice == "1":
                tickets_to_create = all_tickets
                selection_desc = "all tickets"
            elif choice == "2":
                tickets_to_create = [t for t in all_tickets if t.get("category") == "critical"]
                selection_desc = "critical issues"
            elif choice == "3":
                tickets_to_create = [t for t in all_tickets if t.get("category") == "features"]
                selection_desc = "feature requests"
            elif choice == "4":
                tickets_to_create = [t for t in all_tickets if t.get("category") == "performance"]
                selection_desc = "performance issues"
            elif choice == "5":
                tickets_to_create = [t for t in all_tickets if t.get("category") in ["accessibility", "infrastructure"]]
                selection_desc = "accessibility & infrastructure"
            elif choice == "6":
                tickets_to_create = all_tickets[:5]
                selection_desc = "first 5 tickets"
            elif choice == "7":
                count = int(input("How many tickets to create? "))
                tickets_to_create = all_tickets[:count]
                selection_desc = f"first {count} tickets"
            else:
                print("Invalid choice.")
                return

        except (EOFError, KeyboardInterrupt):
            print("\nCancelled.")
            return
        except ValueError:
            print("Invalid input.")
            return

    print(f"\nFeedbackForge → Zendesk Ticket Creator")
    print(f"This will create {len(tickets_to_create)} tickets ({selection_desc})\n")

    # Confirmation
    if not args.yes:
        try:
            response = input("Continue? (yes/no): ")
            if response.lower() not in ["yes", "y"]:
                print("Cancelled.")
                return
        except (EOFError, KeyboardInterrupt):
            print("\nRunning in non-interactive mode. Use --yes flag to proceed automatically.")
            return

    # Create tickets
    print(f"\n{'='*60}")
    print(f"Creating {len(tickets_to_create)} Zendesk Tickets")
    print(f"{'='*60}\n")

    await create_tickets(tickets_to_create)


if __name__ == "__main__":
    asyncio.run(main())
