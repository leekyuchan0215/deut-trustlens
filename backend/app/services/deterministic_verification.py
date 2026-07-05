"""Independent, non-LLM verification for calculator / unit conversion / base
conversion / logic / formula / safe code execution / rule-based claims
(docs/PROMPTS.md #10). The LLM (see app/agents/verification_agent.py) only
extracts structure from the Claim text; every numeric result here is computed
by this module, never trusted from the model.
"""
import ast
import operator
import re
from dataclasses import dataclass, field

_BIN_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}
_UNARY_OPS = {ast.UAdd: operator.pos, ast.USub: operator.neg, ast.Not: operator.not_}
_BOOL_OPS = {ast.And: all, ast.Or: any}
_CMP_OPS = {
    ast.Eq: operator.eq,
    ast.NotEq: operator.ne,
    ast.Lt: operator.lt,
    ast.LtE: operator.le,
    ast.Gt: operator.gt,
    ast.GtE: operator.ge,
}
_SAFE_FUNCS = {"round": round, "abs": abs, "min": min, "max": max, "pow": pow, "int": int, "float": float}


class UnsafeExpressionError(Exception):
    pass


def _eval_node(node: ast.AST, variables: dict[str, float]):
    if isinstance(node, ast.Expression):
        return _eval_node(node.body, variables)
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float, bool)):
            return node.value
        raise UnsafeExpressionError(f"허용되지 않은 상수: {node.value!r}")
    if isinstance(node, ast.Name):
        if node.id in variables:
            return variables[node.id]
        raise UnsafeExpressionError(f"정의되지 않은 변수: {node.id}")
    if isinstance(node, ast.BinOp) and type(node.op) in _BIN_OPS:
        return _BIN_OPS[type(node.op)](_eval_node(node.left, variables), _eval_node(node.right, variables))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY_OPS:
        return _UNARY_OPS[type(node.op)](_eval_node(node.operand, variables))
    if isinstance(node, ast.BoolOp) and type(node.op) in _BOOL_OPS:
        values = [_eval_node(v, variables) for v in node.values]
        return _BOOL_OPS[type(node.op)](values)
    if isinstance(node, ast.Compare):
        left = _eval_node(node.left, variables)
        for op, comparator in zip(node.ops, node.comparators):
            if type(op) not in _CMP_OPS:
                raise UnsafeExpressionError("허용되지 않은 비교 연산자")
            right = _eval_node(comparator, variables)
            if not _CMP_OPS[type(op)](left, right):
                return False
            left = right
        return True
    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name) or node.func.id not in _SAFE_FUNCS:
            raise UnsafeExpressionError("허용되지 않은 함수 호출")
        args = [_eval_node(a, variables) for a in node.args]
        return _SAFE_FUNCS[node.func.id](*args)
    raise UnsafeExpressionError(f"허용되지 않은 표현식: {ast.dump(node)}")


def safe_eval(expression: str, variables: dict[str, float] | None = None):
    variables = variables or {}
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as exc:
        raise UnsafeExpressionError(f"식을 해석할 수 없습니다: {exc}") from exc
    return _eval_node(tree, variables)


_UNIT_TO_BASE = {
    # length -> meters
    "mm": 0.001, "cm": 0.01, "m": 1.0, "km": 1000.0,
    "in": 0.0254, "ft": 0.3048, "yd": 0.9144, "mi": 1609.344,
    # mass -> grams
    "mg": 0.001, "g": 1.0, "kg": 1000.0, "lb": 453.592, "oz": 28.3495,
    # volume -> liters
    "ml": 0.001, "l": 1.0, "gal": 3.78541,
    # time -> seconds
    "s": 1.0, "sec": 1.0, "min": 60.0, "minute": 60.0, "hr": 3600.0, "hour": 3600.0, "day": 86400.0,
}
_LENGTH = {"mm", "cm", "m", "km", "in", "ft", "yd", "mi"}
_MASS = {"mg", "g", "kg", "lb", "oz"}
_VOLUME = {"ml", "l", "gal"}
_TIME = {"s", "sec", "min", "minute", "hr", "hour", "day"}
_TEMP = {"c", "f", "k", "celsius", "fahrenheit", "kelvin"}


def _dimension_of(unit: str) -> str | None:
    unit = unit.lower()
    if unit in _LENGTH:
        return "length"
    if unit in _MASS:
        return "mass"
    if unit in _VOLUME:
        return "volume"
    if unit in _TIME:
        return "time"
    if unit in _TEMP:
        return "temperature"
    return None


def _to_celsius(value: float, unit: str) -> float:
    unit = unit.lower()
    if unit in ("c", "celsius"):
        return value
    if unit in ("f", "fahrenheit"):
        return (value - 32) * 5.0 / 9.0
    if unit in ("k", "kelvin"):
        return value - 273.15
    raise UnsafeExpressionError(f"알 수 없는 온도 단위: {unit}")


