# Submerge
Tool for batch-merging discrete subtitle files into their accompanying MKV video files (and more...)

# About
Submerge is a program intended to streamline the mass modification of MKV files. It uses the `mkvtoolnix` package to perform actions such as:
 * Merging discrete subtitle files into their matching MKV files
 * Properly tagging tracks in an MKV with the correct language

# Usage
Submerge makes use of pluggable modules to extend its functionality. These are stored in the `modules/` folder. To run a module, you call submerge as follows:
```bash
$ python3 -m submerge <module> ...
```
You can see more options by running `python3 -m submerge -h` or `python3 -m submerge <module> -h`.
