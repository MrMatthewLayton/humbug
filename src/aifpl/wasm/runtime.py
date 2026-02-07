"""WASM runtime library for AIFPL.

This module generates WAT code for the runtime library functions
that implement AIFPL operations in WebAssembly.
"""


def generate_value_constructors() -> str:
    """Generate WAT functions for creating AIFPL values."""
    return """\
  ;; ============================================
  ;; Value Constructors
  ;; ============================================

  ;; Create a number value from f64
  (func $make_number (param $value f64) (result (ref eq))
    ;; Check if it's a small integer that fits in i31
    (if (result (ref eq))
      (i32.and
        (f64.eq (local.get $value) (f64.trunc (local.get $value)))  ;; Is integer?
        (i32.and
          (f64.ge (local.get $value) (f64.const -1073741824))  ;; >= -2^30
          (f64.le (local.get $value) (f64.const 1073741823))   ;; <= 2^30-1
        )
      )
      (then
        ;; Use i31ref for small integers
        (ref.i31 (i32.trunc_f64_s (local.get $value)))
      )
      (else
        ;; Box as NumberValue
        (struct.new $NumberValue
          (global.get $TAG_NUMBER)
          (local.get $value))
      )
    )
  )

  ;; Create a number from i32 (for literals)
  (func $make_int (param $value i32) (result (ref eq))
    ;; Check if it fits in i31 (30-bit signed range)
    (if (result (ref eq))
      (i32.and
        (i32.ge_s (local.get $value) (i32.const -1073741824))
        (i32.le_s (local.get $value) (i32.const 1073741823))
      )
      (then
        (ref.i31 (local.get $value))
      )
      (else
        (struct.new $NumberValue
          (global.get $TAG_NUMBER)
          (f64.convert_i32_s (local.get $value)))
      )
    )
  )

  ;; Create a float value (always boxed)
  (func $make_float (param $value f64) (result (ref $NumberValue))
    (struct.new $NumberValue
      (global.get $TAG_NUMBER)
      (local.get $value))
  )

  ;; Create a complex number
  (func $make_complex (param $real f64) (param $imag f64) (result (ref eq))
    ;; If imaginary part is negligible, return real number
    (if (result (ref eq))
      (f64.lt (f64.abs (local.get $imag)) (f64.const 1e-10))
      (then
        (call $make_number (local.get $real))
      )
      (else
        (struct.new $ComplexValue
          (global.get $TAG_COMPLEX)
          (local.get $real)
          (local.get $imag))
      )
    )
  )

  ;; Create a boolean value
  (func $make_bool (param $value i32) (result (ref $BoolValue))
    (if (result (ref $BoolValue))
      (local.get $value)
      (then (global.get $TRUE))
      (else (global.get $FALSE))
    )
  )

  ;; Create a string from a character array
  (func $make_string (param $chars (ref $CharArray)) (result (ref $StringValue))
    (struct.new $StringValue
      (global.get $TAG_STRING)
      (array.len (local.get $chars))
      (local.get $chars))
  )

  ;; Create an empty string
  (func $make_empty_string (result (ref $StringValue))
    (struct.new $StringValue
      (global.get $TAG_STRING)
      (i32.const 0)
      (array.new $CharArray (i32.const 0) (i32.const 0)))
  )

  ;; Create a symbol
  (func $make_symbol (param $name (ref $StringValue)) (result (ref $SymbolValue))
    (struct.new $SymbolValue
      (global.get $TAG_SYMBOL)
      (local.get $name))
  )

  ;; Create a cons cell (list node)
  (func $make_cons (param $head (ref null eq)) (param $tail (ref null eq)) (result (ref $ListValue))
    (struct.new $ListValue
      (global.get $TAG_LIST)
      (local.get $head)
      (local.get $tail))
  )

  ;; Get nil singleton
  (func $make_nil (result (ref $NilValue))
    (global.get $NIL)
  )

  ;; Create a function value (closure)
  (func $make_function
    (param $arity i32)
    (param $code (ref $UserFuncType))
    (param $env (ref null $Environment))
    (result (ref $FunctionValue))
    (struct.new $FunctionValue
      (global.get $TAG_FUNCTION)
      (local.get $arity)
      (local.get $code)
      (local.get $env))
  )

  ;; Create an alist
  (func $make_alist (param $entries (ref $AlistEntryArray)) (result (ref $AlistValue))
    (struct.new $AlistValue
      (global.get $TAG_ALIST)
      (local.get $entries))
  )

  ;; Create an empty alist
  (func $make_empty_alist (result (ref $AlistValue))
    (struct.new $AlistValue
      (global.get $TAG_ALIST)
      (array.new $AlistEntryArray (ref.null $AlistEntry) (i32.const 0)))
  )

  ;; Create an alist entry
  (func $make_alist_entry (param $key (ref null eq)) (param $value (ref null eq)) (result (ref $AlistEntry))
    (struct.new $AlistEntry
      (local.get $key)
      (local.get $value))
  )
"""


