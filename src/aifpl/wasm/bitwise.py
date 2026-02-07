"""WASM bitwise operations for AIFPL.

This module generates WAT code for bitwise operations.
"""


def generate_bitwise_ops() -> str:
    """Generate WAT functions for bitwise operations."""
    return """\
  ;; ============================================
  ;; Bitwise Operations
  ;; ============================================

  ;; bit-and - bitwise AND
  (func $aifpl_bit_and (param $a (ref null eq)) (param $b (ref null eq)) (result (ref eq))
    (call $make_int
      (i32.and
        (call $to_i32 (local.get $a))
        (call $to_i32 (local.get $b))))
  )

  ;; bit-or - bitwise OR
  (func $aifpl_bit_or (param $a (ref null eq)) (param $b (ref null eq)) (result (ref eq))
    (call $make_int
      (i32.or
        (call $to_i32 (local.get $a))
        (call $to_i32 (local.get $b))))
  )

  ;; bit-xor - bitwise XOR
  (func $aifpl_bit_xor (param $a (ref null eq)) (param $b (ref null eq)) (result (ref eq))
    (call $make_int
      (i32.xor
        (call $to_i32 (local.get $a))
        (call $to_i32 (local.get $b))))
  )

  ;; bit-not - bitwise NOT (complement)
  (func $aifpl_bit_not (param $a (ref null eq)) (result (ref eq))
    (call $make_int
      (i32.xor
        (call $to_i32 (local.get $a))
        (i32.const -1)))
  )

  ;; bit-shift-left - left shift
  (func $aifpl_bit_shl (param $a (ref null eq)) (param $b (ref null eq)) (result (ref eq))
    (call $make_int
      (i32.shl
        (call $to_i32 (local.get $a))
        (call $to_i32 (local.get $b))))
  )

  ;; bit-shift-right - arithmetic right shift (preserves sign)
  (func $aifpl_bit_shr (param $a (ref null eq)) (param $b (ref null eq)) (result (ref eq))
    (call $make_int
      (i32.shr_s
        (call $to_i32 (local.get $a))
        (call $to_i32 (local.get $b))))
  )

  ;; bit-shift-right-unsigned - logical right shift (fills with zeros)
  (func $aifpl_bit_shr_u (param $a (ref null eq)) (param $b (ref null eq)) (result (ref eq))
    (call $make_int
      (i32.shr_u
        (call $to_i32 (local.get $a))
        (call $to_i32 (local.get $b))))
  )

  ;; bit-count - count number of 1 bits (popcount)
  (func $aifpl_bit_count (param $a (ref null eq)) (result (ref eq))
    (call $make_int
      (i32.popcnt
        (call $to_i32 (local.get $a))))
  )

  ;; bit-length - number of bits needed to represent value
  (func $aifpl_bit_length (param $a (ref null eq)) (result (ref eq))
    (local $val i32)
    (local.set $val (call $to_i32 (local.get $a)))

    ;; For negative numbers, use absolute value
    (if (i32.lt_s (local.get $val) (i32.const 0))
      (then
        (local.set $val (i32.xor (local.get $val) (i32.const -1)))
      )
    )

    ;; 32 - clz gives the number of significant bits
    (call $make_int
      (i32.sub
        (i32.const 32)
        (i32.clz (local.get $val))))
  )

  ;; bit-set? - test if bit at position is set
  (func $aifpl_bit_set (param $a (ref null eq)) (param $pos (ref null eq)) (result (ref $BoolValue))
    (call $make_bool
      (i32.and
        (i32.shr_u
          (call $to_i32 (local.get $a))
          (call $to_i32 (local.get $pos)))
        (i32.const 1)))
  )

  ;; bit-set - set bit at position to 1
  (func $aifpl_bit_set_to_1 (param $a (ref null eq)) (param $pos (ref null eq)) (result (ref eq))
    (call $make_int
      (i32.or
        (call $to_i32 (local.get $a))
        (i32.shl (i32.const 1) (call $to_i32 (local.get $pos)))))
  )

  ;; bit-clear - set bit at position to 0
  (func $aifpl_bit_clear (param $a (ref null eq)) (param $pos (ref null eq)) (result (ref eq))
    (call $make_int
      (i32.and
        (call $to_i32 (local.get $a))
        (i32.xor
          (i32.shl (i32.const 1) (call $to_i32 (local.get $pos)))
          (i32.const -1))))
  )

  ;; bit-flip - flip bit at position
  (func $aifpl_bit_flip (param $a (ref null eq)) (param $pos (ref null eq)) (result (ref eq))
    (call $make_int
      (i32.xor
        (call $to_i32 (local.get $a))
        (i32.shl (i32.const 1) (call $to_i32 (local.get $pos)))))
  )
"""


def generate_bitwise_library() -> str:
    """Generate the complete bitwise library WAT code."""
    return generate_bitwise_ops()


BITWISE_LIBRARY_WAT = generate_bitwise_library()
