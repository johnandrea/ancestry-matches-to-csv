import sys
import re
import glob

"""
Ancestry DNA shared matches to a csv file, intended to create a matrix of
matches to each other.
For your own, and from your matches "shared matches" pages, use browser to
"save page as text".
Name each one as .txt and place all together with this program.
Program output to stdout.

Assumptions: english pages, names contain only ascii
Needs: Python 3.6+

This code is released under the MIT License: https://opensource.org/licenses/MIT
Copyright (c) 2022 John A. Andrea
v1.0

No support provided.
"""

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

def got_url( s, line_pattern ):
    return line_pattern.search( s )

def get_cm( s, line_pattern ):
    result = None
    m = line_pattern.match( s.lower() )
    if m:
       # also remove the hundreds separator (,)
       result = m.group(1).replace( ',', '' )
    return result

def escape_quote( s ):
    return str(s).replace( '"', '\"').replace( "'", "\'" )

def output( one, two, three ):
    # as csv
    q = '"'
    c = ','
    qc = '",'
    qcq = q + c + q
    print( q + one + qcq + two + qc + three )

def is_int( s ):
    try:
       x = int( s )
       return True
    except ValueError:
       return False


# output only those with at least this size a match
min_cm = 32


name_pattern1 = re.compile( r'^(.*)\'s DNA Matches$' ) # account owner page
name_pattern2 = re.compile( r'^You and (.*)$' ) # page is a match of account owner
url_pattern = re.compile( r'discoveryui-matches/compare' )
cm_pattern = re.compile( r'^([0-9].*[0-9]) cm | ' )

not_names = [] # must be lower case
not_names.append( 'view match' )
not_names.append( 'common ancestor' )
not_names.append( 'do you recognize them?' )


# these are the case labels for the loop over lines
first_step = 'owner'
person_url = 'person url'
person_name = 'person name'
cm_tag = 'cm'

for filename in glob.glob( '*.txt' ):
    #print( filename, file=sys.stderr )

    owner_name = None
    match_name = None
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
                   if got_url( line, url_pattern ):
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
                      if is_int( cm ) and int(cm) >= min_cm:
                         output( owner_name, escape_quote(match_name), str(cm) )
                      look_for = person_url

         if not owner_name:
            print( filename, ':reached and of file without finding owner', file=sys.stderr )

         if look_for != person_url:
            print( filename, 'didnt complete search', look_for, file=sys.stderr )
