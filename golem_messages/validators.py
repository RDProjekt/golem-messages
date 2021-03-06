from golem_messages import exceptions


def validate_varchar(field_name, value, max_length):
    if not (isinstance(value, str) and len(value) <= max_length):
        raise exceptions.FieldError(
            "Should be a string of length <= {max_length}".format(
                max_length=max_length,
            ),
            field=field_name,
            value=value,
        )


def validate_integer(field_name, value):
    if not isinstance(value, int):
        raise exceptions.FieldError(
            "Should be an integer field",
            field=field_name,
            value=value,
        )
