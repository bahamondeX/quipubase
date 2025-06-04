from __future__ import annotations

import typing as tp

from pydantic import BaseModel, computed_field


class ChunkFile(BaseModel):
    chunks: list[str]
    created: float
    chunkedCount: int


class FileType(BaseModel):
    url: str
    path: str


class GetOrCreateFile(BaseModel):
    data: FileType
    created: float


class TreeNode(BaseModel):
    type: tp.Literal["file", "folder"]
    name: str
    path: str
    content: str | list[TreeNode]


class ScanFiles(BaseModel):
    data: TreeNode
    created: float

    @computed_field(return_type=int)
    @property
    def count(self) -> int:
        """Count the number of files in the tree"""
        i = 0

        def count_files(node: TreeNode):
            nonlocal i
            if isinstance(node.content, str):
                i += 1
            else:
                for child in node.content:
                    count_files(child)

        count_files(self.data)
        return i

    @computed_field(return_type=int)
    @property
    def size(self) -> int:
        """Calculate the size of the files in the tree"""
        i = 0

        def size_files(node: TreeNode):
            nonlocal i
            if isinstance(node.content, str):
                i += len(node.content)
            else:
                for child in node.content:
                    size_files(child)

        size_files(self.data)
        return i


TreeNode.model_rebuild()
