"""WASM GC type definitions for AIFPL values.

This module generates the WAT type definitions for representing AIFPL values
in WebAssembly using the GC proposal types (structs and arrays).
"""

from typing import List


# Type tags for runtime type checking
class TypeTag:
    """Type tags for AIFPL values."""
    NUMBER = 0      # f64 number (float or large int)
    SMALL_INT = 1   # i31 small integer (optimization)
    COMPLEX = 2     # Complex number (real + imag)
    STRING = 3      # String value
    BOOLEAN = 4     # Boolean value
    LIST = 5        # List (cons cell)
    NIL = 6         # Empty list
    SYMBOL = 7      # Symbol
    FUNCTION = 8    # Function/closure
    ALIST = 9       # Association list
    BUILTIN = 10    # Built-in function reference


def generate_type_definitions() -> str:
    """Generate WAT type definitions for all AIFPL value types.

    Returns:
        WAT code defining all types needed for AIFPL values.
    """
    return """\
  ;; ============================================
  ;; AIFPL Value Type Definitions (WASM GC)
  ;; ============================================

  ;; Forward declarations using recursive type group
  (rec
    ;; Base value type - all AIFPL values use this or i31ref
    (type $Value (sub (struct
      (field $tag i32)
    )))

    ;; Number value (for floats and integers that don't fit in i31)
    (type $NumberValue (sub $Value (struct
      (field $tag i32)
      (field $value f64)
    )))

    ;; Complex number value
    (type $ComplexValue (sub $Value (struct
      (field $tag i32)
      (field $real f64)
      (field $imag f64)
    )))

    ;; Character array for strings (UTF-32 code points)
    (type $CharArray (array (mut i32)))

    ;; String value
    (type $StringValue (sub $Value (struct
      (field $tag i32)
      (field $length i32)
      (field $chars (ref $CharArray))
    )))

    ;; Boolean value
    (type $BoolValue (sub $Value (struct
      (field $tag i32)
      (field $value i32)
    )))

    ;; Symbol value (interned string)
    (type $SymbolValue (sub $Value (struct
      (field $tag i32)
      (field $name (ref $StringValue))
    )))

    ;; Nil value (empty list singleton)
    (type $NilValue (sub $Value (struct
      (field $tag i32)
    )))

    ;; List value (cons cell)
    (type $ListValue (sub $Value (struct
      (field $tag i32)
      (field $head (ref null eq))
      (field $tail (ref null eq))
    )))

    ;; Value array for function arguments and alist entries
    (type $ValueArray (array (mut (ref null eq))))

    ;; Binding in environment
    (type $Binding (struct
      (field $name (ref $StringValue))
      (field $value (ref null eq))
    ))

    ;; Binding array
    (type $BindingArray (array (mut (ref null $Binding))))

    ;; Environment for lexical scoping
    (type $Environment (struct
      (field $bindings (ref $BindingArray))
      (field $parent (ref null $Environment))
    ))

    ;; Function type for user-defined functions
    (type $UserFuncType (func (param (ref $ValueArray) (ref null $Environment)) (result (ref null eq))))

    ;; Function value (closure)
    (type $FunctionValue (sub $Value (struct
      (field $tag i32)
      (field $arity i32)
      (field $code (ref $UserFuncType))
      (field $env (ref null $Environment))
    )))

    ;; Built-in function reference
    (type $BuiltinValue (sub $Value (struct
      (field $tag i32)
      (field $name (ref $StringValue))
      (field $arity i32)  ;; -1 for variadic
    )))

    ;; Alist entry (key-value pair)
    (type $AlistEntry (struct
      (field $key (ref null eq))
      (field $value (ref null eq))
    ))

    ;; Alist entry array
    (type $AlistEntryArray (array (mut (ref null $AlistEntry))))

    ;; Alist value
    (type $AlistValue (sub $Value (struct
      (field $tag i32)
      (field $entries (ref $AlistEntryArray))
    )))
  )

  ;; ============================================
  ;; Global Constants
  ;; ============================================

  ;; Type tag constants
  (global $TAG_NUMBER i32 (i32.const 0))
  (global $TAG_SMALL_INT i32 (i32.const 1))
  (global $TAG_COMPLEX i32 (i32.const 2))
  (global $TAG_STRING i32 (i32.const 3))
  (global $TAG_BOOLEAN i32 (i32.const 4))
  (global $TAG_LIST i32 (i32.const 5))
  (global $TAG_NIL i32 (i32.const 6))
  (global $TAG_SYMBOL i32 (i32.const 7))
  (global $TAG_FUNCTION i32 (i32.const 8))
  (global $TAG_ALIST i32 (i32.const 9))
  (global $TAG_BUILTIN i32 (i32.const 10))

  ;; Singleton nil value
  (global $NIL (ref $NilValue) (struct.new $NilValue (i32.const 6)))

  ;; Boolean singletons
  (global $TRUE (ref $BoolValue) (struct.new $BoolValue (i32.const 4) (i32.const 1)))
  (global $FALSE (ref $BoolValue) (struct.new $BoolValue (i32.const 4) (i32.const 0)))

  ;; Empty environment
  (global $EMPTY_ENV (ref $Environment)
    (struct.new $Environment
      (array.new $BindingArray (ref.null $Binding) (i32.const 0))
      (ref.null $Environment)))

  ;; Mathematical constants
  (global $PI f64 (f64.const 3.141592653589793))
  (global $E f64 (f64.const 2.718281828459045))
"""


def generate_type_tag_constants() -> str:
    """Generate Python constants matching the WAT type tags."""
    return f"""\
# Type tag constants (must match WAT definitions)
TAG_NUMBER = {TypeTag.NUMBER}
TAG_SMALL_INT = {TypeTag.SMALL_INT}
TAG_COMPLEX = {TypeTag.COMPLEX}
TAG_STRING = {TypeTag.STRING}
TAG_BOOLEAN = {TypeTag.BOOLEAN}
TAG_LIST = {TypeTag.LIST}
TAG_NIL = {TypeTag.NIL}
TAG_SYMBOL = {TypeTag.SYMBOL}
TAG_FUNCTION = {TypeTag.FUNCTION}
TAG_ALIST = {TypeTag.ALIST}
TAG_BUILTIN = {TypeTag.BUILTIN}
"""


# Pre-generate the type definitions
TYPE_DEFINITIONS_WAT = generate_type_definitions()
