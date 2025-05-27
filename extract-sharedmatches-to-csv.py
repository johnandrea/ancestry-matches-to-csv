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
# ...
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
# No support provided.


def get_version():
    return '4.0.2'


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
    # -- updaated
    # "you","cM with Other","relation with Other"
    # ,"Other","Other id"
    # ,"Match","cM with Other","relation with Other"

    out = '"you","Your cM with Match"'
    if options['add-relation']:
       out += ',"Your relation with Match"'

    out += ',"Shared person"'
    if options['add-id'] and not options['id-with-name']:
       out += ',"Shared person id"'

    out += ',"Match","Match\\\'s cM with shared person"'
    if options['add-relation']:
       out += ',"Match\\\'s relationship to shared person"'
    out += ',"Managed by"'

    print( out, file=f )


#def output( owner, owner_cm, owner_relation, other_name, other_id, match_name, match_cm, match_relation, managed_by, f ):
def output( data, f ):
    # as csv
    if is_int( data['your_cm'] ) and int(data['your_cm']) >= options['min-cm']:
       name1 = escape_quote( data['owner'] )
       name2 = escape_quote( data['other_name'] )
       name3 = escape_quote( data['name_of_match'] )

       if options['add-id']:
          if options['id-with-name']:
             name2 += '/' + data['other_id']

       out = quoted( name1 )
       out += ',' + quoted( data['your_cm'] )
       if options['add-relation']:
          out += ',' + quoted( data['your_relation'] )
       out += ',' + quoted( name2 )
       if options['separate-id']:
          out += ',' + quoted( data['other_id'] )
       out += ',' + quoted( name3 )
       out += ',' + quoted( data['match_cm'] )
       if options['add-relation']:
          out += ',' + quoted( data['match_relation'] )
       out += ',' + quoted( data['managed_by'] )

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
     data['owner'] = 'you'

     for filename in glob.glob( '*.txt' ):
         with open( filename, 'r', encoding='utf-8' ) as inf:
              found_you_and = False
              data['name_of_match'] = ''

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

              data['other_name'] = ''
              data['your_cm'] = ''
              data['your_relation'] = ''
              data['match_cm'] = ''
              data['managed_by'] = ''

              prev_line = ''

              for line in inf:
                  line = line.strip()
                  if line:

                     if line.startswith( 'You and ' ) and not found_you_and:
                        # this occors only once per input file
                        found_you_and = True
                        name_of_match = line.replace( 'You and ', '' )
                        # the name might look like: You and First Second <https://www.ancestry...
                        # so also get rid of that url
                        data['name_of_match'] = re.sub( partial_url, '', name_of_match )

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
                              data['other_name'] = m.group(1)
                              #owner_id = m.group(2)  # not useful
                              data['other_id'] = m.group(3)

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
