from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
from typing import Optional, List, Tuple
import os


@dataclass
class ObjectType(str, Enum):
    Blob = 'blob'
    Commit = 'comm'
    Tree = 'tree'


@dataclass
class Commit:
    tree: str
    parent: str
    description: str

    def serialize(self) -> str:
        return f'parent:{self.parent}\n' \
               f'tree:{self.tree}\n\n' \
               f'{self.description}'

    @staticmethod
    def deserialize(input_str: str) -> Commit:
        double_newline_index = input_str.find('\n\n')
        keyword_part = input_str[:double_newline_index]
        keyword_lines = keyword_part.split('\n')

        parent_str = keyword_lines[0]
        parent = parent_str.split(':')[1]

        tree_str = keyword_lines[1]
        tree = tree_str.split(':')[1]
        
        description = input_str[double_newline_index + 2:]

        return Commit(tree=tree, parent=parent, description=description)

    def compute_sha(self) -> str:
        return hashlib.sha1(self.serialize().encode('UTF-8')).hexdigest()


@dataclass
class TreeLeaf:
    object_type: ObjectType
    path: str
    sha: str

    @staticmethod
    def deserialize(line: str) -> TreeLeaf:
        index_of_first_space = line.index(' ')
        object_type = ObjectType(line[:index_of_first_space])

        rest = line[index_of_first_space+1:]
        index_of_second_space = rest.index(' ')
        sha = rest[:index_of_second_space]

        path = rest[index_of_second_space+1:]
        return TreeLeaf(object_type=object_type, path=path, sha=sha)

    def serialize(self) -> str:
        return f'{self.object_type} {self.sha} {self.path}'


@dataclass
class Tree:
    leafs: List[TreeLeaf]
    sha: Optional[str] = None


    @staticmethod
    def deserialize(sha: str, input_str: str) -> Tree:
        leafs = []
        for line in input_str.split('\n'):
            leaf = TreeLeaf.deserialize(line)
            leafs.append(leaf)
        
        return Tree(sha=sha, leafs=leafs)

    def serialize(self) -> str:
        leaf_strs = []
        for leaf in self.leafs:
            leaf_strs.append(leaf.serialize())

        return '\n'.join(leaf_strs)

    def compute_sha(self):
        return hashlib.sha1(self.serialize().encode('UTF-8')).hexdigest()


@dataclass
class Object:
    content_hash: str
    object_type: ObjectType
    content: str


    @staticmethod
    def from_file(file_path: str) -> Object:
        with open(file_path, 'r') as f:
            content = f.read()
            content_hash = hashlib.sha1(content.encode('UTF-8')).hexdigest()
        return Object(content_hash=content_hash, object_type=ObjectType.Blob, content=content)

    @staticmethod
    def from_commit(commit: Commit) -> Object:
        content = commit.serialize()
        content_hash = hashlib.sha1(content.encode('UTF-8')).hexdigest()
        return Object(object_type=ObjectType.Commit, content_hash=content_hash, content=content)

    @staticmethod
    def from_tree(tree: Tree) -> Object:
        content = tree.serialize()
        content_hash = hashlib.sha1(content.encode('UTF-8')).hexdigest()
        return Object(object_type=ObjectType.Tree, content_hash=content_hash, content=content)
