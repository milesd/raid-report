#!/usr/bin/env python2.7
#
# Author:        Joe Linoff
# Version:       1
# Creation Date: 2012-03-10
# RCS Id:        $Id: raid.py,v 1.3 2012/03/12 21:29:11 jlinoff Exp jlinoff $
# Description:
#     Report the mean time to data loss (MTTDL) for RAID
#     configurations as well as the JBOD cabinet capacity.
#
# License:
#     Copyright (c) 2012 by Joe Linoff
#     
#     The raid tool is free software; you can redistribute it and/or
#     modify it under the terms of the GNU General Public License as
#     published by the Free Software Foundation; either version 2 of the
#     License, or (at your option) any later version.
#     
#     The raid tool is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#     General Public License for more details. You should have received
#     a copy of the GNU General Public License along with the change
#     tool; if not, write to the Free Software Foundation, Inc., 59
#     Temple Place, Suite 330, Boston, MA 02111-1307 USA.
#
import getopt
import os
import sys
import re

VERSION='1.2'

def usage():
    global VERSION
    p = os.path.basename(sys.argv[0])
    print """
NAME
        %s - RAID configuration analyzer

SYNOPSIS
        %s [OPTIONS]

DESCRIPTION
        Report the mean time to data loss (MTTDL) for RAID
        configurations as well as the JBOD cabinet capacity.

        It is useful for planning a storage system.

        By default it covers these RAID configurations:

          Config        Description
          ============  =============================
          RAID-0        Striping.
          RAID-1/10/01  Parity 1 mirror with stripes.
          RAID-5/Z1     1 parity stripe.
          RAID-6/Z2     2 parity stripes.
          RAID-Z3       3 parity stripes.
          RAID-10(M)    RAID-10 with M-1 mirrors

OPTIONS
        -c <n>, --jbod-capacity <n>
                        The JBOD capacity where n is the number of
                        disks. The default is 24.

        --csv           Output the data in CSV format for inclusion
                        into a spreadsheet. The title and key are not
                        printed.

        -d <name>, --disk-name <name>
                        The name of the disks being used. This
                        information is only used for reporting.
                        Ex. -d 'Seagate Barracuda ST2000DM001'


        -f <pattern>, --filter <pattern>
                        Filter out RAID types that do not match the
                        pattern. By default all of them are
                        printed. If you only wanted to analyze RAID-5
                        and RAID-6 patterns you could specify -f
                        'RAID-5' -f 'RAID-6'.

        -h, --help      This help message.

        -n <num>        The number of disks in each RAID array. A 
                        JBOD will consist of multiple arrays, each
                        array will have <num> disks. This switch can
                        be specified multiple times or with ranges or
                        discrete values to specify different
                        configurations. For example, to analyze RAID
                        configurations for arrays sizes of 4,5,6,7,8
                        and 12 you could specify -n 4-8,12. The
                        default is 6.

        --mtbf <hrs>    The mean time between failures for the disks in
                        hours as specified by the manufacturer. A
                        typical value is 750000. The default is 750000.

        --mttr <hrs>    The mean time to repair a failed disk in hours.
                        This includes the time to physically replace
                        disk and the time to re-silver (format,
                        populate) it. A typical value is 24. The
                        default is 24.

        --no-key        Do not print the key (explanation of terms).

        --no-header     Do not display the column headers.

        --no-title      Do not print the title.

        -s <TB>, --disk-size <TB>
                        The disk size in TB. A disk that is smaller
                        than 1 TB can be specified as a fractional
                        number. For example, a 500GB can be specified
                        as "-s .5". The default is 2TB.
EXAMPLES
        %% # ================================================================
        %% # Example 1:
        %% # Look at a number of different options.
        %% # ================================================================
        %% python %s -n 3-8 -s 2 \\
                -d 'Seagate Barracuda ST2000DM001' \\
                --mtbf 750000 --mttr 24
        
                                  MTTDL RAID Configuration Report
                                   Seagate Barracuda ST2000DM001
                                       MTBF: 750,000 (85.6)
                                             MTTR: 24
                                        Disk Size: 2.000TB
                                         JBOD Capacity: 24
        
              MTTDL    MTTDL                
        N  P  (hrs)    (yrs)    AFR       FT DC %%   DC   Min C  BD B  S  JDC   Types
        == == ======== ======== ========= == ====== ==== === == == == == ===== ============
         3  0  2.5e+05     28.5      3.5%%  0 100.0%%  6.0   1 24 21  7  3  42.0 RAID-0
         3  1 3.91e+09 4.46e+05 0.000224%%  1  50.0%%  3.0   2 24 21  7  3  21.0 RAID-1/10/01
         3  1 3.91e+09 4.46e+05 0.000224%%  1  66.7%%  4.0   2 24 21  7  3  28.0 RAID-5/Z1
         3  2 1.22e+14 1.39e+10 7.18e-09%%  2  33.3%%  2.0   3 24 21  7  3  14.0 RAID-6/Z2
         3  2 1.22e+14 1.39e+10 7.18e-09%%  2  33.3%%  2.0   3 24 21  7  3  14.0 RAID-10(M=2)
        
         4  0 1.88e+05     21.4     4.67%%  0 100.0%%  8.0   1 24 20  5  4  40.0 RAID-0
         4  1 1.95e+09 2.23e+05 0.000449%%  1  50.0%%  4.0   2 24 20  5  4  20.0 RAID-1/10/01
         4  1 1.95e+09 2.23e+05 0.000449%%  1  75.0%%  6.0   2 24 20  5  4  30.0 RAID-5/Z1
         4  2 3.05e+13 3.48e+09 2.87e-08%%  2  50.0%%  4.0   3 24 20  5  4  20.0 RAID-6/Z2
         4  3 9.54e+17 1.09e+14 9.19e-13%%  3  25.0%%  2.0   4 24 20  5  4  10.0 RAID-Z3
         4  3 9.54e+17 1.09e+14 9.19e-13%%  3  25.0%%  2.0   4 24 20  5  4  10.0 RAID-10(M=3)
        
         5  0  1.5e+05     17.1     5.84%%  0 100.0%% 10.0   1 24 20  4  4  40.0 RAID-0
         5  1 1.17e+09 1.34e+05 0.000748%%  1  50.0%%  5.0   2 24 20  4  4  20.0 RAID-1/10/01
         5  1 1.17e+09 1.34e+05 0.000748%%  1  80.0%%  8.0   2 24 20  4  4  32.0 RAID-5/Z1
         5  2 1.22e+13 1.39e+09 7.18e-08%%  2  60.0%%  6.0   3 24 20  4  4  24.0 RAID-6/Z2
         5  3 1.91e+17 2.18e+13 4.59e-12%%  3  40.0%%  4.0   4 24 20  4  4  16.0 RAID-Z3
         5  4 5.96e+21  6.8e+17 1.47e-16%%  4  20.0%%  2.0   5 24 20  4  4   8.0 RAID-10(M=4)
        
         6  0 1.25e+05     14.3     7.01%%  0 100.0%% 12.0   1 24 18  3  6  36.0 RAID-0
         6  1 7.81e+08 8.92e+04  0.00112%%  1  50.0%%  6.0   2 24 18  3  6  18.0 RAID-1/10/01
         6  1 7.81e+08 8.92e+04  0.00112%%  1  83.3%% 10.0   2 24 18  3  6  30.0 RAID-5/Z1
         6  2  6.1e+12 6.97e+08 1.44e-07%%  2  66.7%%  8.0   3 24 18  3  6  24.0 RAID-6/Z2
         6  3 6.36e+16 7.26e+12 1.38e-11%%  3  50.0%%  6.0   4 24 18  3  6  18.0 RAID-Z3
         6  5  3.1e+25 3.54e+21 2.82e-20%%  5  16.7%%  2.0   6 24 18  3  6   6.0 RAID-10(M=5)
        
         7  0 1.07e+05     12.2     8.18%%  0 100.0%% 14.0   1 24 21  3  3  42.0 RAID-0
         7  1 5.58e+08 6.37e+04  0.00157%%  1  50.0%%  7.0   2 24 21  3  3  21.0 RAID-1/10/01
         7  1 5.58e+08 6.37e+04  0.00157%%  1  85.7%% 12.0   2 24 21  3  3  36.0 RAID-5/Z1
         7  2 3.49e+12 3.98e+08 2.51e-07%%  2  71.4%% 10.0   3 24 21  3  3  30.0 RAID-6/Z2
         7  3 2.72e+16 3.11e+12 3.21e-11%%  3  57.1%%  8.0   4 24 21  3  3  24.0 RAID-Z3
         7  6 1.39e+29 1.58e+25 6.32e-24%%  6  14.3%%  2.0   7 24 21  3  3   6.0 RAID-10(M=6)
        
         8  0 9.38e+04     10.7     9.34%%  0 100.0%% 16.0   1 24 16  2  8  32.0 RAID-0
         8  1 4.19e+08 4.78e+04  0.00209%%  1  50.0%%  8.0   2 24 16  2  8  16.0 RAID-1/10/01
         8  1 4.19e+08 4.78e+04  0.00209%%  1  87.5%% 14.0   2 24 16  2  8  28.0 RAID-5/Z1
         8  2 2.18e+12 2.49e+08 4.02e-07%%  2  75.0%% 12.0   3 24 16  2  8  24.0 RAID-6/Z2
         8  3 1.36e+16 1.56e+12 6.43e-11%%  3  62.5%% 10.0   4 24 16  2  8  20.0 RAID-Z3
         8  7 5.41e+32 6.18e+28 1.62e-27%%  7  12.5%%  2.0   8 24 16  2  8   4.0 RAID-10(M=7)
        
        
                     Term    Definition
                     ======= ================================================
                     AFR     Annualized Failure Rate in years
                     B       Number of RAID blocks
                     BD      Number of RAID block disks
                     C       JBOD capacity (number of disks)
                     DC      RAID data capacity (TB)
                     FT      Fault Tolerance: max bad disks with no data loss
                     JDC     JBOD data capacity in TB
                     Min     Minimum number of disks allowed
                     MTBF    Mean Time Between Failures in hours
                     MTTDL   Mean Time To Data Loss in hours
                     MTTR    Mean Time To Recover (repair) in hours
                     N       Number of disks in each RAID array
                     P       Parity
                     S       Spares, must be greater than zero

        %% # ================================================================
        %% # Example 2:
        %% # Just look at the Z2 options for different array sizes.
        %% # ================================================================
        %% python %s -n 3-8 -s 2 \\
                -d 'Seagate Barracuda ST2000DM001' \\
                --mtbf 750000 --mttr 24  -f 'Z2'
        
                                  MTTDL RAID Configuration Report
                                   Seagate Barracuda ST2000DM001
                                       MTBF: 750,000 (85.6)
                                             MTTR: 24
                                        Disk Size: 2.000TB
                                         JBOD Capacity: 24
        
              MTTDL    MTTDL                
        N  P  (hrs)    (yrs)    AFR       FT DC %%   DC   Min C  BD B  S  JDC   Types
        == == ======== ======== ========= == ====== ==== === == == == == ===== ============
         3  2 1.22e+14 1.39e+10 7.18e-09%%  2  33.3%%  2.0   3 24 21  7  3  14.0 RAID-6/Z2
         4  2 3.05e+13 3.48e+09 2.87e-08%%  2  50.0%%  4.0   3 24 20  5  4  20.0 RAID-6/Z2
         5  2 1.22e+13 1.39e+09 7.18e-08%%  2  60.0%%  6.0   3 24 20  4  4  24.0 RAID-6/Z2
         6  2  6.1e+12 6.97e+08 1.44e-07%%  2  66.7%%  8.0   3 24 18  3  6  24.0 RAID-6/Z2
         7  2 3.49e+12 3.98e+08 2.51e-07%%  2  71.4%% 10.0   3 24 21  3  3  30.0 RAID-6/Z2
         8  2 2.18e+12 2.49e+08 4.02e-07%%  2  75.0%% 12.0   3 24 16  2  8  24.0 RAID-6/Z2
        
                     Term    Definition
                     ======= ================================================
                     AFR     Annualized Failure Rate in years
                     B       Number of RAID blocks
                     BD      Number of RAID block disks
                     C       JBOD capacity (number of disks)
                     DC      RAID data capacity (TB)
                     FT      Fault Tolerance: max bad disks with no data loss
                     JDC     JBOD data capacity in TB
                     Min     Minimum number of disks allowed
                     MTBF    Mean Time Between Failures in hours
                     MTTDL   Mean Time To Data Loss in hours
                     MTTR    Mean Time To Recover (repair) in hours
                     N       Number of disks in each RAID array
                     P       Parity
                     S       Spares, must be greater than zero


        %% # ================================================================
        %% # Example 3:
        %% # Just look at the Z2 options for different array sizes.
        %% # Output it in CSV format to include in a spreadsheet.
        %% # ================================================================
        %% python %s -n 3-8 -s 2 \\
                -d 'Seagate Barracuda ST2000DM001' \\
                --mtbf 750000 --mttr 24  -f 'Z2' \\
                --csv
        Disk,Seagate Barracuda ST2000DM001
        Size,2.000
        MTBF,750000
        MTTR,24
        
        ,,N,Parity,MTTDL (hrs),MTTDL (yrs),AFR,FT,DC %%,DC,Min,C,BD,B,S,JDC,Types
        ,,3,2,1.22e+14,1.39e+10,7.1762e-11,2,0.333,2.0,3,24,21,7,3,14.0,RAID-6/Z2
        ,,4,2,3.05e+13,3.48e+09,2.8705e-10,2,0.500,4.0,3,24,20,5,4,20.0,RAID-6/Z2
        ,,5,2,1.22e+13,1.39e+09,7.1762e-10,2,0.600,6.0,3,24,20,4,4,24.0,RAID-6/Z2
        ,,6,2,6.1e+12,6.97e+08,1.4352e-09,2,0.667,8.0,3,24,18,3,6,24.0,RAID-6/Z2
        ,,7,2,3.49e+12,3.98e+08,2.5117e-09,2,0.714,10.0,3,24,21,3,3,30.0,RAID-6/Z2
        ,,8,2,2.18e+12,2.49e+08,4.0187e-09,2,0.750,12.0,3,24,16,2,8,24.0,RAID-6/Z2

        %% # ================================================================
        %% # Example 4:
        %% # Script to print out storage diffs for Z1, Z2 and Z3 options.
        %% # ================================================================
        %% cat >x.sh <<EOF
        #!/bin/bash
        python %s -n 3-8 -s 2 \\
            -d 'Seagate Barracuda ST2000DM001' \\
            --mtbf 750000 --mttr 24  -f 'Z1' \\
            --no-key
        
        python %s -n 3-8 -s 2 \\
            -d 'Seagate Barracuda ST2000DM001' \\
            --mtbf 750000 --mttr 24  -f 'Z2' \\
            --no-title --no-header --no-key
        
        python %s -n 3-8 -s 2 \\
            -d 'Seagate Barracuda ST2000DM001' \\
            --mtbf 750000 --mttr 24  -f 'Z3' \\
            --no-title --no-header --no-key
        EOF
        %% chmod a+x x.sh
        %% ./x.sh

                                  MTTDL RAID Configuration Report
                                   Seagate Barracuda ST2000DM001
                                       MTBF: 750,000 (85.6)
                                             MTTR: 24
                                        Disk Size: 2.000TB
                                         JBOD Capacity: 24
        
              MTTDL    MTTDL
        N  P  (hrs)    (yrs)    AFR       FT DC %   DC   Min C  BD B  S  JDC   Types
        == == ======== ======== ========= == ====== ==== === == == == == ===== ============
         3  1 3.91e+09 4.46e+05 0.000224%  1  66.7%  4.0   2 24 21  7  3  28.0 RAID-5/Z1
         4  1 1.95e+09 2.23e+05 0.000449%  1  75.0%  6.0   2 24 20  5  4  30.0 RAID-5/Z1
         5  1 1.17e+09 1.34e+05 0.000748%  1  80.0%  8.0   2 24 20  4  4  32.0 RAID-5/Z1
         6  1 7.81e+08 8.92e+04  0.00112%  1  83.3% 10.0   2 24 18  3  6  30.0 RAID-5/Z1
         7  1 5.58e+08 6.37e+04  0.00157%  1  85.7% 12.0   2 24 21  3  3  36.0 RAID-5/Z1
         8  1 4.19e+08 4.78e+04  0.00209%  1  87.5% 14.0   2 24 16  2  8  28.0 RAID-5/Z1
        
         3  2 1.22e+14 1.39e+10 7.18e-09%  2  33.3%  2.0   3 24 21  7  3  14.0 RAID-6/Z2
         4  2 3.05e+13 3.48e+09 2.87e-08%  2  50.0%  4.0   3 24 20  5  4  20.0 RAID-6/Z2
         5  2 1.22e+13 1.39e+09 7.18e-08%  2  60.0%  6.0   3 24 20  4  4  24.0 RAID-6/Z2
         6  2  6.1e+12 6.97e+08 1.44e-07%  2  66.7%  8.0   3 24 18  3  6  24.0 RAID-6/Z2
         7  2 3.49e+12 3.98e+08 2.51e-07%  2  71.4% 10.0   3 24 21  3  3  30.0 RAID-6/Z2
         8  2 2.18e+12 2.49e+08 4.02e-07%  2  75.0% 12.0   3 24 16  2  8  24.0 RAID-6/Z2
        
         4  3 9.54e+17 1.09e+14 9.19e-13%  3  25.0%  2.0   4 24 20  5  4  10.0 RAID-Z3
         5  3 1.91e+17 2.18e+13 4.59e-12%  3  40.0%  4.0   4 24 20  4  4  16.0 RAID-Z3
         6  3 6.36e+16 7.26e+12 1.38e-11%  3  50.0%  6.0   4 24 18  3  6  18.0 RAID-Z3
         7  3 2.72e+16 3.11e+12 3.21e-11%  3  57.1%  8.0   4 24 21  3  3  24.0 RAID-Z3
         8  3 1.36e+16 1.56e+12 6.43e-11%  3  62.5% 10.0   4 24 16  2  8  20.0 RAID-Z3

AUTHOR
        Joe Linoff

VERSION
        %s

REFERENCES
        1. http://www.cs.swarthmore.edu/~newhall/readings/raid.pdf
        2. http://blog.richardelling.com/2010/02/zfs-data-protection-comparison.html

LICENSE
        This is for the RAID configuration analysis tool.
    
        Copyright (c) 2012 by Joe Linoff
    
        The RAID configuration analysis tool is free software; you can
        redistribute it and/or modify it under the terms of the GNU
        General Public License as published by the Free Software
        Foundation; either version 2 of the License, or (at your
        option) any later version.
        
        The RAID configuration analysis tool is distributed in the
        hope that it will be useful, but WITHOUT ANY WARRANTY; without
        even the implied warranty of MERCHANTABILITY or FITNESS FOR A
        PARTICULAR PURPOSE.  See the GNU General Public License for
        more details. You should have received a copy of the GNU
        General Public License along with the RAID configuration
        analysis tool; if not, write to the Free Software Foundation,
        Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA.
""" % (p,p,p,p,p,p,p,p,VERSION)
    sys.exit(0)

