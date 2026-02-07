"""Tests for the AIFPL WASM compiler."""

import pytest
from aifpl.wasm.compiler import AIFPLWasmCompiler


class TestWasmCompilerBasic:
    """Basic compilation tests."""

    @pytest.fixture
    def compiler(self):
        return AIFPLWasmCompiler()

    def test_compile_integer(self, compiler):
        """Test compiling a simple integer."""
        wat = compiler.compile_to_wat("42")
        assert "(module" in wat
        assert "42" in wat

    def test_compile_float(self, compiler):
        """Test compiling a float."""
        wat = compiler.compile_to_wat("3.14")
        assert "3.14" in wat

    def test_compile_boolean_true(self, compiler):
        """Test compiling #t."""
        wat = compiler.compile_to_wat("#t")
        assert "$TRUE" in wat

    def test_compile_boolean_false(self, compiler):
        """Test compiling #f."""
        wat = compiler.compile_to_wat("#f")
        assert "$FALSE" in wat

    def test_compile_string(self, compiler):
        """Test compiling a string."""
        wat = compiler.compile_to_wat('"hello"')
        assert "$StringValue" in wat

    def test_compile_addition(self, compiler):
        """Test compiling addition."""
        wat = compiler.compile_to_wat("(+ 1 2)")
        assert "$add" in wat

    def test_compile_nested_arithmetic(self, compiler):
        """Test compiling nested arithmetic."""
        wat = compiler.compile_to_wat("(+ (* 2 3) (- 10 5))")
        assert "$add" in wat
        assert "$mul" in wat
        assert "$sub" in wat

    def test_compile_if(self, compiler):
        """Test compiling if expression."""
        wat = compiler.compile_to_wat('(if #t 1 2)')
        assert "(if" in wat
        assert "$to_bool" in wat

    def test_compile_let(self, compiler):
        """Test compiling let expression."""
        wat = compiler.compile_to_wat("(let ((x 5)) x)")
        assert "$env_extend" in wat

    def test_compile_lambda(self, compiler):
        """Test compiling lambda expression."""
        wat = compiler.compile_to_wat("(lambda (x) (* x x))")
        assert "$FunctionValue" in wat
        assert "$lambda_" in wat

    def test_compile_quote(self, compiler):
        """Test compiling quote expression."""
        wat = compiler.compile_to_wat("(quote (1 2 3))")
        assert "$make_cons" in wat

    def test_compile_list_operations(self, compiler):
        """Test compiling list operations."""
        wat = compiler.compile_to_wat("(first (list 1 2 3))")
        assert "$aifpl_first" in wat


