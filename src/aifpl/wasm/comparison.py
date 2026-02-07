"""WASM comparison and boolean operations for AIFPL.

This module generates WAT code for comparison and boolean operations.
"""


def generate_comparison_ops() -> str:
    """Generate WAT functions for comparison operations."""
    return """\
  ;; ============================================
  ;; Comparison Operations
  ;; ============================================

  ;; Numeric equality comparison
  (func $num_eq (param $a (ref null eq)) (param $b (ref null eq)) (result i32)
    (local $tag_a i32)
    (local $tag_b i32)
    (local.set $tag_a (call $get_tag (local.get $a)))
    (local.set $tag_b (call $get_tag (local.get $b)))

    ;; Both complex
    (if (result i32)
      (i32.and
        (i32.eq (local.get $tag_a) (global.get $TAG_COMPLEX))
        (i32.eq (local.get $tag_b) (global.get $TAG_COMPLEX))
      )
      (then
        (i32.and
          (f64.eq (call $get_real (local.get $a)) (call $get_real (local.get $b)))
          (f64.eq (call $get_imag (local.get $a)) (call $get_imag (local.get $b))))
      )
      (else
        ;; At least one is real - compare as f64
        (f64.eq (call $to_f64 (local.get $a)) (call $to_f64 (local.get $b)))
      )
    )
  )

  ;; String equality comparison
  (func $string_eq (param $a (ref null eq)) (param $b (ref null eq)) (result i32)
    (local $sa (ref $StringValue))
    (local $sb (ref $StringValue))
    (local $len i32)
    (local $i i32)

    (local.set $sa (ref.cast (ref $StringValue) (local.get $a)))
    (local.set $sb (ref.cast (ref $StringValue) (local.get $b)))

    ;; Check lengths
    (local.set $len (struct.get $StringValue $length (local.get $sa)))
    (if (result i32)
      (i32.ne (local.get $len) (struct.get $StringValue $length (local.get $sb)))
      (then (i32.const 0))
      (else
        ;; Compare character by character
        (local.set $i (i32.const 0))
        (block $equal (result i32)
          (block $not_equal
            (loop $loop
              (br_if $equal (i32.ge_s (local.get $i) (local.get $len)) (i32.const 1))
              (br_if $not_equal
                (i32.ne
                  (array.get $CharArray
                    (struct.get $StringValue $chars (local.get $sa))
                    (local.get $i))
                  (array.get $CharArray
                    (struct.get $StringValue $chars (local.get $sb))
                    (local.get $i))))
              (local.set $i (i32.add (local.get $i) (i32.const 1)))
              (br $loop)
            )
          )
          (i32.const 0)
        )
      )
    )
  )

  ;; List equality comparison (deep)
  (func $list_eq (param $a (ref null eq)) (param $b (ref null eq)) (result i32)
    (local $nil_a i32)
    (local $nil_b i32)

    (local.set $nil_a (call $is_nil (local.get $a)))
    (local.set $nil_b (call $is_nil (local.get $b)))

    ;; Both nil
    (if (result i32)
      (i32.and (local.get $nil_a) (local.get $nil_b))
      (then (i32.const 1))
      (else
        ;; One nil, one not
        (if (result i32)
          (i32.or (local.get $nil_a) (local.get $nil_b))
          (then (i32.const 0))
          (else
            ;; Both are cons cells - compare recursively
            (i32.and
              (call $value_eq
                (call $list_first (local.get $a))
                (call $list_first (local.get $b)))
              (call $list_eq
                (call $list_rest (local.get $a))
                (call $list_rest (local.get $b))))
          )
        )
      )
    )
  )

  ;; General value equality
  (func $value_eq (param $a (ref null eq)) (param $b (ref null eq)) (result i32)
    (local $tag_a i32)
    (local $tag_b i32)

    ;; Handle null
    (if (result i32)
      (ref.is_null (local.get $a))
      (then (ref.is_null (local.get $b)))
      (else
        (if (result i32)
          (ref.is_null (local.get $b))
          (then (i32.const 0))
          (else
            (local.set $tag_a (call $get_tag (local.get $a)))
            (local.set $tag_b (call $get_tag (local.get $b)))

            ;; Numbers (including small ints)
            (if (result i32)
              (i32.and
                (call $is_number (local.get $a))
                (call $is_number (local.get $b))
              )
              (then (call $num_eq (local.get $a) (local.get $b)))
              (else
                ;; Must have same tag for other types
                (if (result i32)
                  (i32.ne (local.get $tag_a) (local.get $tag_b))
                  (then (i32.const 0))
                  (else
                    ;; Dispatch by type
                    (if (result i32)
                      (i32.eq (local.get $tag_a) (global.get $TAG_STRING))
                      (then (call $string_eq (local.get $a) (local.get $b)))
                      (else
                        (if (result i32)
                          (i32.eq (local.get $tag_a) (global.get $TAG_BOOLEAN))
                          (then
                            (i32.eq
                              (struct.get $BoolValue $value (ref.cast (ref $BoolValue) (local.get $a)))
                              (struct.get $BoolValue $value (ref.cast (ref $BoolValue) (local.get $b))))
                          )
                          (else
                            (if (result i32)
                              (i32.or
                                (i32.eq (local.get $tag_a) (global.get $TAG_LIST))
                                (i32.eq (local.get $tag_a) (global.get $TAG_NIL))
                              )
                              (then (call $list_eq (local.get $a) (local.get $b)))
                              (else
                                (if (result i32)
                                  (i32.eq (local.get $tag_a) (global.get $TAG_COMPLEX))
                                  (then
                                    (i32.and
                                      (f64.eq (call $get_real (local.get $a)) (call $get_real (local.get $b)))
                                      (f64.eq (call $get_imag (local.get $a)) (call $get_imag (local.get $b))))
                                  )
                                  (else
                                    ;; For functions, symbols: reference equality
                                    (ref.eq (local.get $a) (local.get $b))
                                  )
                                )
                              )
                            )
                          )
                        )
                      )
                    )
                  )
                )
              )
            )
          )
        )
      )
    )
  )

  ;; AIFPL = operator
  (func $aifpl_eq (param $a (ref null eq)) (param $b (ref null eq)) (result (ref $BoolValue))
    (call $make_bool (call $value_eq (local.get $a) (local.get $b)))
  )

  ;; AIFPL != operator
  (func $aifpl_ne (param $a (ref null eq)) (param $b (ref null eq)) (result (ref $BoolValue))
    (call $make_bool (i32.eqz (call $value_eq (local.get $a) (local.get $b))))
  )

  ;; Numeric less than
  (func $aifpl_lt (param $a (ref null eq)) (param $b (ref null eq)) (result (ref $BoolValue))
    (call $make_bool
      (f64.lt (call $to_f64 (local.get $a)) (call $to_f64 (local.get $b))))
  )

  ;; Numeric less than or equal
  (func $aifpl_le (param $a (ref null eq)) (param $b (ref null eq)) (result (ref $BoolValue))
    (call $make_bool
      (f64.le (call $to_f64 (local.get $a)) (call $to_f64 (local.get $b))))
  )

  ;; Numeric greater than
  (func $aifpl_gt (param $a (ref null eq)) (param $b (ref null eq)) (result (ref $BoolValue))
    (call $make_bool
      (f64.gt (call $to_f64 (local.get $a)) (call $to_f64 (local.get $b))))
  )

  ;; Numeric greater than or equal
  (func $aifpl_ge (param $a (ref null eq)) (param $b (ref null eq)) (result (ref $BoolValue))
    (call $make_bool
      (f64.ge (call $to_f64 (local.get $a)) (call $to_f64 (local.get $b))))
  )
"""