def commaize(n,f='%.0f'):
    """
    Insert commas into a number.
    @param n  The number
    @param f  The format.
    @returns the comma-ized number.
    """
    s = f % (n)
    m = len(s)
    if m>3:
        r = ''
        for i in range(m):
            if i and (i%3) == (m%3):
                r += ','
            r += s[i]
        s = r
    return s

def parse_nums(nums):
    """
    Parse an argument from the command line that can consist of a
    number, a range separated by a dash or a list of numbers and
    ranges separated by commas.

    Examples:
        1
        1,2,3,4
        1,2,3-6
        4-10

    @param nums  The argument list.
    @returns the explicit list of all numbers implied
    """
    a = []

    # Is it a simple number?
    # ex. -N 10
    m = re.search('^\d+$',nums)
    if m:
        a.append(int(nums))
        return a

    # Is it a simple range?
    # ex. -N 3-12
    m = re.search('^(\d+)-(\d+)$',nums)
    if m:
        beg = int(m.group(1))
        end = int(m.group(2))
        for p in range(beg,end+1):
            a.append(p)
        return a

    # Is it a combination of simple numbers and ranges?
    # ex. -N 1,2,4-10
    if ',' in nums:
        ps = nums.split(',')
        for p in ps:
            m = re.search('^\d+$',p)
            if m:
                a.append(int(p))
                continue
            m = re.search('^(\d+)-(\d+)$',p)
            if m:
                beg = int(m.group(1))
                end = int(m.group(2))
                for p in range(beg,end+1):
                    a.append(p)
                continue
            raise 'bad syntax in number expression found for %s' % (nums)
        return a

    raise 'bad syntax in number expression found for %s' % (nums)

