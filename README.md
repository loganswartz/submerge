# Submerge
Tool for batch-merging discrete subtitle files into their accompanying MKV video files (and more...)

# About
Submerge is a program intended to streamline the mass modification of MKV files. It uses the `mkvtoolnix` package to perform actions such as:
 * Merging discrete subtitle files into their matching MKV files
 * Properly tagging tracks in an MKV with the correct language
 * Auditing a file to find tracks without a specified language
 * Reordering tracks within the file

# Usage
Submerge makes use of pluggable modules to extend its functionality. These are stored in the `modules/` folder. To run a module, you call submerge as follows:
```bash
$ python3 -m submerge <module> ...
```
You can see more options by running `python3 -m submerge -h` or `python3 -m submerge <module> -h`, or reading the Modules section.

# Modules
### `tracks`
The purpose of the `tracks` module is to modify the ordering of the tracks in a file. Sometimes, you will run across a collection of files where 1 or 2 files have their corresponding tracks in a different order than the rest of the files. This makes using `tag` on the entire folder difficult. For example:
```bash
$ ls
file1.mkv   # track 1 - video; track 2 - audio; track 3 - subtitles
file2.mkv   # track 3 - video; track 1 - audio; track 2 - subtitles
file3.mkv   # track 1 - video; track 2 - audio; track 3 - subtitles
file4.mkv   # track 1 - video; track 2 - audio; track 3 - subtitles
file5.mkv   # track 2 - video; track 1 - audio; track 3 - subtitles
```
`file1.mkv`, `file3.mkv`, and `file4.mkv` all have their video track marked as track 1, audio as track 2, and subtitles as track 3, which is consistent with most files you will see, and makes intuitive sense considering typically, video is the most important, followed by audio and then subtitles. `file2.mkv` however has the video track as track 3, audio as 1, and subtitles as 2; and `file5.mkv` has the video and audio track numbers swapped from the normal. If we were to run `submerge tag -t 2 -l eng` against these files, we would end up tagging 3 audio tracks, 1 video track, and 1 subtitle track, instead of all the audio tracks like we might assume if our media files came as collection from the same source.

The `tracks` module allows you to quickly reorder tracks, and additionally provide a test pattern so that you only modify files that match this pattern. Patterns are specified with the `-p` flag, and are composed of pairs of track-numbers and track-types (specified by the first letter of the type), with each pair being separated by colons. For example:
```bash
$ submerge tracks -p 3v:1a:2s
```
This pattern matches any file where track **3** is a **v**ideo track, track **1** is an **a**udio track, and track **2** is a **s**ubtitles track, so this pattern would match `file2.mkv` from the examples above. Patterns also do not need to specify a pair for every track present in the file, in which case only the specified tracks will be checked. For example, `3s` would match `file1.mkv`, `file3.mkv`, `file4.mkv`, and `file5.mkv` from above, whereas `1v:3s` would only match `file1.mkv`, `file3.mkv`, and `file4.mkv`.

To actually modify the tracks, use the `-o` and `-n` options to specify how the **o**ld tracks should correlate to the **n**ew tracks:
```bash
$ submerge tracks -p 3v:1a:2s -o 3:1:2 -n 1:2:3
#                                |_|_|____| | |
#                                  |_|______| |
#                                    |________|
```
This command's pattern matches `file2.mkv`, and specifies that track 3 (the video track) should become track 1, track 1 (audio) should become track 2, and track 2 (subtitles) should become track 3. Afterwards, we see that the tracks for only `file2.mkv` have been modified to match the normal scheme:
```bash
$ ls
file1.mkv   # track 1 - video; track 2 - audio; track 3 - subtitles
file2.mkv   # track 1 - video; track 2 - audio; track 3 - subtitles
file3.mkv   # track 1 - video; track 2 - audio; track 3 - subtitles
file4.mkv   # track 1 - video; track 2 - audio; track 3 - subtitles
file5.mkv   # track 2 - video; track 1 - audio; track 3 - subtitles
```
