import json
import typing as tp
import xml.etree.ElementTree as ET
from dataclasses import dataclass

import typing_extensions as tpe

from ._base import Artifact


@dataclass
class XMLLoader(Artifact):
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

    def _element_to_dict(self, element: ET.Element) -> dict[str, tp.Any]:
        """Convert XML element to dictionary representation."""
        result: dict[str, tp.Any] = {}

        # Add attributes if present
        if element.attrib:
            result["@attributes"] = dict(element.attrib)

        # Process children
        children = list(element)
        if children:
            child_result: dict[str, list[dict[str, tp.Any]]] = {}

            # Group by tag name
            for child in children:
                tag = child.tag
                child_dict = self._element_to_dict(child)

                if tag in child_result:
                    # If this tag already exists, add to the list
                    child_result[tag].append(child_dict)
                else:
                    child_result[tag] = [child_dict]

            # Add children to result
            result.update(child_result)

        # Add text if present
        if element.text and element.text.strip():
            if children:
                result["#text"] = element.text.strip()
            else:
                result = {"#text": element.text.strip()}

        return result

    def extract(self) -> tp.Generator[str, None, None]:
        """
        Extract data from XML files.

        Yields:
            JSON strings representing elements from the XML
        """
        file_path = self.retrieve()

        try:
            # Parse XML file
            tree = ET.parse(file_path)
            root = tree.getroot()

            # Yield root element information
            yield json.dumps(
                {
                    "type": "xml_metadata",
                    "root_tag": root.tag,
                    "root_attributes": dict(root.attrib) if root.attrib else {},
                }
            )

            # Process the XML data
            data = self._element_to_dict(root)

            if "@attributes" in data:
                yield json.dumps(
                    {"element": root.tag, "attributes": data["@attributes"]}
                )

            # Then yield each top-level element
            has_elements = False
            for key, value in data.items():
                if key not in ["@attributes", "#text"]:
                    has_elements = True
                    if isinstance(value, list):
                        for idx, item in enumerate(value):  # type: ignore
                            try:
                                yield json.dumps(
                                    {"element": key, "index": idx, "data": item}
                                )
                            except Exception:
                                # If serialization fails, convert to string
                                yield json.dumps(
                                    {
                                        "element": key,
                                        "index": idx,
                                        "data": str(item),  # type: ignore
                                    }
                                )
                    else:
                        try:
                            yield json.dumps({"element": key, "data": value})
                        except Exception:
                            # If serialization fails, convert to string
                            yield json.dumps({"element": key, "data": str(value)})

            # For simple XML with no elements processed above, yield the entire structure
            if not has_elements:
                yield json.dumps(data)

        except Exception as e:
            # Handle errors gracefully
            yield json.dumps({"error": f"Error processing XML file: {str(e)}"})
