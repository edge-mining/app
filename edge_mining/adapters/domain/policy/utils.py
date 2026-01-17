"""Utility functions for policy domain adapters."""

from enum import Enum
from typing import Any, List, Optional, Union, get_args, get_origin

from pydantic import BaseModel, Field


class FieldStructureSchema(BaseModel):
    """Schema representing a single field in the decisional context structure."""

    path: str = Field(..., description="Full path in dot notation (e.g., 'energy_state.battery.state_of_charge')")
    type: str = Field(..., description="Type of the field (e.g., 'float', 'str', 'datetime')")
    description: Optional[str] = Field(None, description="Description of the field")
    is_optional: bool = Field(default=False, description="Whether the field is optional (can be None)")
    values: Optional[List[str]] = Field(None, description="Possible values")
    children: Optional[List["FieldStructureSchema"]] = Field(
        None, description="Nested fields if this is a complex type"
    )


# Update forward references for recursive schema
FieldStructureSchema.model_rebuild()


def _extract_schema_structure(
    schema_class: type[BaseModel], prefix: str = "", visited: Optional[set] = None
) -> List[FieldStructureSchema]:
    """
    Recursively extract structure from a Pydantic schema.

    Args:
        schema_class: The Pydantic schema class to extract from
        prefix: Current path prefix in dot notation
        visited: Set of already visited schema classes to avoid infinite recursion

    Returns:
        List of FieldStructureSchema representing the schema structure
    """
    if visited is None:
        visited = set()

    # Avoid infinite recursion
    schema_id = id(schema_class)
    if schema_id in visited:
        return []

    visited.add(schema_id)

    fields_structure = []

    # Get all fields from the schema
    if hasattr(schema_class, "model_fields"):
        for field_name, field_info in schema_class.model_fields.items():
            # Skip 'id' fields from the structure
            if field_name == "id":
                continue

            # Skip fields that are references to other entities (ending with _id)
            if field_name.endswith("_id"):
                continue

            # Skip 'timestamp' and other datetime fields in nested schemas (but not at root level)
            if prefix and field_name in ("timestamp", "created_at", "updated_at", "last_modified"):
                continue

            # Build the full path
            full_path = f"{prefix}.{field_name}" if prefix else field_name

            # Get type information
            field_type = field_info.annotation

            # Check if this is a nested schema (BaseModel subclass)
            children = None
            inner_type: Any = field_type

            # Handle Optional types to get the inner type
            origin = get_origin(field_type)
            if origin is Union:
                args = get_args(field_type)
                non_none_args = [arg for arg in args if arg is not type(None)]
                if len(non_none_args) == 1:
                    inner_type = non_none_args[0]

            type_name, is_optional, values = _get_field_type_name(field_type)

            # Get description from Field
            description = field_info.description

            # Check if inner_type is a List and extract element type
            inner_origin = get_origin(inner_type)
            if inner_origin is list:
                list_args = get_args(inner_type)
                if list_args and isinstance(list_args[0], type) and issubclass(list_args[0], BaseModel):
                    # Extract structure from list element type with array notation
                    # Use .0, .1, etc. to indicate array element access
                    array_path = f"{full_path}.0"
                    children = _extract_schema_structure(list_args[0], array_path, visited.copy())
                else:
                    children = None
            # Recursively process nested BaseModel schemas (non-list)
            elif isinstance(inner_type, type) and issubclass(inner_type, BaseModel):
                children = _extract_schema_structure(inner_type, full_path, visited.copy())
            else:
                children = None

            field_struct = FieldStructureSchema(
                path=full_path,
                type=type_name,
                description=description,
                is_optional=is_optional,
                values=values,
                children=children if children else None,
            )

            fields_structure.append(field_struct)

    # Extract @computed_field decorated properties (Pydantic v2)
    # Check if the schema has model_computed_fields (Pydantic v2 computed fields)
    if hasattr(schema_class, "model_computed_fields"):
        for field_name, computed_info in schema_class.model_computed_fields.items():
            # Build the full path
            full_path = f"{prefix}.{field_name}" if prefix else field_name

            # Try to infer type from computed field annotations
            property_type = "Any"
            is_optional = False

            # Get the property wrapper
            if hasattr(computed_info, "wrapped_property"):
                prop = computed_info.wrapped_property
                if hasattr(prop.fget, "__annotations__") and "return" in prop.fget.__annotations__:
                    return_type = prop.fget.__annotations__["return"]
                    property_type, is_optional, _ = _get_field_type_name(return_type)

                # Get docstring as description
                description = prop.fget.__doc__.strip() if prop.fget and prop.fget.__doc__ else None
            else:
                description = None

            field_struct = FieldStructureSchema(
                path=full_path,
                type=property_type,
                description=description,
                is_optional=is_optional,
                values=None,
                children=None,
            )

            fields_structure.append(field_struct)

    # Also extract @property decorated methods (for backwards compatibility)
    # Look for properties in the original domain class if the schema has a model_config
    elif hasattr(schema_class, "model_config") and hasattr(schema_class.model_config, "from_attributes"):
        # Try to find properties by inspecting the class
        for attr_name in dir(schema_class):
            if attr_name.startswith("_") or attr_name in ["model_fields", "model_config"]:
                continue

            try:
                attr = getattr(schema_class, attr_name)
                if isinstance(attr, property):
                    # Build the full path
                    full_path = f"{prefix}.{attr_name}" if prefix else attr_name

                    # Try to infer type from property getter annotations if available
                    property_type = "Any"
                    is_optional = False
                    if hasattr(attr.fget, "__annotations__") and "return" in attr.fget.__annotations__:
                        return_type = attr.fget.__annotations__["return"]
                        property_type, is_optional, _ = _get_field_type_name(return_type)

                    # Get docstring as description
                    description = attr.fget.__doc__.strip() if attr.fget and attr.fget.__doc__ else None

                    field_struct = FieldStructureSchema(
                        path=full_path,
                        type=property_type,
                        description=description,
                        is_optional=is_optional,
                        values=None,
                        children=None,
                    )

                    fields_structure.append(field_struct)
            except (AttributeError, TypeError):
                # Skip if we can't access the attribute
                continue

    return fields_structure


