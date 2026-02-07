"""WASM code generator for AIFPL.

This module generates WAT code from AIFPL AST (AIFPLValue objects).
"""

from typing import List, Optional, Set, Tuple
from aifpl.aifpl_value import (
    AIFPLValue, AIFPLNumber, AIFPLString, AIFPLBoolean,
    AIFPLSymbol, AIFPLList, AIFPLFunction
)


class CodeGenerator:
    """Generates WAT code from AIFPL expressions."""

    def __init__(self):
        self.lambda_counter = 0
        self.string_counter = 0
        self.functions: List[str] = []  # Generated function definitions
        self.string_literals: List[Tuple[str, str]] = []  # (name, value) pairs
        self.local_counter = 0

    def fresh_lambda_name(self) -> str:
        """Generate a fresh lambda function name."""
        name = f"$lambda_{self.lambda_counter}"
        self.lambda_counter += 1
        return name

    def fresh_string_name(self) -> str:
        """Generate a fresh string constant name."""
        name = f"$str_{self.string_counter}"
        self.string_counter += 1
        return name

    def fresh_local(self) -> str:
        """Generate a fresh local variable name."""
        name = f"$tmp_{self.local_counter}"
        self.local_counter += 1
        return name

    def generate_string_literal(self, s: str) -> str:
        """Generate WAT code to create a string literal."""
        if not s:
            return "(call $make_empty_string)"

        # Create character array
        chars = [str(ord(c)) for c in s]
        char_inits = " ".join(f"(i32.const {c})" for c in chars)

        return f"""\
(struct.new $StringValue
  (global.get $TAG_STRING)
  (i32.const {len(s)})
  (array.new_fixed $CharArray {len(s)} {char_inits}))"""

    def generate_expr(self, expr: AIFPLValue, env: Optional[Set[str]] = None) -> str:
        """Generate WAT code for an AIFPL expression.

        Args:
            expr: The AIFPL expression to compile
            env: Set of variable names in scope (for detecting free variables)

        Returns:
            WAT code that evaluates to a (ref null eq)
        """
        if env is None:
            env = set()

        if isinstance(expr, AIFPLNumber):
            return self._gen_number(expr)
        elif isinstance(expr, AIFPLString):
            return self._gen_string(expr)
        elif isinstance(expr, AIFPLBoolean):
            return self._gen_boolean(expr)
        elif isinstance(expr, AIFPLSymbol):
            return self._gen_symbol_ref(expr, env)
        elif isinstance(expr, AIFPLList):
            return self._gen_list_expr(expr, env)
        else:
            raise ValueError(f"Unknown expression type: {type(expr)}")

    def _gen_number(self, num: AIFPLNumber) -> str:
        """Generate code for a number literal."""
        value = num.value
        if isinstance(value, complex):
            return f"(call $make_complex (f64.const {value.real}) (f64.const {value.imag}))"
        elif isinstance(value, float):
            return f"(call $make_number (f64.const {value}))"
        else:
            # Integer - use i31 optimization for small ints
            if -1073741824 <= value <= 1073741823:
                return f"(ref.i31 (i32.const {value}))"
            else:
                return f"(call $make_number (f64.const {float(value)}))"

    def _gen_string(self, s: AIFPLString) -> str:
        """Generate code for a string literal."""
        return self.generate_string_literal(s.value)

    def _gen_boolean(self, b: AIFPLBoolean) -> str:
        """Generate code for a boolean literal."""
        return "(global.get $TRUE)" if b.value else "(global.get $FALSE)"

    def _gen_symbol_ref(self, sym: AIFPLSymbol, env: Set[str]) -> str:
        """Generate code for a symbol reference (variable lookup)."""
        name = sym.name

        # Check for built-in constants
        if name == "pi":
            return "(call $make_number (global.get $PI))"
        elif name == "e":
            return "(call $make_number (global.get $E))"
        elif name == "j":
            return "(call $make_complex (f64.const 0) (f64.const 1))"
        elif name == "true":
            return "(global.get $TRUE)"
        elif name == "false":
            return "(global.get $FALSE)"

        # Variable lookup from environment
        return f"(call $env_lookup (local.get $env) {self.generate_string_literal(name)})"

    def _gen_list_expr(self, lst: AIFPLList, env: Set[str]) -> str:
        """Generate code for a list expression (function call or special form)."""
        elements = lst.elements

        if not elements:
            # Empty list literal
            return "(global.get $NIL)"

        first = elements[0]

        # Check for special forms
        if isinstance(first, AIFPLSymbol):
            name = first.name

            if name == "quote":
                return self._gen_quote(elements[1] if len(elements) > 1 else AIFPLList([]))

            elif name == "if":
                return self._gen_if(elements[1:], env)

            elif name == "let":
                return self._gen_let(elements[1:], env)

            elif name == "lambda":
                return self._gen_lambda(elements[1:], env)

            elif name == "and":
                return self._gen_and(elements[1:], env)

            elif name == "or":
                return self._gen_or(elements[1:], env)

            elif name == "match":
                return self._gen_match(elements[1:], env)

            elif name == "alist":
                return self._gen_alist(elements[1:], env)

            # Built-in functions
            elif name in BUILTIN_FUNCTIONS:
                return self._gen_builtin_call(name, elements[1:], env)

        # General function call
        return self._gen_function_call(first, elements[1:], env)

    def _gen_quote(self, expr: AIFPLValue) -> str:
        """Generate code for a quote expression."""
        if isinstance(expr, AIFPLNumber):
            return self._gen_number(expr)
        elif isinstance(expr, AIFPLString):
            return self._gen_string(expr)
        elif isinstance(expr, AIFPLBoolean):
            return self._gen_boolean(expr)
        elif isinstance(expr, AIFPLSymbol):
            # Create a symbol value
            return f"(call $make_symbol {self.generate_string_literal(expr.name)})"
        elif isinstance(expr, AIFPLList):
            if not expr.elements:
                return "(global.get $NIL)"
            # Build list from quoted elements
            result = "(global.get $NIL)"
            for elem in reversed(expr.elements):
                quoted_elem = self._gen_quote(elem)
                result = f"(call $make_cons {quoted_elem} {result})"
            return result
        else:
            raise ValueError(f"Cannot quote: {type(expr)}")

    def _gen_if(self, args: List[AIFPLValue], env: Set[str]) -> str:
        """Generate code for an if expression."""
        if len(args) != 3:
            raise ValueError("if requires exactly 3 arguments: condition, then, else")

        cond = self.generate_expr(args[0], env)
        then_branch = self.generate_expr(args[1], env)
        else_branch = self.generate_expr(args[2], env)

        return f"""\
(if (result (ref null eq))
  (call $to_bool {cond})
  (then {then_branch})
  (else {else_branch}))"""

    def _gen_let(self, args: List[AIFPLValue], env: Set[str]) -> str:
        """Generate code for a let expression."""
        if len(args) < 2:
            raise ValueError("let requires bindings and body")

        bindings = args[0]
        body = args[1]

        if not isinstance(bindings, AIFPLList):
            raise ValueError("let bindings must be a list")

        # Start with current environment
        code_parts = []
        new_env = env.copy()

        for binding in bindings.elements:
            if not isinstance(binding, AIFPLList) or len(binding.elements) != 2:
                raise ValueError("let binding must be (name value)")

            name_sym = binding.elements[0]
            if not isinstance(name_sym, AIFPLSymbol):
                raise ValueError("let binding name must be a symbol")

            name = name_sym.name
            value_code = self.generate_expr(binding.elements[1], new_env)
            name_str = self.generate_string_literal(name)

            code_parts.append(f"(local.set $env (call $env_extend (local.get $env) {name_str} {value_code}))")
            new_env.add(name)

        body_code = self.generate_expr(body, new_env)

        # Wrap in a block to manage environment
        return f"""\
(block (result (ref null eq))
  {chr(10).join(code_parts)}
  {body_code})"""

    def _gen_lambda(self, args: List[AIFPLValue], env: Set[str]) -> str:
        """Generate code for a lambda expression."""
        if len(args) != 2:
            raise ValueError("lambda requires parameters and body")

        params = args[0]
        body = args[1]

        if not isinstance(params, AIFPLList):
            raise ValueError("lambda parameters must be a list")

        param_names = []
        for p in params.elements:
            if not isinstance(p, AIFPLSymbol):
                raise ValueError("lambda parameter must be a symbol")
            param_names.append(p.name)

        # Generate a new function for this lambda
        func_name = self.fresh_lambda_name()

        # New environment includes parameters
        new_env = env.copy()
        new_env.update(param_names)

        body_code = self.generate_expr(body, new_env)

        # Generate parameter binding code
        param_bindings = []
        for i, name in enumerate(param_names):
            name_str = self.generate_string_literal(name)
            param_bindings.append(
                f"(local.set $env (call $env_extend (local.get $env) {name_str} "
                f"(array.get $ValueArray (local.get $args) (i32.const {i}))))"
            )

        func_def = f"""\
  (func {func_name} (param $args (ref $ValueArray)) (param $env (ref null $Environment)) (result (ref null eq))
    {chr(10).join(param_bindings)}
    {body_code})"""

        self.functions.append(func_def)

        # Return a FunctionValue
        return f"""\
(struct.new $FunctionValue
  (global.get $TAG_FUNCTION)
  (i32.const {len(param_names)})
  (ref.func {func_name})
  (local.get $env))"""

    def _gen_and(self, args: List[AIFPLValue], env: Set[str]) -> str:
        """Generate code for lazy and."""
        if len(args) == 0:
            return "(global.get $TRUE)"
        if len(args) == 1:
            return self.generate_expr(args[0], env)

        # Lazy evaluation: if first is false, return false without evaluating rest
        first = self.generate_expr(args[0], env)
        rest = self._gen_and(args[1:], env)

        return f"""\
(if (result (ref null eq))
  (call $to_bool {first})
  (then {rest})
  (else (global.get $FALSE)))"""

    def _gen_or(self, args: List[AIFPLValue], env: Set[str]) -> str:
        """Generate code for lazy or."""
        if len(args) == 0:
            return "(global.get $FALSE)"
        if len(args) == 1:
            return self.generate_expr(args[0], env)

        # Lazy evaluation: if first is true, return true without evaluating rest
        first = self.generate_expr(args[0], env)
        rest = self._gen_or(args[1:], env)

        return f"""\
(if (result (ref null eq))
  (call $to_bool {first})
  (then (global.get $TRUE))
  (else {rest}))"""

    def _gen_match(self, args: List[AIFPLValue], env: Set[str]) -> str:
        """Generate code for pattern matching."""
        if len(args) < 2:
            raise ValueError("match requires expression and at least one pattern")

        expr = args[0]
        patterns = args[1:]

        expr_code = self.generate_expr(expr, env)
        expr_local = self.fresh_local()

        # Generate pattern matching code
        code = f"(local.set {expr_local} {expr_code})\n"

        # Generate cascading if-else for patterns
        match_code = self._gen_pattern_cases(expr_local, patterns, env)

        return f"""\
(block (result (ref null eq))
  {code}
  {match_code})"""

    def _gen_pattern_cases(self, expr_local: str, patterns: List[AIFPLValue], env: Set[str]) -> str:
        """Generate code for pattern cases."""
        if not patterns:
            return "(unreachable)  ;; No pattern matched"

        pattern_expr = patterns[0]
        if not isinstance(pattern_expr, AIFPLList) or len(pattern_expr.elements) != 2:
            raise ValueError("match pattern must be (pattern result)")

        pattern = pattern_expr.elements[0]
        result = pattern_expr.elements[1]

        # Generate pattern matching condition and bindings
        cond_code, bindings = self._compile_pattern(pattern, expr_local)

        # Create new environment with bindings
        new_env = env.copy()
        new_env.update(bindings.keys())

        # Generate binding code
        binding_code = ""
        for name, value_code in bindings.items():
            name_str = self.generate_string_literal(name)
            binding_code += f"(local.set $env (call $env_extend (local.get $env) {name_str} {value_code}))\n"

        result_code = self.generate_expr(result, new_env)
        rest_code = self._gen_pattern_cases(expr_local, patterns[1:], env)

        return f"""\
(if (result (ref null eq))
  {cond_code}
  (then
    {binding_code}
    {result_code})
  (else
    {rest_code}))"""

    def _compile_pattern(self, pattern: AIFPLValue, expr_local: str) -> Tuple[str, dict]:
        """Compile a pattern to a condition and bindings.

        Returns:
            (condition_code, {name: value_code})
        """
        if isinstance(pattern, AIFPLNumber):
            # Literal number pattern
            val = pattern.value
            return (f"(call $value_eq (local.get {expr_local}) (call $make_number (f64.const {val})))", {})

        elif isinstance(pattern, AIFPLString):
            # Literal string pattern
            str_code = self.generate_string_literal(pattern.value)
            return (f"(call $value_eq (local.get {expr_local}) {str_code})", {})

        elif isinstance(pattern, AIFPLBoolean):
            # Literal boolean pattern
            bool_code = "(global.get $TRUE)" if pattern.value else "(global.get $FALSE)"
            return (f"(call $value_eq (local.get {expr_local}) {bool_code})", {})

        elif isinstance(pattern, AIFPLSymbol):
            name = pattern.name
            if name == "_":
                # Wildcard - always matches, no binding
                return ("(i32.const 1)", {})
            else:
                # Variable pattern - always matches, binds the value
                return ("(i32.const 1)", {name: f"(local.get {expr_local})"})

        elif isinstance(pattern, AIFPLList):
            elements = pattern.elements
            if not elements:
                # Empty list pattern
                return (f"(call $is_nil (local.get {expr_local}))", {})

            first = elements[0]

            # Type pattern: (number? n), (string? s), etc.
            if isinstance(first, AIFPLSymbol) and first.name.endswith("?"):
                type_pred = first.name
                if len(elements) == 2 and isinstance(elements[1], AIFPLSymbol):
                    var_name = elements[1].name
                    pred_func = TYPE_PREDICATES.get(type_pred)
                    if pred_func:
                        return (f"(call {pred_func} (local.get {expr_local}))",
                                {var_name: f"(local.get {expr_local})"})

            # Check for cons pattern: (head . tail)
            if len(elements) == 3 and isinstance(elements[1], AIFPLSymbol) and elements[1].name == ".":
                # Cons pattern
                head_pattern = elements[0]
                tail_pattern = elements[2]

                # Condition: is a non-empty list
                cond = f"(i32.and (call $is_list (local.get {expr_local})) (i32.eqz (call $is_nil (local.get {expr_local}))))"

                head_local = self.fresh_local()
                tail_local = self.fresh_local()

                # Compile sub-patterns
                head_cond, head_bindings = self._compile_pattern(head_pattern, head_local)
                tail_cond, tail_bindings = self._compile_pattern(tail_pattern, tail_local)

                all_bindings = {**head_bindings, **tail_bindings}

                full_cond = f"""\
(block (result i32)
  (if (result i32)
    {cond}
    (then
      (local.set {head_local} (call $list_first (local.get {expr_local})))
      (local.set {tail_local} (call $list_rest (local.get {expr_local})))
      (i32.and {head_cond} {tail_cond}))
    (else (i32.const 0))))"""

                return (full_cond, all_bindings)

            # Fixed-length list pattern: (a b c)
            n = len(elements)
            bindings = {}
            conditions = [f"(call $is_list (local.get {expr_local}))",
                          f"(i32.eq (call $list_length (local.get {expr_local})) (i32.const {n}))"]

            for i, elem_pattern in enumerate(elements):
                elem_local = self.fresh_local()
                elem_cond, elem_bindings = self._compile_pattern(elem_pattern, elem_local)
                bindings.update(elem_bindings)

                # Add condition and set up local
                conditions.append(f"""\
(block (result i32)
  (local.set {elem_local} (call $aifpl_list_ref (local.get {expr_local}) (call $make_int (i32.const {i}))))
  {elem_cond})""")

            # Combine all conditions with and
            full_cond = conditions[0]
            for c in conditions[1:]:
                full_cond = f"(i32.and {full_cond} {c})"

            return (full_cond, bindings)

        raise ValueError(f"Unknown pattern type: {type(pattern)}")

    def _gen_alist(self, args: List[AIFPLValue], env: Set[str]) -> str:
        """Generate code for alist construction."""
        if not args:
            return "(call $make_empty_alist)"

        # Each arg should be a (key value) pair
        entries = []
        for arg in args:
            if not isinstance(arg, AIFPLList) or len(arg.elements) != 2:
                raise ValueError("alist entry must be (key value)")
            key_code = self.generate_expr(arg.elements[0], env)
            val_code = self.generate_expr(arg.elements[1], env)
            entries.append(f"(call $make_alist_entry {key_code} {val_code})")

        # Create array of entries
        n = len(entries)
        array_init = " ".join(entries)

        return f"""\
(call $make_alist
  (array.new_fixed $AlistEntryArray {n} {array_init}))"""

    def _gen_builtin_call(self, name: str, args: List[AIFPLValue], env: Set[str]) -> str:
        """Generate code for a built-in function call."""
        func_info = BUILTIN_FUNCTIONS[name]
        func_name = func_info["wat_name"]
        arity = func_info.get("arity", -1)  # -1 for variadic

        arg_codes = [self.generate_expr(arg, env) for arg in args]

        if arity == -1:
            # Variadic function - need special handling
            return self._gen_variadic_call(func_name, arg_codes)
        else:
            if len(args) != arity:
                raise ValueError(f"{name} requires {arity} arguments, got {len(args)}")
            return f"(call {func_name} {' '.join(arg_codes)})"

    def _gen_variadic_call(self, base_name: str, arg_codes: List[str]) -> str:
        """Generate code for a variadic function call."""
        if not arg_codes:
            raise ValueError("Variadic function requires at least one argument")

        # For binary operators, chain them
        result = arg_codes[0]
        for arg in arg_codes[1:]:
            result = f"(call {base_name} {result} {arg})"
        return result

    def _gen_function_call(self, func_expr: AIFPLValue, args: List[AIFPLValue], env: Set[str]) -> str:
        """Generate code for a general function call."""
        func_code = self.generate_expr(func_expr, env)
        arg_codes = [self.generate_expr(arg, env) for arg in args]

        # Create args array
        n = len(args)
        if n == 0:
            args_array = "(array.new $ValueArray (ref.null eq) (i32.const 0))"
        else:
            arg_inits = " ".join(arg_codes)
            args_array = f"(array.new_fixed $ValueArray {n} {arg_inits})"

        func_local = self.fresh_local()

        return f"""\
(block (result (ref null eq))
  (local.set {func_local} {func_code})
  (call_ref $UserFuncType
    {args_array}
    (struct.get $FunctionValue $env (ref.cast (ref $FunctionValue) (local.get {func_local})))
    (struct.get $FunctionValue $code (ref.cast (ref $FunctionValue) (local.get {func_local})))))"""


