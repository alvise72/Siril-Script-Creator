#!/usr/bin/python3

import argparse
import sys
import os
import re

if __name__ == "__main__":
  parser = argparse.ArgumentParser(description="Tool to produce Siril script file")
#  parser.add_argument('-b',
#                    '--bias',
#                    type=str,
#                    required=False,
#                    dest='bias',
#                    default=None,
#                    help="Specify the folder containing the bias frames")
  parser.add_argument('-D',
                    '--dark-flat',
                    type=str,
                    required=False,
                    dest='darkflat',
                    default=None,
                    help="Specify the folder containing the dark for flat frames, or specify a single master darkflat file")
  parser.add_argument('-d',
                    '--dark',
                    type=str,
                    required=False,
                    dest='dark',
                    help="Specify the folder containing the dark frames, or specify a single master dark file")
  parser.add_argument('-l',
                      '--light',
                      type=str,
                      required=False,
                      dest='light',
                      default='Light',
                      help="Specify the folder containing the light frames")
  parser.add_argument('-o',
                      '--output',
                      type=str,
                      dest='output',
                      required=False,
                      help="Specify the filename of the siril script to create")
  parser.add_argument('-f',
                      '--flat',
                      type=str,
                      dest='flat',
                      required=False,
                      help="Specify the folder containing the flat/vignetting files")
  #parser.add_argument('-R',
  #                    '--raw',
  #                    action='store_true',
  #                    dest='raw',
  #                    required=False,
  #                    default=False,
  #                    help="Specify if source files are RAW from DSLR")
  parser.add_argument('-c',
                      '--cpu',
                      type=int,
                      dest='cpu',
                      required=False,
                      default=4,
                      help="Specify the number of cpu/cores to use")  
  parser.add_argument('dsoname',
                      metavar='DeepSpace Object Name',
                      type=str,
                      help="Specify the mandatory name of the deep sky object name")
  parser.add_argument('-S',
          		'--sigma-clipping',
          		type=str,
          		dest='sigmaclip',
          		required=False,
          		default="5,2",
          		help='Specify custom sigma low,high clipping parameters (format is #,#)'
          		)
  parser.add_argument('-E',
          		'--extract-ha-oiii',
          		action='store_true',
          		dest='extract_ha_oiii',
          		required=False,
          		default=False,
          		help='extract Hydrogen-alpha and Oxygen-III channels'
          		)