class TestWasmCompilerExecution:
    """Tests that compile and execute AIFPL code."""

    @pytest.fixture
    def compiler(self):
        return AIFPLWasmCompiler()

    @pytest.mark.skipif(
        not AIFPLWasmCompiler()._check_wasmtime(),
        reason="wasmtime not available"
    )
    def test_run_integer(self, compiler):
        """Test running a simple integer."""
        result = compiler.compile_and_run("42")
        assert result == 42

    @pytest.mark.skipif(
        not AIFPLWasmCompiler()._check_wasmtime(),
        reason="wasmtime not available"
    )
    def test_run_addition(self, compiler):
        """Test running addition."""
        result = compiler.compile_and_run("(+ 1 2 3)")
        assert result == 6

    @pytest.mark.skipif(
        not AIFPLWasmCompiler()._check_wasmtime(),
        reason="wasmtime not available"
    )
    def test_run_multiplication(self, compiler):
        """Test running multiplication."""
        result = compiler.compile_and_run("(* 2 3 4)")
        assert result == 24

    @pytest.mark.skipif(
        not AIFPLWasmCompiler()._check_wasmtime(),
        reason="wasmtime not available"
    )
    def test_run_subtraction(self, compiler):
        """Test running subtraction."""
        result = compiler.compile_and_run("(- 10 3)")
        assert result == 7

    @pytest.mark.skipif(
        not AIFPLWasmCompiler()._check_wasmtime(),
        reason="wasmtime not available"
    )
    def test_run_division(self, compiler):
        """Test running division."""
        result = compiler.compile_and_run("(/ 12 3)")
        assert result == 4

    @pytest.mark.skipif(
        not AIFPLWasmCompiler()._check_wasmtime(),
        reason="wasmtime not available"
    )
    def test_run_nested_arithmetic(self, compiler):
        """Test running nested arithmetic."""
        result = compiler.compile_and_run("(+ (* 2 3) (- 10 5))")
        assert result == 11

    @pytest.mark.skipif(
        not AIFPLWasmCompiler()._check_wasmtime(),
        reason="wasmtime not available"
    )
    def test_run_boolean_true(self, compiler):
        """Test running #t."""
        result = compiler.compile_and_run("#t")
        assert result is True

    @pytest.mark.skipif(
        not AIFPLWasmCompiler()._check_wasmtime(),
        reason="wasmtime not available"
    )
    def test_run_boolean_false(self, compiler):
        """Test running #f."""
        result = compiler.compile_and_run("#f")
        assert result is False

    @pytest.mark.skipif(
        not AIFPLWasmCompiler()._check_wasmtime(),
        reason="wasmtime not available"
    )
    def test_run_if_true_branch(self, compiler):
        """Test running if with true condition."""
        result = compiler.compile_and_run("(if #t 1 2)")
        assert result == 1

    @pytest.mark.skipif(
        not AIFPLWasmCompiler()._check_wasmtime(),
        reason="wasmtime not available"
    )
    def test_run_if_false_branch(self, compiler):
        """Test running if with false condition."""
        result = compiler.compile_and_run("(if #f 1 2)")
        assert result == 2

    @pytest.mark.skipif(
        not AIFPLWasmCompiler()._check_wasmtime(),
        reason="wasmtime not available"
    )
    def test_run_comparison_gt(self, compiler):
        """Test running > comparison."""
        result = compiler.compile_and_run("(> 5 3)")
        assert result is True

    @pytest.mark.skipif(
        not AIFPLWasmCompiler()._check_wasmtime(),
        reason="wasmtime not available"
    )
    def test_run_comparison_lt(self, compiler):
        """Test running < comparison."""
        result = compiler.compile_and_run("(< 3 5)")
        assert result is True

    @pytest.mark.skipif(
        not AIFPLWasmCompiler()._check_wasmtime(),
        reason="wasmtime not available"
    )
    def test_run_comparison_eq(self, compiler):
        """Test running = comparison."""
        result = compiler.compile_and_run("(= 5 5)")
        assert result is True

    @pytest.mark.skipif(
        not AIFPLWasmCompiler()._check_wasmtime(),
        reason="wasmtime not available"
    )
    def test_run_let_simple(self, compiler):
        """Test running simple let."""
        result = compiler.compile_and_run("(let ((x 5)) x)")
        assert result == 5

    @pytest.mark.skipif(
        not AIFPLWasmCompiler()._check_wasmtime(),
        reason="wasmtime not available"
    )
    def test_run_let_with_arithmetic(self, compiler):
        """Test running let with arithmetic."""
        result = compiler.compile_and_run("(let ((x 5)) (+ x 10))")
        assert result == 15

    @pytest.mark.skipif(
        not AIFPLWasmCompiler()._check_wasmtime(),
        reason="wasmtime not available"
    )
    def test_run_let_multiple_bindings(self, compiler):
        """Test running let with multiple bindings."""
        result = compiler.compile_and_run("(let ((x 3) (y 4)) (+ (* x x) (* y y)))")
        assert result == 25

    @pytest.mark.skipif(
        not AIFPLWasmCompiler()._check_wasmtime(),
        reason="wasmtime not available"
    )
    def test_run_lambda_immediate(self, compiler):
        """Test running immediately invoked lambda."""
        result = compiler.compile_and_run("((lambda (x) (* x x)) 5)")
        assert result == 25

    @pytest.mark.skipif(
        not AIFPLWasmCompiler()._check_wasmtime(),
        reason="wasmtime not available"
    )
    def test_run_lambda_with_let(self, compiler):
        """Test running lambda stored in let."""
        result = compiler.compile_and_run("""
            (let ((square (lambda (x) (* x x))))
              (square 6))
        """)
        assert result == 36

    @pytest.mark.skipif(
        not AIFPLWasmCompiler()._check_wasmtime(),
        reason="wasmtime not available"
    )
    def test_run_pi_constant(self, compiler):
        """Test running pi constant."""
        result = compiler.compile_and_run("pi")
        assert abs(result - 3.141592653589793) < 1e-10

    @pytest.mark.skipif(
        not AIFPLWasmCompiler()._check_wasmtime(),
        reason="wasmtime not available"
    )
    def test_run_abs(self, compiler):
        """Test running abs function."""
        result = compiler.compile_and_run("(abs -5)")
        assert result == 5

    @pytest.mark.skipif(
        not AIFPLWasmCompiler()._check_wasmtime(),
        reason="wasmtime not available"
    )
    def test_run_floor_division(self, compiler):
        """Test running floor division."""
        result = compiler.compile_and_run("(// 7 3)")
        assert result == 2

    @pytest.mark.skipif(
        not AIFPLWasmCompiler()._check_wasmtime(),
        reason="wasmtime not available"
    )
    def test_run_modulo(self, compiler):
        """Test running modulo."""
        result = compiler.compile_and_run("(% 7 3)")
        assert result == 1