# Type predicates mapping
TYPE_PREDICATES = {
    "number?": "$is_number",
    "integer?": "$is_integer",
    "float?": "$is_float",
    "complex?": "$is_complex",
    "string?": "$is_string",
    "boolean?": "$is_boolean",
    "list?": "$is_list",
    "null?": "$is_nil",
    "symbol?": "$is_symbol",
    "function?": "$is_function",
    "alist?": "$is_alist",
}

# Built-in functions mapping
BUILTIN_FUNCTIONS = {
    # Arithmetic (variadic)
    "+": {"wat_name": "$add", "arity": -1},
    "-": {"wat_name": "$sub", "arity": -1},
    "*": {"wat_name": "$mul", "arity": -1},
    "/": {"wat_name": "$div", "arity": -1},
    "//": {"wat_name": "$floor_div", "arity": 2},
    "%": {"wat_name": "$mod", "arity": 2},
    "**": {"wat_name": "$pow", "arity": 2},

    # Unary math
    "abs": {"wat_name": "$abs", "arity": 1},
    "neg": {"wat_name": "$neg", "arity": 1},
    "sin": {"wat_name": "$aifpl_sin", "arity": 1},
    "cos": {"wat_name": "$aifpl_cos", "arity": 1},
    "tan": {"wat_name": "$aifpl_tan", "arity": 1},
    "sqrt": {"wat_name": "$aifpl_sqrt", "arity": 1},
    "log": {"wat_name": "$aifpl_log", "arity": 1},
    "exp": {"wat_name": "$aifpl_exp", "arity": 1},
    "floor": {"wat_name": "$aifpl_floor", "arity": 1},
    "ceil": {"wat_name": "$aifpl_ceil", "arity": 1},
    "round": {"wat_name": "$aifpl_round", "arity": 1},

    # Binary math
    "min": {"wat_name": "$aifpl_min", "arity": 2},
    "max": {"wat_name": "$aifpl_max", "arity": 2},

    # Comparison (variadic for chaining)
    "=": {"wat_name": "$aifpl_eq", "arity": 2},
    "!=": {"wat_name": "$aifpl_ne", "arity": 2},
    "<": {"wat_name": "$aifpl_lt", "arity": 2},
    "<=": {"wat_name": "$aifpl_le", "arity": 2},
    ">": {"wat_name": "$aifpl_gt", "arity": 2},
    ">=": {"wat_name": "$aifpl_ge", "arity": 2},

    # Boolean
    "not": {"wat_name": "$aifpl_not", "arity": 1},

    # Complex
    "complex": {"wat_name": "$make_complex", "arity": 2},
    "real": {"wat_name": "$get_real", "arity": 1},
    "imag": {"wat_name": "$get_imag", "arity": 1},

    # List
    "list": {"wat_name": "$make_list", "arity": -1},  # Special handling needed
    "cons": {"wat_name": "$aifpl_cons", "arity": 2},
    "first": {"wat_name": "$aifpl_first", "arity": 1},
    "rest": {"wat_name": "$aifpl_rest", "arity": 1},
    "last": {"wat_name": "$aifpl_last", "arity": 1},
    "length": {"wat_name": "$aifpl_length", "arity": 1},
    "null?": {"wat_name": "$aifpl_null", "arity": 1},
    "list-ref": {"wat_name": "$aifpl_list_ref", "arity": 2},
    "append": {"wat_name": "$aifpl_append", "arity": 2},
    "reverse": {"wat_name": "$aifpl_reverse", "arity": 1},
    "member?": {"wat_name": "$aifpl_member", "arity": 2},
    "remove": {"wat_name": "$aifpl_remove", "arity": 2},
    "position": {"wat_name": "$aifpl_position", "arity": 2},
    "take": {"wat_name": "$aifpl_take", "arity": 2},
    "drop": {"wat_name": "$aifpl_drop", "arity": 2},
    "range": {"wat_name": "$aifpl_range_2", "arity": 2},  # 2-arg version

    # Higher-order
    "map": {"wat_name": "$aifpl_map", "arity": 2},
    "filter": {"wat_name": "$aifpl_filter", "arity": 2},
    "fold": {"wat_name": "$aifpl_fold", "arity": 3},
    "find": {"wat_name": "$aifpl_find", "arity": 2},
    "any?": {"wat_name": "$aifpl_any", "arity": 2},
    "all?": {"wat_name": "$aifpl_all", "arity": 2},

    # String
    "string-append": {"wat_name": "$aifpl_string_append", "arity": -1},
    "string-length": {"wat_name": "$aifpl_string_length", "arity": 1},
    "string-ref": {"wat_name": "$aifpl_string_ref", "arity": 2},
    "substring": {"wat_name": "$aifpl_substring", "arity": 3},
    "string-upcase": {"wat_name": "$aifpl_string_upcase", "arity": 1},
    "string-downcase": {"wat_name": "$aifpl_string_downcase", "arity": 1},
    "string-trim": {"wat_name": "$aifpl_string_trim", "arity": 1},
    "string-contains?": {"wat_name": "$aifpl_string_contains", "arity": 2},
    "string-prefix?": {"wat_name": "$aifpl_string_prefix", "arity": 2},
    "string-suffix?": {"wat_name": "$aifpl_string_suffix", "arity": 2},
    "string=?": {"wat_name": "$aifpl_string_eq", "arity": 2},
    "string->list": {"wat_name": "$aifpl_string_to_list", "arity": 1},
    "list->string": {"wat_name": "$aifpl_list_to_string", "arity": 1},
    "number->string": {"wat_name": "$aifpl_number_to_string", "arity": 1},
    "string->number": {"wat_name": "$aifpl_string_to_number", "arity": 1},

    # Type predicates
    "number?": {"wat_name": "$is_number", "arity": 1},
    "integer?": {"wat_name": "$is_integer", "arity": 1},
    "float?": {"wat_name": "$is_float", "arity": 1},
    "complex?": {"wat_name": "$is_complex", "arity": 1},
    "string?": {"wat_name": "$is_string", "arity": 1},
    "boolean?": {"wat_name": "$is_boolean", "arity": 1},
    "list?": {"wat_name": "$is_list", "arity": 1},
    "symbol?": {"wat_name": "$is_symbol", "arity": 1},
    "function?": {"wat_name": "$is_function", "arity": 1},
    "alist?": {"wat_name": "$is_alist", "arity": 1},

    # Alist operations
    "alist-get": {"wat_name": "$aifpl_alist_get", "arity": 2},
    "alist-set": {"wat_name": "$aifpl_alist_set", "arity": 3},
    "alist-has?": {"wat_name": "$aifpl_alist_has", "arity": 2},
    "alist-remove": {"wat_name": "$aifpl_alist_remove", "arity": 2},
    "alist-keys": {"wat_name": "$aifpl_alist_keys", "arity": 1},
    "alist-values": {"wat_name": "$aifpl_alist_values", "arity": 1},
    "alist-length": {"wat_name": "$aifpl_alist_length", "arity": 1},
    "alist-merge": {"wat_name": "$aifpl_alist_merge", "arity": 2},

    # Bitwise operations
    "bit-and": {"wat_name": "$aifpl_bit_and", "arity": 2},
    "bit-or": {"wat_name": "$aifpl_bit_or", "arity": 2},
    "bit-xor": {"wat_name": "$aifpl_bit_xor", "arity": 2},
    "bit-not": {"wat_name": "$aifpl_bit_not", "arity": 1},
    "bit-shift-left": {"wat_name": "$aifpl_bit_shl", "arity": 2},
    "bit-shift-right": {"wat_name": "$aifpl_bit_shr", "arity": 2},
    "bit-shift-right-unsigned": {"wat_name": "$aifpl_bit_shr_u", "arity": 2},
    "bit-count": {"wat_name": "$aifpl_bit_count", "arity": 1},
    "bit-length": {"wat_name": "$aifpl_bit_length", "arity": 1},
    "bit-set?": {"wat_name": "$aifpl_bit_set", "arity": 2},
    "bit-set": {"wat_name": "$aifpl_bit_set_to_1", "arity": 2},
    "bit-clear": {"wat_name": "$aifpl_bit_clear", "arity": 2},
    "bit-flip": {"wat_name": "$aifpl_bit_flip", "arity": 2},
}