def _get_field_type_name(field_type: Any) -> tuple[str, bool, Optional[List[str]]]:
    """
    Extract a readable type name from a field type annotation.

    Returns:
        Tuple of (type_name, is_optional, values)
        - type_name: The base type without Optional wrapper
        - is_optional: Whether the field is Optional
        - values: List of possible values if it's an Enum, None otherwise
    """
    is_optional = False
    values = None

    # Handle Optional types
    origin = get_origin(field_type)
    if origin is Union:
        args = get_args(field_type)
        # Filter out NoneType to get the actual type for Optional
        non_none_args = [arg for arg in args if arg is not type(None)]
        if len(non_none_args) == 1 and type(None) in args:
            # This is Optional[T]
            is_optional = True
            field_type = non_none_args[0]
            origin = get_origin(field_type)
        elif len(args) > 1:
            # Multiple types in Union, not just Optional
            type_names = [_get_field_type_name(arg)[0] for arg in non_none_args]
            return f"Union[{', '.join(type_names)}]", is_optional, None

    # Re-check origin after unwrapping Optional
    if origin is list:
        args = get_args(field_type)
        if args:
            inner_name, _, _ = _get_field_type_name(args[0])
            return f"List[{inner_name}]", is_optional, None
    elif origin is dict:
        args = get_args(field_type)
        if args and len(args) >= 2:
            key_type, _, _ = _get_field_type_name(args[0])
            value_type, _, _ = _get_field_type_name(args[1])
            return f"Dict[{key_type}, {value_type}]", is_optional, None
        return "Dict", is_optional, None
    elif origin:
        return str(field_type), is_optional, None

    # Check if it's an Enum
    if isinstance(field_type, type) and issubclass(field_type, Enum):
        values = [item.value for item in field_type]
        # Determine the base type from the enum values
        if values:
            first_value = values[0]
            if isinstance(first_value, str):
                type_name = "str"
            elif isinstance(first_value, int):
                type_name = "int"
            elif isinstance(first_value, float):
                type_name = "float"
            elif isinstance(first_value, bool):
                type_name = "bool"
            else:
                type_name = type(first_value).__name__
        else:
            type_name = "str"  # Default to str if no values
        return type_name, is_optional, values

    # Handle BaseModel subclasses (return class name without "Schema" suffix for clarity)
    type_name_attr = getattr(field_type, "__name__", None)
    if type_name_attr:
        type_name = str(type_name_attr)
        # Remove "Schema" suffix if present for cleaner output
        if type_name.endswith("Schema"):
            type_name = type_name[:-6]
        return type_name, is_optional, None

    return str(field_type), is_optional, None
