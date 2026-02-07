"""WASM alist operations for AIFPL.

This module generates WAT code for association list (alist) operations.
"""


def generate_alist_ops() -> str:
    """Generate WAT functions for alist operations."""
    return """\
  ;; ============================================
  ;; Alist Operations
  ;; ============================================

  ;; alist-get - get value by key, returns #f if not found
  (func $aifpl_alist_get (param $alist (ref null eq)) (param $key (ref null eq)) (result (ref null eq))
    (local $al (ref $AlistValue))
    (local $entries (ref $AlistEntryArray))
    (local $len i32)
    (local $i i32)
    (local $entry (ref null $AlistEntry))

    (local.set $al (ref.cast (ref $AlistValue) (local.get $alist)))
    (local.set $entries (struct.get $AlistValue $entries (local.get $al)))
    (local.set $len (array.len (local.get $entries)))
    (local.set $i (i32.const 0))

    (block $found (result (ref null eq))
      (loop $loop
        (if (i32.ge_s (local.get $i) (local.get $len))
          (then
            (br $found (global.get $FALSE))
          )
        )

        (local.set $entry (array.get $AlistEntryArray (local.get $entries) (local.get $i)))

        (if (ref.is_null (local.get $entry))
          (then
            (local.set $i (i32.add (local.get $i) (i32.const 1)))
            (br $loop)
          )
        )

        (if (call $value_eq
              (struct.get $AlistEntry $key (ref.as_non_null (local.get $entry)))
              (local.get $key))
          (then
            (br $found (struct.get $AlistEntry $value (ref.as_non_null (local.get $entry))))
          )
        )

        (local.set $i (i32.add (local.get $i) (i32.const 1)))
        (br $loop)
      )
      (unreachable)
    )
  )

  ;; alist-has? - check if key exists
  (func $aifpl_alist_has (param $alist (ref null eq)) (param $key (ref null eq)) (result (ref $BoolValue))
    (local $al (ref $AlistValue))
    (local $entries (ref $AlistEntryArray))
    (local $len i32)
    (local $i i32)
    (local $entry (ref null $AlistEntry))

    (local.set $al (ref.cast (ref $AlistValue) (local.get $alist)))
    (local.set $entries (struct.get $AlistValue $entries (local.get $al)))
    (local.set $len (array.len (local.get $entries)))
    (local.set $i (i32.const 0))

    (block $found (result (ref $BoolValue))
      (loop $loop
        (if (i32.ge_s (local.get $i) (local.get $len))
          (then
            (br $found (global.get $FALSE))
          )
        )

        (local.set $entry (array.get $AlistEntryArray (local.get $entries) (local.get $i)))

        (if (ref.is_null (local.get $entry))
          (then
            (local.set $i (i32.add (local.get $i) (i32.const 1)))
            (br $loop)
          )
        )

        (if (call $value_eq
              (struct.get $AlistEntry $key (ref.as_non_null (local.get $entry)))
              (local.get $key))
          (then
            (br $found (global.get $TRUE))
          )
        )

        (local.set $i (i32.add (local.get $i) (i32.const 1)))
        (br $loop)
      )
      (unreachable)
    )
  )

  ;; alist-set - set/update a key-value pair (returns new alist)
  (func $aifpl_alist_set (param $alist (ref null eq)) (param $key (ref null eq)) (param $value (ref null eq)) (result (ref $AlistValue))
    (local $al (ref $AlistValue))
    (local $old_entries (ref $AlistEntryArray))
    (local $old_len i32)
    (local $new_entries (ref $AlistEntryArray))
    (local $i i32)
    (local $j i32)
    (local $entry (ref null $AlistEntry))
    (local $found i32)

    (local.set $al (ref.cast (ref $AlistValue) (local.get $alist)))
    (local.set $old_entries (struct.get $AlistValue $entries (local.get $al)))
    (local.set $old_len (array.len (local.get $old_entries)))
    (local.set $found (i32.const 0))

    ;; First pass: check if key exists
    (local.set $i (i32.const 0))
    (block $check_done
      (loop $check_loop
        (br_if $check_done (i32.ge_s (local.get $i) (local.get $old_len)))
        (local.set $entry (array.get $AlistEntryArray (local.get $old_entries) (local.get $i)))
        (if (i32.and
              (i32.eqz (ref.is_null (local.get $entry)))
              (call $value_eq
                (struct.get $AlistEntry $key (ref.as_non_null (local.get $entry)))
                (local.get $key)))
          (then
            (local.set $found (i32.const 1))
            (br $check_done)
          )
        )
        (local.set $i (i32.add (local.get $i) (i32.const 1)))
        (br $check_loop)
      )
    )

    ;; Create new entries array
    (if (result (ref $AlistValue))
      (local.get $found)
      (then
        ;; Key exists - replace it (same size)
        (local.set $new_entries (array.new $AlistEntryArray (ref.null $AlistEntry) (local.get $old_len)))
        (local.set $i (i32.const 0))
        (block $copy_done
          (loop $copy_loop
            (br_if $copy_done (i32.ge_s (local.get $i) (local.get $old_len)))
            (local.set $entry (array.get $AlistEntryArray (local.get $old_entries) (local.get $i)))
            (if (i32.and
                  (i32.eqz (ref.is_null (local.get $entry)))
                  (call $value_eq
                    (struct.get $AlistEntry $key (ref.as_non_null (local.get $entry)))
                    (local.get $key)))
              (then
                ;; Replace this entry
                (array.set $AlistEntryArray (local.get $new_entries) (local.get $i)
                  (call $make_alist_entry (local.get $key) (local.get $value)))
              )
              (else
                ;; Copy existing entry
                (array.set $AlistEntryArray (local.get $new_entries) (local.get $i) (local.get $entry))
              )
            )
            (local.set $i (i32.add (local.get $i) (i32.const 1)))
            (br $copy_loop)
          )
        )
        (call $make_alist (local.get $new_entries))
      )
      (else
        ;; Key doesn't exist - add new entry (size + 1)
        (local.set $new_entries (array.new $AlistEntryArray (ref.null $AlistEntry) (i32.add (local.get $old_len) (i32.const 1))))
        ;; Copy old entries
        (local.set $i (i32.const 0))
        (block $copy_done2
          (loop $copy_loop2
            (br_if $copy_done2 (i32.ge_s (local.get $i) (local.get $old_len)))
            (array.set $AlistEntryArray (local.get $new_entries) (local.get $i)
              (array.get $AlistEntryArray (local.get $old_entries) (local.get $i)))
            (local.set $i (i32.add (local.get $i) (i32.const 1)))
            (br $copy_loop2)
          )
        )
        ;; Add new entry at end
        (array.set $AlistEntryArray (local.get $new_entries) (local.get $old_len)
          (call $make_alist_entry (local.get $key) (local.get $value)))
        (call $make_alist (local.get $new_entries))
      )
    )
  )

  ;; alist-remove - remove a key (returns new alist)
  (func $aifpl_alist_remove (param $alist (ref null eq)) (param $key (ref null eq)) (result (ref $AlistValue))
    (local $al (ref $AlistValue))
    (local $old_entries (ref $AlistEntryArray))
    (local $old_len i32)
    (local $new_entries (ref $AlistEntryArray))
    (local $new_len i32)
    (local $i i32)
    (local $j i32)
    (local $entry (ref null $AlistEntry))

    (local.set $al (ref.cast (ref $AlistValue) (local.get $alist)))
    (local.set $old_entries (struct.get $AlistValue $entries (local.get $al)))
    (local.set $old_len (array.len (local.get $old_entries)))

    ;; Count entries to keep
    (local.set $new_len (i32.const 0))
    (local.set $i (i32.const 0))
    (block $count_done
      (loop $count_loop
        (br_if $count_done (i32.ge_s (local.get $i) (local.get $old_len)))
        (local.set $entry (array.get $AlistEntryArray (local.get $old_entries) (local.get $i)))
        (if (i32.and
              (i32.eqz (ref.is_null (local.get $entry)))
              (i32.eqz (call $value_eq
                (struct.get $AlistEntry $key (ref.as_non_null (local.get $entry)))
                (local.get $key))))
          (then
            (local.set $new_len (i32.add (local.get $new_len) (i32.const 1)))
          )
        )
        (local.set $i (i32.add (local.get $i) (i32.const 1)))
        (br $count_loop)
      )
    )

    ;; Create new array and copy non-matching entries
    (local.set $new_entries (array.new $AlistEntryArray (ref.null $AlistEntry) (local.get $new_len)))
    (local.set $i (i32.const 0))
    (local.set $j (i32.const 0))
    (block $copy_done
      (loop $copy_loop
        (br_if $copy_done (i32.ge_s (local.get $i) (local.get $old_len)))
        (local.set $entry (array.get $AlistEntryArray (local.get $old_entries) (local.get $i)))
        (if (i32.and
              (i32.eqz (ref.is_null (local.get $entry)))
              (i32.eqz (call $value_eq
                (struct.get $AlistEntry $key (ref.as_non_null (local.get $entry)))
                (local.get $key))))
          (then
            (array.set $AlistEntryArray (local.get $new_entries) (local.get $j) (local.get $entry))
            (local.set $j (i32.add (local.get $j) (i32.const 1)))
          )
        )
        (local.set $i (i32.add (local.get $i) (i32.const 1)))
        (br $copy_loop)
      )
    )

    (call $make_alist (local.get $new_entries))
  )

  ;; alist-keys - get all keys as a list
  (func $aifpl_alist_keys (param $alist (ref null eq)) (result (ref null eq))
    (local $al (ref $AlistValue))
    (local $entries (ref $AlistEntryArray))
    (local $len i32)
    (local $i i32)
    (local $entry (ref null $AlistEntry))
    (local $result (ref null eq))

    (local.set $al (ref.cast (ref $AlistValue) (local.get $alist)))
    (local.set $entries (struct.get $AlistValue $entries (local.get $al)))
    (local.set $len (array.len (local.get $entries)))
    (local.set $result (global.get $NIL))

    ;; Build list in reverse order (iterate backwards)
    (local.set $i (i32.sub (local.get $len) (i32.const 1)))
    (block $done
      (loop $loop
        (br_if $done (i32.lt_s (local.get $i) (i32.const 0)))
        (local.set $entry (array.get $AlistEntryArray (local.get $entries) (local.get $i)))
        (if (i32.eqz (ref.is_null (local.get $entry)))
          (then
            (local.set $result
              (call $make_cons
                (struct.get $AlistEntry $key (ref.as_non_null (local.get $entry)))
                (local.get $result)))
          )
        )
        (local.set $i (i32.sub (local.get $i) (i32.const 1)))
        (br $loop)
      )
    )

    (local.get $result)
  )

  ;; alist-values - get all values as a list
  (func $aifpl_alist_values (param $alist (ref null eq)) (result (ref null eq))
    (local $al (ref $AlistValue))
    (local $entries (ref $AlistEntryArray))
    (local $len i32)
    (local $i i32)
    (local $entry (ref null $AlistEntry))
    (local $result (ref null eq))

    (local.set $al (ref.cast (ref $AlistValue) (local.get $alist)))
    (local.set $entries (struct.get $AlistValue $entries (local.get $al)))
    (local.set $len (array.len (local.get $entries)))
    (local.set $result (global.get $NIL))

    ;; Build list in reverse order (iterate backwards)
    (local.set $i (i32.sub (local.get $len) (i32.const 1)))
    (block $done
      (loop $loop
        (br_if $done (i32.lt_s (local.get $i) (i32.const 0)))
        (local.set $entry (array.get $AlistEntryArray (local.get $entries) (local.get $i)))
        (if (i32.eqz (ref.is_null (local.get $entry)))
          (then
            (local.set $result
              (call $make_cons
                (struct.get $AlistEntry $value (ref.as_non_null (local.get $entry)))
                (local.get $result)))
          )
        )
        (local.set $i (i32.sub (local.get $i) (i32.const 1)))
        (br $loop)
      )
    )

    (local.get $result)
  )

  ;; alist-length - get number of entries
  (func $aifpl_alist_length (param $alist (ref null eq)) (result (ref eq))
    (local $al (ref $AlistValue))
    (call $make_int
      (array.len
        (struct.get $AlistValue $entries
          (ref.cast (ref $AlistValue) (local.get $alist)))))
  )

  ;; alist-merge - merge two alists (second overwrites first on conflicts)
  (func $aifpl_alist_merge (param $alist1 (ref null eq)) (param $alist2 (ref null eq)) (result (ref $AlistValue))
    (local $al1 (ref $AlistValue))
    (local $al2 (ref $AlistValue))
    (local $entries1 (ref $AlistEntryArray))
    (local $entries2 (ref $AlistEntryArray))
    (local $len1 i32)
    (local $len2 i32)
    (local $i i32)
    (local $entry (ref null $AlistEntry))
    (local $result (ref $AlistValue))

    (local.set $al1 (ref.cast (ref $AlistValue) (local.get $alist1)))
    (local.set $al2 (ref.cast (ref $AlistValue) (local.get $alist2)))
    (local.set $entries2 (struct.get $AlistValue $entries (local.get $al2)))
    (local.set $len2 (array.len (local.get $entries2)))

    ;; Start with first alist
    (local.set $result (local.get $al1))

    ;; Add all entries from second alist (overwriting conflicts)
    (local.set $i (i32.const 0))
    (block $done
      (loop $loop
        (br_if $done (i32.ge_s (local.get $i) (local.get $len2)))
        (local.set $entry (array.get $AlistEntryArray (local.get $entries2) (local.get $i)))
        (if (i32.eqz (ref.is_null (local.get $entry)))
          (then
            (local.set $result
              (call $aifpl_alist_set
                (local.get $result)
                (struct.get $AlistEntry $key (ref.as_non_null (local.get $entry)))
                (struct.get $AlistEntry $value (ref.as_non_null (local.get $entry)))))
          )
        )
        (local.set $i (i32.add (local.get $i) (i32.const 1)))
        (br $loop)
      )
    )

    (local.get $result)
  )
"""


def generate_alist_library() -> str:
    """Generate the complete alist library WAT code."""
    return generate_alist_ops()


ALIST_LIBRARY_WAT = generate_alist_library()
