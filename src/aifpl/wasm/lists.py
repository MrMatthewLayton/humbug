"""WASM list operations for AIFPL.

This module generates WAT code for list operations.
"""


def generate_list_ops() -> str:
    """Generate WAT functions for list operations."""
    return """\
  ;; ============================================
  ;; List Operations
  ;; ============================================

  ;; cons - prepend element to list
  (func $aifpl_cons (param $head (ref null eq)) (param $tail (ref null eq)) (result (ref eq))
    ;; Verify tail is a list
    (if (result (ref eq))
      (i32.eqz (call $is_list (local.get $tail)))
      (then (unreachable))  ;; Type error: cons requires list as second argument
      (else
        (call $make_cons (local.get $head) (local.get $tail))
      )
    )
  )

  ;; first - get first element
  (func $aifpl_first (param $v (ref null eq)) (result (ref null eq))
    (call $list_first (local.get $v))
  )

  ;; rest - get rest of list
  (func $aifpl_rest (param $v (ref null eq)) (result (ref null eq))
    (call $list_rest (local.get $v))
  )

  ;; last - get last element
  (func $aifpl_last (param $v (ref null eq)) (result (ref null eq))
    (local $current (ref null eq))
    (local $next (ref null eq))

    (if (result (ref null eq))
      (call $is_nil (local.get $v))
      (then (unreachable))  ;; Error: last of empty list
      (else
        (local.set $current (local.get $v))
        (block $done
          (loop $loop
            (local.set $next (call $list_rest (local.get $current)))
            (br_if $done (call $is_nil (local.get $next)))
            (local.set $current (local.get $next))
            (br $loop)
          )
        )
        (call $list_first (local.get $current))
      )
    )
  )

  ;; length - get list length
  (func $aifpl_length (param $v (ref null eq)) (result (ref eq))
    (call $make_int (call $list_length (local.get $v)))
  )

  ;; null? - check if empty list
  (func $aifpl_null (param $v (ref null eq)) (result (ref $BoolValue))
    (call $make_bool (call $is_nil (local.get $v)))
  )

  ;; list-ref - get element at index
  (func $aifpl_list_ref (param $lst (ref null eq)) (param $idx (ref null eq)) (result (ref null eq))
    (local $i i32)
    (local $current (ref null eq))

    (local.set $i (call $to_i32 (local.get $idx)))
    (local.set $current (local.get $lst))

    ;; Check for negative index
    (if (i32.lt_s (local.get $i) (i32.const 0))
      (then (unreachable))  ;; Index out of bounds
    )

    ;; Traverse to index
    (block $done
      (loop $loop
        (br_if $done (i32.le_s (local.get $i) (i32.const 0)))
        (if (call $is_nil (local.get $current))
          (then (unreachable))  ;; Index out of bounds
        )
        (local.set $current (call $list_rest (local.get $current)))
        (local.set $i (i32.sub (local.get $i) (i32.const 1)))
        (br $loop)
      )
    )

    (if (result (ref null eq))
      (call $is_nil (local.get $current))
      (then (unreachable))  ;; Index out of bounds
      (else (call $list_first (local.get $current)))
    )
  )

  ;; append - concatenate two lists
  (func $aifpl_append (param $a (ref null eq)) (param $b (ref null eq)) (result (ref null eq))
    ;; If first list is empty, return second
    (if (result (ref null eq))
      (call $is_nil (local.get $a))
      (then (local.get $b))
      (else
        ;; Recursive: cons (first a) (append (rest a) b)
        (call $make_cons
          (call $list_first (local.get $a))
          (call $aifpl_append (call $list_rest (local.get $a)) (local.get $b)))
      )
    )
  )

  ;; reverse - reverse a list
  (func $aifpl_reverse (param $v (ref null eq)) (result (ref null eq))
    (local $result (ref null eq))
    (local $current (ref null eq))

    (local.set $result (global.get $NIL))
    (local.set $current (local.get $v))

    (block $done
      (loop $loop
        (br_if $done (call $is_nil (local.get $current)))
        (local.set $result
          (call $make_cons
            (call $list_first (local.get $current))
            (local.get $result)))
        (local.set $current (call $list_rest (local.get $current)))
        (br $loop)
      )
    )

    (local.get $result)
  )

  ;; member? - check if element is in list
  (func $aifpl_member (param $elem (ref null eq)) (param $lst (ref null eq)) (result (ref $BoolValue))
    (local $current (ref null eq))

    (local.set $current (local.get $lst))

    (block $done (result (ref $BoolValue))
      (loop $loop
        (if (call $is_nil (local.get $current))
          (then
            (br $done (global.get $FALSE))
          )
        )
        (if (call $value_eq (local.get $elem) (call $list_first (local.get $current)))
          (then
            (br $done (global.get $TRUE))
          )
        )
        (local.set $current (call $list_rest (local.get $current)))
        (br $loop)
      )
      (unreachable)
    )
  )

  ;; remove - remove all occurrences of element
  (func $aifpl_remove (param $elem (ref null eq)) (param $lst (ref null eq)) (result (ref null eq))
    (if (result (ref null eq))
      (call $is_nil (local.get $lst))
      (then (global.get $NIL))
      (else
        (if (result (ref null eq))
          (call $value_eq (local.get $elem) (call $list_first (local.get $lst)))
          (then
            ;; Skip this element
            (call $aifpl_remove (local.get $elem) (call $list_rest (local.get $lst)))
          )
          (else
            ;; Keep this element
            (call $make_cons
              (call $list_first (local.get $lst))
              (call $aifpl_remove (local.get $elem) (call $list_rest (local.get $lst))))
          )
        )
      )
    )
  )

  ;; position - find index of element (returns #f if not found)
  (func $aifpl_position (param $elem (ref null eq)) (param $lst (ref null eq)) (result (ref null eq))
    (local $current (ref null eq))
    (local $idx i32)

    (local.set $current (local.get $lst))
    (local.set $idx (i32.const 0))

    (block $done (result (ref null eq))
      (loop $loop
        (if (call $is_nil (local.get $current))
          (then
            (br $done (global.get $FALSE))
          )
        )
        (if (call $value_eq (local.get $elem) (call $list_first (local.get $current)))
          (then
            (br $done (call $make_int (local.get $idx)))
          )
        )
        (local.set $current (call $list_rest (local.get $current)))
        (local.set $idx (i32.add (local.get $idx) (i32.const 1)))
        (br $loop)
      )
      (unreachable)
    )
  )

  ;; take - take first n elements
  (func $aifpl_take (param $n (ref null eq)) (param $lst (ref null eq)) (result (ref null eq))
    (local $count i32)

    (local.set $count (call $to_i32 (local.get $n)))

    (if (result (ref null eq))
      (i32.or
        (i32.le_s (local.get $count) (i32.const 0))
        (call $is_nil (local.get $lst))
      )
      (then (global.get $NIL))
      (else
        (call $make_cons
          (call $list_first (local.get $lst))
          (call $aifpl_take
            (call $make_int (i32.sub (local.get $count) (i32.const 1)))
            (call $list_rest (local.get $lst))))
      )
    )
  )

  ;; drop - drop first n elements
  (func $aifpl_drop (param $n (ref null eq)) (param $lst (ref null eq)) (result (ref null eq))
    (local $count i32)
    (local $current (ref null eq))

    (local.set $count (call $to_i32 (local.get $n)))
    (local.set $current (local.get $lst))

    (block $done
      (loop $loop
        (br_if $done (i32.le_s (local.get $count) (i32.const 0)))
        (br_if $done (call $is_nil (local.get $current)))
        (local.set $current (call $list_rest (local.get $current)))
        (local.set $count (i32.sub (local.get $count) (i32.const 1)))
        (br $loop)
      )
    )

    (local.get $current)
  )

  ;; range - generate list of numbers [start, end) with optional step
  (func $aifpl_range_2 (param $start (ref null eq)) (param $end (ref null eq)) (result (ref null eq))
    (call $aifpl_range_3 (local.get $start) (local.get $end) (call $make_int (i32.const 1)))
  )

  (func $aifpl_range_3 (param $start (ref null eq)) (param $end (ref null eq)) (param $step (ref null eq)) (result (ref null eq))
    (local $s f64)
    (local $e f64)
    (local $st f64)

    (local.set $s (call $to_f64 (local.get $start)))
    (local.set $e (call $to_f64 (local.get $end)))
    (local.set $st (call $to_f64 (local.get $step)))

    (if (result (ref null eq))
      (f64.gt (local.get $st) (f64.const 0))
      (then
        ;; Ascending
        (if (result (ref null eq))
          (f64.ge (local.get $s) (local.get $e))
          (then (global.get $NIL))
          (else
            (call $make_cons
              (call $make_number (local.get $s))
              (call $aifpl_range_3
                (call $make_number (f64.add (local.get $s) (local.get $st)))
                (local.get $end)
                (local.get $step)))
          )
        )
      )
      (else
        ;; Descending
        (if (result (ref null eq))
          (f64.le (local.get $s) (local.get $e))
          (then (global.get $NIL))
          (else
            (call $make_cons
              (call $make_number (local.get $s))
              (call $aifpl_range_3
                (call $make_number (f64.add (local.get $s) (local.get $st)))
                (local.get $end)
                (local.get $step)))
          )
        )
      )
    )
  )
"""


