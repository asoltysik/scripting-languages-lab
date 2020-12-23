from dataclasses import dataclass
from typing import Optional
import os
import sys

import click

from .objects import *


@dataclass
class Repository:
    working_directory: str
    git_directory: str

    head: Optional[str] = None
    
    def init_git_directory(self):
        objects_path = os.path.join(self.git_directory, 'objects')

        os.mkdir(self.git_directory)
        os.mkdir(objects_path)

    def __post_init__(self):
        try:
            with open(os.path.join(self.git_directory, 'HEAD'), 'r') as f:
                self.head = f.read()
        except FileNotFoundError:
            self.head = ''

    def overwite_head(self, new_sha: str):
        head_path = os.path.join(self.git_directory, 'HEAD')
        with open(head_path, 'w+') as f:
            f.write(new_sha)

    def clean_working_dir(self):
        for entry in os.scandir(self.working_directory):
            if entry.name in ['.mygit', '.git']:
                continue

            if entry.is_dir():
                os.removedirs(entry.path)
            else:
                os.remove(entry.path)

    def checkout_walk(self, tree: Tree, path: str):
        for item in tree.leafs:
            obj = self.read_object(item.sha)
            target_path = os.path.join(path, item.path)

            if obj.object_type.value == ObjectType.Tree.value:
                os.mkdir(target_path)
                tree = self.get_tree(item.sha)
                self.checkout_walk(tree, target_path)
            elif obj.object_type.value == ObjectType.Blob.value:
                with open(target_path, 'w+') as f:
                    f.write(obj.content)

    def get_commit(self, sha: str) -> Commit:
        obj = self.read_object(sha)
        if obj.object_type != ObjectType.Commit:
            click.echo('Object is not a commit', err=True)
            sys.exit(1)

        commit = Commit.deserialize(obj.content)

        return commit

    def get_tree(self, sha: str) -> Tree:
        obj = self.read_object(sha)
        if obj.object_type != ObjectType.Tree:
            click.echo('Object is not a tree', err=True)
            sys.exit(1)
        
        tree = Tree.deserialize(sha, obj.content)
        return tree

    def read_object(self, sha: str) -> Object:
        with open(os.path.join(self.git_directory, 'objects', sha), 'r') as f:
            first_line = f.readline().strip()
            obj_type = ObjectType(first_line)
            content = f.read()

            return Object(object_type=obj_type, content_hash=sha, content=content)


    def write_object(self, object: Object):
        path = os.path.join(self.git_directory, 'objects', object.content_hash)
        if not os.path.exists(path):
            with open(path, 'w+') as f:
                f.write(object.object_type.value)
                f.write('\n')
                f.write(object.content)


def find_repo() -> Optional[Repository]:
    if os.path.exists(os.path.join(os.getcwd(), '.mygit')):
        working_dir = os.getcwd()
        return Repository(working_dir, os.path.join(working_dir, '.mygit'))
    else:
        return None


def create_tree(repo: Repository, working_dir: str) -> Tuple[Tree, List[Tree]]:
    all_trees = []
    leaves = []
    with os.scandir(working_dir) as it:
        for entry in it:
            if entry.name in ['.git', '.mygit']:
                continue

            if entry.is_file():
                obj = Object.from_file(entry.path)
                repo.write_object(obj)
                
                sha = obj.content_hash
                leaf = TreeLeaf(object_type=ObjectType.Blob, path=entry.name, sha=sha)
                leaves.append(leaf)

            if entry.is_dir():
                tree, trees = create_tree(repo, entry.path)
                sha = tree.compute_sha()
                leaf = TreeLeaf(object_type=ObjectType.Tree, path=entry.name, sha=sha)

                leaves.append(leaf)
                all_trees.extend(trees)

    tree = Tree(leafs=leaves)
    sha = tree.compute_sha()
    all_trees.append(tree)

    return (tree, all_trees)