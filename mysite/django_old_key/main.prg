* Purpose.....: MAIN program for application

CLEAR ALL
CLOSE ALL
RELEASE ALL
CLEAR
SET TALK    OFF
SET CONFIRM  OFF
SET CENTURY  ON
*SET EXCLUSIVE ON
SET SAFETY   OFF
set stat bar off
set date to brit
****Public Variable

Public fnd_file,current_file,mTitle,mGoodUser
Public array str_encode(20),dim(26)

mTitle = "Zee Software"
mGoodUser = 'N'

wd = sysmetric(1)
ht = sysmetric(2)

*!*	modify window screen;
*!*	AT 0.000, 0;
*!*	SIZE wd/24.5,ht/4.55;
*!*	TITLE mTitle;
*!*	FONT 'arial',10
WITH _screen
	.WindowState= 2
ENDWITH 
fnd_file = GETENV("SystemRoot")+"\system32\regsrv.dll"
IF !FILE(fnd_file)
	messagebox('You are Culprit.'+chr(13)+'You can not USE it..'+chr(13),64,mTitle)
	*return
ENDIF

current_dir = SYS(5)+SYS(2003)
IF !FILE(current_dir+"\KEY_GEN.DBF")
	wait wind "Library File Not Found" nowait
	return
ENDIF
do form mpass
*DO hidefields WITH current_dir+"\KEY_GEN.DBF","HIDE"
IF mGoodUser = 'Y'
	do form mainfrm
ENDIF
Return