def generate_higher_order_ops() -> str:
    """Generate WAT functions for higher-order list functions."""
    return """\
  ;; ============================================
  ;; Higher-Order Functions
  ;; ============================================

  ;; map - apply function to each element
  (func $aifpl_map (param $func (ref null eq)) (param $lst (ref null eq)) (result (ref null eq))
    (local $fn (ref $FunctionValue))
    (local $args (ref $ValueArray))

    (if (result (ref null eq))
      (call $is_nil (local.get $lst))
      (then (global.get $NIL))
      (else
        ;; Apply function to first element
        (local.set $fn (ref.cast (ref $FunctionValue) (local.get $func)))
        (local.set $args (array.new $ValueArray (ref.null eq) (i32.const 1)))
        (array.set $ValueArray (local.get $args) (i32.const 0) (call $list_first (local.get $lst)))

        (call $make_cons
          (call_ref $UserFuncType
            (local.get $args)
            (struct.get $FunctionValue $env (local.get $fn))
            (struct.get $FunctionValue $code (local.get $fn)))
          (call $aifpl_map (local.get $func) (call $list_rest (local.get $lst))))
      )
    )
  )

  ;; filter - select elements matching predicate
  (func $aifpl_filter (param $pred (ref null eq)) (param $lst (ref null eq)) (result (ref null eq))
    (local $fn (ref $FunctionValue))
    (local $args (ref $ValueArray))
    (local $head (ref null eq))
    (local $result (ref null eq))

    (if (result (ref null eq))
      (call $is_nil (local.get $lst))
      (then (global.get $NIL))
      (else
        (local.set $fn (ref.cast (ref $FunctionValue) (local.get $pred)))
        (local.set $head (call $list_first (local.get $lst)))
        (local.set $args (array.new $ValueArray (ref.null eq) (i32.const 1)))
        (array.set $ValueArray (local.get $args) (i32.const 0) (local.get $head))

        ;; Apply predicate
        (local.set $result
          (call_ref $UserFuncType
            (local.get $args)
            (struct.get $FunctionValue $env (local.get $fn))
            (struct.get $FunctionValue $code (local.get $fn))))

        ;; Check if predicate returned true
        (if (result (ref null eq))
          (call $to_bool (local.get $result))
          (then
            (call $make_cons
              (local.get $head)
              (call $aifpl_filter (local.get $pred) (call $list_rest (local.get $lst))))
          )
          (else
            (call $aifpl_filter (local.get $pred) (call $list_rest (local.get $lst)))
          )
        )
      )
    )
  )

  ;; fold - accumulate with function (left fold)
  (func $aifpl_fold (param $func (ref null eq)) (param $init (ref null eq)) (param $lst (ref null eq)) (result (ref null eq))
    (local $fn (ref $FunctionValue))
    (local $args (ref $ValueArray))
    (local $acc (ref null eq))
    (local $current (ref null eq))

    (local.set $fn (ref.cast (ref $FunctionValue) (local.get $func)))
    (local.set $acc (local.get $init))
    (local.set $current (local.get $lst))
    (local.set $args (array.new $ValueArray (ref.null eq) (i32.const 2)))

    (block $done
      (loop $loop
        (br_if $done (call $is_nil (local.get $current)))

        ;; Call function with (acc, element)
        (array.set $ValueArray (local.get $args) (i32.const 0) (local.get $acc))
        (array.set $ValueArray (local.get $args) (i32.const 1) (call $list_first (local.get $current)))

        (local.set $acc
          (call_ref $UserFuncType
            (local.get $args)
            (struct.get $FunctionValue $env (local.get $fn))
            (struct.get $FunctionValue $code (local.get $fn))))

        (local.set $current (call $list_rest (local.get $current)))
        (br $loop)
      )
    )

    (local.get $acc)
  )

  ;; find - find first element matching predicate
  (func $aifpl_find (param $pred (ref null eq)) (param $lst (ref null eq)) (result (ref null eq))
    (local $fn (ref $FunctionValue))
    (local $args (ref $ValueArray))
    (local $head (ref null eq))
    (local $result (ref null eq))
    (local $current (ref null eq))

    (local.set $fn (ref.cast (ref $FunctionValue) (local.get $pred)))
    (local.set $args (array.new $ValueArray (ref.null eq) (i32.const 1)))
    (local.set $current (local.get $lst))

    (block $done (result (ref null eq))
      (loop $loop
        (if (call $is_nil (local.get $current))
          (then
            (br $done (global.get $FALSE))
          )
        )

        (local.set $head (call $list_first (local.get $current)))
        (array.set $ValueArray (local.get $args) (i32.const 0) (local.get $head))

        (local.set $result
          (call_ref $UserFuncType
            (local.get $args)
            (struct.get $FunctionValue $env (local.get $fn))
            (struct.get $FunctionValue $code (local.get $fn))))

        (if (call $to_bool (local.get $result))
          (then
            (br $done (local.get $head))
          )
        )

        (local.set $current (call $list_rest (local.get $current)))
        (br $loop)
      )
      (unreachable)
    )
  )

  ;; any? - check if any element matches predicate
  (func $aifpl_any (param $pred (ref null eq)) (param $lst (ref null eq)) (result (ref $BoolValue))
    (local $fn (ref $FunctionValue))
    (local $args (ref $ValueArray))
    (local $result (ref null eq))
    (local $current (ref null eq))

    (local.set $fn (ref.cast (ref $FunctionValue) (local.get $pred)))
    (local.set $args (array.new $ValueArray (ref.null eq) (i32.const 1)))
    (local.set $current (local.get $lst))

    (block $done (result (ref $BoolValue))
      (loop $loop
        (if (call $is_nil (local.get $current))
          (then
            (br $done (global.get $FALSE))
          )
        )

        (array.set $ValueArray (local.get $args) (i32.const 0) (call $list_first (local.get $current)))

        (local.set $result
          (call_ref $UserFuncType
            (local.get $args)
            (struct.get $FunctionValue $env (local.get $fn))
            (struct.get $FunctionValue $code (local.get $fn))))

        (if (call $to_bool (local.get $result))
          (then
            (br $done (global.get $TRUE))
          )
        )

        (local.set $current (call $list_rest (local.get $current)))
        (br $loop)
      )
      (unreachable)
    )
  )

  ;; all? - check if all elements match predicate
  (func $aifpl_all (param $pred (ref null eq)) (param $lst (ref null eq)) (result (ref $BoolValue))
    (local $fn (ref $FunctionValue))
    (local $args (ref $ValueArray))
    (local $result (ref null eq))
    (local $current (ref null eq))

    (local.set $fn (ref.cast (ref $FunctionValue) (local.get $pred)))
    (local.set $args (array.new $ValueArray (ref.null eq) (i32.const 1)))
    (local.set $current (local.get $lst))

    (block $done (result (ref $BoolValue))
      (loop $loop
        (if (call $is_nil (local.get $current))
          (then
            (br $done (global.get $TRUE))
          )
        )

        (array.set $ValueArray (local.get $args) (i32.const 0) (call $list_first (local.get $current)))

        (local.set $result
          (call_ref $UserFuncType
            (local.get $args)
            (struct.get $FunctionValue $env (local.get $fn))
            (struct.get $FunctionValue $code (local.get $fn))))

        (if (i32.eqz (call $to_bool (local.get $result)))
          (then
            (br $done (global.get $FALSE))
          )
        )

        (local.set $current (call $list_rest (local.get $current)))
        (br $loop)
      )
      (unreachable)
    )
  )
"""


def generate_list_library() -> str:
    """Generate the complete list library WAT code."""
    return generate_list_ops() + generate_higher_order_ops()


LIST_LIBRARY_WAT = generate_list_library()
