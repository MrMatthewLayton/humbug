"""WASM arithmetic operations for AIFPL.

This module generates WAT code for arithmetic operations
with proper type promotion (int -> float -> complex).
"""


def generate_arithmetic_ops() -> str:
    """Generate WAT functions for arithmetic operations."""
    return """\
  ;; ============================================
  ;; Arithmetic Operations
  ;; ============================================

  ;; Add two values (with type promotion)
  (func $add (param $a (ref null eq)) (param $b (ref null eq)) (result (ref eq))
    (local $tag_a i32)
    (local $tag_b i32)
    (local.set $tag_a (call $get_tag (local.get $a)))
    (local.set $tag_b (call $get_tag (local.get $b)))

    ;; Check for complex numbers
    (if (result (ref eq))
      (i32.or
        (i32.eq (local.get $tag_a) (global.get $TAG_COMPLEX))
        (i32.eq (local.get $tag_b) (global.get $TAG_COMPLEX))
      )
      (then
        ;; Complex addition
        (call $make_complex
          (f64.add (call $get_real (local.get $a)) (call $get_real (local.get $b)))
          (f64.add (call $get_imag (local.get $a)) (call $get_imag (local.get $b))))
      )
      (else
        ;; Real number addition
        (call $make_number
          (f64.add (call $to_f64 (local.get $a)) (call $to_f64 (local.get $b))))
      )
    )
  )

  ;; Subtract two values
  (func $sub (param $a (ref null eq)) (param $b (ref null eq)) (result (ref eq))
    (local $tag_a i32)
    (local $tag_b i32)
    (local.set $tag_a (call $get_tag (local.get $a)))
    (local.set $tag_b (call $get_tag (local.get $b)))

    (if (result (ref eq))
      (i32.or
        (i32.eq (local.get $tag_a) (global.get $TAG_COMPLEX))
        (i32.eq (local.get $tag_b) (global.get $TAG_COMPLEX))
      )
      (then
        (call $make_complex
          (f64.sub (call $get_real (local.get $a)) (call $get_real (local.get $b)))
          (f64.sub (call $get_imag (local.get $a)) (call $get_imag (local.get $b))))
      )
      (else
        (call $make_number
          (f64.sub (call $to_f64 (local.get $a)) (call $to_f64 (local.get $b))))
      )
    )
  )

  ;; Multiply two values
  (func $mul (param $a (ref null eq)) (param $b (ref null eq)) (result (ref eq))
    (local $tag_a i32)
    (local $tag_b i32)
    (local $ar f64) (local $ai f64)
    (local $br f64) (local $bi f64)
    (local.set $tag_a (call $get_tag (local.get $a)))
    (local.set $tag_b (call $get_tag (local.get $b)))

    (if (result (ref eq))
      (i32.or
        (i32.eq (local.get $tag_a) (global.get $TAG_COMPLEX))
        (i32.eq (local.get $tag_b) (global.get $TAG_COMPLEX))
      )
      (then
        ;; Complex multiplication: (ar + ai*i) * (br + bi*i)
        ;; = (ar*br - ai*bi) + (ar*bi + ai*br)*i
        (local.set $ar (call $get_real (local.get $a)))
        (local.set $ai (call $get_imag (local.get $a)))
        (local.set $br (call $get_real (local.get $b)))
        (local.set $bi (call $get_imag (local.get $b)))
        (call $make_complex
          (f64.sub
            (f64.mul (local.get $ar) (local.get $br))
            (f64.mul (local.get $ai) (local.get $bi)))
          (f64.add
            (f64.mul (local.get $ar) (local.get $bi))
            (f64.mul (local.get $ai) (local.get $br))))
      )
      (else
        (call $make_number
          (f64.mul (call $to_f64 (local.get $a)) (call $to_f64 (local.get $b))))
      )
    )
  )

  ;; Divide two values
  (func $div (param $a (ref null eq)) (param $b (ref null eq)) (result (ref eq))
    (local $tag_a i32)
    (local $tag_b i32)
    (local $ar f64) (local $ai f64)
    (local $br f64) (local $bi f64)
    (local $denom f64)
    (local.set $tag_a (call $get_tag (local.get $a)))
    (local.set $tag_b (call $get_tag (local.get $b)))

    (if (result (ref eq))
      (i32.or
        (i32.eq (local.get $tag_a) (global.get $TAG_COMPLEX))
        (i32.eq (local.get $tag_b) (global.get $TAG_COMPLEX))
      )
      (then
        ;; Complex division: (ar + ai*i) / (br + bi*i)
        ;; = ((ar*br + ai*bi) + (ai*br - ar*bi)*i) / (br^2 + bi^2)
        (local.set $ar (call $get_real (local.get $a)))
        (local.set $ai (call $get_imag (local.get $a)))
        (local.set $br (call $get_real (local.get $b)))
        (local.set $bi (call $get_imag (local.get $b)))
        (local.set $denom
          (f64.add
            (f64.mul (local.get $br) (local.get $br))
            (f64.mul (local.get $bi) (local.get $bi))))
        (call $make_complex
          (f64.div
            (f64.add
              (f64.mul (local.get $ar) (local.get $br))
              (f64.mul (local.get $ai) (local.get $bi)))
            (local.get $denom))
          (f64.div
            (f64.sub
              (f64.mul (local.get $ai) (local.get $br))
              (f64.mul (local.get $ar) (local.get $bi)))
            (local.get $denom)))
      )
      (else
        (call $make_number
          (f64.div (call $to_f64 (local.get $a)) (call $to_f64 (local.get $b))))
      )
    )
  )

  ;; Floor division (integer division)
  (func $floor_div (param $a (ref null eq)) (param $b (ref null eq)) (result (ref eq))
    (call $make_number
      (f64.floor
        (f64.div (call $to_f64 (local.get $a)) (call $to_f64 (local.get $b)))))
  )

  ;; Modulo
  (func $mod (param $a (ref null eq)) (param $b (ref null eq)) (result (ref eq))
    (local $va f64)
    (local $vb f64)
    (local.set $va (call $to_f64 (local.get $a)))
    (local.set $vb (call $to_f64 (local.get $b)))
    ;; a % b = a - b * floor(a / b)
    (call $make_number
      (f64.sub
        (local.get $va)
        (f64.mul
          (local.get $vb)
          (f64.floor (f64.div (local.get $va) (local.get $vb))))))
  )

  ;; Power (exponentiation)
  ;; Using x^y = exp(y * ln(x)) for general case
  (func $pow (param $a (ref null eq)) (param $b (ref null eq)) (result (ref eq))
    (local $base f64)
    (local $exp f64)
    (local $tag_a i32)
    (local $tag_b i32)
    (local.set $tag_a (call $get_tag (local.get $a)))
    (local.set $tag_b (call $get_tag (local.get $b)))

    ;; For complex numbers, we need more complex handling
    ;; For now, handle real numbers only
    (if (result (ref eq))
      (i32.or
        (i32.eq (local.get $tag_a) (global.get $TAG_COMPLEX))
        (i32.eq (local.get $tag_b) (global.get $TAG_COMPLEX))
      )
      (then
        ;; Complex power - simplified implementation
        ;; TODO: Full complex power support
        (unreachable)
      )
      (else
        (local.set $base (call $to_f64 (local.get $a)))
        (local.set $exp (call $to_f64 (local.get $b)))
        ;; Check for negative base with non-integer exponent (would give complex result)
        (if (result (ref eq))
          (i32.and
            (f64.lt (local.get $base) (f64.const 0))
            (f64.ne (local.get $exp) (f64.trunc (local.get $exp)))
          )
          (then
            ;; Result is complex
            ;; For now, simplified: return NaN
            ;; TODO: Proper complex power
            (call $make_number (f64.const nan))
          )
          (else
            ;; Use WASM's built-in power approximation
            ;; x^y = exp(y * ln(|x|)) * sign handling
            (if (result (ref eq))
              (f64.eq (local.get $exp) (f64.const 0))
              (then (call $make_number (f64.const 1)))
              (else
                (if (result (ref eq))
                  (f64.eq (local.get $base) (f64.const 0))
                  (then (call $make_number (f64.const 0)))
                  (else
                    ;; General case: use logarithm
                    (call $make_number
                      (call $f64_pow (local.get $base) (local.get $exp)))
                  )
                )
              )
            )
          )
        )
      )
    )
  )

  ;; Helper: f64 power function using exp and log
  (func $f64_pow (param $base f64) (param $exp f64) (result f64)
    (local $abs_base f64)
    (local $result f64)
    (local.set $abs_base (f64.abs (local.get $base)))

    ;; Special cases
    (if (result f64)
      (f64.eq (local.get $exp) (f64.const 0))
      (then (f64.const 1))
      (else
        (if (result f64)
          (f64.eq (local.get $abs_base) (f64.const 0))
          (then (f64.const 0))
          (else
            (if (result f64)
              (f64.eq (local.get $exp) (f64.const 1))
              (then (local.get $base))
              (else
                (if (result f64)
                  (f64.eq (local.get $exp) (f64.const 2))
                  (then (f64.mul (local.get $base) (local.get $base)))
                  (else
                    ;; General: exp(exp * log(|base|))
                    (local.set $result
                      (call $f64_exp
                        (f64.mul
                          (local.get $exp)
                          (call $f64_log (local.get $abs_base)))))
                    ;; Handle sign for negative base with integer exponent
                    (if (result f64)
                      (i32.and
                        (f64.lt (local.get $base) (f64.const 0))
                        (f64.eq (local.get $exp) (f64.trunc (local.get $exp)))
                      )
                      (then
                        ;; Odd exponent -> negative result
                        (if (result f64)
                          (f64.ne
                            (f64.trunc (f64.div (local.get $exp) (f64.const 2)))
                            (f64.div (local.get $exp) (f64.const 2)))
                          (then (f64.neg (local.get $result)))
                          (else (local.get $result))
                        )
                      )
                      (else (local.get $result))
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

  ;; Negate a value
  (func $neg (param $a (ref null eq)) (result (ref eq))
    (local $tag i32)
    (local.set $tag (call $get_tag (local.get $a)))
    (if (result (ref eq))
      (i32.eq (local.get $tag) (global.get $TAG_COMPLEX))
      (then
        (call $make_complex
          (f64.neg (call $get_real (local.get $a)))
          (f64.neg (call $get_imag (local.get $a))))
      )
      (else
        (call $make_number (f64.neg (call $to_f64 (local.get $a))))
      )
    )
  )

  ;; Absolute value
  (func $abs (param $a (ref null eq)) (result (ref eq))
    (local $tag i32)
    (local $r f64)
    (local $i f64)
    (local.set $tag (call $get_tag (local.get $a)))
    (if (result (ref eq))
      (i32.eq (local.get $tag) (global.get $TAG_COMPLEX))
      (then
        ;; |a + bi| = sqrt(a^2 + b^2)
        (local.set $r (call $get_real (local.get $a)))
        (local.set $i (call $get_imag (local.get $a)))
        (call $make_number
          (f64.sqrt
            (f64.add
              (f64.mul (local.get $r) (local.get $r))
              (f64.mul (local.get $i) (local.get $i)))))
      )
      (else
        (call $make_number (f64.abs (call $to_f64 (local.get $a))))
      )
    )
  )
"""


