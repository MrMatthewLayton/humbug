"""WASM string operations for AIFPL.

This module generates WAT code for string operations.
"""


def generate_string_ops() -> str:
    """Generate WAT functions for string operations."""
    return """\
  ;; ============================================
  ;; String Operations
  ;; ============================================

  ;; string-append - concatenate strings
  (func $aifpl_string_append (param $a (ref null eq)) (param $b (ref null eq)) (result (ref $StringValue))
    (local $sa (ref $StringValue))
    (local $sb (ref $StringValue))
    (local $len_a i32)
    (local $len_b i32)
    (local $total_len i32)
    (local $result (ref $CharArray))
    (local $i i32)

    (local.set $sa (ref.cast (ref $StringValue) (local.get $a)))
    (local.set $sb (ref.cast (ref $StringValue) (local.get $b)))
    (local.set $len_a (struct.get $StringValue $length (local.get $sa)))
    (local.set $len_b (struct.get $StringValue $length (local.get $sb)))
    (local.set $total_len (i32.add (local.get $len_a) (local.get $len_b)))

    ;; Create new character array
    (local.set $result (array.new $CharArray (i32.const 0) (local.get $total_len)))

    ;; Copy first string
    (local.set $i (i32.const 0))
    (block $done1
      (loop $loop1
        (br_if $done1 (i32.ge_s (local.get $i) (local.get $len_a)))
        (array.set $CharArray (local.get $result) (local.get $i)
          (array.get $CharArray (struct.get $StringValue $chars (local.get $sa)) (local.get $i)))
        (local.set $i (i32.add (local.get $i) (i32.const 1)))
        (br $loop1)
      )
    )

    ;; Copy second string
    (local.set $i (i32.const 0))
    (block $done2
      (loop $loop2
        (br_if $done2 (i32.ge_s (local.get $i) (local.get $len_b)))
        (array.set $CharArray (local.get $result) (i32.add (local.get $len_a) (local.get $i))
          (array.get $CharArray (struct.get $StringValue $chars (local.get $sb)) (local.get $i)))
        (local.set $i (i32.add (local.get $i) (i32.const 1)))
        (br $loop2)
      )
    )

    (struct.new $StringValue
      (global.get $TAG_STRING)
      (local.get $total_len)
      (local.get $result))
  )

  ;; string-length
  (func $aifpl_string_length (param $s (ref null eq)) (result (ref eq))
    (call $make_int (call $string_len (local.get $s)))
  )

  ;; string-ref - get character at index (returns single-char string)
  (func $aifpl_string_ref (param $s (ref null eq)) (param $idx (ref null eq)) (result (ref $StringValue))
    (local $i i32)
    (local $str (ref $StringValue))
    (local $result (ref $CharArray))

    (local.set $i (call $to_i32 (local.get $idx)))
    (local.set $str (ref.cast (ref $StringValue) (local.get $s)))

    ;; Bounds check
    (if (i32.or
          (i32.lt_s (local.get $i) (i32.const 0))
          (i32.ge_s (local.get $i) (struct.get $StringValue $length (local.get $str))))
      (then (unreachable))  ;; Index out of bounds
    )

    ;; Create single-character string
    (local.set $result (array.new $CharArray (i32.const 0) (i32.const 1)))
    (array.set $CharArray (local.get $result) (i32.const 0)
      (array.get $CharArray (struct.get $StringValue $chars (local.get $str)) (local.get $i)))

    (struct.new $StringValue
      (global.get $TAG_STRING)
      (i32.const 1)
      (local.get $result))
  )

  ;; substring
  (func $aifpl_substring (param $s (ref null eq)) (param $start (ref null eq)) (param $end (ref null eq)) (result (ref $StringValue))
    (local $str (ref $StringValue))
    (local $st i32)
    (local $en i32)
    (local $len i32)
    (local $new_len i32)
    (local $result (ref $CharArray))
    (local $i i32)

    (local.set $str (ref.cast (ref $StringValue) (local.get $s)))
    (local.set $st (call $to_i32 (local.get $start)))
    (local.set $en (call $to_i32 (local.get $end)))
    (local.set $len (struct.get $StringValue $length (local.get $str)))

    ;; Clamp indices
    (if (i32.lt_s (local.get $st) (i32.const 0))
      (then (local.set $st (i32.const 0)))
    )
    (if (i32.gt_s (local.get $en) (local.get $len))
      (then (local.set $en (local.get $len)))
    )
    (if (i32.gt_s (local.get $st) (local.get $en))
      (then (local.set $st (local.get $en)))
    )

    (local.set $new_len (i32.sub (local.get $en) (local.get $st)))
    (local.set $result (array.new $CharArray (i32.const 0) (local.get $new_len)))

    ;; Copy substring
    (local.set $i (i32.const 0))
    (block $done
      (loop $loop
        (br_if $done (i32.ge_s (local.get $i) (local.get $new_len)))
        (array.set $CharArray (local.get $result) (local.get $i)
          (array.get $CharArray
            (struct.get $StringValue $chars (local.get $str))
            (i32.add (local.get $st) (local.get $i))))
        (local.set $i (i32.add (local.get $i) (i32.const 1)))
        (br $loop)
      )
    )

    (struct.new $StringValue
      (global.get $TAG_STRING)
      (local.get $new_len)
      (local.get $result))
  )

  ;; string-upcase
  (func $aifpl_string_upcase (param $s (ref null eq)) (result (ref $StringValue))
    (local $str (ref $StringValue))
    (local $len i32)
    (local $result (ref $CharArray))
    (local $i i32)
    (local $c i32)

    (local.set $str (ref.cast (ref $StringValue) (local.get $s)))
    (local.set $len (struct.get $StringValue $length (local.get $str)))
    (local.set $result (array.new $CharArray (i32.const 0) (local.get $len)))

    (local.set $i (i32.const 0))
    (block $done
      (loop $loop
        (br_if $done (i32.ge_s (local.get $i) (local.get $len)))
        (local.set $c (array.get $CharArray (struct.get $StringValue $chars (local.get $str)) (local.get $i)))
        ;; Convert lowercase a-z (97-122) to uppercase A-Z (65-90)
        (if (i32.and
              (i32.ge_s (local.get $c) (i32.const 97))
              (i32.le_s (local.get $c) (i32.const 122)))
          (then
            (local.set $c (i32.sub (local.get $c) (i32.const 32)))
          )
        )
        (array.set $CharArray (local.get $result) (local.get $i) (local.get $c))
        (local.set $i (i32.add (local.get $i) (i32.const 1)))
        (br $loop)
      )
    )

    (struct.new $StringValue
      (global.get $TAG_STRING)
      (local.get $len)
      (local.get $result))
  )

  ;; string-downcase
  (func $aifpl_string_downcase (param $s (ref null eq)) (result (ref $StringValue))
    (local $str (ref $StringValue))
    (local $len i32)
    (local $result (ref $CharArray))
    (local $i i32)
    (local $c i32)

    (local.set $str (ref.cast (ref $StringValue) (local.get $s)))
    (local.set $len (struct.get $StringValue $length (local.get $str)))
    (local.set $result (array.new $CharArray (i32.const 0) (local.get $len)))

    (local.set $i (i32.const 0))
    (block $done
      (loop $loop
        (br_if $done (i32.ge_s (local.get $i) (local.get $len)))
        (local.set $c (array.get $CharArray (struct.get $StringValue $chars (local.get $str)) (local.get $i)))
        ;; Convert uppercase A-Z (65-90) to lowercase a-z (97-122)
        (if (i32.and
              (i32.ge_s (local.get $c) (i32.const 65))
              (i32.le_s (local.get $c) (i32.const 90)))
          (then
            (local.set $c (i32.add (local.get $c) (i32.const 32)))
          )
        )
        (array.set $CharArray (local.get $result) (local.get $i) (local.get $c))
        (local.set $i (i32.add (local.get $i) (i32.const 1)))
        (br $loop)
      )
    )

    (struct.new $StringValue
      (global.get $TAG_STRING)
      (local.get $len)
      (local.get $result))
  )

  ;; string-trim
  (func $aifpl_string_trim (param $s (ref null eq)) (result (ref $StringValue))
    (local $str (ref $StringValue))
    (local $len i32)
    (local $start i32)
    (local $end i32)
    (local $c i32)

    (local.set $str (ref.cast (ref $StringValue) (local.get $s)))
    (local.set $len (struct.get $StringValue $length (local.get $str)))
    (local.set $start (i32.const 0))
    (local.set $end (local.get $len))

    ;; Find start (skip leading whitespace)
    (block $done_start
      (loop $loop_start
        (br_if $done_start (i32.ge_s (local.get $start) (local.get $len)))
        (local.set $c (array.get $CharArray (struct.get $StringValue $chars (local.get $str)) (local.get $start)))
        ;; Check for whitespace (space, tab, newline, carriage return)
        (br_if $done_start
          (i32.and
            (i32.ne (local.get $c) (i32.const 32))   ;; space
            (i32.and
              (i32.ne (local.get $c) (i32.const 9))   ;; tab
              (i32.and
                (i32.ne (local.get $c) (i32.const 10))  ;; newline
                (i32.ne (local.get $c) (i32.const 13))  ;; carriage return
              )
            )
          )
        )
        (local.set $start (i32.add (local.get $start) (i32.const 1)))
        (br $loop_start)
      )
    )

    ;; Find end (skip trailing whitespace)
    (block $done_end
      (loop $loop_end
        (br_if $done_end (i32.le_s (local.get $end) (local.get $start)))
        (local.set $c (array.get $CharArray (struct.get $StringValue $chars (local.get $str)) (i32.sub (local.get $end) (i32.const 1))))
        (br_if $done_end
          (i32.and
            (i32.ne (local.get $c) (i32.const 32))
            (i32.and
              (i32.ne (local.get $c) (i32.const 9))
              (i32.and
                (i32.ne (local.get $c) (i32.const 10))
                (i32.ne (local.get $c) (i32.const 13))
              )
            )
          )
        )
        (local.set $end (i32.sub (local.get $end) (i32.const 1)))
        (br $loop_end)
      )
    )

    (call $aifpl_substring (local.get $s) (call $make_int (local.get $start)) (call $make_int (local.get $end)))
  )

  ;; string-contains?
  (func $aifpl_string_contains (param $haystack (ref null eq)) (param $needle (ref null eq)) (result (ref $BoolValue))
    (local $h (ref $StringValue))
    (local $n (ref $StringValue))
    (local $h_len i32)
    (local $n_len i32)
    (local $i i32)
    (local $j i32)
    (local $match i32)

    (local.set $h (ref.cast (ref $StringValue) (local.get $haystack)))
    (local.set $n (ref.cast (ref $StringValue) (local.get $needle)))
    (local.set $h_len (struct.get $StringValue $length (local.get $h)))
    (local.set $n_len (struct.get $StringValue $length (local.get $n)))

    ;; Empty needle always matches
    (if (i32.eq (local.get $n_len) (i32.const 0))
      (then (return (global.get $TRUE)))
    )

    ;; Needle longer than haystack - no match
    (if (i32.gt_s (local.get $n_len) (local.get $h_len))
      (then (return (global.get $FALSE)))
    )

    ;; Search for needle
    (local.set $i (i32.const 0))
    (block $found (result (ref $BoolValue))
      (loop $outer
        (if (i32.gt_s (i32.add (local.get $i) (local.get $n_len)) (local.get $h_len))
          (then
            (br $found (global.get $FALSE))
          )
        )

        ;; Check if needle matches at position i
        (local.set $match (i32.const 1))
        (local.set $j (i32.const 0))
        (block $no_match
          (loop $inner
            (br_if $no_match (i32.ge_s (local.get $j) (local.get $n_len)))
            (if (i32.ne
                  (array.get $CharArray (struct.get $StringValue $chars (local.get $h)) (i32.add (local.get $i) (local.get $j)))
                  (array.get $CharArray (struct.get $StringValue $chars (local.get $n)) (local.get $j)))
              (then
                (local.set $match (i32.const 0))
                (br $no_match)
              )
            )
            (local.set $j (i32.add (local.get $j) (i32.const 1)))
            (br $inner)
          )
        )

        (if (local.get $match)
          (then (br $found (global.get $TRUE)))
        )

        (local.set $i (i32.add (local.get $i) (i32.const 1)))
        (br $outer)
      )
      (unreachable)
    )
  )

  ;; string-prefix?
  (func $aifpl_string_prefix (param $s (ref null eq)) (param $prefix (ref null eq)) (result (ref $BoolValue))
    (local $str (ref $StringValue))
    (local $pre (ref $StringValue))
    (local $s_len i32)
    (local $p_len i32)
    (local $i i32)

    (local.set $str (ref.cast (ref $StringValue) (local.get $s)))
    (local.set $pre (ref.cast (ref $StringValue) (local.get $prefix)))
    (local.set $s_len (struct.get $StringValue $length (local.get $str)))
    (local.set $p_len (struct.get $StringValue $length (local.get $pre)))

    ;; Prefix longer than string - no match
    (if (i32.gt_s (local.get $p_len) (local.get $s_len))
      (then (return (global.get $FALSE)))
    )

    (local.set $i (i32.const 0))
    (block $done (result (ref $BoolValue))
      (loop $loop
        (if (i32.ge_s (local.get $i) (local.get $p_len))
          (then
            (br $done (global.get $TRUE))
          )
        )
        (if (i32.ne
              (array.get $CharArray (struct.get $StringValue $chars (local.get $str)) (local.get $i))
              (array.get $CharArray (struct.get $StringValue $chars (local.get $pre)) (local.get $i)))
          (then (br $done (global.get $FALSE)))
        )
        (local.set $i (i32.add (local.get $i) (i32.const 1)))
        (br $loop)
      )
      (unreachable)
    )
  )

  ;; string-suffix?
  (func $aifpl_string_suffix (param $s (ref null eq)) (param $suffix (ref null eq)) (result (ref $BoolValue))
    (local $str (ref $StringValue))
    (local $suf (ref $StringValue))
    (local $s_len i32)
    (local $u_len i32)
    (local $offset i32)
    (local $i i32)

    (local.set $str (ref.cast (ref $StringValue) (local.get $s)))
    (local.set $suf (ref.cast (ref $StringValue) (local.get $suffix)))
    (local.set $s_len (struct.get $StringValue $length (local.get $str)))
    (local.set $u_len (struct.get $StringValue $length (local.get $suf)))

    ;; Suffix longer than string - no match
    (if (i32.gt_s (local.get $u_len) (local.get $s_len))
      (then (return (global.get $FALSE)))
    )

    (local.set $offset (i32.sub (local.get $s_len) (local.get $u_len)))
    (local.set $i (i32.const 0))
    (block $done (result (ref $BoolValue))
      (loop $loop
        (if (i32.ge_s (local.get $i) (local.get $u_len))
          (then
            (br $done (global.get $TRUE))
          )
        )
        (if (i32.ne
              (array.get $CharArray (struct.get $StringValue $chars (local.get $str)) (i32.add (local.get $offset) (local.get $i)))
              (array.get $CharArray (struct.get $StringValue $chars (local.get $suf)) (local.get $i)))
          (then (br $done (global.get $FALSE)))
        )
        (local.set $i (i32.add (local.get $i) (i32.const 1)))
        (br $loop)
      )
      (unreachable)
    )
  )

  ;; string=?
  (func $aifpl_string_eq (param $a (ref null eq)) (param $b (ref null eq)) (result (ref $BoolValue))
    (call $make_bool (call $string_eq (local.get $a) (local.get $b)))
  )

  ;; string->list
  (func $aifpl_string_to_list (param $s (ref null eq)) (result (ref null eq))
    (local $str (ref $StringValue))
    (local $len i32)
    (local $result (ref null eq))
    (local $i i32)
    (local $char_arr (ref $CharArray))

    (local.set $str (ref.cast (ref $StringValue) (local.get $s)))
    (local.set $len (struct.get $StringValue $length (local.get $str)))
    (local.set $result (global.get $NIL))

    ;; Build list in reverse, then it will be in correct order
    (local.set $i (i32.sub (local.get $len) (i32.const 1)))
    (block $done
      (loop $loop
        (br_if $done (i32.lt_s (local.get $i) (i32.const 0)))

        ;; Create single-char string
        (local.set $char_arr (array.new $CharArray (i32.const 0) (i32.const 1)))
        (array.set $CharArray (local.get $char_arr) (i32.const 0)
          (array.get $CharArray (struct.get $StringValue $chars (local.get $str)) (local.get $i)))

        (local.set $result
          (call $make_cons
            (struct.new $StringValue
              (global.get $TAG_STRING)
              (i32.const 1)
              (local.get $char_arr))
            (local.get $result)))

        (local.set $i (i32.sub (local.get $i) (i32.const 1)))
        (br $loop)
      )
    )

    (local.get $result)
  )

  ;; list->string
  (func $aifpl_list_to_string (param $lst (ref null eq)) (result (ref $StringValue))
    (local $len i32)
    (local $result (ref $CharArray))
    (local $current (ref null eq))
    (local $i i32)
    (local $j i32)
    (local $char_str (ref $StringValue))

    ;; First count the total length
    (local.set $len (i32.const 0))
    (local.set $current (local.get $lst))
    (block $count_done
      (loop $count_loop
        (br_if $count_done (call $is_nil (local.get $current)))
        (local.set $char_str (ref.cast (ref $StringValue) (call $list_first (local.get $current))))
        (local.set $len (i32.add (local.get $len) (struct.get $StringValue $length (local.get $char_str))))
        (local.set $current (call $list_rest (local.get $current)))
        (br $count_loop)
      )
    )

    ;; Create result array
    (local.set $result (array.new $CharArray (i32.const 0) (local.get $len)))

    ;; Copy characters
    (local.set $i (i32.const 0))
    (local.set $current (local.get $lst))
    (block $copy_done
      (loop $copy_loop
        (br_if $copy_done (call $is_nil (local.get $current)))
        (local.set $char_str (ref.cast (ref $StringValue) (call $list_first (local.get $current))))

        ;; Copy all chars from this string element
        (local.set $j (i32.const 0))
        (block $inner_done
          (loop $inner_loop
            (br_if $inner_done (i32.ge_s (local.get $j) (struct.get $StringValue $length (local.get $char_str))))
            (array.set $CharArray (local.get $result) (local.get $i)
              (array.get $CharArray (struct.get $StringValue $chars (local.get $char_str)) (local.get $j)))
            (local.set $i (i32.add (local.get $i) (i32.const 1)))
            (local.set $j (i32.add (local.get $j) (i32.const 1)))
            (br $inner_loop)
          )
        )

        (local.set $current (call $list_rest (local.get $current)))
        (br $copy_loop)
      )
    )

    (struct.new $StringValue
      (global.get $TAG_STRING)
      (local.get $len)
      (local.get $result))
  )
"""


