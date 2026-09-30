*----------encrypt.prg----------
* 
* Alias for cipher
? encrypt("zaheer")
FUNCTION encrypt
LPARAMETERS tcStr, tcPassword
RETURN cipher(tcStr, tcPassword)
*----------decrypt.prg----------
* 
* Alias for cipher
FUNCTION decrypt
LPARAMETERS tcStr, tcPassword
RETURN cipher(tcStr, tcPassword)

*----------cipher.prg----------
FUNCTION cipher
LPARAMETERS tcStr, tcPassword

#define   ERRORNEGL    -1L
#define   PW_MIN_LEN   3        &&  /* number of chars in password */
#define   PW_MIN_NUM   1000 	  &&  /* number of digits in password return number */

LOCAL lnStrLen, lnPassLen, lnPassNum, laPassword[1,2], lcPassword
LOCAL lcStrOut, lnPassPos, lnNum01, lcStrOut, lnInPos, lnPassPos

IF TYPE("tcStr") <> "C" ;
		OR TYPE("tcPassword") <> "C" ;
		OR LEN(tcPassword) < PW_MIN_LEN
	Error 11
ENDIF

lnStrLen = LEN(tcStr)

* Because of the bug in the original C code we've to add CHR(0) to the password
* 		and use it later
lcPassword = tcPassword + CHR(0)
lnPassLen = LEN(lcPassword)
DIMENSION laPassword[lnPassLen+1,2]
FOR lnPassPos=1 TO lnPassLen
	laPassword[lnPassPos,2] = SUBSTR(lcPassword,lnPassPos,1)
	laPassword[lnPassPos,1] = ASC(laPassword[lnPassPos,2])
ENDFOR

* Get seed value
lnPassNum = INT((((CipherGetPnum(lcPassword)/997) - 1) % 254) + 1 )
lcStrOut = ""
lnPassPos = 1

* Encode/decode each character
FOR lnInPos=0 TO lnStrLen-1
	* Get new seed value
	lnNum01 = (( lnPassNum + (lnInPos - lnStrLen)) - 1)
	lnPassNum = (ABS(lnNum01) % 254) * SIGN(lnNum01) + 1
	* Encode current character
	lnByte = BITXOR( ASC(SUBSTR(tcStr,lnInPos+1,1)), ;
		BITXOR(lnPassNum, laPassword[lnPassPos,1]))
	* Convert signed value to unsigned, if necessary
	lnByte = BITAND(lnByte, 0xFF)
	* If result is zero, use current character
	lcStrOut = lcStrOut + IIF(lnByte = 0, SUBSTR(tcStr,lnInPos+1,1), CHR(lnByte))
	* Advance to the next password character
	lnPassPos = IIF( lnPassPos => lnPassLen, 1, lnPassPos + 1)
ENDFOR

RETURN lcStrOut

* Returns a seed value based on the string passed as parameter
FUNCTION CipherGetPnum(tcStr)
	LOCAL liRet, lnPos
	liRet = 1
	FOR lnPos=0 TO LEN(tcStr ) - 1
		liRet = liRet + ASC(SUBSTR(tcStr,lnPos+1,1)) + lnPos
	ENDFOR
	DO WHILE (liRet < PW_MIN_NUM)
		liRet = BITLSHIFT(liRet,1)
	ENDDO
	RETURN liRet
ENDFUNC