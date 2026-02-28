"""
FAQ Command Module
==================

Implements the FAQ generation command for the FeedbackForge CLI.
This module provides the FAQ subcommand: python -m feedbackforge faq
"""

import argparse
import logging
from typing import Any, Dict

try:
    from .faq_generator import generate_faq
except ImportError:
    from feedbackforge.faq_generator import generate_faq

logger = logging.getLogger(__name__)


class FAQCommand:
    """FAQ generation command handler."""

    @staticmethod
    def setup_parser(parser: argparse.ArgumentParser) -> None:
        """Configure FAQ command parser with arguments.

        Args:
            parser: ArgumentParser or subparser to configure
        """
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Number of days to look back (default: 30)'
        )

        parser.add_argument(
            '--min-mentions',
            type=int,
            default=3,
            help='Minimum mentions for FAQ inclusion (default: 3)'
        )

        parser.add_argument(
            '--max-faqs',
            type=int,
            default=15,
            help='Maximum FAQs to generate (default: 15)'
        )

        parser.add_argument(
            '--style',
            choices=['helpful', 'friendly', 'technical'],
            default='helpful',
            help='Answer style (default: helpful)'
        )

        parser.add_argument(
            '--formats',
            nargs='+',
            choices=['markdown', 'json', 'html'],
            default=['markdown', 'json', 'html'],
            help='Export formats (default: all)'
        )

        parser.epilog = """
Examples:
  # Generate FAQs from last 30 days
  python -m feedbackforge faq

  # Generate from last 7 days, minimum 5 mentions
  python -m feedbackforge faq --days 7 --min-mentions 5

  # Generate top 20 FAQs in friendly style
  python -m feedbackforge faq --max-faqs 20 --style friendly

  # Export only to HTML
  python -m feedbackforge faq --formats html

  # Export to all formats
  python -m feedbackforge faq --formats markdown json html
        """

    def execute(self, args: argparse.Namespace) -> int:
        """Execute the FAQ generation command.

        Args:
            args: Parsed command-line arguments

        Returns:
            Exit code (0 for success, 1 for failure)
        """
        logger.info("=" * 70)
        logger.info("📚 Auto FAQ Generator")
        logger.info("=" * 70)
        logger.info("")

        try:
            # Generate FAQs
            result = generate_faq(
                timeframe_days=args.days,
                min_occurrences=args.min_mentions,
                max_faqs=args.max_faqs,
                answer_style=args.style,
                output_formats=args.formats
            )

            if not result['faqs']:
                logger.info("❌ No FAQs generated. Try:")
                logger.info("   - Reducing --min-mentions")
                logger.info("   - Increasing --days")
                logger.info("   - Checking if RAG search is properly configured")
                return 1

            logger.info("")
            logger.info("✅ FAQ Generation Complete!")
            logger.info(f"   • Generated: {len(result['faqs'])} FAQs")
            logger.info(f"   • From: {result['theme_count']} common themes")
            logger.info(f"   • Exported to: {len(result['exports'])} files")
            logger.info("")
            logger.info("📄 Output Files:")
            for filepath in result['exports']:
                logger.info(f"   ✓ {filepath}")
            logger.info("")
            logger.info("=" * 70)

            return 0

        except Exception as e:
            logger.error(f"FAQ generation failed: {e}", exc_info=True)
            logger.info("")
            logger.info(f"❌ Error: {e}")
            logger.info("=" * 70)
            return 1


# Backwards compatibility: export functions for __main__.py
def setup_faq_parser(parser: argparse.ArgumentParser) -> None:
    """Legacy function wrapper for backwards compatibility.

    Use FAQCommand.setup_parser() instead.
    """
    FAQCommand.setup_parser(parser)


def run_faq_command(args: argparse.Namespace) -> int:
    """Legacy function wrapper for backwards compatibility.

    Use FAQCommand().execute() instead.
    """
    return FAQCommand().execute(args)
