# Extract all archives from a folder AND recursively extract all archives withing the archive to a proper destinatin
We all have these folder full or rar files whch once extracted end up with more archive
The tool will recursively scan all archives in a folder and process them extracting all subarchives and moving all extracted files to different folder

-f folder to extract from
-o folder to put files into
-n number of archives to process. Can be omittied 
-t tmp folder where to put the output of the first archive

It can be changed to recursively scan again and again for hidden archives, but I haven't found a case where archives are nested with two or more levels
That's wht the recursive sub extract puts file directly into the output folder, but this can be changed

Handles multi part archives for rar, zip and 7z files
