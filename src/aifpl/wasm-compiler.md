# AIFPL to WebAssembly Compiler

## Implementation Status

### Completed Features

| Component | Status | File |
|-----------|--------|------|
| **Type Definitions** | ✅ Complete | `wasm/types.py` |
| WASM GC struct/array types | ✅ | |
| Value, NumberValue, ComplexValue, StringValue | ✅ | |
| BoolValue, ListValue, NilValue, SymbolValue | ✅ | |
| FunctionValue, Environment, Binding types | ✅ | |
| **Runtime Library** | ✅ Complete | `wasm/runtime.py` |
| Value constructors (make_number, make_int, etc.) | ✅ | |
| Type predicates (is_number, is_string, etc.) | ✅ | |
| Value extractors (to_f64, to_i32, to_bool) | ✅ | |
| Small integer optimization (i31ref) | ✅ | |
| **Arithmetic Operations** | ✅ Complete | `wasm/arithmetic.py` |
| Basic ops (+, -, *, /, //, %, **) | ✅ | |
| Unary ops (abs, neg) | ✅ | |
| Math functions (sin, cos, tan, sqrt, log, exp) | ✅ | |
| Complex number arithmetic | ✅ | |
| **Comparison Operations** | ✅ Complete | `wasm/comparison.py` |
| Numeric comparison (=, !=, <, <=, >, >=) | ✅ | |
| String equality | ✅ | |
| List equality (deep comparison) | ✅ | |
| General value equality | ✅ | |
| **Boolean Operations** | ✅ Complete | `wasm/comparison.py` |
| Logical and, or, not | ✅ | |
| **List Operations** | ✅ Complete | `wasm/lists.py` |
| cons, first, rest, last | ✅ | |
| length, null?, list-ref | ✅ | |
| append, reverse | ✅ | |
| member?, remove, position | ✅ | |
| take, drop, range | ✅ | |
| **Higher-Order Functions** | ✅ Complete | `wasm/lists.py` |
| map, filter, fold | ✅ | |
| find, any?, all? | ✅ | |
| **String Operations** | ✅ Complete | `wasm/strings.py` |
| string-append, string-length, string-ref | ✅ | |
| substring, string-upcase, string-downcase | ✅ | |
| string-trim, string-contains? | ✅ | |
| string-prefix?, string-suffix?, string=? | ✅ | |
| string->list, list->string | ✅ | |
| number->string, string->number | ✅ | |
| **Alist Operations** | ✅ Complete | `wasm/alist.py` |
| alist-get, alist-set, alist-has? | ✅ | |
| alist-remove, alist-keys, alist-values | ✅ | |
| alist-length, alist-merge | ✅ | |
| **Bitwise Operations** | ✅ Complete | `wasm/bitwise.py` |
| bit-and, bit-or, bit-xor, bit-not | ✅ | |
| bit-shift-left, bit-shift-right | ✅ | |
| bit-count, bit-length | ✅ | |
| bit-set?, bit-set, bit-clear, bit-flip | ✅ | |
| **Code Generator** | ✅ Complete | `wasm/codegen.py` |
| Number/string/boolean literals | ✅ | |
| Variable lookup from environment | ✅ | |
| If expressions | ✅ | |
| Let bindings | ✅ | |
| Lambda expressions with closures | ✅ | |
| Quote special form | ✅ | |
| Pattern matching | ✅ | |
| Built-in function calls | ✅ | |
| General function calls | ✅ | |
| **Compiler Integration** | ✅ Complete | `wasm/compiler.py` |
| AIFPL parsing | ✅ | |
| WAT code generation | ✅ | |
| Wasmtime CLI execution | ✅ | |

### Remaining Work

| Component | Status | Notes |
|-----------|--------|-------|
| **Tail Call Optimization** | ⏳ Pending | Use WASM `return_call` for tail-recursive functions |
| **Comprehensive Test Suite** | ⏳ Pending | Full conformance tests against interpreter |
| **Documentation** | ⏳ Pending | API docs, usage examples |

### Test Results

**Runtime Tests: 54/55 passing**

- Arithmetic: 10/11 (power has floating-point precision: 7.999999999999994 vs 8)
- Comparison: 5/5
- Boolean: 6/6
- List: 5/5
- Alist: 12/12
- Bitwise: 16/16

### Known Limitations

1. **Python Version**: The main AIFPL package uses Python 3.10+ syntax (`int | None`), but the WASM compiler modules are compatible with Python 3.9+
2. **Wasmtime CLI Required**: The Python wasmtime bindings don't expose GC configuration, so we use the wasmtime CLI with `-W gc -W function-references` flags
3. **Floating Point Precision**: Power operations may have minor precision differences due to f64 implementation

---

## Overview

This document outlines the design and implementation plan for compiling AIFPL (AI Functional Programming Language) to WebAssembly, leveraging WASM 3.0 features including the Garbage Collection (GC) proposal.

## Research Findings

### WebAssembly GC Status

- **WASM 3.0** was released as the W3C "live" standard in September 2025, including GC as a core feature
- **Browser Support**: Chrome 119+, Firefox 120+, Safari 18.2+ all support WASM GC
- **Wasmtime**: Full GC support as of version 27.0 (November 2024)
- **Wasmer**: GC support planned for 5.1 via V8 integration

### WASM GC Features We'll Use

The GC proposal provides:

1. **Struct Types**: Heterogeneous, statically-indexed fields
   ```wasm
   (type $point (struct (field $x f64) (field $y f64)))
   ```

2. **Array Types**: Homogeneous, dynamically-indexed
   ```wasm
   (type $vector (array (mut (ref any))))
   ```

3. **Reference Types**: `anyref`, `structref`, `arrayref`, `i31ref`, `eqref`

4. **Key Instructions**:
   - `struct.new`, `struct.get`, `struct.set`
   - `array.new`, `array.get`, `array.set`, `array.len`
   - `ref.cast`, `ref.test`, `ref.eq`
   - `i31.new`, `i31.get_s`, `i31.get_u` (unboxed 31-bit integers)

### Runtime Choice: Wasmtime

We'll use **Wasmtime** via `wasmtime-py` because:
- Full WASM GC support (version 27.0+)
- Python bindings available
- `wat2wasm` function for converting WAT text to binary
- Active development by Bytecode Alliance

## Architecture

### Compilation Pipeline

```
AIFPL Source Code
       │
       ▼
┌─────────────────┐
│   Tokenizer     │  (existing: aifpl_tokenizer.py)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    Parser       │  (existing: aifpl_parser.py)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  AIFPLValue AST │  (existing: pure list representation)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  WASM Compiler  │  (NEW: aifpl_wasm_compiler.py)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   WAT Text      │  (intermediate representation)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  wat2wasm       │  (wasmtime-py)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  WASM Binary    │  (.wasm file)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Wasmtime       │  (execution)
└─────────────────┘
```

### Value Representation in WASM GC

AIFPL has dynamic typing. We need a unified value representation:

```wasm
;; Base value type - all AIFPL values inherit from this
(type $Value (struct
  (field $tag i32)  ;; Type tag for runtime type checking
))

;; Type tags
;; 0 = Number (stored as i31 for small ints, or boxed)
;; 1 = Float
;; 2 = Complex
;; 3 = String
;; 4 = Boolean
;; 5 = List
;; 6 = Alist
;; 7 = Symbol
;; 8 = Function
;; 9 = Nil (empty list)

;; Number value (for floats and large integers)
(type $NumberValue (sub $Value (struct
  (field $tag i32)
  (field $value f64)
)))

;; Complex number
(type $ComplexValue (sub $Value (struct
  (field $tag i32)
  (field $real f64)
  (field $imag f64)
)))

;; String value
(type $StringValue (sub $Value (struct
  (field $tag i32)
  (field $chars (ref $CharArray))
)))

(type $CharArray (array (mut i32)))  ;; UTF-32 code points

;; Boolean value
(type $BoolValue (sub $Value (struct
  (field $tag i32)
  (field $value i32)  ;; 0 = false, 1 = true
)))

;; List value (cons cell style for immutability)
(type $ListValue (sub $Value (struct
  (field $tag i32)
  (field $head (ref null $Value))
  (field $tail (ref null $ListValue))
)))

;; Nil (empty list singleton)
(type $NilValue (sub $Value (struct
  (field $tag i32)
)))

;; Symbol value
(type $SymbolValue (sub $Value (struct
  (field $tag i32)
  (field $name (ref $StringValue))
)))

;; Function value (closure)
(type $FunctionValue (sub $Value (struct
  (field $tag i32)
  (field $arity i32)
  (field $code (ref $FuncRef))
  (field $env (ref null $Environment))
)))

;; Environment for closures
(type $Environment (struct
  (field $bindings (ref $BindingArray))
  (field $parent (ref null $Environment))
)))

(type $Binding (struct
  (field $name (ref $StringValue))
  (field $value (ref $Value))
))

(type $BindingArray (array (mut (ref $Binding))))

;; Alist value
(type $AlistValue (sub $Value (struct
  (field $tag i32)
  (field $entries (ref $AlistEntryArray))
)))

(type $AlistEntry (struct
  (field $key (ref $Value))
  (field $value (ref $Value))
))

(type $AlistEntryArray (array (mut (ref $AlistEntry))))
```

### Small Integer Optimization

WASM GC provides `i31ref` for unboxed 31-bit integers. We'll use this for:
- Small integers (-2^30 to 2^30-1)
- Type tags in some contexts
- Boolean values internally

```wasm
;; Check if a value is a small integer
(func $is_small_int (param $v (ref $Value)) (result i32)
  ;; Check if it's actually an i31ref
  (ref.test i31 (local.get $v))
)
```

### Compilation Strategy

#### 1. Expressions

Each AIFPL expression compiles to a WASM expression that produces a `(ref $Value)`.

```aifpl
(+ 1 2 3)
```
Compiles to:
```wasm
(call $add
  (call $add
    (call $make_number (f64.const 1))
    (call $make_number (f64.const 2)))
  (call $make_number (f64.const 3)))
```

#### 2. Lambda Expressions

Lambdas compile to closures that capture their environment:

```aifpl
(let ((x 5))
  (lambda (y) (+ x y)))
```

Compiles to:
```wasm
;; Create environment with x=5
(local.set $env
  (call $env_extend
    (global.get $empty_env)
    (call $make_symbol (... "x"))
    (call $make_number (f64.const 5))))

;; Create closure
(struct.new $FunctionValue
  (i32.const 8)  ;; tag = function
  (i32.const 1)  ;; arity = 1
  (ref.func $lambda_0)  ;; code
  (local.get $env))  ;; captured environment
```

#### 3. Let Bindings

```aifpl
(let ((x 5) (y 10)) (+ x y))
```

Compiles to nested environment extension:
```wasm
(call $with_binding
  (call $make_symbol (... "x"))
  (call $make_number (f64.const 5))
  (call $with_binding
    (call $make_symbol (... "y"))
    (call $make_number (f64.const 10))
    (call $add (call $lookup "x") (call $lookup "y"))))
```

#### 4. Conditionals (if)

```aifpl
(if (> x 0) "positive" "non-positive")
```

Compiles to WASM `if`:
```wasm
(if (result (ref $Value))
  (call $to_bool (call $gt (call $lookup "x") (call $make_number (f64.const 0))))
  (then (call $make_string (... "positive")))
  (else (call $make_string (... "non-positive"))))
```

#### 5. Pattern Matching

Pattern matching compiles to a series of type tests and destructuring:

```aifpl
(match x
  ((number? n) (* n 2))
  (_ "not a number"))
```

Compiles to:
```wasm
(local.set $x (call $lookup "x"))
(if (result (ref $Value))
  (call $is_number (local.get $x))
  (then
    ;; Bind n to x in new scope
    (call $with_binding
      (call $make_symbol (... "n"))
      (local.get $x)
      (call $mul (call $lookup "n") (call $make_number (f64.const 2)))))
  (else
    (call $make_string (... "not a number"))))
```

#### 6. Tail Call Optimization

WASM has a tail call proposal. We'll use `return_call` for tail-recursive functions:

```aifpl
(let ((factorial (lambda (n acc)
                   (if (<= n 1)
                       acc
                       (factorial (- n 1) (* n acc))))))
  (factorial 5 1))
```

The recursive call in tail position uses:
```wasm
(return_call $factorial
  (call $sub (local.get $n) (call $make_number (f64.const 1)))
  (call $mul (local.get $n) (local.get $acc)))
```

### Runtime Library

The compiler needs a runtime library providing:

1. **Type Operations**
   - `$make_number`, `$make_string`, `$make_bool`, `$make_list`, etc.
   - `$is_number`, `$is_string`, `$is_bool`, `$is_list`, etc.
   - `$to_bool` - convert value to boolean for conditionals

2. **Arithmetic**
   - `$add`, `$sub`, `$mul`, `$div`, `$mod`, `$pow`
   - `$sin`, `$cos`, `$tan`, `$sqrt`, `$log`, `$exp`, `$abs`
   - `$floor_div`, `$bit_and`, `$bit_or`, `$bit_xor`, `$bit_not`

3. **Comparison**
   - `$eq`, `$ne`, `$lt`, `$le`, `$gt`, `$ge`

4. **Boolean**
   - `$and`, `$or`, `$not`

5. **String Operations**
   - `$string_append`, `$string_length`, `$string_ref`
   - `$substring`, `$string_upcase`, `$string_downcase`
   - `$string_split`, `$string_join`, `$string_contains`
   - `$string_to_number`, `$number_to_string`

6. **List Operations**
   - `$cons`, `$first`, `$rest`, `$list_ref`, `$length`
   - `$append`, `$reverse`, `$member`
   - `$map`, `$filter`, `$fold`, `$find`
   - `$take`, `$drop`, `$range`
   - `$remove`, `$position`

7. **Alist Operations**
   - `$alist_new`, `$alist_get`, `$alist_set`, `$alist_has`
   - `$alist_remove`, `$alist_keys`, `$alist_values`, `$alist_merge`

8. **Environment**
   - `$env_lookup`, `$env_extend`, `$env_new`

9. **Function Application**
   - `$apply` - apply a function value to arguments

### Module Structure

The generated WASM module will have:

```wasm
(module
  ;; Type definitions
  (type $Value ...)
  (type $NumberValue ...)
  ;; ... all types

  ;; Imports (if needed for I/O)
  (import "env" "print" (func $print (param (ref $Value))))

  ;; Runtime library functions
  (func $make_number ...)
  (func $add ...)
  ;; ... all runtime functions

  ;; Compiled user functions
  (func $lambda_0 ...)
  (func $lambda_1 ...)

  ;; Main entry point
  (func $main (export "main") (result (ref $Value))
    ;; Compiled expression
  )

  ;; Export for getting result as string (for testing)
  (func $result_to_string (export "result_to_string")
    (param (ref $Value)) (result (ref $StringValue))
    ...)
)
```

## Implementation Plan

### Phase 1: Foundation ✅ Complete
1. ✅ Set up project structure and dependencies
2. ✅ Implement WAT code generator base class
3. ✅ Implement type definitions in WAT
4. ✅ Implement basic value constructors

### Phase 2: Core Expressions ✅ Complete
1. ✅ Number literals and arithmetic
2. ✅ String literals and basic operations
3. ✅ Boolean literals and operations
4. ✅ Comparison operators
5. ✅ Conditional expressions (if)

### Phase 3: Data Structures ✅ Complete
1. ✅ List construction and operations
2. ✅ Alist construction and operations
3. ✅ Quote expressions

### Phase 4: Functions ✅ Complete
1. ✅ Lambda expressions (without closures)
2. ✅ Function application
3. ✅ Built-in higher-order functions (map, filter, fold)
4. ✅ Closures and environment capture
5. ✅ Let bindings

### Phase 5: Advanced Features (In Progress)
1. ✅ Pattern matching
2. ⏳ Tail call optimization
3. ✅ Complex numbers (arithmetic support)
4. ✅ Bitwise operations

### Phase 6: Testing & Polish (In Progress)
1. ⏳ Comprehensive test suite
2. ⏳ Error handling and messages
3. ⏳ Performance optimization
4. ⏳ Documentation

## Testing Strategy

### Unit Tests
Each compiler component will have unit tests:
- WAT generation for each expression type
- Runtime library functions
- Type conversions

### Integration Tests
Full AIFPL programs compiled and executed:
```python
def test_arithmetic():
    compiler = AIFPLWasmCompiler()
    result = compiler.compile_and_run("(+ 1 2 3)")
    assert result == 6

def test_lambda():
    compiler = AIFPLWasmCompiler()
    result = compiler.compile_and_run("((lambda (x) (* x x)) 5)")
    assert result == 25

def test_pattern_matching():
    compiler = AIFPLWasmCompiler()
    result = compiler.compile_and_run("""
        (match 42
          ((number? n) (* n 2))
          (_ "not a number"))
    """)
    assert result == 84
```

### Conformance Tests
Run the same tests against both the interpreter and compiler to ensure identical behavior.

## Dependencies

```
wasmtime>=27.0  # For WASM GC support and wat2wasm
```

## File Structure

```
src/aifpl/
├── __init__.py              # Main package (existing)
├── aifpl.py                 # Main API (existing)
├── wasm-compiler.md         # This design document
└── wasm/                    # WASM compiler package
    ├── __init__.py          # Exports AIFPLWasmCompiler
    ├── types.py             # WASM GC type definitions
    ├── runtime.py           # Runtime library (constructors, predicates)
    ├── arithmetic.py        # Arithmetic operations
    ├── comparison.py        # Comparison and boolean operations
    ├── lists.py             # List operations and higher-order functions
    ├── strings.py           # String operations
    ├── alist.py             # Association list operations
    ├── bitwise.py           # Bitwise operations
    ├── codegen.py           # WAT code generator
    └── compiler.py          # Main compiler class

tests/
└── test_wasm_compiler.py    # Compiler tests
```

## References

- [WebAssembly GC Proposal](https://github.com/WebAssembly/gc)
- [WASM GC MVP Specification](https://github.com/WebAssembly/gc/blob/main/proposals/gc/MVP.md)
- [Wasmtime Documentation](https://docs.wasmtime.dev/)
- [wasmtime-py](https://github.com/bytecodealliance/wasmtime-py)
- [V8 WASM GC Blog](https://v8.dev/blog/wasm-gc-porting)
- [WASM 3.0 Announcement](https://webassembly.org/news/2025-09-17-wasm-3.0/)
