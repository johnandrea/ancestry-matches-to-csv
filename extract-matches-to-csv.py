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
--skip-id default true
--id-with-name default false
--skip-header default false
--min-cm default 22

Assumptions: English pages, names contain only ascii
Needs: Python 3.6+

This code is released under the MIT License:
https://opensource.org/licenses/MIT
Copyright (c) 2022 John A. Andrea
v2.0

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

def get_owner_name( s, pattern1, pattern2 ):
    result = None
    m = pattern1.match( s )
    if m:
       result = m.group(1)
    else:
       m = pattern2.match( s )
       if m:
          result = m.group(1)
    return result

def get_url( s, line_pattern ):
    ids = []
    m = line_pattern.match( s )
    if m:
       ids.append( m.group(1) )
       ids.append( m.group(2) )
    return ids

def get_cm( s, line_pattern ):
    result = None
    m = line_pattern.match( s.lower() )
    if m:
       # also remove the hundreds separator (,)
       result = m.group(1).replace( ',', '' )
    return result

def escape_quote( s ):
    return str(s).replace( '"', '\"').replace( "'", "\'" )

def output( one, two, three, four, five, f ):
    # as csv
    out = '"' + one + '"'
    out += ',"' + two + '"'
    out += ',"' + three + '"'
    if four:
       out += ',"' + four + '","' + five + '"'
    print( out, file=f )

def is_int( s ):
    try:
       x = int( s )
       return True
    except ValueError:
       return False


options = get_program_options()

name_pattern1 = re.compile( r'^(.*)\'s DNA Matches$' ) # account owner
name_pattern2 = re.compile( r'^You and (.*)$' ) # matches of account owner
url_pattern = re.compile( r'^.*discoveryui-matches/compare/([A-Za-z0-9-]*)/with/([A-Za-z0-9-]*)>' )
cm_pattern = re.compile( r'^(.*) cm | ' )

not_names = [] # must be lower case
not_names.append( 'view match' )
not_names.append( 'common ancestor' )
not_names.append( 'do you recognize them?' )

with open( options['out-file'], 'w' ) as outf:

     if options['add-header']:
        header = '"name 1","name 2","cM"'
        if options['add-id'] and not options['id-with-name']:
           header += ',"id 1","id 2"'
        print( header, file=outf )

     # these are the case labels for the loop over lines
     first_step = 'owner'
     person_url = 'person url'
     person_name = 'person name'
     cm_tag = 'cm'

     for filename in glob.glob( '*.txt' ):
         #print( filename, file=sys.stderr )

         owner_name = None
         match_name = None
         url_ids = []
         look_for = first_step

         with open( filename ) as inf:
              for line in inf:
                  line = line.strip()
                  if line:
                     if look_for == first_step:
                        name = get_owner_name( line, name_pattern1, name_pattern2 )
                        if name:
                           owner_name = escape_quote( name )
                           look_for = person_url

                     elif look_for == person_url:
                        url_ids = get_url( line, url_pattern )
                        if url_ids:
                           look_for = person_name

                     elif look_for == person_name:
                        # this will be the next line after the url
                        if line.lower() in not_names:
                           # this is a clickable item, keep looking for the person start line
                           look_for = person_url
                        else:
                           match_name = line
                           look_for = cm_tag

                     elif look_for == cm_tag:
                        cm = get_cm( line, cm_pattern )
                        if cm:
                           if is_int( cm ) and int(cm) >= options['min-cm']:
                              name1 = owner_name
                              name2 = escape_quote(match_name)
                              if options['add-id']:
                                 if options['id-with-name']:
                                    output( name1 + '/' + url_ids[0], name2 + '/' + url_ids[1], str(cm), None, None, outf )
                                 else:
                                    output( name1, name2, str(cm), url_ids[0], url_ids[1], outf )
                              else:
                                 output( name1, name2, str(cm), None, None, outf )
                           look_for = person_url

              if not owner_name:
                 print( filename, ':reached and of file without finding owner', file=sys.stderr )

              if look_for != person_url:
                 print( filename, 'didnt complete search', look_for, file=sys.stderr )
