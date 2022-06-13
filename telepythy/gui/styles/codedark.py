# -*- coding: utf-8 -*-
"""
    Codedark Colorscheme
    ~~~~~~~~~~~~~~~~~~~~

    Converted by Vim Colorscheme Converter
"""
from pygments.style import Style
from pygments.token import (Token, Operator, Name, Comment, Generic,
    Keyword, Number, String)

class CodedarkStyle(Style):

    background_color = '#1E1E1E'
    default_style = ''

    styles = {
        Comment:            '#6A9955 bold',
        Comment.Preproc:    '#C586C0 underline',

        Generic.Deleted:    '#8a2be2 bg:#6F1313 bold',
        Generic.Emph:       'underline',
        Generic.Error:      '#F44747 bg:#1E1E1E',
        Generic.Heading:    'bold',
        Generic.Inserted:   'bg:#4B5632 bold',
        Generic.Output:     '#E1E1E1',
        Generic.Subheading: 'bold',
        Generic.Traceback:  '#F44747 bg:#1E1E1E',

        Keyword:            '#C586C0 bold',
        Keyword.Type:       '#569CD6 underline',

        Name.Attribute:     '#DCDCAA',
        Name.Constant:      '#569CD6 underline',
        Name.Entity:        '#D7BA7D bold',
        Name.Exception:     '#C586C0',
        Name.Function:      '#CBDAA8',
        Name.Label:         '#C586C0',
        Name.Tag:           '#C586C0 bold',
        Name.Variable:      '#9CDCFE underline',

        Number:             '#B5CEA8',
        Number.Float:       '#B5CEA8',

        Operator.Word:      '#D4D4D4',
        String:             '#CE9178',
        Token:              '#D4D4D4 bg:#1E1E1E',
    }
