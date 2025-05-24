import sys
import re
import glob
import argparse

'''
Ancestry DNA shared matches to a csv file, intended to create a matrix of  matches to each other.
For your own, and from your matches "shared matches" pages, use browser to
"save page as text".
Name each one as .txt and place all together with this program.

Options:
--out-file default matches.csv
--skip-id default false
--id-with-name default false
--skip-header default false
--min-cm default 22

Assumptions: English pages, names contain only ascii
Needs: Python 3.6+

This code is released under the MIT License:
https://opensource.org/licenses/MIT
Copyright (c) 2025 John A. Andrea
v3.0

No support provided.
'''

def get_program_options():
    results = dict()

    # defaults
    results['out-file'] = 'matches.csv'
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


def escape_quote( s ):
    return str(s).replace( '"', '\"').replace( "'", "\'" )


def quoted( s ):
    return '"' + s.strip() + '"'


def output( owner, match, owner_id, match_id, cm, f ):
    # as csv
    if is_int( cm ) and int(cm) >= options['min-cm']:
       name1 = escape_quote( owner )
       name2 = escape_quote( match )

       rest = ''
       if options['add-id']:
          if options['id-with-name']:
             name1 += '/' + owner_id
             name2 += '/' + match_id
          else:
             rest = ',' + quoted( owner_id )
             rest += ',' + quoted( match_id )

       out = quoted( name1 )
       out += ',' + quoted( name2 )
       out += ',' + quoted( cm )
       out += rest
       print( out, file=f )


def is_int( s ):
    try:
       x = int( s )
       return True
    except ValueError:
       return False


options = get_program_options()

compareurl_pattern = re.compile( r'^.*discoveryui-matches/compare/([A-Za-z0-9-]*)/with/([A-Za-z0-9-]*)>' )
cm_pattern = re.compile( r'^(.*) cM | ' )

with open( options['out-file'], 'w' ) as outf:

     if options['add-header']:
        header = '"name 1","name 2","cM"'
        if options['add-id'] and not options['id-with-name']:
           header += ',"id 1","id 2"'
        print( header, file=outf )

     # as of 2025 the owner's name does not appear on the saved match page
     owner_name = 'you'

     for filename in glob.glob( '*.txt' ):
         #print( filename, file=sys.stderr )

         with open( filename ) as inf:
              match_name = ''
              owner_id = ''
              match_id = ''
              prev_line = ''
              for line in inf:
                  line = line.strip()
                  if line:
                     m = compareurl_pattern.match( line )
                     if m:
                        # name was previous line
                        match_name = prev_line
                        owner_id = m.group(1)
                        match_id = m.group(2)
                     else:
                        m = cm_pattern.match( line )
                        if m:
                           # also remove the hundreds separator (,)
                           cm = m.group(1).replace( ',', '' )

                           output( owner_name, match_name, owner_id, match_id, cm, outf )
                     prev_line = line