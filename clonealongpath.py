#!/usr/bin/env python
'''
Copyright (C) 2006 Jean-Francois Barraud, barraud@math.univ-lille1.fr
Copyright (C) 2012 Eduardo Suarez-Santana

This file is part of Clone Along Path Inkscape Extension.

Clone Along Path Inkscape Extension is free software: you can
redistribute it and/or modify it under the terms of the GNU General
Public License as published by the Free Software Foundation, either
version 3 of the License, or any later version.

Clone Along Path Inkscape Extension is distributed in the hope that it
will be useful, but WITHOUT ANY WARRANTY; without even the implied
warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License along
with Clone Along Path Inkscape Extension. If not, see
<http://www.gnu.org/licenses/>.

Quick description:
This script clones an object (the pattern) along other paths (skeletons).
The first selected object is the pattern. The last selected ones are the
skeletons.

Warning: a maximum separation too small will increase the number of
copies and may hang your computer.
'''

import inkex, cubicsuperpath, bezmisc
import pathmodifier,simpletransform
import copy, math, re, random
import gettext
_ = gettext.gettext

def offset(pathcomp,dx,dy):
    for ctl in pathcomp:
        for pt in ctl:
            pt[0]+=dx
            pt[1]+=dy

def linearize(p, tolerance=.0001):
    '''
    This function recieves a component of a 'cubicsuperpath' and returns
    two things: The path subdivided in many straight segments, and an
    array containing the length of each segment.
    
    We could work with bezier path as well, but bezier arc lengths are
    (re)computed for each point in the deformed object. For complex
    paths, this might take a while.
    '''
    zero=0.000001
    i=0
    lengths=[]
    while i<len(p)-1:
        chord = bezmisc.pointdistance(p[i][1], p[i+1][1])
        if chord > tolerance:
            b1, b2 = bezmisc.beziersplitatt([p[i][1],p[i][2],p[i+1][0],p[i+1][1]], 0.5)
            p[i  ][2][0],p[i  ][2][1]=b1[1]
            p[i+1][0][0],p[i+1][0][1]=b2[2]
            p.insert(i+1,[[b1[2][0],b1[2][1]],[b1[3][0],b1[3][1]],[b2[1][0],b2[1][1]]])
        else:
            lengths.append(chord)
            i+=1
    new=[p[i][1] for i in range(0,len(p)-1) if lengths[i]>zero]
    new.append(p[-1][1])
    return new

class CloneAlongPath(pathmodifier.Diffeo):
    def __init__(self):
        pathmodifier.Diffeo.__init__(self)
        self.OptionParser.add_option("--title")
        self.OptionParser.add_option("-y", "--yoffset",
                        action="store", type="float",
                        dest="yoffset", default=0.0, help="vertical offset")
        self.OptionParser.add_option("-x", "--xoffset",
                        action="store", type="float",
                        dest="xoffset", default=0.0, help="horizontal offset")
        self.OptionParser.add_option("-p", "--space",
                        action="store", type="float", 
                        dest="space", default=0.0)
        self.OptionParser.add_option("-d", "--duplicate",
                        action="store", type="inkbool", 
                        dest="duplicate", default=False,
                        help="duplicate pattern before deformation")

    def prepareSelectionList(self):

        idList=self.options.ids
        idList=pathmodifier.zSort(self.document.getroot(),idList)
        id = idList[-1]
        self.patterns={id:self.selected[id]}

        if self.options.duplicate:
            self.patterns=self.duplicateNodes(self.patterns)
        self.expandGroupsUnlinkClones(self.patterns, True, True)
        self.objectsToPaths(self.patterns)
        del self.selected[id]

        self.skeletons=self.selected
        self.expandGroupsUnlinkClones(self.skeletons, True, False)
        self.objectsToPaths(self.skeletons)

    def effect(self):
        if len(self.options.ids)<2:
            inkex.errormsg(_("This extension requires two selected paths."))
            return
        self.prepareSelectionList()
        self.tolerance=math.pow(10,self.options.space);
                    
        for id, node in self.patterns.iteritems():
            if node.tag == inkex.addNS('path','svg') or node.tag=='path':
                d = node.get('d')
                p0 = cubicsuperpath.parsePath(d)
                origin = p0[0][0][1];

                newp=[]
                for skelnode in self.skeletons.itervalues(): 
                    self.curSekeleton=cubicsuperpath.parsePath(skelnode.get('d'))
                    for comp in self.curSekeleton:
                        self.skelcomp=linearize(comp,self.tolerance)
                        for comp in self.skelcomp:
                            p=copy.deepcopy(p0)
                            for sub in p:
                                xoffset=comp[0]-origin[0]+self.options.xoffset
                                yoffset=comp[1]-origin[1]+self.options.yoffset
                                offset(sub,xoffset,yoffset)
                            newp+=p

                node.set('d', cubicsuperpath.formatPath(newp))

if __name__ == '__main__':
    e = CloneAlongPath()
    e.affect()

                    
# vim: expandtab shiftwidth=4 tabstop=8 softtabstop=4 textwidth=72