def generate_type_predicates() -> str:
    """Generate WAT functions for type checking."""
    return """\
  ;; ============================================
  ;; Type Predicates
  ;; ============================================

  ;; Get the type tag of a value
  (func $get_tag (param $v (ref null eq)) (result i32)
    (if (result i32)
      (ref.is_null (local.get $v))
      (then (global.get $TAG_NIL))
      (else
        (if (result i32)
          (ref.test i31ref (local.get $v))
          (then (global.get $TAG_SMALL_INT))
          (else
            (struct.get $Value $tag
              (ref.cast (ref $Value) (local.get $v)))
          )
        )
      )
    )
  )

  ;; Check if value is a number (int, float, or small int)
  (func $is_number (param $v (ref null eq)) (result i32)
    (local $tag i32)
    (local.set $tag (call $get_tag (local.get $v)))
    (i32.or
      (i32.eq (local.get $tag) (global.get $TAG_NUMBER))
      (i32.eq (local.get $tag) (global.get $TAG_SMALL_INT))
    )
  )

  ;; Check if value is an integer (whole number)
  (func $is_integer (param $v (ref null eq)) (result i32)
    (local $tag i32)
    (local.set $tag (call $get_tag (local.get $v)))
    (if (result i32)
      (i32.eq (local.get $tag) (global.get $TAG_SMALL_INT))
      (then (i32.const 1))
      (else
        (if (result i32)
          (i32.eq (local.get $tag) (global.get $TAG_NUMBER))
          (then
            ;; Check if the f64 is a whole number
            (f64.eq
              (struct.get $NumberValue $value (ref.cast (ref $NumberValue) (local.get $v)))
              (f64.trunc (struct.get $NumberValue $value (ref.cast (ref $NumberValue) (local.get $v)))))
          )
          (else (i32.const 0))
        )
      )
    )
  )

  ;; Check if value is a float
  (func $is_float (param $v (ref null eq)) (result i32)
    (local $tag i32)
    (local.set $tag (call $get_tag (local.get $v)))
    (i32.and
      (i32.eq (local.get $tag) (global.get $TAG_NUMBER))
      (i32.eqz (call $is_integer (local.get $v)))
    )
  )

  ;; Check if value is complex
  (func $is_complex (param $v (ref null eq)) (result i32)
    (i32.eq (call $get_tag (local.get $v)) (global.get $TAG_COMPLEX))
  )

  ;; Check if value is a string
  (func $is_string (param $v (ref null eq)) (result i32)
    (i32.eq (call $get_tag (local.get $v)) (global.get $TAG_STRING))
  )

  ;; Check if value is a boolean
  (func $is_boolean (param $v (ref null eq)) (result i32)
    (i32.eq (call $get_tag (local.get $v)) (global.get $TAG_BOOLEAN))
  )

  ;; Check if value is a list (including nil)
  (func $is_list (param $v (ref null eq)) (result i32)
    (local $tag i32)
    (local.set $tag (call $get_tag (local.get $v)))
    (i32.or
      (i32.eq (local.get $tag) (global.get $TAG_LIST))
      (i32.eq (local.get $tag) (global.get $TAG_NIL))
    )
  )

  ;; Check if value is nil (empty list)
  (func $is_nil (param $v (ref null eq)) (result i32)
    (i32.eq (call $get_tag (local.get $v)) (global.get $TAG_NIL))
  )

  ;; Check if value is a symbol
  (func $is_symbol (param $v (ref null eq)) (result i32)
    (i32.eq (call $get_tag (local.get $v)) (global.get $TAG_SYMBOL))
  )

  ;; Check if value is a function
  (func $is_function (param $v (ref null eq)) (result i32)
    (local $tag i32)
    (local.set $tag (call $get_tag (local.get $v)))
    (i32.or
      (i32.eq (local.get $tag) (global.get $TAG_FUNCTION))
      (i32.eq (local.get $tag) (global.get $TAG_BUILTIN))
    )
  )

  ;; Check if value is an alist
  (func $is_alist (param $v (ref null eq)) (result i32)
    (i32.eq (call $get_tag (local.get $v)) (global.get $TAG_ALIST))
  )

  ;; Convert value to boolean (for if conditions)
  ;; Only #t is true, #f is false. All other values cause error.
  (func $to_bool (param $v (ref null eq)) (result i32)
    (if (result i32)
      (call $is_boolean (local.get $v))
      (then
        (struct.get $BoolValue $value
          (ref.cast (ref $BoolValue) (local.get $v)))
      )
      (else
        ;; Type error - only booleans allowed in conditions
        (unreachable)
      )
    )
  )
"""