class TestWasmCompilerConformance:
    """Tests comparing WASM compiler results with interpreter."""

    @pytest.fixture
    def compiler(self):
        return AIFPLWasmCompiler()

    @pytest.fixture
    def interpreter(self):
        from aifpl import AIFPL
        return AIFPL()

    @pytest.mark.skipif(
        not AIFPLWasmCompiler()._check_wasmtime(),
        reason="wasmtime not available"
    )
    def test_conformance_arithmetic(self, compiler, interpreter):
        """Test that compiler matches interpreter for arithmetic."""
        expressions = [
            "(+ 1 2 3)",
            "(- 10 3)",
            "(* 2 3 4)",
            "(/ 12 3)",
            "(// 7 3)",
            "(% 7 3)",
            "(** 2 3)",
        ]
        for expr in expressions:
            wasm_result = compiler.compile_and_run(expr)
            interp_result = interpreter.evaluate(expr)
            assert wasm_result == interp_result, f"Mismatch for {expr}: WASM={wasm_result}, interp={interp_result}"

    @pytest.mark.skipif(
        not AIFPLWasmCompiler()._check_wasmtime(),
        reason="wasmtime not available"
    )
    def test_conformance_comparisons(self, compiler, interpreter):
        """Test that compiler matches interpreter for comparisons."""
        expressions = [
            "(> 5 3)",
            "(< 3 5)",
            "(= 5 5)",
            "(!= 5 3)",
            "(>= 5 5)",
            "(<= 3 3)",
        ]
        for expr in expressions:
            wasm_result = compiler.compile_and_run(expr)
            interp_result = interpreter.evaluate(expr)
            assert wasm_result == interp_result, f"Mismatch for {expr}: WASM={wasm_result}, interp={interp_result}"

    @pytest.mark.skipif(
        not AIFPLWasmCompiler()._check_wasmtime(),
        reason="wasmtime not available"
    )
    def test_conformance_if(self, compiler, interpreter):
        """Test that compiler matches interpreter for if expressions."""
        expressions = [
            "(if #t 1 2)",
            "(if #f 1 2)",
            "(if (> 5 3) 10 20)",
            "(if (< 5 3) 10 20)",
        ]
        for expr in expressions:
            wasm_result = compiler.compile_and_run(expr)
            interp_result = interpreter.evaluate(expr)
            assert wasm_result == interp_result, f"Mismatch for {expr}: WASM={wasm_result}, interp={interp_result}"

    @pytest.mark.skipif(
        not AIFPLWasmCompiler()._check_wasmtime(),
        reason="wasmtime not available"
    )
    def test_conformance_let(self, compiler, interpreter):
        """Test that compiler matches interpreter for let expressions."""
        expressions = [
            "(let ((x 5)) x)",
            "(let ((x 5)) (+ x 10))",
            "(let ((x 3) (y 4)) (+ x y))",
            "(let ((x 5) (y (* x 2))) (+ x y))",
        ]
        for expr in expressions:
            wasm_result = compiler.compile_and_run(expr)
            interp_result = interpreter.evaluate(expr)
            assert wasm_result == interp_result, f"Mismatch for {expr}: WASM={wasm_result}, interp={interp_result}"


