import sys
import re
import glob
import argparse
sys.stdout.reconfigure(encoding='utf-8')

# Read through an Ancestry match page(s) saved as a text file.
# Example input:
# ----------------------------
# You and *MATCH NAME* <https://www.ancestry
#
# *SHARED NAME* <https://www.ancestry.../discoveryui-matches/compare/
# *YOUR ID*
# /with/
# *SHARED ID*
# /matchesofmatches>
# ...
# Managed by *MANAGED NAME*
# ...
# Your:
# *YOUR RELATIONSHIP WITH SHARED*
# *YOUR CM WITH SHARED* cM
# ...
# MATCH NAME's:
# *MATCH RELATIONSHIP WITH SHARED*
# *MATCH CM WITH SHARED* cM
# ...
# -----------------------------
# Program assumptions: English pages, names contain only ascii, cM values are integers
# Needs: Python 3.6+
#
# This code is released under the MIT License:
# https://opensource.org/licenses/MIT
# Copyright (c) 2025 John A. Andrea
# No support provided.


def get_version():
    return '4.1'


def get_program_options():
    results = dict()

    # defaults
    results['out-file'] = 'shared-matches.csv'
    results['min-cm'] = 22
    results['id-with-name'] = False

    # with names flipped into 'positive' verbs
    results['add-id'] = True
    results['add-header'] = True
    results['add-relation'] = True

    arg_help = 'Convert Ancestry matches output to CSV list.'
    parser = argparse.ArgumentParser( description=arg_help )

    arg_help = 'Show version then exit.'
    parser.add_argument( '--version', action='version', version=get_version() )

    arg_help = 'Do not include a header in the output file.'
    arg_default = not results['add-header']
    parser.add_argument( '--skip-header', default=arg_default, action='store_true', help=arg_help )

    arg_help = 'Do not include relationship estimates in the output file.'
    arg_default = not results['add-relation']
    parser.add_argument( '--skip-relationship', default=arg_default, action='store_true', help=arg_help )

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
    results['add-relation'] = not args.skip_relationship

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
    # inside a csv
    return '"' + s.strip() + '"'


def output_header( f ):
    # you vs shared
    out = '"Your cM with Shared person"'
    if options['add-relation']:
       out += ',"Your relation to Shared person"'

    # shared
    out += ',"Shared person"'
    if options['add-id'] and not options['id-with-name']:
       out += ',"Shared person id"'

    # match vs shared
    out += ',"Match","Match cM with Shared person"'
    if options['add-relation']:
       out += ',"Match relation to Shared person"'

    out += ',"Managed by"'

    print( out, file=f )


def output( data, f ):
    # as csv
    if is_int( data['your_cm'] ) and int(data['your_cm']) >= options['min-cm']:
       shared = escape_quote( data['shared_name'] )
       match = escape_quote( data['match_name'] )

       out = ''

       if options['add-id']:
          if options['id-with-name']:
             shared += '/' + data['shared_id']

       # you vs shared
       out += ',' + quoted( data['your_cm'] )
       if options['add-relation']:
          out += ',' + quoted( data['your_relation'] )

       # shared
       out += ',' + quoted( shared )
       if options['separate-id']:
          out += ',' + quoted( data['shared_id'] )

       # match vs shared
       out += ',' + quoted( match )
       out += ',' + quoted( data['match_cm'] )
       if options['add-relation']:
          out += ',' + quoted( data['match_relation'] )

       out += ',' + quoted( data['managed_by'] )

       # remove leading comma
       if out.startswith( ',' ):
          out = out.replace( ',', '', 1 )

       print( out, file=f )


start_pattern = re.compile( r'^.*<https://www.ancestry.*/discoveryui-matches/' )
end_pattern = re.compile( r'^.*matchesofmatches> *$' )

full_pattern = re.compile( r'^(.*) <https://www.ancestry.*/discoveryui-matches/compare/([A-Za-z0-9-]*)/with/([A-Za-z0-9-]*)/matchesofmatches>' )

cm_pattern = re.compile( r'^([0-9,]+) cM$')

partial_url = re.compile( r' <http.*' )

options = get_program_options()

# make a separate option
options['separate-id'] = options['add-id'] and not options['id-with-name']

with open( options['out-file'], 'w', encoding='utf-8' ) as outf:
     print( 'output in', options['out-file'] )

     if options['add-header']:
        output_header( outf )

     data = dict()

     for filename in glob.glob( '*.txt' ):
         with open( filename, 'r', encoding='utf-8' ) as inf:
              found_you_and = False
              data['match_name'] = ''

              # found the line that starts with other name and ids
              match_open = False

              # found the end of the ids url
              match_ready = False

              # what the whole match line will be
              match_line = ''

              # found the line "Your:"
              cm_open = False

              # number of cM lines after "Your:"
              cm_count = 0

              data['shared_name'] = ''
              data['shared_id'] = ''
              data['your_cm'] = ''        # with shared
              data['your_relation'] = ''  # with shared
              data['match_cm'] = ''       # with shared
              data['match_relation'] = '' # with shared
              data['managed_by'] = ''

              prev_line = ''

              for line in inf:
                  line = line.strip()
                  if line:

                     if line.startswith( 'You and ' ) and not found_you_and:
                        # this occors only once per input file
                        found_you_and = True
                        match_name = line.replace( 'You and ', '' )
                        # the name might look like: You and First Second <https://www.ancestry...
                        # so also get rid of that url
                        data['match_name'] = re.sub( partial_url, '', match_name )

                     m = start_pattern.match( line )
                     if m and found_you_and:
                        match_open = True
                        match_line = ''

                     if match_open:
                        match_line += line

                     m = end_pattern.match( line )
                     if m and match_open:
                        match_open = False
                        match_ready = True

                     if match_ready and line.startswith( 'Managed by ' ):
                        data['managed_by'] = line.replace( 'Managed by ', '' )

                     if match_ready and line == 'Your:':
                        cm_open = True
                        cm_count = 0

                     m = cm_pattern.match( line)
                     if m and cm_open:
                        cm_count += 1
                        cm = line.replace( ' cM', '' ).replace( ',', '' )

                        if cm_count == 1:
                           data['your_cm'] = cm
                           data['your_relation'] = prev_line

                        else:
                           # second cM line
                           data['match_cm'] = cm
                           data['match_relation'] = prev_line

                           m = full_pattern.match( match_line )
                           if m:
                              data['shared_name'] = m.group(1)
                              #owner_id = m.group(2)  # not useful
                              data['shared_id'] = m.group(3)

                              #output( 'you', your_cm, your_relation, other_name, other_id, name_of_match, match_cm, match_relation, managed_by, outf )
                              output( data, outf )

                           else:
                              # it is possible something was wrong
                              print( 'didnt match compare url:', file=sys.stderr )
                              print( match_line, file=sys.stderr )

                           # start looking for another match
                           match_open = False
                           match_ready = False
                           cm_open = False
                           data['managed_by'] = ''

                     prev_line = line
