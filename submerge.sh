#!/bin/bash

mkvdir="$1"
subdir="$2"

echo mkvdir = $1
echo subdir = $2
echo mkvdir:0:1 = ${mkvdir:0:1}
echo Full dir = "$(pwd)/$mkvdir"
echo '$mkvdir$subdir' = "$mkvdir/$subdir"
echo ""
echo ""

# if no directory is specified, assume pwd, else, if dir doesn't start with /, assume a relative path and make it absolute
if [ "$mkvdir" == "" ]
then
	mkvdir="$(pwd)"
elif [ "$mkvdir" == "." ]
then
	mkvdir="$(pwd)"
elif [ "${mkvdir:0:1}" != "/" ]
then
	mkvdir="$(pwd)/$mkvdir"
fi


if [ "${mkvdir:(-1)}" == "/" ]
then
	mkvdir="${mkvdir:0:-1}"
fi


echo "mkvdir = $mkvdir"

# if subdir isn't specified, assume same as mkvdir, else, if dir doesn't start with /, assume a relative path and make it absolute
if [ "$subdir" == "" ]
then
	subdir="$mkvdir"
elif [ "${subdir:0:1}" != "/" ]
then
	subdir="$mkvdir/$subdir"
fi


if [ "${subdir:(-1)}" == "/" ]
then
	subdir="${subdir:0:-1}"
fi


echo "subdir = $subdir"

# regex for checking if sub file exists
# regex="\.\/(.+)\.(srt|ass|ssa|usf|pgs|idx)$"

# for all mkv files in mkvdir, check if there exists a correlating sub file
cd "$mkvdir"
for file in ./*.mkv
do
	escapedfilename="$(printf '%s' "$subdir/${file:2}" | sed 's/[.[\*^C()+?{|]/\\&/g')" # escapes regex tokens found in filename pre-search
	subfile=$(find "$subdir" -regextype posix-extended -regex "${escapedfilename:0:-5}.+\.(srt|ass|ssa|usf|pgs|idx)$")
	outfile="${file:0:-4}-SUBBED.mkv"
	echo $file
	echo "\$(find . -regextype posix-extended -regex \"${escapedfilename:0:-3}(srt|ass|ssa|usf|pgs|idx)$\")"
	
	# if subfile found is a .idx, also include the accompanying .sub file
	if [ "$subfile" == "" ]
	then
		echo "Subs not found. Skipping $file."
	elif [ "${subfile:(-3)}" == "idx" ]
	then
		echo ""
		echo ""
		echo "File and subtitles found. Merging $file and $subfile."
		mkvmerge -o "$outfile" "$file" --language 0:eng --track-name 0:English --default-track 0:0 "$subfile" "${subfile:0:-4}.sub"
		# echo "mkvmerge -o \"$outfile\" \"$file\" --language 0:eng --track-name 0:English --default-track 0:0 \"$subfile\" \"${subfile:0:-4}.sub\""
		# echo "Subs are .idx"
	else
		echo ""
		echo ""
		echo "File and subtitles found. Merging $file and $subfile."
		mkvmerge -o "$outfile" "$file" --language 0:eng --track-name 0:English --default-track 0:0 "$subfile" "${subfile:0:-4}.sub"
		mkvmerge -o "$outfile" "$file" --language 0:eng --track-name 0:English --default-track 0:0 "$subfile"
		echo "mkvmerge -o \"$outfile\" \"$file\" --language 0:eng --track-name 0:English --default-track 0:0 \"$subfile\""
		# echo "Subs are not .idx"
	fi
done

exit 0