class TestWasmListOperations:
    """Tests for list operations."""

    @pytest.fixture
    def compiler(self):
        return AIFPLWasmCompiler()

    @pytest.mark.skipif(
        not AIFPLWasmCompiler()._check_wasmtime(),
        reason="wasmtime not available"
    )
    def test_list_first(self, compiler):
        """Test first on a list."""
        result = compiler.compile_and_run("(first (list 1 2 3))")
        assert result == 1

    @pytest.mark.skipif(
        not AIFPLWasmCompiler()._check_wasmtime(),
        reason="wasmtime not available"
    )
    def test_list_rest_first(self, compiler):
        """Test rest then first."""
        result = compiler.compile_and_run("(first (rest (list 1 2 3)))")
        assert result == 2

    @pytest.mark.skipif(
        not AIFPLWasmCompiler()._check_wasmtime(),
        reason="wasmtime not available"
    )
    def test_list_length(self, compiler):
        """Test length of a list."""
        result = compiler.compile_and_run("(length (list 1 2 3 4 5))")
        assert result == 5

    @pytest.mark.skipif(
        not AIFPLWasmCompiler()._check_wasmtime(),
        reason="wasmtime not available"
    )
    def test_list_last(self, compiler):
        """Test last element of a list."""
        result = compiler.compile_and_run("(last (list 1 2 3))")
        assert result == 3

    @pytest.mark.skipif(
        not AIFPLWasmCompiler()._check_wasmtime(),
        reason="wasmtime not available"
    )
    def test_list_ref(self, compiler):
        """Test list-ref indexing."""
        result = compiler.compile_and_run("(list-ref (list 10 20 30) 1)")
        assert result == 20

    @pytest.mark.skipif(
        not AIFPLWasmCompiler()._check_wasmtime(),
        reason="wasmtime not available"
    )
    def test_list_take(self, compiler):
        """Test take from list."""
        result = compiler.compile_and_run("(length (take 2 (list 1 2 3 4)))")
        assert result == 2

    @pytest.mark.skipif(
        not AIFPLWasmCompiler()._check_wasmtime(),
        reason="wasmtime not available"
    )
    def test_list_drop(self, compiler):
        """Test drop from list."""
        result = compiler.compile_and_run("(first (drop 2 (list 1 2 3 4)))")
        assert result == 3

    @pytest.mark.skipif(
        not AIFPLWasmCompiler()._check_wasmtime(),
        reason="wasmtime not available"
    )
    def test_list_reverse(self, compiler):
        """Test reverse list."""
        result = compiler.compile_and_run("(first (reverse (list 1 2 3)))")
        assert result == 3

    @pytest.mark.skipif(
        not AIFPLWasmCompiler()._check_wasmtime(),
        reason="wasmtime not available"
    )
    def test_list_append_length(self, compiler):
        """Test append two lists."""
        result = compiler.compile_and_run("(length (append (list 1 2) (list 3 4 5)))")
        assert result == 5


