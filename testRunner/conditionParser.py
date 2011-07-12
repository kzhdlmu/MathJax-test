# -*- Mode: Python; tab-width: 2; indent-tabs-mode:nil; -*-
# vim: set ts=2 et sw=2 tw=80:
# ***** BEGIN LICENSE BLOCK *****
# Version: Apache License 2.0
#
# Copyright (c) 2011 Design Science, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Contributor(s):
#   Frederic Wang <fred.wang@free.fr> (original author)
#
# ***** END LICENSE BLOCK *****

"""
@file conditionParser.py
The file for the @ref conditionParser module.

@package conditionParser
This module implements a simple parser for boolean expressions
@see http://www.dabeaz.com/ply/ply.html

@details The tokens are simple strings named t_*. Among them, there are the
usual boolean operators @ref t_NOT, @ref t_OR etc. The literals are simple
token strings @ref t_OPERATINGSYSTEM, @ref t_BROWSER etc referring to a
configuration. They are evaluated to true iff the testing instance satisfies
this configuration.

The grammar is defined by the expressions p_*. In BNF notation, it is:

closedTerm := OPERATINGSYSTEM | BROWSER | BROWSERMODE | FONT | NATIVEMATHML |
              LEFTPARENTHESIS expr RIGHTPARENTHESIS

expr1 := closedTerm | NOT expr1

expr2 := expr1 | expr2 AND expr1

expr3 := expr2 | expr3 OR expr2

expr := expr3

They are evaluated with the usual rules of Logic. As an example, the expression 
(Linux||MSIE)&&!TeX is accepted by the grammar and is evaluated to true iff
TeX fonts are used in combination with Linux or Internet Explorer.

@var gSelenium
@brief seleniumMathJax instance from the caller of this module

@var tokens
@brief the list of tokens for the tokenizer

@var t_ignore
@brief the list of characters ignored by the tokenizer. None since whitespaces
are not accepted inside the boolean expressions.

@var lexer
the tokenizer

@var parser
the parser

@var t_NOT
!
@var t_AND
&&

@var t_OR
||

@var t_LEFTPARENTHESIS
(

@var t_RIGHTPARENTHESIS
)
"""

import ply.lex as lex
import ply.yacc as yacc
import seleniumMathJax

gSelenium = None

################################################################################

tokens = (
   "NOT",
   "AND",
   "OR",
   'LEFTPARENTHESIS',
   'RIGHTPARENTHESIS',
   "OPERATINGSYSTEM",
   "BROWSER",
   "BROWSERMODE",
   "FONT",
   "NATIVEMATHML"
)

t_ignore = ""

def t_error(t):
    """
    @fn t_error(t)
    @brief Function called when the tokenizer finds an error

    @param t data for the error

    @exception "conditionParser::t_error, syntax error"
    """
    raise NameError("conditionParser::t_error, syntax error")

t_NOT = r"\!"
t_AND = r"\&\&"
t_OR = r"\|\|"
t_LEFTPARENTHESIS = r"\("
t_RIGHTPARENTHESIS = r"\)"

## Windows, Linux or Mac
def t_OPERATINGSYSTEM(t):
    r"Windows|Linux|Mac"
    t.value = (gSelenium == None or t.value == gSelenium.mOperatingSystem)
    return t

##  Firefox, Safari, Chrome, Opera, MSIE or Konqueror
def t_BROWSER(t):
    r"Firefox|Safari|Chrome|Opera|MSIE|Konqueror"
    t.value = (gSelenium == None or t.value == gSelenium.mBrowser)
    return t

## StandardMode, Quirks, IE7, IE8 or IE9
def t_BROWSERMODE(t):
    r"StandardMode|Quirks|IE7|IE8|IE9"
    t.value = (gSelenium == None or t.value == gSelenium.mBrowserMode)
    return t

## STIX, TeX or ImageTeX
def t_FONT(t):
    r"STIX|TeX|ImageTeX"
    t.value = (gSelenium == None or t.value == gSelenium.mFont)
    return t

##  nativeMathML
def t_NATIVEMATHML(t):
    r"nativeMathML"
    t.value = (gSelenium == None or gSelenium.mNativeMathML)
    return t

lexer = lex.lex()

################################################################################

def p_error(p):
    """
    @fn p_error(p)
    @brief Function called when the parser finds an error

    @param p data for the error

    @exception "conditionParser::p_error, syntax error"
    """
    raise NameError("conditionParser::p_error, syntax error")

def p_closedTerm_token(p):
    '''closedTerm : OPERATINGSYSTEM
                  | BROWSER
                  | BROWSERMODE
                  | FONT
                  | NATIVEMATHML'''
    p[0] = p[1]

def p_closeTerm_parenthesis(p):
    '''closedTerm : LEFTPARENTHESIS expr RIGHTPARENTHESIS'''
    p[0] = p[2]

def p_expr1_(p):
    '''expr1 : closedTerm'''
    p[0] = p[1]

def p_expr1_not(p):
    '''expr1 : NOT expr1'''
    p[0] = not p[2]

def p_expr2_(p):
    '''expr2 : expr1'''
    p[0] = p[1]

def p_expr2_and(p):
    '''expr2 : expr2 AND expr1'''
    p[0] = p[1] and p[3]

def p_expr3_(p):
    '''expr3 : expr2'''
    p[0] = p[1]

def p_expr3_or(p):
    '''expr3 : expr3 OR expr2'''
    p[0] = p[1] or p[3]

def p_expr(p):
    '''expr : expr3'''
    p[0] = p[1]

parser = yacc.yacc()

################################################################################

def parse(aSelenium, aCondition):
    """
    @fn parse(aSelenium, aCondition)
    @brief parse a boolean expression

    @param aSelenium The @ref seleniumMathJax object in which the tests are
    executed.
    @param aCondition the condition to parse
    
    @return whether the condition is true according to the configuration

    @details If aSelenium is None, aCondition is evaluated but @ref parse
    will always return true. This allows runTestsuite.py -p to list all the
    tests and to detect syntax errors in the boolean expressions. Otherwise,
    the configuration of aSelenium is taken into account to assign boolean
    values to the token litterals and evaluate the expression.
    """
    global gSelenium
    gSelenium = aSelenium
    result = parser.parse(aCondition)
    return (result or gSelenium == None)