def generate_math_functions() -> str:
    """Generate WAT functions for mathematical functions."""
    return """\
  ;; ============================================
  ;; Mathematical Functions
  ;; ============================================

  ;; Natural logarithm approximation using Taylor series
  ;; ln(x) = 2 * sum_{n=0}^{inf} (1/(2n+1)) * ((x-1)/(x+1))^(2n+1)
  (func $f64_log (param $x f64) (result f64)
    (local $y f64)
    (local $y2 f64)
    (local $term f64)
    (local $sum f64)
    (local $n i32)

    ;; Handle special cases
    (if (result f64)
      (f64.le (local.get $x) (f64.const 0))
      (then (f64.const nan))
      (else
        (if (result f64)
          (f64.eq (local.get $x) (f64.const 1))
          (then (f64.const 0))
          (else
            ;; Reduce to range [1, 2) using ln(x * 2^n) = ln(x) + n*ln(2)
            (local.set $n (i32.const 0))
            (block $done
              (loop $reduce_high
                (br_if $done (f64.lt (local.get $x) (f64.const 2)))
                (local.set $x (f64.div (local.get $x) (f64.const 2)))
                (local.set $n (i32.add (local.get $n) (i32.const 1)))
                (br $reduce_high)
              )
            )
            (block $done2
              (loop $reduce_low
                (br_if $done2 (f64.ge (local.get $x) (f64.const 1)))
                (local.set $x (f64.mul (local.get $x) (f64.const 2)))
                (local.set $n (i32.sub (local.get $n) (i32.const 1)))
                (br $reduce_low)
              )
            )

            ;; y = (x-1)/(x+1)
            (local.set $y
              (f64.div
                (f64.sub (local.get $x) (f64.const 1))
                (f64.add (local.get $x) (f64.const 1))))
            (local.set $y2 (f64.mul (local.get $y) (local.get $y)))

            ;; Taylor series: 2 * (y + y^3/3 + y^5/5 + ...)
            (local.set $sum (local.get $y))
            (local.set $term (local.get $y))

            ;; 10 iterations for good precision
            (local.set $term (f64.mul (local.get $term) (local.get $y2)))
            (local.set $sum (f64.add (local.get $sum) (f64.div (local.get $term) (f64.const 3))))
            (local.set $term (f64.mul (local.get $term) (local.get $y2)))
            (local.set $sum (f64.add (local.get $sum) (f64.div (local.get $term) (f64.const 5))))
            (local.set $term (f64.mul (local.get $term) (local.get $y2)))
            (local.set $sum (f64.add (local.get $sum) (f64.div (local.get $term) (f64.const 7))))
            (local.set $term (f64.mul (local.get $term) (local.get $y2)))
            (local.set $sum (f64.add (local.get $sum) (f64.div (local.get $term) (f64.const 9))))
            (local.set $term (f64.mul (local.get $term) (local.get $y2)))
            (local.set $sum (f64.add (local.get $sum) (f64.div (local.get $term) (f64.const 11))))

            ;; Result: 2*sum + n*ln(2)
            (f64.add
              (f64.mul (f64.const 2) (local.get $sum))
              (f64.mul
                (f64.convert_i32_s (local.get $n))
                (f64.const 0.6931471805599453)))  ;; ln(2)
          )
        )
      )
    )
  )

  ;; Exponential function using Taylor series
  ;; exp(x) = sum_{n=0}^{inf} x^n / n!
  (func $f64_exp (param $x f64) (result f64)
    (local $sum f64)
    (local $term f64)
    (local $n i32)
    (local $k i32)
    (local $scale f64)

    ;; Handle special cases
    (if (result f64)
      (f64.eq (local.get $x) (f64.const 0))
      (then (f64.const 1))
      (else
        ;; Reduce range: exp(x) = exp(x/2^k)^(2^k)
        (local.set $k (i32.const 0))
        (block $done
          (loop $reduce
            (br_if $done (f64.lt (f64.abs (local.get $x)) (f64.const 1)))
            (local.set $x (f64.div (local.get $x) (f64.const 2)))
            (local.set $k (i32.add (local.get $k) (i32.const 1)))
            (br $reduce)
          )
        )

        ;; Taylor series
        (local.set $sum (f64.const 1))
        (local.set $term (f64.const 1))
        (local.set $n (i32.const 1))

        (block $done2
          (loop $taylor
            (br_if $done2 (i32.gt_s (local.get $n) (i32.const 20)))
            (local.set $term
              (f64.div
                (f64.mul (local.get $term) (local.get $x))
                (f64.convert_i32_s (local.get $n))))
            (local.set $sum (f64.add (local.get $sum) (local.get $term)))
            (local.set $n (i32.add (local.get $n) (i32.const 1)))
            (br $taylor)
          )
        )

        ;; Square k times to get final result
        (block $done3
          (loop $square
            (br_if $done3 (i32.le_s (local.get $k) (i32.const 0)))
            (local.set $sum (f64.mul (local.get $sum) (local.get $sum)))
            (local.set $k (i32.sub (local.get $k) (i32.const 1)))
            (br $square)
          )
        )

        (local.get $sum)
      )
    )
  )

  ;; Sine using Taylor series
  (func $f64_sin (param $x f64) (result f64)
    (local $x2 f64)
    (local $term f64)
    (local $sum f64)
    (local $n i32)

    ;; Reduce to [-pi, pi]
    (local.set $x
      (f64.sub
        (local.get $x)
        (f64.mul
          (f64.trunc (f64.div (local.get $x) (f64.mul (f64.const 2) (global.get $PI))))
          (f64.mul (f64.const 2) (global.get $PI)))))

    (local.set $x2 (f64.mul (local.get $x) (local.get $x)))
    (local.set $sum (local.get $x))
    (local.set $term (local.get $x))

    ;; sin(x) = x - x^3/3! + x^5/5! - x^7/7! + ...
    (local.set $term (f64.div (f64.mul (local.get $term) (f64.neg (local.get $x2))) (f64.const 6)))
    (local.set $sum (f64.add (local.get $sum) (local.get $term)))
    (local.set $term (f64.div (f64.mul (local.get $term) (f64.neg (local.get $x2))) (f64.const 20)))
    (local.set $sum (f64.add (local.get $sum) (local.get $term)))
    (local.set $term (f64.div (f64.mul (local.get $term) (f64.neg (local.get $x2))) (f64.const 42)))
    (local.set $sum (f64.add (local.get $sum) (local.get $term)))
    (local.set $term (f64.div (f64.mul (local.get $term) (f64.neg (local.get $x2))) (f64.const 72)))
    (local.set $sum (f64.add (local.get $sum) (local.get $term)))
    (local.set $term (f64.div (f64.mul (local.get $term) (f64.neg (local.get $x2))) (f64.const 110)))
    (local.set $sum (f64.add (local.get $sum) (local.get $term)))

    (local.get $sum)
  )

  ;; Cosine using Taylor series
  (func $f64_cos (param $x f64) (result f64)
    (local $x2 f64)
    (local $term f64)
    (local $sum f64)

    ;; Reduce to [-pi, pi]
    (local.set $x
      (f64.sub
        (local.get $x)
        (f64.mul
          (f64.trunc (f64.div (local.get $x) (f64.mul (f64.const 2) (global.get $PI))))
          (f64.mul (f64.const 2) (global.get $PI)))))

    (local.set $x2 (f64.mul (local.get $x) (local.get $x)))
    (local.set $sum (f64.const 1))
    (local.set $term (f64.const 1))

    ;; cos(x) = 1 - x^2/2! + x^4/4! - x^6/6! + ...
    (local.set $term (f64.div (f64.mul (local.get $term) (f64.neg (local.get $x2))) (f64.const 2)))
    (local.set $sum (f64.add (local.get $sum) (local.get $term)))
    (local.set $term (f64.div (f64.mul (local.get $term) (f64.neg (local.get $x2))) (f64.const 12)))
    (local.set $sum (f64.add (local.get $sum) (local.get $term)))
    (local.set $term (f64.div (f64.mul (local.get $term) (f64.neg (local.get $x2))) (f64.const 30)))
    (local.set $sum (f64.add (local.get $sum) (local.get $term)))
    (local.set $term (f64.div (f64.mul (local.get $term) (f64.neg (local.get $x2))) (f64.const 56)))
    (local.set $sum (f64.add (local.get $sum) (local.get $term)))
    (local.set $term (f64.div (f64.mul (local.get $term) (f64.neg (local.get $x2))) (f64.const 90)))
    (local.set $sum (f64.add (local.get $sum) (local.get $term)))

    (local.get $sum)
  )

  ;; Tangent
  (func $f64_tan (param $x f64) (result f64)
    (f64.div (call $f64_sin (local.get $x)) (call $f64_cos (local.get $x)))
  )

  ;; Square root (using Newton-Raphson)
  (func $f64_sqrt_impl (param $x f64) (result f64)
    (f64.sqrt (local.get $x))  ;; WASM has native sqrt
  )

  ;; AIFPL math function wrappers
  (func $aifpl_sin (param $a (ref null eq)) (result (ref eq))
    (call $make_number (call $f64_sin (call $to_f64 (local.get $a))))
  )

  (func $aifpl_cos (param $a (ref null eq)) (result (ref eq))
    (call $make_number (call $f64_cos (call $to_f64 (local.get $a))))
  )

  (func $aifpl_tan (param $a (ref null eq)) (result (ref eq))
    (call $make_number (call $f64_tan (call $to_f64 (local.get $a))))
  )

  (func $aifpl_sqrt (param $a (ref null eq)) (result (ref eq))
    (local $val f64)
    (local.set $val (call $to_f64 (local.get $a)))
    (if (result (ref eq))
      (f64.lt (local.get $val) (f64.const 0))
      (then
        ;; Square root of negative -> complex
        (call $make_complex
          (f64.const 0)
          (f64.sqrt (f64.neg (local.get $val))))
      )
      (else
        (call $make_number (f64.sqrt (local.get $val)))
      )
    )
  )

  (func $aifpl_log (param $a (ref null eq)) (result (ref eq))
    (call $make_number (call $f64_log (call $to_f64 (local.get $a))))
  )

  (func $aifpl_exp (param $a (ref null eq)) (result (ref eq))
    (call $make_number (call $f64_exp (call $to_f64 (local.get $a))))
  )

  (func $aifpl_floor (param $a (ref null eq)) (result (ref eq))
    (call $make_number (f64.floor (call $to_f64 (local.get $a))))
  )

  (func $aifpl_ceil (param $a (ref null eq)) (result (ref eq))
    (call $make_number (f64.ceil (call $to_f64 (local.get $a))))
  )

  (func $aifpl_round (param $a (ref null eq)) (result (ref eq))
    (call $make_number (f64.nearest (call $to_f64 (local.get $a))))
  )

  ;; min/max for two values
  (func $aifpl_min (param $a (ref null eq)) (param $b (ref null eq)) (result (ref eq))
    (call $make_number (f64.min (call $to_f64 (local.get $a)) (call $to_f64 (local.get $b))))
  )

  (func $aifpl_max (param $a (ref null eq)) (param $b (ref null eq)) (result (ref eq))
    (call $make_number (f64.max (call $to_f64 (local.get $a)) (call $to_f64 (local.get $b))))
  )
"""


def generate_arithmetic_library() -> str:
    """Generate the complete arithmetic library WAT code."""
    return generate_arithmetic_ops() + generate_math_functions()


ARITHMETIC_LIBRARY_WAT = generate_arithmetic_library()