class TestWasmBitwiseOperations:
    """Tests for bitwise operations."""

    @pytest.fixture
    def compiler(self):
        return AIFPLWasmCompiler()

    @pytest.mark.skipif(
        not AIFPLWasmCompiler()._check_wasmtime(),
        reason="wasmtime not available"
    )
    def test_bit_and(self, compiler):
        """Test bitwise AND: 12 & 10 = 8."""
        result = compiler.compile_and_run("(bit-and 12 10)")
        assert result == 8

    @pytest.mark.skipif(
        not AIFPLWasmCompiler()._check_wasmtime(),
        reason="wasmtime not available"
    )
    def test_bit_or(self, compiler):
        """Test bitwise OR: 12 | 10 = 14."""
        result = compiler.compile_and_run("(bit-or 12 10)")
        assert result == 14

    @pytest.mark.skipif(
        not AIFPLWasmCompiler()._check_wasmtime(),
        reason="wasmtime not available"
    )
    def test_bit_xor(self, compiler):
        """Test bitwise XOR: 12 ^ 10 = 6."""
        result = compiler.compile_and_run("(bit-xor 12 10)")
        assert result == 6

    @pytest.mark.skipif(
        not AIFPLWasmCompiler()._check_wasmtime(),
        reason="wasmtime not available"
    )
    def test_bit_not(self, compiler):
        """Test bitwise NOT: ~0 = -1."""
        result = compiler.compile_and_run("(bit-not 0)")
        assert result == -1

    @pytest.mark.skipif(
        not AIFPLWasmCompiler()._check_wasmtime(),
        reason="wasmtime not available"
    )
    def test_bit_shift_left(self, compiler):
        """Test left shift: 1 << 3 = 8."""
        result = compiler.compile_and_run("(bit-shift-left 1 3)")
        assert result == 8

    @pytest.mark.skipif(
        not AIFPLWasmCompiler()._check_wasmtime(),
        reason="wasmtime not available"
    )
    def test_bit_shift_right(self, compiler):
        """Test right shift: 16 >> 2 = 4."""
        result = compiler.compile_and_run("(bit-shift-right 16 2)")
        assert result == 4

    @pytest.mark.skipif(
        not AIFPLWasmCompiler()._check_wasmtime(),
        reason="wasmtime not available"
    )
    def test_bit_count(self, compiler):
        """Test popcount: popcount(11) = 3."""
        result = compiler.compile_and_run("(bit-count 11)")
        assert result == 3

    @pytest.mark.skipif(
        not AIFPLWasmCompiler()._check_wasmtime(),
        reason="wasmtime not available"
    )
    def test_bit_length(self, compiler):
        """Test bit-length: 8 needs 4 bits."""
        result = compiler.compile_and_run("(bit-length 8)")
        assert result == 4


class TestWasmAlistOperations:
    """Tests for association list operations."""

    @pytest.fixture
    def compiler(self):
        return AIFPLWasmCompiler()

    @pytest.mark.skipif(
        not AIFPLWasmCompiler()._check_wasmtime(),
        reason="wasmtime not available"
    )
    def test_alist_get(self, compiler):
        """Test alist-get retrieves a value."""
        result = compiler.compile_and_run("""
            (alist-get (quote b)
                       (list (list (quote a) 1)
                             (list (quote b) 2)
                             (list (quote c) 3)))
        """)
        assert result == 2

    @pytest.mark.skipif(
        not AIFPLWasmCompiler()._check_wasmtime(),
        reason="wasmtime not available"
    )
    def test_alist_length(self, compiler):
        """Test alist-length counts entries."""
        result = compiler.compile_and_run("""
            (alist-length (list (list (quote a) 1)
                               (list (quote b) 2)
                               (list (quote c) 3)))
        """)
        assert result == 3