def _from_celsius(value: float, unit: str) -> float:
    unit = unit.lower()
    if unit in ("c", "celsius"):
        return value
    if unit in ("f", "fahrenheit"):
        return value * 9.0 / 5.0 + 32
    if unit in ("k", "kelvin"):
        return value + 273.15
    raise UnsafeExpressionError(f"알 수 없는 온도 단위: {unit}")


def convert_unit(value: float, from_unit: str, to_unit: str) -> float:
    from_dim = _dimension_of(from_unit)
    to_dim = _dimension_of(to_unit)
    if from_dim is None or to_dim is None or from_dim != to_dim:
        raise UnsafeExpressionError(f"호환되지 않는 단위 변환: {from_unit} -> {to_unit}")
    if from_dim == "temperature":
        return _from_celsius(_to_celsius(value, from_unit), to_unit)
    base_value = value * _UNIT_TO_BASE[from_unit.lower()]
    return base_value / _UNIT_TO_BASE[to_unit.lower()]


_BASE_DIGIT_RE = re.compile(r"^[0-9a-zA-Z]+$")


def convert_base(value_str: str, from_base: int, to_base: int) -> str:
    value_str = value_str.strip()
    if not _BASE_DIGIT_RE.match(value_str):
        raise UnsafeExpressionError(f"허용되지 않은 진법 표현: {value_str}")
    if not (2 <= from_base <= 36 and 2 <= to_base <= 36):
        raise UnsafeExpressionError("진법은 2~36 사이여야 합니다.")
    decimal_value = int(value_str, from_base)
    if to_base == 10:
        return str(decimal_value)
    digits = "0123456789abcdefghijklmnopqrstuvwxyz"
    if decimal_value == 0:
        return "0"
    out = []
    n = decimal_value
    while n > 0:
        out.append(digits[n % to_base])
        n //= to_base
    return "".join(reversed(out))


@dataclass
class DeterministicResult:
    check_type: str
    input_expression: str
    expected_result: str
    ai_claimed_result: str
    check_passed: bool
    verification_status: str
    verification_confidence: float
    verification_reason: str
    execution_detail: dict = field(default_factory=dict)
    limitations: list[str] = field(default_factory=list)


def _parse_bool(raw: str | None) -> bool | None:
    if raw is None:
        return None
    norm = raw.strip().lower()
    if norm in ("true", "1", "참", "yes"):
        return True
    if norm in ("false", "0", "거짓", "no"):
        return False
    return None


def _results_match(expected, claimed_raw: str | None) -> bool:
    if claimed_raw is None or claimed_raw.strip() == "":
        return False
    try:
        expected_f = float(expected)
        claimed_f = float(str(claimed_raw).strip().replace(",", ""))
        return abs(expected_f - claimed_f) < 1e-6
    except (TypeError, ValueError):
        return str(expected).strip().lower() == str(claimed_raw).strip().lower()


