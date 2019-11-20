#!/usr/bin/env python3.6
'''Gitmines commit hashes starting with 000000'''

from datetime import datetime
from hashlib import sha1
import os
import subprocess
import sys
import zlib

GIT_STORE = '.git/objects/'

def make_commit(message):
    '''Composes commits with given msg in a loop until it finds one with
    6 preceding 0's'''
    tree_hash, parent_hash = get_tree_and_parent_hashes()
    user_name, user_email = get_user_name_and_email()
    timestamp = int(datetime.now().timestamp())
    # number used once we increment as proof of work in finding right sha1
    nonce = 0
    sha1 = ''
    while not sha1.startswith('000000'):
        # append nonce as 8-digit hex to message
        msg = f'{message}\n{nonce:08x}'
        # compose commit data
        commit = (
            f'tree {tree_hash}\n'
            f'{"parent " + parent_hash + os.linesep if parent_hash else ""}'
            f'author {user_name} <{user_email}> {timestamp} -0800\n'
            f'committer {user_name} <{user_email}> {timestamp} -0800\n\n'
            f'{msg}'
        )
        # header contains length of commit followed by null char
        header = f'commit {len(commit)}\0'
        store = header + commit
        sha1 = make_sha1(store)
        nonce += 1
        #if nonce > 2: break
    print(sha1)
    write_git_object(sha1, zlib_compress(store))
    hard_reset_to_generated_commit(sha1)
    
def hard_reset_to_generated_commit(sha1):
    '''Hard resets git staging area to generated commit state for pushing'''
    subprocess.check_output(['git', 'reset', '--hard', sha1]).decode('utf-8')[:-1]

def zlib_compress(store):
    '''Compresses object data via zlib'''
    return zlib.compress(bytes(store, 'utf-8'))

def write_git_object(sha1, compressed):
    '''Writes data associated with sha1 to git object store'''
    # dir name is first two characters of sha1
    dirname = GIT_STORE + sha1[:2]
    # file name is remaining sha1
    fullname = dirname + '/' + sha1[2:]
    if not os.path.isdir(dirname):
        os.mkdir(dirname)
    with open(fullname, 'wb') as f:
        f.write(compressed)

def make_sha1(commit):
    '''Encodes commit data as sha1 hex string'''
    return sha1(commit.encode('utf-8')).hexdigest()

def get_tree_and_parent_hashes():
    '''Gets tree_hash representing repo file tree and tries parent_hash'''
    tree_hash = subprocess.check_output(['git', 'write-tree']).decode('utf-8')[:-1]
    try:
        parent_hash = subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode('utf-8')[:-1]
    except subprocess.CalledProcessError:
        parent_hash = None
    return (tree_hash, parent_hash)

def get_user_name_and_email():
    '''Tries to get user name/email via git config or default data'''
    try:
        user_name = subprocess.check_output(['git', 'config', 'user.name']).decode('utf-8')[:-1]
    except subprocess.CalledProcessError:
        user_name = 'Dan Kozlowski'
    try:
        user_email = subprocess.check_output(['git', 'config', 'user.email']).decode('utf-8')[:-1]
    except subprocess.CalledProcessError:
        user_email = 'koz@planetscale.com'
    return (user_name, user_email)

if __name__ == '__main__':
    if len(sys.argv) < 3 or sys.argv[1] not in ['add', 'commit']:
        print('USAGE: gitchain <add|commit> <args>')
        exit(1)
    if sys.argv[1] == 'commit':
        if len(sys.argv) > 4 and sys.argv[2] == '-m':
            make_commit(sys.argv[3])
        else:
            print('USAGE: gitchain commit -m <message>')
    elif sys.argv[1] == 'add':
        try:
            subprocess.check_output(['git', 'add'] + sys.argv[2:])
        except Exception:
            Pass
