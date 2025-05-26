import sys
import re
import glob
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
# Program assumptions: English pages, names contain only ascii
# Needs: Python 3.6+
#
# This code is released under the MIT License:
# https://opensource.org/licenses/MIT
# Copyright (c) 2025 John A. Andrea
# v0.9.3
# No support provided.


def escape_quote( s ):
    # inside a csv file, add the escape slash
    return str(s).replace( '"', '\\"').replace( "'", "\\'" )


def quoted( s ):
    return '"' + s.strip() + '"'


start_pattern = re.compile( r'^.*<https://www.ancestry.*/discoveryui-matches/' )
end_pattern = re.compile( r'^.*matchesofmatches> *$' )

full_pattern = re.compile( r'^(.*) <https://www.ancestry.*/discoveryui-matches/compare/([A-Za-z0-9-]*)/with/([A-Za-z0-9-]*)/matchesofmatches>' )

partial_url = re.compile( r' <http.*' )

with open( 'shared-matches.csv', 'w', encoding='utf-8' ) as outf:
     print( 'output in', 'shared-matches.csv' )

     header = '"you","cM with Other","Other","Other id","Match,"cM with Other","Match id"'
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

                           out = quoted( 'you' )
                           out += ',' + quoted( your_cm )
                           out += ',' + quoted( escape_quote( other_name ) )
                           out += ',' + quoted( other_id )
                           out += ',' + quoted( escape_quote( name_of_match ) )
                           out += ',' + quoted( match_cm )
                           out += ',' + quoted( match_id )
                           print( out, file=outf )

                        else:
                           print( 'didnt match:', file=sys.stderr )
                           print( match_line, file=sys.stderr )

                        match_open = False
                        match_ready = False
                        match_line = ''
                        your_line = 0
