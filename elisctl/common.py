import json
import functools
from typing import Callable, IO, Optional

import click

from elisctl.schema.xlsx import SchemaContent, XlsxToSchema


def schema_content_factory(file_decorator):
    def schema_content(command: Optional[Callable] = None, **file_decorator_kwargs):
        def _load_func(schema_content_file_: Optional[IO[bytes]]) -> Optional[SchemaContent]:
            if schema_content_file_ is None:
                return None

            errors = []
            for load_func in (json.load, XlsxToSchema().convert):
                try:
                    return load_func(schema_content_file_)  # type: ignore
                except Exception as e:
                    errors.append(str(e))
                    schema_content_file_.seek(0)

            raise NotImplementedError(", ".join(errors))

        def decorator(command_: Callable):
            @file_decorator(**file_decorator_kwargs)
            @functools.wraps(command_)
            def wrapped(*args, schema_content_file_: Optional[IO[bytes]], **kwargs):
                try:
                    schema_content_ = _load_func(schema_content_file_)
                except Exception as e:
                    raise click.ClickException(
                        f"File {schema_content_file_} could not be loaded. Because of {e}"
                    ) from e

                return command_(*args, schema_content=schema_content_, **kwargs)

            return wrapped

        if command is None:
            return decorator
        return decorator(command)

    return schema_content