def center(width, title):
    """
    Center and print a title line.

    If the title is zero length, nothing is printed.

    @param width  The width of the display area.
    @param title  The title.
    """
    if title not in ['',None]:
        prefix = (width - len(title)) / 2 # Center
        print '%*s%s' % (prefix,' ',title)

def main():
    """
    main
    """
    try:
        opts, args = getopt.gnu_getopt(sys.argv[1:],
                                       'c:d:f:hn:s:vV',
                                       ['jbod-capacity=',
                                        'csv',
                                        'disk-name=',
                                        'disk-size=',
                                        'filters=',
                                        'help',
                                        'mtbf=',
                                        'mttr=',
                                        'no-key',
                                        'no-header',
                                        'no-title',
                                        'verbose',
                                        'version'])
    except getopt.GetoptError, err:
        print str(err)
        print 'exiting ...'
        sys.exit(1)
        
    disk = ''
    first=True
    Ns = [6]
    C = 24  # JBOD capacity
    mtbf = 750000  # mean time between failures in hours
    mttr = 24      # mean time to recovery in hours
    disk = ''
    size = 2.0 # TB
    filters = []
    verbose = 0
    print_key = True
    print_header = True
    print_title = True
    fmt = 'text'
    for opt,arg in opts:
        if opt in ['-h','--help'] :
            usage()
        elif opt in ['-c', '--jbod-capacity']:
            if not re.search('^\d+$',arg):
                sys.exit('syntax error for %s, expected a number but found: %s' % (opt,arg))
            C = int(arg)
        elif opt in ['--csv']:
            fmt = 'csv'
        elif opt in ['-d', '--disk-name']:
            disk = arg
        elif opt in ['-f', '--filter']:
            filters.append(arg)
        elif opt in ['--mtbf'] :
            if not re.search('^\d+$',arg):
                sys.exit('syntax error for %s, expected a number but found: %s' % (opt,arg))
            mtbf = int(arg)
        elif opt in ['--mttr'] :
            if not re.search('^\d+$',arg):
                sys.exit('syntax error for %s, expected a number but found: %s' % (opt,arg))
            mttr = int(arg)
        elif opt in ['--no-key'] :
            print_key = False
        elif opt in ['--no-header'] :
            print_header = False
        elif opt in ['--no-title'] :
            print_title = False
        elif opt in ['-n'] :
            if first:
                first = False
                Ns = []
            try:
                m = parse_nums(arg)
                for n in m:
                    Ns.append(n)
            except Exception as msg:
                sys.exit(msg)
        elif opt in ["-s", "--disk-size"] :
            size = float(arg)
        elif opt in ['-v','--verbose'] :
            verbose += 1
        elif opt in ['-V','--version'] :
            global VERSION
            msg.info('Version: '+VERSION)
            sys.exit(0)
        else:
            sys.exit('Unrecognized option '+opt)

    hdr = []
    hdr.append('      MTTDL    MTTDL')
    hdr.append('N  P  (hrs)    (yrs)    AFR       FT DC %   DC   Min C  BD B  S  JDC   Types')
    hdr.append('== == ======== ======== ========= == ====== ==== === == == == == ===== ============')
    hdr_width = max(len(h) for h in hdr)

    if fmt == 'text':
        if print_title:
            print
            center(hdr_width,'MTTDL RAID Configuration Report')
            center(hdr_width,disk)
            center(hdr_width,'MTBF: %s (%.3g)'%(commaize(mtbf),(float(mtbf)/(24.*365.))))
            center(hdr_width,'MTTR: %d'%(mttr))
            if size>0:
                center(hdr_width,'Disk Size: %.3fTB' % (size))
            if C>0:
                center(hdr_width,'JBOD Capacity: %d' % (C))
        if print_header:
            print
            for h in hdr:
                print h
    elif fmt == 'csv':
        if disk != '':
            print 'Disk,%s' % (disk)
        if size>0:
            print 'Size,%.3f' % (size)
        print 'MTBF,%d' % (mtbf)
        print 'MTTR,%d' % (mttr)
        print
        print ',,N,Parity,MTTDL (hrs),MTTDL (yrs),AFR,FT,DC %,DC,Min,C,BD,B,S,JDC,Types'

    if len(Ns)>1:
        Ns = sorted(Ns)
    for N in Ns:
        pt = ['RAID-0', 'RAID-1/10/01', 'RAID-5/Z1', 'RAID-6/Z2', 'RAID-Z3', 'RAID-10(M=%d)' % (N-1)]
        pf = [0,1,1,2,3,N-1]
        pm = [1,2,2,3,4,N]
        pe = [1.,0.5,float((N-1.0)/N),float((N-2.0)/N),float((N-3.0)/N),float(1.0/N)]
        i = 0
        num_lines_printed = 0
        for p in pf:
            if N < pm[i]:
                # Skip if this level parity is not supported.
                i += 1
                continue

            if len(filters)>0:
                # Skip if the match criteria isn't met.
                skip = True
                for f in filters:
                    if re.search(f,pt[i]):
                        skip = False
                        break
                if skip:
                    i += 1
                    continue

            num_lines_printed += 1
            n1 = pow(mtbf,p+1)
            d1 = pow(mttr,p)
            d2l = list(N-x for x in range(p+1))
            d2 = reduce(lambda x,y: x*y,d2l)
            mttdl = n1 / (d1*d2) # hours
            mttdl_yrs = float(mttdl) / float(365*24)
            AFR = 100.*(1./float(mttdl_yrs)) # annualized failure rate
            DCp =  100.*pe[i] 
            DC = float(size)*float(N)*pe[i]
            m = C%N
            B = C/N
            if m>0:
                S = m
            else:
                S = N
                B -= 1
            BD = N*B
            JDC = float(B) * float(DC)
            if fmt == 'text':
                print '%2d %2d %8.3g %8.3g %8.3g%% %2d %5.1f%% %4.1f %3d %2d %2d %2d %2d %5.1f %s' % (N,p,mttdl,mttdl_yrs, AFR, pf[i], DCp, DC, pm[i], C, BD, B, S, JDC, pt[i])
            elif fmt == 'csv':
                print ',,%d,%d,%.3g,%.3g,%.5g,%d,%.3f,%.1f,%d,%d,%d,%d,%d,%.1f,%s' % (N,p,mttdl,mttdl_yrs, AFR/100., pf[i], DCp/100., DC, pm[i], C, BD, B, S, JDC, pt[i])

            i += 1
        if num_lines_printed>1:
            print

    if fmt == 'text' and print_key:
        key = []
        key.append('KEY')
        key.append('Term    Definition')
        key.append('======= ================================================')
        key.append('AFR     Annualized Failure Rate in years')
        key.append('B       Number of RAID blocks')
        key.append('BD      Number of RAID block disks')
        key.append('C       JBOD capacity (number of disks)')
        key.append('DC      RAID data capacity (TB)')
        key.append('FT      Fault Tolerance: max bad disks with no data loss')
        key.append('JDC     JBOD data capacity in TB')
        key.append('Min     Minimum number of disks allowed')
        key.append('MTBF    Mean Time Between Failures in hours')
        key.append('MTTDL   Mean Time To Data Loss in hours')
        key.append('MTTR    Mean Time To Recover (repair) in hours')
        key.append('N       Number of disks in each RAID array')
        key.append('P       Parity')
        key.append('S       Spares, must be greater than zero')
        key_width = max(len(k) for k in key)
        p = (hdr_width - key_width)/2
        ps = ' '*p
        print
        for k in key:
            print ps+k
    print

if __name__ == '__main__':
    main()