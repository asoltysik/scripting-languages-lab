from __future__ import annotations
from typing import Optional, List, Tuple
import click
import os
import sys
import hashlib
from dataclasses import dataclass
from enum import Enum

from .repository import Repository, find_repo, create_tree
from .objects import *



@click.group()
def cli():
    pass


@cli.command()
def init():
    if find_repo():
        click.echo('Repository is already initalized in this directory.')
        return
    
    working_directory = os.getcwd()
    git_directory = os.path.join(working_directory, '.mygit')

    repo = Repository(working_directory=working_directory, git_directory=git_directory)

    repo.init_git_directory()

    click.echo('Initialized mygit repository.')


@cli.command()
def log():
    repo = find_repo()
    if not repo:
        click.echo('Repository is not initialized. Use `mygit init` to initialize it.', err=True)
        return

    parent = repo.head
    commits = []
    while parent != '':
        commit = repo.get_commit(parent)
        commits.append(commit)
        parent = commit.parent

    commit_infos = [f'sha:{commit.compute_sha()}\n{commit.serialize()}' for commit in commits]
    log = '\n----------\n'.join(commit_infos)
    click.echo(log)



@cli.command()
@click.argument('description')
def commit(description):
    repo = find_repo()
    if not repo:
        click.echo('Repository is not initialized. Use `mygit init` to initialize it.', err=True)
        return
    
    top_tree, all_trees = create_tree(repo, repo.working_directory)

    commit = Commit(tree=Object.from_tree(top_tree).content_hash, parent=repo.head, description=description)
    commit_obj = Object.from_commit(commit=commit)

    objects = [Object.from_tree(tree) for tree in all_trees]
    objects.append(commit_obj)

    for obj in objects:
        repo.write_object(obj)

    repo.overwite_head(commit_obj.content_hash)

    
@cli.command()
@click.argument('commit-sha')
def checkout(commit_sha):
    repo = find_repo()
    if not repo:
        click.echo('Repository is not initialized. Use `mygit init` to initialize it.', err=True)
        return

    commit = repo.get_commit(commit_sha)
    tree = repo.get_tree(commit.tree)

    repo.clean_working_dir()
    repo.checkout_walk(tree, repo.working_directory)
    repo.overwite_head(commit_sha)