#  parser.add_argument(  '-O',
#  			'--extract-o3',
#  			action='store_true',
#  			dest='oiii',
#  			required=False,
#  			default=False,
#  			help='extract Oxygen-III channel' )
          		
  options = parser.parse_args()

  if options.sigmaclip != "5,2":
    if re.match('^[0-9]+,[0-9]+$', options.sigmaclip) == False:
      print("Bad format for sigma clipping parameters %s. Must be: 'number,number' specifying low,high sigma clipping. Stop!" %options.sigmaclip)
      sys.exit(1)  
  slow = options.sigmaclip.split(",")[0]
  shigh = options.sigmaclip.split(",")[1]
  #debayer=''
  #if options.raw == True:
  #  debayer=' -debayer -cfa'
  if options.extract_ha_oiii == False:
    color_options = '-cfa -equalize_cfa -debayer'
  else:
    color_options = '-cfa -equalize_cfa'
  output = "requires 0.99.8\n#set32bits\nsetmem 0.5"

  if options.cpu is not None:
    output += "\nsetcpu %d" %options.cpu

  master_darkflat = False
  master_dark = False

  if options.darkflat is not None:
    if os.path.isfile(options.darkflat) == True:
      master_darkflat = True
    else:
      if os.path.isdir(options.darkflat) == False:
        print("Element specified as --dark-flat option (%s) is not a file neither a directory. Stop!" %options.darkflat)
        sys.exit(1)

  if options.dark is not None:
    if os.path.isfile(options.dark) == True:
      master_dark = True
    else:
      if os.path.isdir(options.dark) == False:
        print("Element specified as --dark option (%s) is not a file neither a directory. Stop!" %options.dark)
        sys.exit(1)
      

  #------------------------------------------------------------------------------------------------------------------------------

  if options.darkflat is not None:
    if master_darkflat == False:
      output += "\n# DARK FLAT\ncd %s\nconvert %s -out=../Siril " %(options.darkflat.rstrip('/'), options.darkflat.rstrip('/'))
      output += "\ncd ../Siril\nstack DarkFlat median -nonorm -out=master-DarkFlat\ncd ../"

  #------------------------------------------------------------------------------------------------------------------------------

  if options.dark is not None:
    if master_dark == False:
      output += "\n# DARK\ncd %s\nconvert %s -out=../Siril \ncd ../Siril" %(options.dark.rstrip('/'), options.dark.rstrip('/'))
      output += "\nstack %s median -nonorm -out=master-%s" %(options.dark.rstrip('/'), options.dark.rstrip('/'))
      output += "\ncd ../"
     
  #------------------------------------------------------------------------------------------------------------------------------

  if options.flat is not None:
    output += "\n# FLAT\ncd %s\nconvert %s -out=../Siril \ncd ../Siril" %(options.flat.rstrip('/'), options.flat.rstrip('/'))
    if options.darkflat is not None:
      if master_darkflat == True:
        output += "\npreprocess %s -dark=%s %s -prefix=cal_ " %(options.flat.rstrip('/'), os.path.abspath(options.darkflat), color_options )
        output += "\nstack cal_%s median -norm=mul -out=master-%s" %(options.flat.rstrip('/'), options.flat.rstrip('/'))
      else:
        output += "\npreprocess %s -dark=master-DarkFlat %s -prefix=cal_ " %(options.flat.rstrip('/'), color_options)
        output += "\nstack cal_%s median -norm=mul -out=master-%s" %(options.flat.rstrip('/'), options.flat.rstrip('/'))
    else:
      output += "\nstack %s median -norm=mul -out=master-%s" %(options.flat.rstrip('/'), options.flat.rstrip('/'))
    output += "\ncd ../"

  #------------------------------------------------------------------------------------------------------------------------------
  
  output += "\n# LIGHT\ncd %s\nconvert %s -out=../Siril \ncd ../Siril" % (options.light.rstrip('/'), options.light.rstrip('/'))
  if options.dark is not None or options.flat is not None:
    output += "\npreprocess %s %s -prefix=cal_" %(options.light.rstrip('/'), color_options)
    if options.dark is not None:
      if master_dark == True:
        output += " -dark=%s" %os.path.abspath(options.dark)
      else:
        output += " -dark=master-%s" %options.dark.rstrip('/')
    if options.flat is not None:
      output += " -flat=master-%s" %options.flat.rstrip('/')
    
    # extract_HaOIII pp_light
    if options.extract_ha_oiii==True:
      output += "\nseqextract_HaOIII cal_%s" %options.light.rstrip('/')
      output += "\nregister Ha_cal_%s -prefix=reg_" %options.light.rstrip('/')
      output += "\nregister OIII_cal_%s -prefix=reg_" %options.light.rstrip('/')
      output += "\nstack reg_Ha_cal_%s rej %d %d -norm=addscale -output_norm -out=Ha_%s" %(options.light.rstrip('/'), int(slow), int(shigh), options.dsoname)
      output += "\nstack reg_OIII_cal_%s rej %d %d -norm=addscale -output_norm -out=OIII_%s" %(options.light.rstrip('/'), int(slow), int(shigh), options.dsoname)
    else:
      output += "\nregister cal_%s -prefix=reg_" %options.light.rstrip('/')
      output += "\nstack reg_cal_%s rej %d %d -norm=addscale -output_norm -out=%s" %(options.light.rstrip('/'), int(slow), int(shigh), options.dsoname)
      
  else:
    
    # extract_HaOIII pp_light
    if options.extract_ha_oiii==True:
      output += "\nseqextract_HaOIII cal_%s" %options.light.rstrip('/')
      output += "\nregister Ha_%s -prefix=reg_" %options.light.rstrip('/')
      output += "\nregister OIII_%s -prefix=reg_" %options.light.rstrip('/')
      output += "\nstack reg_Ha_%s rej %d %d -norm=addscale -output_norm -out=Ha_%s" %(options.light.rstrip('/'), int(slow), int(shigh), options.dsoname)      
      output += "\nstack reg_OIII_%s rej %d %d -norm=addscale -output_norm -out=OIII_%s" %(options.light.rstrip('/'), int(slow), int(shigh), options.dsoname)
    else:
      output += "\nregister %s -prefix=reg_" %options.light.rstrip('/')
      output += "\nstack reg_%s rej %d %d -norm=addscale -output_norm -out=%s" %(options.light.rstrip('/'), int(slow), int(shigh), options.dsoname)

  output += "\nclose"
  if options.extract_ha_oiii==True:
    output += "\ncd ..\nload Siril/Ha_%s.fit" %options.dsoname
    output += "\nsave Ha_%s" %options.dsoname
    output += "\nsavetif Ha_%s" %options.dsoname
    output += "\nsavepng Ha_%s" %options.dsoname
    output += "\nsavetif32 Ha_%s_32" %options.dsoname  
    output += "\n\nload Siril/OIII_%s.fit" %options.dsoname
    output += "\nsave OIII_%s" %options.dsoname
    output += "\nsavetif OIII_%s" %options.dsoname
    output += "\nsavepng OIII_%s" %options.dsoname
    output += "\nsavetif32 OIII_%s_32" %options.dsoname
  else:
    output += "\ncd ..\nload Siril/%s.fit" %options.dsoname
    output += "\nsave %s" %options.dsoname
    output += "\nsavetif %s" %options.dsoname
    output += "\nsavepng %s" %options.dsoname
    output += "\nsavetif32 %s_32" %options.dsoname
  #output += "\nsavejpg %s 100" %options.dsoname

  if options.output is not None:
    with open(options.output, 'w') as f:
      sys.stdout = f # Change the standard output to the file we created.
      print(output)
  else:
    print(output)