class TestWasmHigherOrderFunctions:
    """Tests for higher-order functions."""

    @pytest.fixture
    def compiler(self):
        return AIFPLWasmCompiler()

    @pytest.mark.skipif(
        not AIFPLWasmCompiler()._check_wasmtime(),
        reason="wasmtime not available"
    )
    def test_lambda_call(self, compiler):
        """Test calling a lambda function."""
        result = compiler.compile_and_run("((lambda (x) (* x x)) 7)")
        assert result == 49

    @pytest.mark.skipif(
        not AIFPLWasmCompiler()._check_wasmtime(),
        reason="wasmtime not available"
    )
    def test_lambda_closure(self, compiler):
        """Test lambda capturing environment."""
        result = compiler.compile_and_run("""
            (let ((a 10))
              ((lambda (x) (+ x a)) 5))
        """)
        assert result == 15

    @pytest.mark.skipif(
        not AIFPLWasmCompiler()._check_wasmtime(),
        reason="wasmtime not available"
    )
    def test_lambda_multiple_args(self, compiler):
        """Test lambda with multiple arguments."""
        result = compiler.compile_and_run("((lambda (x y z) (+ x y z)) 1 2 3)")
        assert result == 6

    @pytest.mark.skipif(
        not AIFPLWasmCompiler()._check_wasmtime(),
        reason="wasmtime not available"
    )
    def test_curried_function(self, compiler):
        """Test curried function pattern."""
        result = compiler.compile_and_run("""
            (let ((add (lambda (x) (lambda (y) (+ x y)))))
              ((add 5) 3))
        """)
        assert result == 8


class TestWasmMathFunctions:
    """Tests for mathematical functions."""

    @pytest.fixture
    def compiler(self):
        return AIFPLWasmCompiler()

    @pytest.mark.skipif(
        not AIFPLWasmCompiler()._check_wasmtime(),
        reason="wasmtime not available"
    )
    def test_abs_negative(self, compiler):
        """Test abs of negative number."""
        result = compiler.compile_and_run("(abs -42)")
        assert result == 42

    @pytest.mark.skipif(
        not AIFPLWasmCompiler()._check_wasmtime(),
        reason="wasmtime not available"
    )
    def test_abs_positive(self, compiler):
        """Test abs of positive number."""
        result = compiler.compile_and_run("(abs 42)")
        assert result == 42

    @pytest.mark.skipif(
        not AIFPLWasmCompiler()._check_wasmtime(),
        reason="wasmtime not available"
    )
    def test_min(self, compiler):
        """Test min function."""
        result = compiler.compile_and_run("(min 3 7 1 9 2)")
        assert result == 1

    @pytest.mark.skipif(
        not AIFPLWasmCompiler()._check_wasmtime(),
        reason="wasmtime not available"
    )
    def test_max(self, compiler):
        """Test max function."""
        result = compiler.compile_and_run("(max 3 7 1 9 2)")
        assert result == 9

    @pytest.mark.skipif(
        not AIFPLWasmCompiler()._check_wasmtime(),
        reason="wasmtime not available"
    )
    def test_floor(self, compiler):
        """Test floor function."""
        result = compiler.compile_and_run("(floor 3.7)")
        assert result == 3

    @pytest.mark.skipif(
        not AIFPLWasmCompiler()._check_wasmtime(),
        reason="wasmtime not available"
    )
    def test_ceil(self, compiler):
        """Test ceiling function."""
        result = compiler.compile_and_run("(ceil 3.2)")
        assert result == 4

    @pytest.mark.skipif(
        not AIFPLWasmCompiler()._check_wasmtime(),
        reason="wasmtime not available"
    )
    def test_sqrt(self, compiler):
        """Test square root."""
        result = compiler.compile_and_run("(sqrt 16)")
        assert result == 4

    @pytest.mark.skipif(
        not AIFPLWasmCompiler()._check_wasmtime(),
        reason="wasmtime not available"
    )
    def test_power(self, compiler):
        """Test exponentiation."""
        result = compiler.compile_and_run("(** 2 10)")
        assert result == 1024