def generate_boolean_ops() -> str:
    """Generate WAT functions for boolean operations."""
    return """\
  ;; ============================================
  ;; Boolean Operations
  ;; ============================================

  ;; Boolean AND (strict - both must be booleans)
  (func $aifpl_and (param $a (ref null eq)) (param $b (ref null eq)) (result (ref $BoolValue))
    (if (result (ref $BoolValue))
      (i32.eqz (call $is_boolean (local.get $a)))
      (then (unreachable))  ;; Type error
      (else
        (if (result (ref $BoolValue))
          (i32.eqz (call $is_boolean (local.get $b)))
          (then (unreachable))  ;; Type error
          (else
            (call $make_bool
              (i32.and
                (struct.get $BoolValue $value (ref.cast (ref $BoolValue) (local.get $a)))
                (struct.get $BoolValue $value (ref.cast (ref $BoolValue) (local.get $b)))))
          )
        )
      )
    )
  )

  ;; Boolean OR (strict - both must be booleans)
  (func $aifpl_or (param $a (ref null eq)) (param $b (ref null eq)) (result (ref $BoolValue))
    (if (result (ref $BoolValue))
      (i32.eqz (call $is_boolean (local.get $a)))
      (then (unreachable))
      (else
        (if (result (ref $BoolValue))
          (i32.eqz (call $is_boolean (local.get $b)))
          (then (unreachable))
          (else
            (call $make_bool
              (i32.or
                (struct.get $BoolValue $value (ref.cast (ref $BoolValue) (local.get $a)))
                (struct.get $BoolValue $value (ref.cast (ref $BoolValue) (local.get $b)))))
          )
        )
      )
    )
  )

  ;; Boolean NOT (strict - must be boolean)
  (func $aifpl_not (param $a (ref null eq)) (result (ref $BoolValue))
    (if (result (ref $BoolValue))
      (i32.eqz (call $is_boolean (local.get $a)))
      (then (unreachable))
      (else
        (call $make_bool
          (i32.eqz
            (struct.get $BoolValue $value (ref.cast (ref $BoolValue) (local.get $a)))))
      )
    )
  )
"""


def generate_comparison_library() -> str:
    """Generate the complete comparison and boolean library WAT code."""
    return generate_comparison_ops() + generate_boolean_ops()


COMPARISON_LIBRARY_WAT = generate_comparison_library()
