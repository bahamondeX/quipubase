import csv
import json
import typing as tp
from dataclasses import dataclass

import typing_extensions as tpe

from ._base import Artifact
from .utils import get_logger

logger = get_logger(__name__)


@dataclass
class CSVLoader(Artifact):
    ref: tpe.Annotated[
        str,
        tpe.Doc(
            """
        This `ref` can represent one out of three things:

        - An HTTP URL.
        - A file path (temporary or not) within the local filesystem.
        - A text file content.
        """
        ),
    ]

    def extract(self) -> tp.Generator[str, None, None]:
        """
        Extract data from CSV files.

        Yields:
            JSON strings representing rows from the CSV
        """
        file_path = self.retrieve()

        try:
            with open(
                file_path.as_posix(), "r", newline="", encoding="utf-8"
            ) as csvfile:
                # Try to detect the dialect
                try:
                    dialect = csv.Sniffer().sniff(csvfile.read(1024))
                    csvfile.seek(0)
                except csv.Error:
                    # Default to Excel dialect if detection fails
                    dialect = "excel"

                # First try with headers
                try:
                    csvfile.seek(0)
                    reader = csv.DictReader(csvfile, dialect=dialect)
                    headers = reader.fieldnames

                    if headers:
                        # Yield header information
                        yield json.dumps({"type": "csv_metadata", "headers": headers})

                        # Yield each row as a JSON object
                        for row_idx, row in enumerate(reader):
                            try:
                                # Clean up empty or None values
                                clean_row = {
                                    k: (v if v else "") for k, v in row.items()
                                }
                                yield json.dumps(
                                    {
                                        "row": row_idx
                                        + 1,  # 1-based indexing for humans
                                        "data": clean_row,
                                    }
                                )
                            except Exception as row_error:
                                yield f"Error processing row {row_idx + 1}: {str(row_error)}"
                    else:
                        # No headers detected, use regular reader
                        csvfile.seek(0)
                        reader = csv.reader(csvfile, dialect=dialect)

                        for row_idx, row in enumerate(reader):
                            try:
                                yield json.dumps({"row": row_idx + 1, "data": row})
                            except Exception as row_error:
                                yield f"Error processing row {row_idx + 1}: {str(row_error)}"

                except Exception as reader_error:
                    # Fall back to simpler reading approach
                    logger.error(f"Error reading CSV file: {str(reader_error)}")
                    csvfile.seek(0)
                    reader = csv.reader(csvfile)
                    for row_idx, row in enumerate(reader):
                        yield json.dumps({"row": row_idx + 1, "data": row})

        except Exception as e:
            # Handle errors gracefully
            yield f"Error processing CSV file: {str(e)}"
