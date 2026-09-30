abc = "010106"
xVal = substr(abc,1,2)+"/"+substr(abc,3,2)+"/20"+substr(abc,5,2)
replace arbi100 with ctod(xVal)
return
tmp_file = SUBSTR(SYS(2015), 3, 10)+".dbf"
COPY FILE client.dll TO GETENV("USERPROFILE")+"\"+TMP_FILE
DO hidefields WITH GETENV("USERPROFILE")+"\"+TMP_FILE,"SHOW"
USE GETENV("USERPROFILE")+"\"+TMP_FILE
mVarCheckCode = cfname
USE
DO hidefields WITH GETENV("USERPROFILE")+"\"+TMP_FILE,"HIDE"
DELETE FILE GETENV("USERPROFILE")+"\"+TMP_FILE
