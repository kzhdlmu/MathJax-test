#!/usr/bin/env python
# -*- Mode: Python; tab-width: 2; indent-tabs-mode:nil; -*-
# vim: set ts=2 et sw=2 tw=80:
#
# Copyright (c) 2013 Design Science, Inc.
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

"""
@package LiPlusXML
This modules implements LiPlus's testcase interface for XML documents where
tokens are elements and attributes. The HTML parser can also be used.
"""

from collections import deque
from lxml import etree

NS_LIPLUS = "http://www.mathjax.org/namespace/LiPlus"
ATTRIBUTE_LIPLUS_REMOVE = "{%s}liplusrm" % NS_LIPLUS

class LiPlusXML:

    def __init__(self,
                 aFileName,
                 aIsXML = True,
                 aSubset = None,
                 aDepthBrowing = False,
                 aElementsOnly = False,
                 aAttributesOnly = False):

        self.mFileName = aFileName
        self.mIsXML = aIsXML

        if aIsXML:
            self.mDocument = etree.parse(self.mFileName)
        else:
            parser = etree.HTMLParser()
            self.mDocument = etree.parse(self.mFileName, parser)

        self.mLiPlusXSLT = etree.XSLT(etree.parse("LiPlusXML.xsl"))

        self.mMarkedAttributes = dict()
        self.mElements = deque()

        root = self.mDocument.getroot()
        if aSubset is not None:
            elements = self.mDocument.xpath("//*[@id='%s']" % aSubset)
            if len(elements) == 1:
                root = elements[0]
            else:
                ns = etree.QName(root).namespace
                root = root.find("{%s}%s" % (ns, aSubset))
        
        if aDepthBrowing:
            self.breadthFirstBrowsing(root, aElementsOnly, aAttributesOnly)
        else:
            self.depthFirstBrowsing(root, aElementsOnly, aAttributesOnly)

        if not aAttributesOnly:
            # never try to remove the root
            self.mElements.pop()

    def breadthFirstBrowsing(self, aRoot, aElementsOnly, aAttributesOnly):
        q = deque()
        q.append(aRoot)
        while q:
            node = q.popleft()

            if not aAttributesOnly and isinstance(node, etree.ElementBase):
                self.mElements.appendleft(node)

            if not aElementsOnly:
                self.mMarkedAttributes[node] = dict()
                for attr in node.attrib:
                    self.mElements.appendleft((node, attr))

            for child in node:
                q.append(child)

    def depthFirstBrowsing(self, aRoot, aElementsOnly, aAttributesOnly):
        q = []
        q.append(aRoot)
        while q:
            node = q.pop()

            if not aAttributesOnly and isinstance(node, etree._Element):
                self.mElements.appendleft(node)

            if not aElementsOnly:
                self.mMarkedAttributes[node] = dict()
                for attr in node.attrib:
                    self.mElements.appendleft((node, attr))

            for child in node.iterchildren(reversed=True):
                q.append(child)

    def getIterable(self):
        return self.mElements

    def mark(self, aElement):
        if isinstance(aElement, etree._Element):
            aElement.set(ATTRIBUTE_LIPLUS_REMOVE, "R")
        else:
            el = aElement[0]
            if el in self.mMarkedAttributes:
                attr = aElement[1]
                self.mMarkedAttributes[el][attr] = el.attrib[attr]
                del el.attrib[attr]

    def unmark(self, aElement):
        if isinstance(aElement, etree._Element):
            del aElement.attrib[ATTRIBUTE_LIPLUS_REMOVE]
        else:
            el = aElement[0]
            if el in self.mMarkedAttributes:
                attr = aElement[1]
                el.attrib[attr] = self.mMarkedAttributes[el][attr]
                del self.mMarkedAttributes[el][attr]

    def remove(self, aElement):
        if isinstance(aElement, etree._Element):
            del self.mMarkedAttributes[aElement]

    def outputFile(self):
        reducedDocument = self.mLiPlusXSLT(self.mDocument)

        outputFile = open(self.mFileName, "w")

        if self.mIsXML:
            outputFile.write(etree.tostring(reducedDocument,
                                            method="xml",
                                            xml_declaration = True,
                                            pretty_print = True,
                                            encoding = "UTF-8"))
        else:
            outputFile.write(etree.tostring(reducedDocument,
                                            method="html",
                                            pretty_print=True,
                                            encoding = "UTF-8"))
