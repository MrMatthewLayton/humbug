"""AIFPL to WebAssembly Compiler.

This module provides the main compiler class that compiles AIFPL expressions
to WebAssembly using the GC proposal.
"""

from typing import Any, Optional, Union

from aifpl.aifpl_tokenizer import AIFPLTokenizer
from aifpl.aifpl_parser import AIFPLParser
from aifpl.aifpl_value import AIFPLValue

from aifpl.wasm.types import TYPE_DEFINITIONS_WAT
from aifpl.wasm.runtime import RUNTIME_LIBRARY_WAT
from aifpl.wasm.arithmetic import ARITHMETIC_LIBRARY_WAT
from aifpl.wasm.comparison import COMPARISON_LIBRARY_WAT
from aifpl.wasm.lists import LIST_LIBRARY_WAT
from aifpl.wasm.strings import STRING_LIBRARY_WAT
from aifpl.wasm.codegen import CodeGenerator


class AIFPLWasmCompiler:
    """Compiles AIFPL expressions to WebAssembly.

    This compiler generates WASM modules using the GC proposal for
    automatic memory management of AIFPL values.

    Example:
        compiler = AIFPLWasmCompiler()
        result = compiler.compile_and_run("(+ 1 2 3)")
        assert result == 6
    """

    def __init__(self):
        """Initialize the AIFPL WASM compiler."""
        self._wasmtime_available = None

    def _check_wasmtime(self) -> bool:
        """Check if wasmtime is available."""
        if self._wasmtime_available is None:
            try:
                import wasmtime
                self._wasmtime_available = True
            except ImportError:
                self._wasmtime_available = False
        return self._wasmtime_available

    def parse(self, expression: str) -> AIFPLValue:
        """Parse an AIFPL expression string to AST.

        Args:
            expression: AIFPL expression string

        Returns:
            Parsed AIFPLValue AST
        """
        tokenizer = AIFPLTokenizer()
        tokens = tokenizer.tokenize(expression)
        parser = AIFPLParser(tokens, expression)
        return parser.parse()

    def compile_to_wat(self, expression: str) -> str:
        """Compile an AIFPL expression to WAT (WebAssembly Text Format).

        Args:
            expression: AIFPL expression string

        Returns:
            WAT code as a string
        """
        ast = self.parse(expression)
        return self._generate_module(ast)

    def _generate_module(self, ast: AIFPLValue) -> str:
        """Generate a complete WASM module from an AST.

        Args:
            ast: Parsed AIFPL expression

        Returns:
            Complete WAT module code
        """
        codegen = CodeGenerator()

        # Generate code for the main expression
        main_code = codegen.generate_expr(ast, set())

        # Collect all generated lambda functions
        lambda_functions = "\n".join(codegen.functions)

        # Build the complete module
        module = f"""\
(module
{TYPE_DEFINITIONS_WAT}

{RUNTIME_LIBRARY_WAT}

{ARITHMETIC_LIBRARY_WAT}

{COMPARISON_LIBRARY_WAT}

{LIST_LIBRARY_WAT}

{STRING_LIBRARY_WAT}

{self._generate_environment_functions()}

{lambda_functions}

  ;; Main entry point
  (func $main (export "main") (result (ref null eq))
    (local $env (ref null $Environment))
    (local.set $env (global.get $EMPTY_ENV))
    {main_code}
  )

  ;; Helper to get result tag for external inspection
  (func $get_result_tag (export "get_result_tag") (param $v (ref null eq)) (result i32)
    (call $get_tag (local.get $v))
  )

  ;; Helper to get numeric result
  (func $get_result_number (export "get_result_number") (param $v (ref null eq)) (result f64)
    (call $to_f64 (local.get $v))
  )

  ;; Helper to check if result is true
  (func $get_result_bool (export "get_result_bool") (param $v (ref null eq)) (result i32)
    (if (result i32)
      (call $is_boolean (local.get $v))
      (then (struct.get $BoolValue $value (ref.cast (ref $BoolValue) (local.get $v))))
      (else (i32.const -1))  ;; Not a boolean
    )
  )
)
"""
        return module

    def _generate_environment_functions(self) -> str:
        """Generate WAT code for environment management."""
        return """\
  ;; ============================================
  ;; Environment Functions
  ;; ============================================

  ;; Look up a variable in the environment
  (func $env_lookup (param $env (ref null $Environment)) (param $name (ref $StringValue)) (result (ref null eq))
    (local $current (ref null $Environment))
    (local $bindings (ref $BindingArray))
    (local $len i32)
    (local $i i32)
    (local $binding (ref null $Binding))

    (local.set $current (local.get $env))

    (block $found (result (ref null eq))
      (loop $env_loop
        ;; Check if we've reached the end of the environment chain
        (br_if $found (ref.is_null (local.get $current))
          (ref.null eq))

        ;; Search bindings in current frame
        (local.set $bindings
          (struct.get $Environment $bindings
            (ref.as_non_null (local.get $current))))
        (local.set $len (array.len (local.get $bindings)))
        (local.set $i (i32.const 0))

        (block $next_frame
          (loop $binding_loop
            (br_if $next_frame (i32.ge_s (local.get $i) (local.get $len)))

            (local.set $binding (array.get $BindingArray (local.get $bindings) (local.get $i)))

            (if (ref.is_null (local.get $binding))
              (then
                (local.set $i (i32.add (local.get $i) (i32.const 1)))
                (br $binding_loop)
              )
            )

            ;; Check if name matches
            (if (call $string_eq
                  (struct.get $Binding $name (ref.as_non_null (local.get $binding)))
                  (local.get $name))
              (then
                (br $found
                  (struct.get $Binding $value (ref.as_non_null (local.get $binding))))
              )
            )

            (local.set $i (i32.add (local.get $i) (i32.const 1)))
            (br $binding_loop)
          )
        )

        ;; Move to parent environment
        (local.set $current
          (struct.get $Environment $parent
            (ref.as_non_null (local.get $current))))
        (br $env_loop)
      )
    )
  )

  ;; Extend environment with a new binding
  (func $env_extend
    (param $env (ref null $Environment))
    (param $name (ref $StringValue))
    (param $value (ref null eq))
    (result (ref $Environment))

    (local $new_bindings (ref $BindingArray))
    (local $binding (ref $Binding))

    ;; Create new binding
    (local.set $binding
      (struct.new $Binding
        (local.get $name)
        (local.get $value)))

    ;; Create new bindings array with just this binding
    (local.set $new_bindings
      (array.new $BindingArray (ref.null $Binding) (i32.const 1)))
    (array.set $BindingArray (local.get $new_bindings) (i32.const 0) (local.get $binding))

    ;; Create new environment frame
    (struct.new $Environment
      (local.get $new_bindings)
      (local.get $env))
  )
"""

    def compile(self, expression: str) -> bytes:
        """Compile an AIFPL expression to WASM binary.

        Args:
            expression: AIFPL expression string

        Returns:
            WASM binary as bytes

        Raises:
            ImportError: If wasmtime is not installed
        """
        if not self._check_wasmtime():
            raise ImportError(
                "wasmtime is required for WASM compilation. "
                "Install it with: pip install 'wasmtime>=27.0'"
            )

        import wasmtime

        wat_code = self.compile_to_wat(expression)
        return wasmtime.wat2wasm(wat_code)

    def compile_and_run(self, expression: str) -> Any:
        """Compile and execute an AIFPL expression.

        Uses the wasmtime CLI with GC support since the Python bindings
        don't yet expose the GC configuration option.

        Args:
            expression: AIFPL expression string

        Returns:
            The result of evaluating the expression, converted to Python types

        Raises:
            RuntimeError: If wasmtime CLI is not available or execution fails
        """
        import subprocess
        import tempfile
        import os

        # Generate WAT code that exports a compute function returning f64
        ast = self.parse(expression)
        wat_code = self._generate_compute_module(ast)

        # Write WAT to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.wat', delete=False) as f:
            f.write(wat_code)
            wat_file = f.name

        try:
            # Find wasmtime CLI
            wasmtime_paths = [
                os.path.expanduser("~/.wasmtime/bin/wasmtime"),
                "/usr/local/bin/wasmtime",
                "wasmtime"
            ]

            wasmtime_cmd = None
            for path in wasmtime_paths:
                try:
                    result = subprocess.run(
                        [path, "--version"],
                        capture_output=True,
                        timeout=5
                    )
                    if result.returncode == 0:
                        wasmtime_cmd = path
                        break
                except (FileNotFoundError, subprocess.TimeoutExpired):
                    continue

            if wasmtime_cmd is None:
                raise RuntimeError(
                    "wasmtime CLI not found. Install it with: "
                    "curl https://wasmtime.dev/install.sh -sSf | bash"
                )

            # Run with GC and function-references enabled
            result = subprocess.run(
                [wasmtime_cmd, "run", "-W", "gc", "-W", "function-references", "--invoke", "compute", wat_file],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                raise RuntimeError(f"WASM execution failed: {result.stderr}")

            # Parse the result
            output = result.stdout.strip()

            # Handle different result types based on the output
            if output == "true":
                return True
            elif output == "false":
                return False
            elif output == "()":
                return []
            else:
                # Try to parse as number
                try:
                    if '.' in output or 'e' in output.lower():
                        val = float(output)
                    else:
                        val = float(output)
                        if val == int(val):
                            return int(val)
                        return val
                    return val
                except ValueError:
                    return output

        finally:
            # Clean up temp file
            os.unlink(wat_file)

    def _generate_compute_module(self, ast: AIFPLValue) -> str:
        """Generate a WASM module with a compute function that returns f64.

        This is used for CLI-based execution where we need to extract
        the numeric result.
        """
        codegen = CodeGenerator()

        # Generate code for the main expression
        main_code = codegen.generate_expr(ast, set())

        # Collect all generated lambda functions
        lambda_functions = "\n".join(codegen.functions)

        # Build the complete module with compute export
        module = f"""\
(module
{TYPE_DEFINITIONS_WAT}

{RUNTIME_LIBRARY_WAT}

{ARITHMETIC_LIBRARY_WAT}

{COMPARISON_LIBRARY_WAT}

{LIST_LIBRARY_WAT}

{STRING_LIBRARY_WAT}

{self._generate_environment_functions()}

{lambda_functions}

  ;; Compute function that returns f64 for CLI output
  (func $compute (export "compute") (result f64)
    (local $env (ref null $Environment))
    (local $result (ref null eq))

    (local.set $env (global.get $EMPTY_ENV))
    (local.set $result {main_code})

    ;; Convert result to f64
    ;; For now, assume numeric result
    (call $to_f64 (local.get $result))
  )

  ;; Main entry point (returns the value directly)
  (func $main (export "main") (result (ref null eq))
    (local $env (ref null $Environment))
    (local.set $env (global.get $EMPTY_ENV))
    {main_code}
  )

  ;; Helper to get result tag for external inspection
  (func $get_result_tag (export "get_result_tag") (param $v (ref null eq)) (result i32)
    (call $get_tag (local.get $v))
  )

  ;; Helper to get numeric result
  (func $get_result_number (export "get_result_number") (param $v (ref null eq)) (result f64)
    (call $to_f64 (local.get $v))
  )

  ;; Helper to check if result is true
  (func $get_result_bool (export "get_result_bool") (param $v (ref null eq)) (result i32)
    (if (result i32)
      (call $is_boolean (local.get $v))
      (then (struct.get $BoolValue $value (ref.cast (ref $BoolValue) (local.get $v))))
      (else (i32.const -1))  ;; Not a boolean
    )
  )
)
"""
        return module

    def _convert_result(self, store, instance, result, tag: int) -> Any:
        """Convert a WASM result to a Python value.

        Args:
            store: Wasmtime store
            instance: Module instance
            result: The externref result
            tag: Type tag

        Returns:
            Python value
        """
        # Type tags from types.py
        TAG_NUMBER = 0
        TAG_SMALL_INT = 1
        TAG_COMPLEX = 2
        TAG_STRING = 3
        TAG_BOOLEAN = 4
        TAG_LIST = 5
        TAG_NIL = 6

        if tag == TAG_NUMBER or tag == TAG_SMALL_INT:
            get_number = instance.exports(store)["get_result_number"]
            value = get_number(store, result)
            # Check if it's an integer
            if value == int(value):
                return int(value)
            return value

        elif tag == TAG_BOOLEAN:
            get_bool = instance.exports(store)["get_result_bool"]
            value = get_bool(store, result)
            return value == 1

        elif tag == TAG_NIL:
            return []

        # For other types, we need more complex handling
        # TODO: Implement string, list, complex extraction

        return result  # Return raw for now


# Convenience function
def compile_aifpl(expression: str) -> bytes:
    """Compile an AIFPL expression to WASM binary.

    Args:
        expression: AIFPL expression string

    Returns:
        WASM binary as bytes
    """
    compiler = AIFPLWasmCompiler()
    return compiler.compile(expression)


def run_aifpl(expression: str) -> Any:
    """Compile and run an AIFPL expression.

    Args:
        expression: AIFPL expression string

    Returns:
        The result of evaluating the expression
    """
    compiler = AIFPLWasmCompiler()
    return compiler.compile_and_run(expression)