def generate_value_extractors() -> str:
    """Generate WAT functions for extracting values from AIFPL values."""
    return """\
  ;; ============================================
  ;; Value Extractors
  ;; ============================================

  ;; Get numeric value as f64
  (func $to_f64 (param $v (ref null eq)) (result f64)
    (local $tag i32)
    (local.set $tag (call $get_tag (local.get $v)))
    (if (result f64)
      (i32.eq (local.get $tag) (global.get $TAG_SMALL_INT))
      (then
        (f64.convert_i32_s (i31.get_s (ref.cast i31ref (local.get $v))))
      )
      (else
        (if (result f64)
          (i32.eq (local.get $tag) (global.get $TAG_NUMBER))
          (then
            (struct.get $NumberValue $value
              (ref.cast (ref $NumberValue) (local.get $v)))
          )
          (else
            ;; Type error
            (unreachable)
          )
        )
      )
    )
  )

  ;; Get numeric value as i32 (for small ints)
  (func $to_i32 (param $v (ref null eq)) (result i32)
    (local $tag i32)
    (local.set $tag (call $get_tag (local.get $v)))
    (if (result i32)
      (i32.eq (local.get $tag) (global.get $TAG_SMALL_INT))
      (then
        (i31.get_s (ref.cast i31ref (local.get $v)))
      )
      (else
        (if (result i32)
          (i32.eq (local.get $tag) (global.get $TAG_NUMBER))
          (then
            (i32.trunc_f64_s
              (struct.get $NumberValue $value
                (ref.cast (ref $NumberValue) (local.get $v))))
          )
          (else
            ;; Type error
            (unreachable)
          )
        )
      )
    )
  )

  ;; Get real part of a number (works for real and complex)
  (func $get_real (param $v (ref null eq)) (result f64)
    (local $tag i32)
    (local.set $tag (call $get_tag (local.get $v)))
    (if (result f64)
      (i32.eq (local.get $tag) (global.get $TAG_COMPLEX))
      (then
        (struct.get $ComplexValue $real
          (ref.cast (ref $ComplexValue) (local.get $v)))
      )
      (else
        (call $to_f64 (local.get $v))
      )
    )
  )

  ;; Get imaginary part of a number (0 for real numbers)
  (func $get_imag (param $v (ref null eq)) (result f64)
    (if (result f64)
      (i32.eq (call $get_tag (local.get $v)) (global.get $TAG_COMPLEX))
      (then
        (struct.get $ComplexValue $imag
          (ref.cast (ref $ComplexValue) (local.get $v)))
      )
      (else
        (f64.const 0)
      )
    )
  )

  ;; Get first element of a list
  (func $list_first (param $v (ref null eq)) (result (ref null eq))
    (if (result (ref null eq))
      (call $is_nil (local.get $v))
      (then
        ;; Error: first of empty list
        (unreachable)
      )
      (else
        (struct.get $ListValue $head
          (ref.cast (ref $ListValue) (local.get $v)))
      )
    )
  )

  ;; Get rest of a list
  (func $list_rest (param $v (ref null eq)) (result (ref null eq))
    (if (result (ref null eq))
      (call $is_nil (local.get $v))
      (then
        ;; Error: rest of empty list
        (unreachable)
      )
      (else
        (struct.get $ListValue $tail
          (ref.cast (ref $ListValue) (local.get $v)))
      )
    )
  )

  ;; Get length of a list
  (func $list_length (param $v (ref null eq)) (result i32)
    (local $count i32)
    (local $current (ref null eq))
    (local.set $count (i32.const 0))
    (local.set $current (local.get $v))
    (block $done
      (loop $loop
        (br_if $done (call $is_nil (local.get $current)))
        (local.set $count (i32.add (local.get $count) (i32.const 1)))
        (local.set $current (call $list_rest (local.get $current)))
        (br $loop)
      )
    )
    (local.get $count)
  )

  ;; Get string length
  (func $string_len (param $v (ref null eq)) (result i32)
    (struct.get $StringValue $length
      (ref.cast (ref $StringValue) (local.get $v)))
  )

  ;; Get character at index in string
  (func $string_char_at (param $v (ref null eq)) (param $idx i32) (result i32)
    (local $s (ref $StringValue))
    (local.set $s (ref.cast (ref $StringValue) (local.get $v)))
    (if (result i32)
      (i32.or
        (i32.lt_s (local.get $idx) (i32.const 0))
        (i32.ge_s (local.get $idx) (struct.get $StringValue $length (local.get $s)))
      )
      (then
        ;; Index out of bounds
        (unreachable)
      )
      (else
        (array.get $CharArray
          (struct.get $StringValue $chars (local.get $s))
          (local.get $idx))
      )
    )
  )
"""


def generate_runtime_library() -> str:
    """Generate the complete runtime library WAT code."""
    return (
        generate_value_constructors() +
        generate_type_predicates() +
        generate_value_extractors()
    )


RUNTIME_LIBRARY_WAT = generate_runtime_library()