def generate_string_conversion_ops() -> str:
    """Generate string conversion functions."""
    return """\
  ;; ============================================
  ;; String Conversion Operations
  ;; ============================================

  ;; number->string (basic integer conversion)
  (func $aifpl_number_to_string (param $n (ref null eq)) (result (ref $StringValue))
    (local $val f64)
    (local $is_neg i32)
    (local $int_part i64)
    (local $digits (ref $CharArray))
    (local $len i32)
    (local $i i32)
    (local $temp i64)
    (local $result (ref $CharArray))

    (local.set $val (call $to_f64 (local.get $n)))
    (local.set $is_neg (f64.lt (local.get $val) (f64.const 0)))

    (if (local.get $is_neg)
      (then (local.set $val (f64.neg (local.get $val))))
    )

    ;; Check if it's an integer
    (if (result (ref $StringValue))
      (f64.eq (local.get $val) (f64.trunc (local.get $val)))
      (then
        ;; Integer conversion
        (local.set $int_part (i64.trunc_f64_s (local.get $val)))

        ;; Handle zero
        (if (result (ref $StringValue))
          (i64.eq (local.get $int_part) (i64.const 0))
          (then
            (local.set $result (array.new $CharArray (i32.const 0) (i32.const 1)))
            (array.set $CharArray (local.get $result) (i32.const 0) (i32.const 48))  ;; '0'
            (struct.new $StringValue (global.get $TAG_STRING) (i32.const 1) (local.get $result))
          )
          (else
            ;; Count digits
            (local.set $len (i32.const 0))
            (local.set $temp (local.get $int_part))
            (block $count_done
              (loop $count_loop
                (br_if $count_done (i64.eq (local.get $temp) (i64.const 0)))
                (local.set $len (i32.add (local.get $len) (i32.const 1)))
                (local.set $temp (i64.div_u (local.get $temp) (i64.const 10)))
                (br $count_loop)
              )
            )

            ;; Add space for negative sign
            (if (local.get $is_neg)
              (then (local.set $len (i32.add (local.get $len) (i32.const 1))))
            )

            ;; Create result array
            (local.set $result (array.new $CharArray (i32.const 0) (local.get $len)))

            ;; Fill digits (backwards)
            (local.set $i (i32.sub (local.get $len) (i32.const 1)))
            (local.set $temp (local.get $int_part))
            (block $fill_done
              (loop $fill_loop
                (br_if $fill_done (i64.eq (local.get $temp) (i64.const 0)))
                (array.set $CharArray (local.get $result) (local.get $i)
                  (i32.add (i32.const 48) (i32.wrap_i64 (i64.rem_u (local.get $temp) (i64.const 10)))))
                (local.set $temp (i64.div_u (local.get $temp) (i64.const 10)))
                (local.set $i (i32.sub (local.get $i) (i32.const 1)))
                (br $fill_loop)
              )
            )

            ;; Add negative sign
            (if (local.get $is_neg)
              (then (array.set $CharArray (local.get $result) (i32.const 0) (i32.const 45)))  ;; '-'
            )

            (struct.new $StringValue (global.get $TAG_STRING) (local.get $len) (local.get $result))
          )
        )
      )
      (else
        ;; Float conversion - simplified, just show as integer for now
        ;; TODO: Proper float to string conversion
        (call $aifpl_number_to_string (call $make_number (f64.trunc (local.get $val))))
      )
    )
  )

  ;; string->number
  (func $aifpl_string_to_number (param $s (ref null eq)) (result (ref null eq))
    (local $str (ref $StringValue))
    (local $len i32)
    (local $i i32)
    (local $c i32)
    (local $is_neg i32)
    (local $result f64)
    (local $has_dot i32)
    (local $decimal_place f64)

    (local.set $str (ref.cast (ref $StringValue) (local.get $s)))
    (local.set $len (struct.get $StringValue $length (local.get $str)))
    (local.set $i (i32.const 0))
    (local.set $is_neg (i32.const 0))
    (local.set $result (f64.const 0))
    (local.set $has_dot (i32.const 0))
    (local.set $decimal_place (f64.const 0.1))

    ;; Empty string
    (if (i32.eq (local.get $len) (i32.const 0))
      (then (return (global.get $FALSE)))
    )

    ;; Check for negative
    (local.set $c (array.get $CharArray (struct.get $StringValue $chars (local.get $str)) (i32.const 0)))
    (if (i32.eq (local.get $c) (i32.const 45))  ;; '-'
      (then
        (local.set $is_neg (i32.const 1))
        (local.set $i (i32.const 1))
      )
    )
    (if (i32.eq (local.get $c) (i32.const 43))  ;; '+'
      (then (local.set $i (i32.const 1)))
    )

    ;; Parse digits
    (block $done
      (loop $loop
        (br_if $done (i32.ge_s (local.get $i) (local.get $len)))
        (local.set $c (array.get $CharArray (struct.get $StringValue $chars (local.get $str)) (local.get $i)))

        ;; Check for decimal point
        (if (i32.eq (local.get $c) (i32.const 46))  ;; '.'
          (then
            (if (local.get $has_dot)
              (then (return (global.get $FALSE)))  ;; Multiple dots
            )
            (local.set $has_dot (i32.const 1))
            (local.set $i (i32.add (local.get $i) (i32.const 1)))
            (br $loop)
          )
        )

        ;; Check for digit
        (if (i32.or
              (i32.lt_s (local.get $c) (i32.const 48))
              (i32.gt_s (local.get $c) (i32.const 57)))
          (then (return (global.get $FALSE)))  ;; Not a digit
        )

        (if (local.get $has_dot)
          (then
            ;; After decimal point
            (local.set $result
              (f64.add (local.get $result)
                (f64.mul
                  (local.get $decimal_place)
                  (f64.convert_i32_s (i32.sub (local.get $c) (i32.const 48))))))
            (local.set $decimal_place (f64.mul (local.get $decimal_place) (f64.const 0.1)))
          )
          (else
            ;; Before decimal point
            (local.set $result
              (f64.add
                (f64.mul (local.get $result) (f64.const 10))
                (f64.convert_i32_s (i32.sub (local.get $c) (i32.const 48)))))
          )
        )

        (local.set $i (i32.add (local.get $i) (i32.const 1)))
        (br $loop)
      )
    )

    (if (local.get $is_neg)
      (then (local.set $result (f64.neg (local.get $result))))
    )

    (call $make_number (local.get $result))
  )
"""


def generate_string_library() -> str:
    """Generate the complete string library WAT code."""
    return generate_string_ops() + generate_string_conversion_ops()


STRING_LIBRARY_WAT = generate_string_library()
