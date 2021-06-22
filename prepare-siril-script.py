#!/usr/bin/python3

import argparse
import sys
import os

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
  parser.add_argument('-H',
          		'--extract-ha',
          		action='store_true',
          		dest='ha',
          		required=False,
          		default=False,
          		help='extract Hydrogen-alpha channel'
          		)
  parser.add_argument(  '-O',
  			'--extract-o3',
  			action='store_true',
  			dest='oiii',
  			required=False,
  			default=False,
  			help='extract Oxygen-III channel' )
          		
  options = parser.parse_args()

  #debayer=''
  #if options.raw == True:
  #  debayer=' -debayer -cfa'

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
        output += "\npreprocess %s -dark=%s -prefix=cal_ " %(options.flat.rstrip('/'), os.path.abspath(options.darkflat) )
        output += "\nstack cal_%s median -norm=mul -out=master-%s" %(options.flat.rstrip('/'), options.flat.rstrip('/'))
      else:
        output += "\npreprocess %s -dark=master-DarkFlat -prefix=cal_ " %options.flat.rstrip('/')
        output += "\nstack cal_%s median -norm=mul -out=master-%s" %(options.flat.rstrip('/'), options.flat.rstrip('/'))
    else:
      output += "\nstack %s median -norm=mul -out=master-%s" %(options.flat.rstrip('/'), options.flat.rstrip('/'))
    output += "\ncd ../"

  #------------------------------------------------------------------------------------------------------------------------------
  
  output += "\n# LIGHT\ncd %s\nconvert %s -out=../Siril \ncd ../Siril" % (options.light.rstrip('/'), options.light.rstrip('/'))
  if options.dark is not None or options.flat is not None:
    output += "\npreprocess %s" %options.light.rstrip('/')
    if options.dark is not None:
      if master_dark == True:
        output += " -dark=%s" %os.path.abspath(options.dark)
      else:
        output += " -dark=master-%s" %options.dark.rstrip('/')
    if options.flat is not None:
      output += " -flat=master-%s" %options.flat.rstrip('/')
    output += "  -cfa -equalize_cfa -debayer -prefix=cal_ "
    output += "\nregister cal_%s -prefix=reg_" %options.light.rstrip('/')
    output += "\nstack reg_cal_%s rej 3 4 -norm=addscale -output_norm -out=%s" %(options.light.rstrip('/'), options.dsoname)
  else:
    output += "\nregister %s -prefix=reg_" %options.light.rstrip('/')
    output += "\nstack reg_%s rej 3 4 -norm=addscale -output_norm -out=%s" %(options.light.rstrip('/'), options.dsoname)

  output += "\nclose"

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
