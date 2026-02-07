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
