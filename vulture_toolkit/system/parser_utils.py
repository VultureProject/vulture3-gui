#!/usr/bin/python
#-*- coding: utf-8 -*-
"""This file is part of Vulture 3.

Vulture 3 is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Vulture 3 is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Vulture 3.  If not, see http://www.gnu.org/licenses/.
"""
__author__ = "Jérémie Jourdin"
__credits__ = []
__license__ = "GPLv3"
__version__ = "3.0.0"
__maintainer__ = "Vulture Project"
__email__ = "contact@vultureproject.org"
__doc__ = 'System Utils Toolkit'

from vulture_toolkit.system.parser_utils_acunetix_9 import acunetix_9_parser
from vulture_toolkit.system.parser_utils_qualys import qualys_parser
from vulture_toolkit.system.parser_utils_zap import zap_parser


def xss_vuln_types():
    return '.*XSS.*|.*Cross [S|s]ite [S|s]cripting.*'

def sqli_vuln_types():
    return '.*SQL [I|i]njection.*|.*[I|i]njection SQL.*'

def pt_vuln_types():
    return '.*Path Traversal.*|.*temporary file/directory.*'

def rfi_vuln_types():
    return '.*Remote File Inclusion.*|.*Inclusion de fichiers distants.*|Local File Inclusion'

def httprs_vuln_types():
    return '.*HTTP Response Splitting.*'

def header_missing_vuln_types():
    return '.*header missing.*|.*header is not set.*|.*header not set.*|.*Framable Page.*$'

def cookie_missing_flags():
    return '^(Session )?Cookie.*HTTPOnly.*|^(Session )?Cookie.*HttpOnly.*|^(Session )?Cookie.*[Ss]ecure.*|.*without HttpOnly.*|.*without Secure.*'

def method_enabled():
    return '.*OPTIONS method is enabled.*'


def scan_to_modsec(parser_type, xml_document):

    """ Build a ModSecurity Rules Set from vulnerabilities found in XML buffer

    :param type: The scanner type
    :param xml_document: XML scan result
    :returns: a list with [string buffer containing ModSecurity rules, log ouput]
    """
    #Types of vulnerabilities we want to cover
    vuln_types = [xss_vuln_types(), sqli_vuln_types(), pt_vuln_types(),
                  rfi_vuln_types(), httprs_vuln_types(), header_missing_vuln_types(),
                  cookie_missing_flags(),method_enabled()]

    if parser_type == "zap":
        return zap_parser(vuln_types, xml_document)
    elif parser_type == "qualys":
        return qualys_parser(vuln_types, xml_document)
    elif parser_type == "acunetix_9":
        return acunetix_9_parser(vuln_types, xml_document)



    return None


