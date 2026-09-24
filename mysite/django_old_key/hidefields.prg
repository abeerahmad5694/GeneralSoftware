*----------------------------------------------------------------------------
* Filename: hidefields.prg
*    Since: 02/10/2005
*       By: DavidTindugan aka MzDarkReligion
*    notes: HideOption = 'HIDE' to hide fields
*                        'SHOW' to show fields
*----------------------------------------------------------------------------
PARAMETERS VFileName, HideOption

vfldctr = 0

IF FILE(VFileName)
  fp = FOPEN(VFileName,12)
  IF fp > 0
    
    *--- skip to the first field ----
    =FSEEK(fp,32,0)
    
    DO WHILE .T.
      VFieldData = FREAD(fp,32)
      vfldctr = vfldctr + 1
    
      VTagChar = SUBSTR(VFieldData,1,1)
    
      *--- is it END OF FIELD Definition tag = 0x0D -----------------
      IF VTagChar = CHR(0x0D)
        EXIT 
      *--- it is a field definition ---------------------------------
      ELSE
        vFldMarker = ASC(SUBSTR(VFieldData,19,1))
        *--- get current file position -----
        vCurPos = FSEEK(fp,0,1)
        
        *--- make sure that it is not a memo ---
        IF vFldMarker = 0x00 OR vFldMarker = 0x01
          DO CASE
            CASE HideOption = 'HIDE'
              *--- reposition and update the flag there ---
              vFlagPos = FSEEK(fp,vcurPos - 14,0)
              FWRITE(fp,CHR(0x01),1)
              *--- reposition to original position --------
              =FSEEK(fp,vCurPos,0)
            CASE HideOption = 'SHOW'
              *--- reposition and update the flag there ---
              vFlagPos = FSEEK(fp,vcurPos - 14,0)
              FWRITE(fp,CHR(0x00),1)
              *--- reposition to original position --------
              =FSEEK(fp,vCurPos,0)
           
          ENDCASE 
        ENDIF 
        
      ENDIF 
    ENDDO
    
    =FCLOSE(fp)
  ELSE
    MESSAGEBOX('Unable to Open Table ' + ALLTRIM(LOWER(vfilename)))
  ENDIF
ELSE
WAIT wind('Table ' + ALLTRIM(LOWER(vfilename)) + ' not found.')
ENDIF

