"""
Unit tests — calculator tool
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import pytest
from app.agent.tools.calculator import calculate


class TestCalculatorBasic:
    def test_addition(self):
        assert calculate("2 + 3") == "5"

    def test_subtraction(self):
        assert calculate("10 - 4") == "6"

    def test_multiplication(self):
        assert calculate("6 * 7") == "42"

    def test_division(self):
        assert calculate("20 / 4") == "5.0"

    def test_power(self):
        assert calculate("2 ** 8") == "256"

    def test_modulo(self):
        assert calculate("17 % 5") == "2"


class TestCalculatorComplex:
    def test_parentheses(self):
        assert calculate("(3 + 5) * 2") == "16"

    def test_nested_parentheses(self):
        assert calculate("((2 + 3) * (4 - 1)) ** 2") == "225"

    def test_float_result(self):
        result = calculate("10 / 3")
        assert result.startswith("3.333")

    def test_negative_number(self):
        assert calculate("-5 + 10") == "5"

    def test_large_numbers(self):
        result = calculate("999999 * 999999")
        assert "999998000001" in result

    def test_chained_operations(self):
        assert calculate("10 + 20 - 5 * 2") == "20"


class TestCalculatorErrors:
    def test_division_by_zero(self):
        result = calculate("10 / 0")
        assert "Error" in result

    def test_invalid_expression(self):
        result = calculate("hello + world")
        assert "Error" in result

    def test_empty_string(self):
        result = calculate("")
        assert "Error" in result

    def test_unsupported_function(self):
        result = calculate("sqrt(16)")
        assert "Error" in result

    def test_sql_injection_attempt(self):
        result = calculate("1; DROP TABLE users")
        assert "Error" in result


class TestCalculatorEdgeCases:
    def test_whitespace_handling(self):
        assert calculate("  2  +  3  ") == "5"

    def test_integer_vs_float(self):
        r1 = calculate("4 / 2")
        assert r1 == "2.0"

    def test_zero_result(self):
        assert calculate("5 - 5") == "0"

    def test_single_number(self):
        assert calculate("42") == "42"
