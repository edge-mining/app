"""Unit tests for value_ref in RuleEvaluator — dynamic field-to-field comparison."""

from datetime import datetime, timezone
from unittest.mock import Mock

import pytest

from edge_mining.adapters.domain.policy.schemas import RuleConditionSchema, LogicalGroupSchema
from edge_mining.adapters.infrastructure.rule_engine.custom.helpers import RuleEvaluator
from edge_mining.domain.climate.value_objects import ClimateStateSnapshot, ClimateZoneReading
from edge_mining.domain.policy.common import OperatorType
from edge_mining.domain.policy.value_objects import DecisionalContext


@pytest.fixture
def context_with_climate():
    """DecisionalContext with climate data including target_temperature."""
    context = Mock(spec=DecisionalContext)

    # Climate snapshot with target
    reading = ClimateZoneReading(
        zone_name="bedroom",
        temperature_celsius=18.5,
        target_temperature=21.0,
        hysteresis_celsius=0.5,
    )
    snapshot = ClimateStateSnapshot(per_zone=[reading])
    context.climate = snapshot

    # Energy state for mixed conditions
    context.energy_state = Mock()
    context.energy_state.battery = Mock()
    context.energy_state.battery.state_of_charge = 60

    context.timestamp = datetime(2026, 5, 22, 14, 0, tzinfo=timezone.utc)

    return context


class TestValueRef:
    """Tests for value_ref dynamic resolution in rule conditions."""

    def test_value_ref_basic_lt(self, context_with_climate):
        """temperature < target → True (18.5 < 21.0)."""
        condition = RuleConditionSchema(
            field="climate.zones.bedroom.temperature_celsius",
            operator=OperatorType.LT,
            value_ref="climate.zones.bedroom.target_temperature",
        )
        result = RuleEvaluator.evaluate_rule_conditions(context_with_climate, condition)
        assert result is True

    def test_value_ref_basic_gt(self, context_with_climate):
        """temperature > target → False (18.5 > 21.0)."""
        condition = RuleConditionSchema(
            field="climate.zones.bedroom.temperature_celsius",
            operator=OperatorType.GT,
            value_ref="climate.zones.bedroom.target_temperature",
        )
        result = RuleEvaluator.evaluate_rule_conditions(context_with_climate, condition)
        assert result is False

    def test_value_ref_eq(self, context_with_climate):
        """temperature == target → False (18.5 != 21.0)."""
        condition = RuleConditionSchema(
            field="climate.zones.bedroom.temperature_celsius",
            operator=OperatorType.EQ,
            value_ref="climate.zones.bedroom.target_temperature",
        )
        result = RuleEvaluator.evaluate_rule_conditions(context_with_climate, condition)
        assert result is False

    def test_value_ref_to_none_field_returns_false(self, context_with_climate):
        """value_ref pointing to a non-existent field → condition returns False."""
        condition = RuleConditionSchema(
            field="climate.zones.bedroom.temperature_celsius",
            operator=OperatorType.LT,
            value_ref="climate.zones.bedroom.nonexistent_field",
        )
        result = RuleEvaluator.evaluate_rule_conditions(context_with_climate, condition)
        assert result is False

    def test_value_ref_to_unavailable_optional_returns_false(self):
        """value_ref on a context with missing optional root → condition returns False."""
        context = Mock(spec=DecisionalContext)
        context.climate = None  # not configured
        context.energy_state = Mock()
        context.energy_state.battery = Mock()
        context.energy_state.battery.state_of_charge = 60

        condition = RuleConditionSchema(
            field="energy_state.battery.state_of_charge",
            operator=OperatorType.GT,
            value_ref="climate.zones.bedroom.target_temperature",
        )
        result = RuleEvaluator.evaluate_rule_conditions(context, condition)
        assert result is False

    def test_mixed_value_and_value_ref_in_group(self, context_with_climate):
        """Rule group with both static value and value_ref conditions."""
        group = LogicalGroupSchema(
            all_of=[
                RuleConditionSchema(
                    field="energy_state.battery.state_of_charge",
                    operator=OperatorType.GT,
                    value=50,
                ),
                RuleConditionSchema(
                    field="climate.zones.bedroom.temperature_celsius",
                    operator=OperatorType.LT,
                    value_ref="climate.zones.bedroom.target_temperature",
                ),
            ]
        )
        result = RuleEvaluator.evaluate_rule_conditions(context_with_climate, group)
        assert result is True

    def test_value_ref_in_any_of(self, context_with_climate):
        """value_ref in an any_of group."""
        group = LogicalGroupSchema(
            any_of=[
                RuleConditionSchema(
                    field="climate.zones.bedroom.temperature_celsius",
                    operator=OperatorType.GT,
                    value_ref="climate.zones.bedroom.target_temperature",
                ),
                RuleConditionSchema(
                    field="energy_state.battery.state_of_charge",
                    operator=OperatorType.GT,
                    value=50,
                ),
            ]
        )
        # First is False (18.5 > 21.0), second is True (60 > 50)
        result = RuleEvaluator.evaluate_rule_conditions(context_with_climate, group)
        assert result is True

    def test_value_ref_from_dict(self, context_with_climate):
        """value_ref works when parsed from dict format."""
        conditions_dict = {
            "field": "climate.zones.bedroom.temperature_celsius",
            "operator": "lt",
            "value_ref": "climate.zones.bedroom.target_temperature",
        }
        result = RuleEvaluator.evaluate_rule_conditions(context_with_climate, conditions_dict)
        assert result is True


class TestValueRefSchemaValidation:
    """Tests for value/value_ref mutual exclusivity validation."""

    def test_both_value_and_value_ref_raises(self):
        """Having both value and value_ref raises validation error."""
        with pytest.raises(Exception):
            RuleConditionSchema(
                field="climate.zones.bedroom.temperature_celsius",
                operator=OperatorType.LT,
                value=20.0,
                value_ref="climate.zones.bedroom.target_temperature",
            )

    def test_neither_value_nor_value_ref_raises(self):
        """Having neither value nor value_ref raises validation error."""
        with pytest.raises(Exception):
            RuleConditionSchema(
                field="climate.zones.bedroom.temperature_celsius",
                operator=OperatorType.LT,
            )

    def test_only_value_valid(self):
        """Only value provided → valid."""
        condition = RuleConditionSchema(
            field="energy_state.battery.state_of_charge",
            operator=OperatorType.GT,
            value=50,
        )
        assert condition.value == 50
        assert condition.value_ref is None

    def test_only_value_ref_valid(self):
        """Only value_ref provided → valid."""
        condition = RuleConditionSchema(
            field="climate.zones.bedroom.temperature_celsius",
            operator=OperatorType.LT,
            value_ref="climate.zones.bedroom.target_temperature",
        )
        assert condition.value is None
        assert condition.value_ref == "climate.zones.bedroom.target_temperature"

    def test_value_ref_invalid_characters_raises(self):
        """value_ref with invalid characters raises validation error."""
        with pytest.raises(Exception):
            RuleConditionSchema(
                field="climate.zones.bedroom.temperature_celsius",
                operator=OperatorType.LT,
                value_ref="climate.zones.bedroom; DROP TABLE",
            )