class TestWasmBooleanLogic:
    """Tests for boolean logic operations."""

    @pytest.fixture
    def compiler(self):
        return AIFPLWasmCompiler()

    @pytest.mark.skipif(
        not AIFPLWasmCompiler()._check_wasmtime(),
        reason="wasmtime not available"
    )
    def test_and_true(self, compiler):
        """Test and with all true."""
        result = compiler.compile_and_run("(and #t #t #t)")
        assert result is True

    @pytest.mark.skipif(
        not AIFPLWasmCompiler()._check_wasmtime(),
        reason="wasmtime not available"
    )
    def test_and_false(self, compiler):
        """Test and with one false."""
        result = compiler.compile_and_run("(and #t #f #t)")
        assert result is False

    @pytest.mark.skipif(
        not AIFPLWasmCompiler()._check_wasmtime(),
        reason="wasmtime not available"
    )
    def test_or_true(self, compiler):
        """Test or with one true."""
        result = compiler.compile_and_run("(or #f #t #f)")
        assert result is True

    @pytest.mark.skipif(
        not AIFPLWasmCompiler()._check_wasmtime(),
        reason="wasmtime not available"
    )
    def test_or_false(self, compiler):
        """Test or with all false."""
        result = compiler.compile_and_run("(or #f #f #f)")
        assert result is False

    @pytest.mark.skipif(
        not AIFPLWasmCompiler()._check_wasmtime(),
        reason="wasmtime not available"
    )
    def test_not_true(self, compiler):
        """Test not of true."""
        result = compiler.compile_and_run("(not #t)")
        assert result is False

    @pytest.mark.skipif(
        not AIFPLWasmCompiler()._check_wasmtime(),
        reason="wasmtime not available"
    )
    def test_not_false(self, compiler):
        """Test not of false."""
        result = compiler.compile_and_run("(not #f)")
        assert result is True


class TestWasmComplexExpressions:
    """Tests for complex nested expressions."""

    @pytest.fixture
    def compiler(self):
        return AIFPLWasmCompiler()

    @pytest.mark.skipif(
        not AIFPLWasmCompiler()._check_wasmtime(),
        reason="wasmtime not available"
    )
    def test_factorial_iterative(self, compiler):
        """Test factorial computation using iteration."""
        # factorial(5) = 120
        result = compiler.compile_and_run("""
            (let ((fact (lambda (n)
                          (let ((result 1)
                                (i n))
                            (* result n (- n 1) (- n 2) (- n 3) (- n 4))))))
              (fact 5))
        """)
        # (5 * 4 * 3 * 2 * 1) = 120
        assert result == 120

    @pytest.mark.skipif(
        not AIFPLWasmCompiler()._check_wasmtime(),
        reason="wasmtime not available"
    )
    def test_nested_let(self, compiler):
        """Test deeply nested let expressions."""
        result = compiler.compile_and_run("""
            (let ((a 1))
              (let ((b (+ a 1)))
                (let ((c (+ b 1)))
                  (let ((d (+ c 1)))
                    (+ a b c d)))))
        """)
        # 1 + 2 + 3 + 4 = 10
        assert result == 10

    @pytest.mark.skipif(
        not AIFPLWasmCompiler()._check_wasmtime(),
        reason="wasmtime not available"
    )
    def test_conditional_chain(self, compiler):
        """Test chained conditionals."""
        result = compiler.compile_and_run("""
            (let ((x 15))
              (if (< x 10)
                  1
                  (if (< x 20)
                      2
                      3)))
        """)
        assert result == 2

    @pytest.mark.skipif(
        not AIFPLWasmCompiler()._check_wasmtime(),
        reason="wasmtime not available"
    )
    def test_complex_arithmetic(self, compiler):
        """Test complex arithmetic expression."""
        result = compiler.compile_and_run("(+ (* 2 3) (/ 12 4) (- 10 5) (% 17 5))")
        # 6 + 3 + 5 + 2 = 16
        assert result == 16
