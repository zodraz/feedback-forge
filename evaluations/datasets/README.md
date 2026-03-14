# Test Cases Dataset

This directory contains test cases for evaluating the FeedbackForge agent.

## File Structure

- `test_cases.json` - Main test case collection
- `test_cases_small.json` - Subset for quick testing (create manually)
- `golden_responses.json` - Reference responses (optional)

## Test Case Format

Each test case should include:

```json
{
  "id": "test_XXX",
  "category": "category_name",
  "query": "User question or request",
  "expected_tools": ["tool1", "tool2"],
  "expected_params": {
    "tool1": {
      "param1": "value1"
    }
  },
  "golden_answer": {
    "should_include": ["keyword1", "keyword2"],
    "required_fields": ["field1", "field2"],
    "facts": {
      "fact_name": "fact_value"
    }
  },
  "metadata": {
    "difficulty": "easy|medium|hard",
    "tags": ["tag1", "tag2"]
  }
}
```

## Categories

- **weekly_summary**: General weekly overview queries
- **issue_details**: Deep-dive into specific issues
- **competitor_insights**: Competitive intelligence
- **customer_context**: Customer-specific queries
- **anomaly_detection**: Anomaly and trend detection
- **action_items**: Action item generation
- **alert_management**: Alert creation and management
- **escalation**: Team escalation
- **multi_turn**: Complex multi-turn conversations
- **edge_case**: Boundary conditions and error handling

## Adding New Test Cases

1. Identify the category
2. Write a clear, realistic query
3. Specify expected tool usage
4. Define golden answer criteria
5. Add metadata (difficulty, tags)
6. Test manually first
7. Add to `test_cases.json`

## Example

```json
{
  "id": "test_011",
  "category": "trend_analysis",
  "query": "Show me the trend of payment issues over the last month",
  "expected_tools": ["get_issue_details"],
  "expected_params": {
    "get_issue_details": {
      "issue_type": "payment",
      "time_range": "month"
    }
  },
  "golden_answer": {
    "should_include": ["payment", "trend", "month", "increase"],
    "required_fields": ["time_period", "data_points"]
  },
  "metadata": {
    "difficulty": "medium",
    "tags": ["trend", "payment", "temporal"]
  }
}
```
