from __future__ import annotations
from typing import Optional, List
import click
import os
import hashlib
from dataclasses import dataclass
from enum import Enum




@dataclass
class Repository:
    working_directory: str
    git_directory: str

    
    def init_git_directory(self):
        objects_path = os.path.join(self.git_directory, 'objects')

        os.mkdir(self.git_directory)
        os.mkdir(objects_path)


@dataclass
class ObjectType(str, Enum):
    Blob = 'blob'
    Commit = 'comm'
    Tree = 'tree'


@dataclass
class Commit:
    repo: Repository

    tree: str
    parent: str
    description: str

    def serialize(self) -> str:
        return f'parent:{self.parent}\n' \
               f'tree:{self.tree}\n\n' \
               f'{self.description}'

    @staticmethod
    def deserialize(repo: Repository, input_str: str) -> Commit:
        double_newline_index = input_str.find('\n\n')
        keyword_part = input_str[:double_newline_index]
        keyword_lines = keyword_part.split('\n')

        parent_str = keyword_lines[0]
        parent = parent_str.split(':')[1]

        tree_str = keyword_lines[1]
        tree = tree_str.split(':')[1]
        
        description = input_str[double_newline_index + 2:]

        return Commit(repo=repo, tree=tree, parent=parent, description=description)


@dataclass
class TreeLeaf:
    path: str
    sha: str

    @staticmethod
    def deserialize(line: str) -> TreeLeaf:
        index_of_first_space = line.index(' ')
        sha = line[:index_of_first_space]
        path = line[index_of_first_space+1:]
        return TreeLeaf(path=path, sha=sha)

    def serialize(self) -> str:
        return f'{self.sha} {self.path}'


@dataclass
class Tree:
    repo: Repository

    sha: str
    leafs: List[TreeLeaf]


    @staticmethod
    def deserialize(repo: Repository, sha: str, input_str: str) -> Tree:
        leafs = []
        for line in input_str.split('\n'):
            leaf = TreeLeaf.deserialize(line)
            leafs.append(leaf)
        
        return Tree(repo=repo, sha=sha, leafs=leafs)

    def serialize(self) -> str:
        leaf_strs = []
        for leaf in self.leafs:
            leaf_strs.append(leaf.serialize())

        return '\n'.join(leaf_strs)


@dataclass
class Object:
    repo: Repository

    content_hash: str
    object_type: ObjectType
    content: bytes


    @staticmethod
    def from_file(repo: Repository, file_path: str) -> Object:
        with open(file_path, 'rb') as f:
            content = f.read()
            content_hash = hashlib.sha1(content).hexdigest()
        return Object(repo=repo, content_hash=content_hash, object_type=ObjectType.Blob, content=content)

    @staticmethod
    def from_commit(repo: Repository, commit: Commit) -> Object:
        content = commit.serialize().encode('UTF-8')
        content_hash = hashlib.sha1(content).hexdigest()
        return Object(repo=repo, object_type=ObjectType.Commit, content_hash=content_hash, content=content)

    @staticmethod
    def from_tree(repo: Repository, tree: Tree) -> Object:
        content = tree.serialize().encode('UTF-8')
        content_hash = hashlib.sha1(content).hexdigest()
        return Object(repo=repo, object_type=ObjectType.Tree, content_hash=content_hash, content=content)

    def write(self):
        with open(os.path.join(self.repo.git_directory, 'objects', self.content_hash), 'wb+') as f:
            f.write(self.object_type.value.encode())
            f.write(b'\n')
            f.write(self.content)


def find_repo() -> Optional[Repository]:
    if os.path.exists(os.path.join(os.getcwd(), '.mygit')):
        working_dir = os.getcwd()
        return Repository(working_dir, os.path.join(working_dir, '.mygit'))
    else:
        return None


@click.group()
def cli():
    pass


@cli.command()
def status():
    click.echo('status of repo')


@cli.command()
def init():
    if find_repo():
        click.echo('Repository is already initalized in this directory')
        return
    
    working_directory = os.getcwd()
    git_directory = os.path.join(working_directory, '.mygit')

    repo = Repository(working_directory=working_directory, git_directory=git_directory)

    repo.init_git_directory()

    click.echo('Initialized mygit repository.')


@cli.command()
@click.argument('description')
def commit(description):
    repo = find_repo()
    if not repo:
        click.echo('Repository is not initialized. Use `mygit init` to initialize it.', err=True)
        return
    
    