def run_check(
    check_type: str,
    input_expression: str | None,
    ai_claimed_result: str | None,
    variables: dict[str, float] | None = None,
    from_unit: str | None = None,
    to_unit: str | None = None,
    value: float | None = None,
    from_base: int | None = None,
    to_base: int | None = None,
) -> DeterministicResult:
    variables = variables or {}
    try:
        if check_type in ("calculator", "formula", "safe_code_execution"):
            if not input_expression:
                raise UnsafeExpressionError("input_expression이 비어 있습니다.")
            expected = safe_eval(input_expression, variables)
            expected_str = str(expected)
            passed = _results_match(expected, ai_claimed_result)
            return DeterministicResult(
                check_type=check_type,
                input_expression=input_expression,
                expected_result=expected_str,
                ai_claimed_result=ai_claimed_result or "",
                check_passed=passed,
                verification_status="verified" if passed else "contradicted",
                verification_confidence=100.0 if passed else 100.0,
                verification_reason=(
                    "독립 계산 결과와 AI 응답이 일치합니다."
                    if passed
                    else f"독립 계산 결과({expected_str})와 AI 응답({ai_claimed_result})이 다릅니다."
                ),
                execution_detail={"engine": "restricted_ast", "expression": input_expression, "variables": variables},
            )

        if check_type == "logic_evaluation":
            if not input_expression:
                raise UnsafeExpressionError("input_expression이 비어 있습니다.")
            expected = bool(safe_eval(input_expression, variables))
            expected_str = "true" if expected else "false"
            claimed_bool = _parse_bool(ai_claimed_result)
            if claimed_bool is None:
                return DeterministicResult(
                    check_type=check_type,
                    input_expression=input_expression,
                    expected_result=expected_str,
                    ai_claimed_result=ai_claimed_result or "",
                    check_passed=False,
                    verification_status="weak_evidence",
                    verification_confidence=40.0,
                    verification_reason="AI가 주장한 결과를 참/거짓으로 해석할 수 없습니다.",
                    execution_detail={"engine": "restricted_ast_logic", "expression": input_expression, "variables": variables},
                    limitations=["AI 응답에서 논리값을 추출하지 못함"],
                )
            passed = claimed_bool == expected
            return DeterministicResult(
                check_type=check_type,
                input_expression=input_expression,
                expected_result=expected_str,
                ai_claimed_result=ai_claimed_result or "",
                check_passed=passed,
                verification_status="verified" if passed else "contradicted",
                verification_confidence=100.0,
                verification_reason=(
                    "논리식 평가 결과가 AI 응답과 일치합니다."
                    if passed
                    else f"논리식 평가 결과({expected_str})와 AI 응답이 다릅니다."
                ),
                execution_detail={"engine": "restricted_ast_logic", "expression": input_expression, "variables": variables},
            )

        if check_type == "unit_conversion":
            if value is None or not from_unit or not to_unit:
                raise UnsafeExpressionError("단위 변환에 필요한 값이 부족합니다.")
            expected = convert_unit(value, from_unit, to_unit)
            expected_str = f"{expected:.6g}"
            passed = _results_match(expected, ai_claimed_result)
            return DeterministicResult(
                check_type=check_type,
                input_expression=f"{value} {from_unit} -> {to_unit}",
                expected_result=expected_str,
                ai_claimed_result=ai_claimed_result or "",
                check_passed=passed,
                verification_status="verified" if passed else "contradicted",
                verification_confidence=100.0,
                verification_reason=(
                    "독립 단위 변환 결과와 AI 응답이 일치합니다."
                    if passed
                    else f"독립 변환 결과({expected_str} {to_unit})와 AI 응답이 다릅니다."
                ),
                execution_detail={"engine": "unit_conversion", "from_unit": from_unit, "to_unit": to_unit, "value": value},
            )

        if check_type == "base_conversion":
            if value is None or from_base is None or to_base is None:
                raise UnsafeExpressionError("진법 변환에 필요한 값이 부족합니다.")
            value_str = str(value).split(".")[0] if isinstance(value, float) else str(value)
            expected_str = convert_base(value_str, from_base, to_base)
            passed = (ai_claimed_result or "").strip().lower() == expected_str.lower()
            return DeterministicResult(
                check_type=check_type,
                input_expression=f"{value_str} (base {from_base}) -> base {to_base}",
                expected_result=expected_str,
                ai_claimed_result=ai_claimed_result or "",
                check_passed=passed,
                verification_status="verified" if passed else "contradicted",
                verification_confidence=100.0,
                verification_reason=(
                    "독립 진법 변환 결과와 AI 응답이 일치합니다."
                    if passed
                    else f"독립 변환 결과({expected_str})와 AI 응답이 다릅니다."
                ),
                execution_detail={"engine": "base_conversion", "from_base": from_base, "to_base": to_base, "value": value_str},
            )

        if check_type == "rule_based":
            if not input_expression:
                raise UnsafeExpressionError("input_expression이 비어 있습니다.")
            expected = bool(safe_eval(input_expression, variables))
            expected_str = "true" if expected else "false"
            claimed_bool = _parse_bool(ai_claimed_result)
            if claimed_bool is None:
                return DeterministicResult(
                    check_type=check_type,
                    input_expression=input_expression,
                    expected_result=expected_str,
                    ai_claimed_result=ai_claimed_result or "",
                    check_passed=False,
                    verification_status="weak_evidence",
                    verification_confidence=40.0,
                    verification_reason="AI가 주장한 결과를 참/거짓으로 해석할 수 없습니다.",
                    execution_detail={"engine": "rule_based", "expression": input_expression, "variables": variables},
                    limitations=["AI 응답에서 논리값을 추출하지 못함"],
                )
            passed = claimed_bool == expected
            return DeterministicResult(
                check_type=check_type,
                input_expression=input_expression,
                expected_result=expected_str,
                ai_claimed_result=ai_claimed_result or "",
                check_passed=passed,
                verification_status="verified" if passed else "contradicted",
                verification_confidence=95.0,
                verification_reason=(
                    "규칙 기반 검증 결과가 AI 응답과 일치합니다."
                    if passed
                    else f"규칙 기반 검증 결과({expected_str})와 AI 응답이 다릅니다."
                ),
                execution_detail={"engine": "rule_based", "expression": input_expression, "variables": variables},
            )

        raise UnsafeExpressionError(f"지원하지 않는 check_type: {check_type}")

    except UnsafeExpressionError as exc:
        return DeterministicResult(
            check_type=check_type,
            input_expression=input_expression or "",
            expected_result="",
            ai_claimed_result=ai_claimed_result or "",
            check_passed=False,
            verification_status="weak_evidence",
            verification_confidence=40.0,
            verification_reason=f"입력 또는 단위가 불명확하여 독립 검증을 완료하지 못했습니다: {exc}",
            execution_detail={"engine": "error", "error": str(exc)},
            limitations=["결정적 검증 입력 불명확"],
        )
