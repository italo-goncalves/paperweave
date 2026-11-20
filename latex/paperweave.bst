%% paperweave.bst -- PaperWeave's author-year reference style (ADR 0004).
%%
%% Produces the same text as src/references.ts, which formats references in the app:
%%   Damianou A C, Lawrence N D (2013) Deep Gaussian processes. In: Proceedings of ..., pp 207--215. https://doi.org/...
%% scripts/test_references.py checks that the two agree. Change both together.
%%
%% natbib-compatible: \bibitem[{Short(Year)Long}]{key}.

ENTRY
  { address author booktitle doi edition editor institution journal note number
    pages publisher school title type url volume year }
  {}
  { label extra.label }

INTEGERS { nameptr numnames last.extra.num }
STRINGS { s t last.label next.extra v vs }

FUNCTION {not} { { #0 } { #1 } if$ }
FUNCTION {field.or.null} { duplicate$ empty$ { pop$ "" } 'skip$ if$ }
FUNCTION {and} { 'skip$ { pop$ #0 } if$ }
FUNCTION {or} { { pop$ #1 } 'skip$ if$ }

%% "Family I I, Family I" for a list of people.
FUNCTION {format.names}
{ 's :=
  #1 'nameptr :=
  s num.names$ 'numnames :=
  ""
  { nameptr numnames > not }
  { s nameptr "{vv~}{ll}{~f{~}}" format.name$ 't :=
    nameptr #1 >
      { ", " * }
      'skip$
    if$
    t *
    nameptr #1 + 'nameptr :=
  }
  while$
}

%% "Family", "Family and Family" or "Family et al." from the authors.
FUNCTION {label.authors}
{ author empty$
    { "Anonymous" }
    { author num.names$ 'numnames :=
      numnames #1 =
        { author #1 "{vv~}{ll}" format.name$ }
        { numnames #2 =
            { author #1 "{vv~}{ll}" format.name$ " and " *
              author #2 "{vv~}{ll}" format.name$ * }
            { author #1 "{vv~}{ll}" format.name$ " et~al." * }
          if$
        }
      if$
    }
  if$
}

%% Appends ", x" to the string on the stack when x is not empty.
FUNCTION {join}
{ 'v :=
  v empty$
    'skip$
    { duplicate$ empty$
        { pop$ v }
        { ", " * v * }
      if$
    }
  if$
}

FUNCTION {prefixed}
{ 't :=
  duplicate$ empty$
    { pop$ "" }
    { t swap$ * }
  if$
}

FUNCTION {venue.article}
{ journal empty$ { "" } { journal } if$
  volume empty$ 'skip$ { " " * volume * } if$
  number empty$ 'skip$ { "(" * number * ")" * } if$
  pages empty$
    'skip$
    { volume empty$ number empty$ and
        { " " * pages * }
        { ":" * pages * }
      if$
    }
  if$
}

FUNCTION {venue.in}
{ booktitle empty$
    { "" }
    { editor empty$
        { "In: " booktitle * }
        { "In: " editor format.names *
          editor num.names$ #1 > { " (eds) " } { " (ed) " } if$ *
          booktitle *
        }
      if$
    }
  if$
  volume field.or.null "vol " prefixed join
  publisher field.or.null join
  address field.or.null join
  pages field.or.null "pp " prefixed join
}

FUNCTION {venue.book}
{ edition empty$ { "" } { edition " edn" * } if$
  publisher field.or.null join
  address field.or.null join
}

FUNCTION {venue.thesis}
{ type empty$ { "PhD thesis" } { type } if$
  school field.or.null join
  address field.or.null join
}

FUNCTION {venue.report}
{ type empty$ { "Tech. rep." } { type } if$
  number empty$ 'skip$ { " " * number * } if$
  institution field.or.null join
  address field.or.null join
}

FUNCTION {venue.misc}
{ ""
  publisher field.or.null join
  address field.or.null join
}

FUNCTION {link}
{ doi empty$
    { url empty$ { "" } { "\url{" url * "}" * } if$ }
    { "\url{https://doi.org/" doi * "}" * }
  if$
}

%% Joins the string on the stack to the text below it with a space.
FUNCTION {then}
{ 'v :=
  v empty$
    'skip$
    { " " * v * }
  if$
}

FUNCTION {stop}
{ duplicate$ empty$ 'skip$ 'add.period$ if$ }

FUNCTION {output.entry}
{ 'vs :=
  newline$
  "\bibitem[{" label.authors * "(" * year * extra.label * ")" * label.authors * "}]{" * cite$ * "}" * write$
  newline$
  author format.names " (" * year * extra.label * ") " * title add.period$ *
  vs stop then
  note field.or.null stop then
  link then
  write$
  newline$
}

FUNCTION {article} { venue.article output.entry }
FUNCTION {inproceedings} { venue.in output.entry }
FUNCTION {incollection} { venue.in output.entry }
FUNCTION {conference} { venue.in output.entry }
FUNCTION {book} { venue.book output.entry }
FUNCTION {phdthesis} { venue.thesis output.entry }
FUNCTION {mastersthesis} { venue.thesis output.entry }
FUNCTION {techreport} { venue.report output.entry }
FUNCTION {misc} { venue.misc output.entry }
FUNCTION {default.type} { misc }

READ

%% a/b suffixes: within equal labels and years, ordered by title and then key.
FUNCTION {presort}
{ label.authors " " * year * 'label :=
  label purify$ "    " * title purify$ "l" change.case$ * "    " * cite$ *
  'sort.key$ :=
}

ITERATE {presort}
SORT

FUNCTION {initialize.extra}
{ "" 'last.label :=
  "" 'next.extra :=
  #0 'last.extra.num :=
}

FUNCTION {forward.pass}
{ last.label label =
    { last.extra.num #1 + 'last.extra.num :=
      last.extra.num int.to.chr$ 'extra.label :=
    }
    { "a" chr.to.int$ 'last.extra.num :=
      "" 'extra.label :=
      label 'last.label :=
    }
  if$
}

FUNCTION {reverse.pass}
{ next.extra "b" =
    { "a" 'extra.label := }
    'skip$
  if$
  extra.label 'next.extra :=
}

EXECUTE {initialize.extra}
ITERATE {forward.pass}
EXECUTE {initialize.extra}
REVERSE {reverse.pass}

%% The list itself: by all authors, then year and title.
FUNCTION {final.sort}
{ author empty$ { "" } { author format.names } if$ purify$ "l" change.case$
  "    " * year * extra.label * "    " * title purify$ "l" change.case$ *
  'sort.key$ :=
}

ITERATE {final.sort}
SORT

FUNCTION {begin.bib}
{ "\begin{thebibliography}{}" write$ newline$
  "\providecommand{\url}[1]{\texttt{#1}}" write$ newline$
}

FUNCTION {end.bib}
{ newline$ "\end{thebibliography}" write$ newline$ }

EXECUTE {begin.bib}
ITERATE {call.type$}
EXECUTE {end.bib}
