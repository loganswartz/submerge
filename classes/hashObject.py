import hashlib
import pathlib
import shutil
import time
import os
import errno

def getHash(inputPath: pathlib.Path, algorithm: str = "sha256"):
    # 64kb
    path = inputPath.expanduser().resolve()

    bufferSize = 65536
    if algorithm not in hashlib.algorithms_guaranteed:
        raise ValueError(f"'{algorithm}' is not supported. (See 'hashlib.algorithms_guaranteed' for valid algorithms)")
    if not path.exists():
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), str(path))

    hash = hashlib.new(algorithm)

    # if dir, return hash of dir and all children
    if path.is_dir():
        hashes = {}
        # directory name is hashed, and inserted into the hash object for the directory as the first entry.
        # this way, the final buffer for the hash object (before final digest) looks like this:
        #   1. hash of directory name
        #   <sorted alphabetically by filename>:
        #       2. hash of contents of file1
        #       3. hash of contents of file2
        #       ... etc etc ...
        #       n. hash of contents of fileN
        #
        # Why do I incorporate the name of the folder as a part of the folder's hash, but don't do the same for files?
        # If I didn't hash the folder names, folders that have different names but have identical contents and sorting positions
        # would have identical hashes. Honestly, I probably don't need to do this, but I felt like it couldn't hurt anything so why not?

        # on further testing, I've figured it out more:
        # Doing this (maybe?) prevents directories with only 1 other directory inside them from being invisible (in the hash)
        #   --> not exactly; as it turns out with this particular implementation, the empty directory at the bottom of the chain
        #       hashes to the "empty hash" for whichever particular algorithm you are using, as I expected. However, the hash at
        #       the bottom of the chain doesn't bubble up like I initially thought, it actually gets hashed each time it bubbles
        #       up. Thus, without the folder name hashing, two sets of empty but differently named directories of the same depth
        #       would have the same hash. Not a very large edge-case, but may as well cover it.
        dirTitleHash = hashlib.new(algorithm)
        dirTitleHash.update(bytes(path.name, 'utf-8'))
        hash.update(bytes(dirTitleHash.hexdigest(), 'utf-8'))
        # get hashes of all children
        for child in path.iterdir():
            # recursively calls this function
            hashes[child.name] = getHash(child)
        # sort list by key and concatenate all hashes as byte-like objects (sorting ensures they're always in the same order)
        for key, value in sorted(hashes.items()):
            hash.update(bytes(value, 'utf-8'))
        # return hash of concatenated hashes
        return hash.hexdigest()
    #else, return hash of file
    elif path.is_file():
        with open(path, 'rb') as f:
            while True:
                data = f.read(bufferSize)
                if not data:
                    break
                hash.update(data)
        return hash.hexdigest()
    else:
        raise Exception("getHash() encountered an object that evaluates false for both the 'pathlib.Path.is_dir()' AND 'pathlib.Path.is_file()' functions, unsure how to process.")


def compareHash(file1: pathlib.Path, file2:pathlib.Path):
    return getHash(file1) == getHash(file2)

def main():
    # allows you to test hashing speeds on different algorithms
    itervalue = 2
    hashalgo1 = "md5"
    hashalgo2 = "sha256"
    src = pathlib.Path("jojo1.mkv").resolve()
    dst = pathlib.Path("jojo2.mkv").resolve()

    hash1begin = time.time()
    for i in range(itervalue):
        fileHash = getHash(src, hashalgo1)
    hash1end = time.time()
    hash2begin = time.time()
    for i in range(itervalue):
        file2Hash = getHash(dst, hashalgo1)
    hash2end = time.time()
    
    print(f"{src.name} hash: {fileHash}\n{dst.name} hash: {file2Hash}")
    
    hash3begin = time.time()
    for i in range(itervalue):
        fileHash = getHash(src, hashalgo2)
    hash3end = time.time()
    hash4begin = time.time()
    for i in range(itervalue):
        file2Hash = getHash(dst, hashalgo2)
    hash4end = time.time()
    
    hash1time = hash1end - hash1begin
    hash2time = hash2end - hash2begin
    hash3time = hash3end - hash3begin
    hash4time = hash4end - hash4begin
    
    # hash speed in MB/s
    md5speed     = (((os.path.getsize(src)+os.path.getsize(dst))/2)/(((hash1time+hash2time)/2)/itervalue))/1000000
    sha256speed  = (((os.path.getsize(src)+os.path.getsize(dst))/2)/(((hash3time+hash4time)/2)/itervalue))/1000000
    
    print(f"{src.name} hash: {fileHash}")
    print(f"{dst.name} hash: {file2Hash}")
    print(f"Hashes are identical? --> {str(compareHash(src, dst))}")
    print()
    print(f"Hash1 time: {format(hash1time, '.2f')}")
    print(f"Hash2 time: {format(hash2time, '.2f')}")
    print(f"Hash3 time: {format(hash3time, '.2f')}")
    print(f"Hash4 time: {format(hash4time, '.2f')}")
    print()
    print(f"{hashalgo1} hash speed: {format(md5speed, '.2f')} MB/s")
    print(f"{hashalgo2} hash speed: {format(sha256speed, '.2f')} MB/s")
    print(f"{hashalgo1} is {format(md5speed/sha256speed, '.2f')}x faster than {hashalgo2}.")
    print(f"{hashalgo2} is {format((1-(sha256speed/md5speed))*100, '.0f')}% slower than {hashalgo1}.")
    
    exit(0)

#    if dir:
#        recursively hash dir
#    elif file:
#        hash file
if __name__ == "__main__":
    main()
