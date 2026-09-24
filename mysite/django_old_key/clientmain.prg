Public mConfirm,mTitle
mConfirm = 'Y'
mTitle = "Zee Software"

wd = sysmetric(1)
ht = sysmetric(2)

modify window screen;
AT 0.000, 0;
SIZE wd/24.5,ht/4.55;
TITLE mTitle;
FONT 'arial',10

current_dir = SYS(5)+SYS(2003)


IF FILE(current_dir+"\client.lib")
	messagebox('Here Enter Client ID',64,mTitle)
	do form new_client_id
	DELETE FILE current_dir+"\client.lib"
ENDIF

IF !FILE(current_dir+"\client.dll")
	wait wind "Original Library File Not Found" nowait
	*return
ENDIF

DO FORM mwait

