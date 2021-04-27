# nopaystationpythondownloader

First of all, I am not an authority on anything. If this seems like it does somethign stupid, let me know. 

First install this badboy

https://github.com/windsurfer1122/PSN_get_pkg_info

Then hit it w/ 
pip3 install -r requirements.txt

i have it check the file integrity when it downloads it but encase you cancel a download in the middle and aren't sure you can set ValidateFiles = 1 and it will check the file integrity even if it's downloaded

when it does the check it only requests the header of the pkg link so only like 1 mb or less

