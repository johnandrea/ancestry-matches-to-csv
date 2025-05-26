import sys
import re
import glob
import argparse
sys.stdout.reconfigure(encoding='utf-8')

# Read through an Ancestry match page(s) saved as a text file.
# Example:
# ----------------------------
# ...
# You and MATCHNAME
# ...
# Your:
# ...
# MATCHNAME's
# ...
# OTHERMATCH <https://www.ancestry.COUNTRY/discoveryui-matches/compare/
# ID1/with/ID2...
# ...ID2/matchesofmatches>
# ...
# Your:
# relation of you with OTHERMATCH
# X cM
# paternal/maternal side
# MATCHNAME's
# relation of MATCHNAME with OTHERMATCH
# Y cM
# ...
# # OTHERMATCH2 <https://www.ancestry.COUNTRY/discoveryui-matches/compare/
# ID1/with/ID2...
# ...ID2/matchesofmatches>
# ...
# -----------------------------
# Program assumptions: English pages, names contain only ascii, cM values are integers
# Needs: Python 3.6+
#
# This code is released under the MIT License:
# https://opensource.org/licenses/MIT
# Copyright (c) 2025 John A. Andrea
# v0.9.5
# No support provided.


def get_program_options():
    results = dict()

    # defaults
    results['out-file'] = 'shared-matches.csv'
    results['min-cm'] = 22
    results['id-with-name'] = False

    # with names flipped into 'positive' verbs
    results['add-id'] = True
    results['add-header'] = True

    arg_help = 'Convert Ancestry matches output to CSV list.'
    parser = argparse.ArgumentParser( description=arg_help )

    arg_help = 'Do not include a header in the output file.'
    arg_default = not results['add-header']
    parser.add_argument( '--skip-header', default=arg_default, action='store_true', help=arg_help )

    arg_help = 'Do not include account unique ids in the output file.'
    arg_default = not results['add-id']
    parser.add_argument( '--skip-id', default=arg_default, action='store_true', help=arg_help )

    arg_help = 'Put id in name column. Otherwise in a separate column.'
    arg_default = results['id-with-name']
    parser.add_argument( '--id-with-name', default=arg_default, action='store_true', help=arg_help )

    arg_help = 'Minimum cM match to consider.'
    arg_help += ' Default is ' + str(results['min-cm'])
    arg_default = int(results['min-cm'])
    parser.add_argument( '--min-cm', default=arg_default, type=int, help=arg_help )

    arg_help = 'Output file. Default is ' + results['out-file']
    arg_default = results['out-file']
    parser.add_argument( '--out-file', default=arg_default, type=argparse.FileType('w'), help=arg_help )

    args = parser.parse_args()

    results['out-file'] = args.out_file.name
    results['min-cm'] = args.min_cm
    results['id-with-name'] = args.id_with_name

    results['add-id'] = not args.skip_id
    results['add-header'] = not args.skip_header

    return results


def is_int( s ):
    try:
       x = int( s )
       return True
    except ValueError:
       return False


def escape_quote( s ):
    # inside a csv file, add the escape slash
    return str(s).replace( '"', '\\"').replace( "'", "\\'" )


def quoted( s ):
    return '"' + s.strip() + '"'


def output( owner, owner_cm, other_name, other_id, match_name, match_id, match_cm, f ):
    # as csv
    if is_int( owner_cm ) and int(owner_cm) >= options['min-cm']:
       name1 = escape_quote( owner )
       name2 = escape_quote( other_name )
       name3 = escape_quote( match_name )

       if options['add-id']:
          if options['id-with-name']:
             name2 += '/' + other_id
             name3 += '/' + match_id

       out = quoted( name1 )
       out += ',' + quoted( owner_cm )
       out += ',' + quoted( name2 )
       if options['separate-id']:
          out += ',' + quoted( other_id )
       out += ',' + quoted( name3 )
       if options['separate-id']:
          out += ',' + quoted( match_id )
       out += ',' + quoted( match_cm )

       print( out, file=f )


start_pattern = re.compile( r'^.*<https://www.ancestry.*/discoveryui-matches/' )
end_pattern = re.compile( r'^.*matchesofmatches> *$' )

full_pattern = re.compile( r'^(.*) <https://www.ancestry.*/discoveryui-matches/compare/([A-Za-z0-9-]*)/with/([A-Za-z0-9-]*)/matchesofmatches>' )

partial_url = re.compile( r' <http.*' )

options = get_program_options()

# make a separate option
options['separate-id'] = options['add-id'] and not options['id-with-name']

with open( options['out-file'], 'w', encoding='utf-8' ) as outf:
     print( 'output in', options['out-file'] )

     if options['add-header']:
        if options['add-id']:
           if options['id-with-name']:
              header = '"you","cM with Other","Other","Match","cM with Other"'
           else:
              header = '"you","cM with Other","Other","Other id","Match","cM with Other","Match id"'
        else:
           header = '"you","cM with Other","Other","Match","cM with Other"'
        print( header, file=outf )

     for filename in glob.glob( '*.txt' ):
         #print( filename, file=sys.stderr )

         with open( filename, 'r', encoding='utf-8' ) as inf:
              found_you_and = False
              name_of_match = ''

              match_open = False
              match_ready = False
              match_line = ''
              your_n = 0

              other_name = ''
              your_cm = ''
              match_cm = ''

              n = 0
              for line in inf:
                  line = line.strip()
                  if line:
                     #print( line )
                     n += 1

                     if line.startswith( 'You and ' ) and not found_you_and:
                        # this occors only once per input file
                        found_you_and = True
                        name_of_match = line.replace( 'You and ', '' )
                        # the name might look like: You and First Second <https://www.ancestry...
                        # so also get rid of that url
                        name_of_match = re.sub( partial_url, '', name_of_match )
                        #print( '! you and', n, name_of_match )

                     m = start_pattern.match( line )
                     if m and found_you_and:
                        match_open = True
                        #print( '! open', n, line )

                     if match_open:
                        match_line += line

                     m = end_pattern.match( line )
                     if m and match_open:
                        match_open = False
                        match_ready = True
                        #print( '! close', n, line )

                     if match_ready and line == 'Your:':
                        your_n = n

                     if match_ready and n == ( your_n + 2 ):
                        your_cm = line.replace( ' cM', '' ).replace( ',', '' )
                        #print( '! your cm', n, your_cm )

                     if match_ready and n == ( your_n + 6 ):
                        match_cm = line.replace( ' cM', '' ).replace( ',', '' )
                        #print( '! match cm', n, match_cm )

                        m = full_pattern.match( match_line )
                        if m:
                           #print( '! output' )
                           other_name = m.group(1)
                           match_id = m.group(2)
                           other_id = m.group(3)

                           output( 'you', your_cm, other_name, other_id, name_of_match, match_id, match_cm, outf )

                        else:
                           print( 'didnt match:', file=sys.stderr )
                           print( match_line, file=sys.stderr )

                        match_open = False
                        match_ready = False
                        match_line = ''
                        your_line = 0
