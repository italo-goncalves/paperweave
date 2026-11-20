%% paperweave.cls -- a Work written as a LaTeX document (ADR 0002).
%%
%% Compiles to the Linear version: a standalone PDF of the Work's graph, in Paper order
%% (ADR 0003), not shaped to any journal. scripts/work_to_latex.py writes documents in
%% this class from the Work format; the reverse converter reads them back. Only the
%% commands defined here, plus ordinary math, are accepted in Node bodies.
%%
%%   \documentclass[tier=full]{paperweave}   tier = gist | summary | full
%%   \documentclass[noprimers]{paperweave}   leave Primers out of the PDF
%%
%% Preamble: \workid \title \author{A \and B} \workyear \venue \doi \code \keywords
%%           \results{id,...} \declarefigure{id}{file}{caption} and an abstract environment.
%% Nodes:    \begin{result}[contribution]{id}{Title} ... \end{result}, likewise method,
%%           concept, context, discussion and conclusion; Primers in primers/<id>.tex,
%%           pulled in with \includeprimer{id}.
%% Inside:   \uses \reliesOn \supports \explains \discusses \situates \synthesises {ids},
%%           \gist{...}, and summary and full environments.
%% Bodies:   \nodelink[text]{id} \showfigure{id} \citep \citet \subsection* itemize
%%           pwtable \href \url \emph \textbf, and math.
\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{paperweave}[2026/11/20 PaperWeave Works as LaTeX documents]

\RequirePackage{kvoptions}
\SetupKeyvalOptions{family=pw,prefix=pw@}
\DeclareStringOption[full]{tier}
\DeclareBoolOption{noprimers}
\DeclareDefaultOption{\PassOptionsToClass{\CurrentOption}{article}}
\ProcessKeyvalOptions*
\LoadClass[11pt,a4paper]{article}

\RequirePackage[T1]{fontenc}
\RequirePackage{lmodern}
\RequirePackage[utf8]{inputenc}
\RequirePackage{newunicodechar}
\RequirePackage{amsmath,amssymb}
\RequirePackage{graphicx}
\RequirePackage[export]{adjustbox}
\RequirePackage{booktabs}
\RequirePackage[dvipsnames]{xcolor}
\RequirePackage{environ}
\RequirePackage[margin=2.5cm]{geometry}
\RequirePackage[most]{tcolorbox}
\RequirePackage[round,authoryear]{natbib}
\RequirePackage{url}
\RequirePackage[colorlinks,linkcolor=pw@link,citecolor=pw@link,urlcolor=pw@link]{hyperref}
\bibliographystyle{paperweave}
\setlength{\parindent}{0pt}
\setlength{\parskip}{0.5em}

%% Characters that appear in Works but not in the T1 fonts.
\newunicodechar{★}{\ensuremath{\star}}
\newunicodechar{≈}{\ensuremath{\approx}}
\newunicodechar{≤}{\ensuremath{\leq}}
\newunicodechar{≥}{\ensuremath{\geq}}
\newunicodechar{×}{\ensuremath{\times}}
\newunicodechar{±}{\ensuremath{\pm}}
\newunicodechar{→}{\ensuremath{\rightarrow}}
\newunicodechar{−}{\ensuremath{-}}
\newunicodechar{ε}{\ensuremath{\varepsilon}}
\newunicodechar{σ}{\ensuremath{\sigma}}
\newunicodechar{μ}{\ensuremath{\mu}}
\newunicodechar{°}{\ensuremath{^\circ}}
\newunicodechar{′}{\ensuremath{'}}
\newunicodechar{″}{\ensuremath{''}}
\newunicodechar{α}{\ensuremath{\alpha}}
\newunicodechar{β}{\ensuremath{\beta}}
\newunicodechar{γ}{\ensuremath{\gamma}}
\newunicodechar{δ}{\ensuremath{\delta}}
\newunicodechar{λ}{\ensuremath{\lambda}}
\newunicodechar{ρ}{\ensuremath{\rho}}
\newunicodechar{τ}{\ensuremath{\tau}}
\newunicodechar{Σ}{\ensuremath{\Sigma}}
\newunicodechar{Δ}{\ensuremath{\Delta}}

%% Node type colours, as in the app.
\definecolor{pw@link}{HTML}{2563EB}
\definecolor{pw@result}{HTML}{C2410C}
\definecolor{pw@method}{HTML}{2563EB}
\definecolor{pw@concept}{HTML}{7C3AED}
\definecolor{pw@primer}{HTML}{0D9488}
\definecolor{pw@context}{HTML}{8A8578}
\definecolor{pw@discussion}{HTML}{CA8A04}
\definecolor{pw@conclusion}{HTML}{BE123C}

%% Detail tier to print: 1 gist, 2 summary, 3 full.
\newcount\pw@tiernum
\def\pw@tmp{gist}\ifx\pw@tier\pw@tmp \pw@tiernum=1 \fi
\def\pw@tmp{summary}\ifx\pw@tier\pw@tmp \pw@tiernum=2 \fi
\def\pw@tmp{full}\ifx\pw@tier\pw@tmp \pw@tiernum=3 \fi
\ifnum\pw@tiernum=0
  \ClassError{paperweave}{Unknown tier `\pw@tier'}{Use tier=gist, tier=summary or tier=full.}
  \pw@tiernum=3
\fi

%% ---- Metadata -------------------------------------------------------------
\def\pw@workid{}\def\pw@workyear{}\def\pw@venue{}\def\pw@doi{}\def\pw@code{}
\def\pw@keywords{}\def\pw@results{}\def\pw@abstract{}
\newcommand\workid[1]{\def\pw@workid{#1}}
\newcommand\workyear[1]{\def\pw@workyear{#1}}
\newcommand\venue[1]{\def\pw@venue{#1}}
\newcommand\doi[1]{\def\pw@doi{#1}}
\newcommand\code[1]{\def\pw@code{#1}}
\newcommand\keywords[1]{\def\pw@keywords{#1}}
\newcommand\results[1]{\def\pw@results{#1}}
\RenewEnviron{abstract}{\global\let\pw@abstract\BODY}

\newcommand\declarefigure[3]{%
  \expandafter\def\csname pw@ff@#1\endcsname{#2}%
  \expandafter\def\csname pw@fc@#1\endcsname{#3}}

%% ---- Titles of Nodes, through the .aux file --------------------------------
%% Written immediately and detokenized, so Nodes left out of the PDF still have them.
\def\pw@auxwrite#1#2#3{%
  \immediate\write\@auxout{\string#1{#2}{\detokenize\expandafter{#3}}}}
\newcommand\pw@settitle[2]{\expandafter\gdef\csname pw@t@#1\endcsname{#2}}
\newcommand\pw@setgist[2]{\expandafter\gdef\csname pw@g@#1\endcsname{#2}}
\newcommand\pw@setsuppressed[2]{\expandafter\gdef\csname pw@s@#1\endcsname{}}
\AtBeginDocument{%
  \immediate\write\@auxout{\string\providecommand\string\pw@settitle[2]{}}%
  \immediate\write\@auxout{\string\providecommand\string\pw@setgist[2]{}}%
  \immediate\write\@auxout{\string\providecommand\string\pw@setsuppressed[2]{}}}

\newcommand\pw@title[1]{%
  \ifcsname pw@t@#1\endcsname \csname pw@t@#1\endcsname
  \else \textbf{??~\detokenize{#1}}\ClassWarning{paperweave}{Unknown Node `#1' (rerun LaTeX?)}\fi}
\newcommand\pw@link[2]{% {id}{text}
  \ifcsname pw@s@#1\endcsname #2\else \hyperlink{node:#1}{#2}\fi}
\newcommand\nodelink[2][]{%
  \if\relax\detokenize{#1}\relax \pw@link{#2}{\pw@title{#2}}\else \pw@link{#2}{#1}\fi}

%% ---- Paper order: Nodes must come grouped by type (ADR 0003) ---------------
\newcount\pw@group \pw@group=0
\def\pw@groupof#1{%
  \ifcsname pw@gr@#1\endcsname\csname pw@gr@#1\endcsname\else0\fi}
\def\pw@gr@context{1}\def\pw@gr@concept{2}\def\pw@gr@primer{2}\def\pw@gr@method{3}
\def\pw@gr@result{4}\def\pw@gr@discussion{5}\def\pw@gr@conclusion{6}
\def\pw@checkorder#1#2{% {type}{id}
  \ifnum\pw@groupof{#1}<\pw@group
    \ClassError{paperweave}{Node `#2' (#1) is out of Paper order}{Write Nodes grouped as Context, Concept and Primer, Method, Result, Discussion, Conclusion.}%
  \fi
  \global\pw@group=\pw@groupof{#1}\relax}

%% ---- Nodes -----------------------------------------------------------------
\newif\ifpw@suppress
\newif\ifpw@contribution
\def\pw@id{}\def\pw@type{}
\def\pw@typelabel@result{Result}\def\pw@typelabel@method{Method}
\def\pw@typelabel@concept{Concept}\def\pw@typelabel@primer{Primer}
\def\pw@typelabel@context{Context}\def\pw@typelabel@discussion{Discussion}
\def\pw@typelabel@conclusion{Conclusion}

\newcommand\pw@heading{%
  \par\addvspace{1.8em}%
  \noindent\hypertarget{node:\pw@id}{}%
  {\small\sffamily\bfseries\color{pw@\pw@type}\MakeUppercase{\csname pw@typelabel@\pw@type\endcsname}%
   \ifpw@contribution\enspace\textcolor{pw@result}{$\star$\,Contribution}\fi}\par\nobreak
  \vspace{0.1em}%
  {\Large\bfseries\boldmath\csname pw@t@\pw@id\endcsname\par}\nobreak}

\newcommand\pw@begin[4]{% {type}{options}{id}{title}
  \pw@checkorder{#1}{#3}%
  \def\pw@type{#1}\def\pw@id{#3}%
  \def\pw@opt{#2}\def\pw@tmp{contribution}%
  \ifx\pw@opt\pw@tmp\pw@contributiontrue\else\pw@contributionfalse\fi
  \pw@auxwrite\pw@settitle{#3}{#4}%
  \expandafter\gdef\csname pw@t@#3\endcsname{#4}%
  \ifpw@suppress\pw@auxwrite\pw@setsuppressed{#3}{}\fi
  \global\let\pw@gist\@empty\global\let\pw@summary\@undefined\global\let\pw@full\@undefined
  \ifpw@suppress\else\pw@heading\fi}

%% At the end of a Node: print the chosen tier (the requested one, or the next shorter one
%% that exists), and run the other tiers through a discarded box, in tier order, so that
%% equation numbers are the same whichever tier is printed.
\newcount\pw@choice
\newcommand\pw@end{%
  \pw@choice=0
  \ifpw@suppress\else
    \ifnum\pw@tiernum>2 \ifdefined\pw@full \pw@choice=2 \fi\fi
    \ifnum\pw@choice=0 \ifnum\pw@tiernum>1 \ifdefined\pw@summary \pw@choice=1 \fi\fi\fi
  \fi
  \ifdefined\pw@summary \ifnum\pw@choice=1 \pw@body\pw@summary\else\pw@discard\pw@summary\fi\fi
  \ifdefined\pw@full \ifnum\pw@choice=2 \pw@body\pw@full\else\pw@discard\pw@full\fi\fi}
\def\pw@body#1{\par\nobreak #1\par}
\newif\ifpw@discarding
\def\pw@discard#1{\setbox\z@\vbox{\pw@discardingtrue #1}}

\newcommand\gist[1]{%
  \pw@auxwrite\pw@setgist{\pw@id}{#1}%
  \ifpw@suppress\else\par{\itshape #1\par}\fi}
\NewEnviron{summary}{\global\let\pw@summary\BODY}
\NewEnviron{full}{\global\let\pw@full\BODY}

\newcommand\pw@defnode[1]{%
  \NewDocumentEnvironment{#1}{O{} m m}{\pw@begin{#1}{##1}{##2}{##3}}{\pw@end}}
\pw@defnode{result}\pw@defnode{method}\pw@defnode{concept}\pw@defnode{context}
\pw@defnode{discussion}\pw@defnode{conclusion}

%% A Primer has no tiers; its body is its single level, boxed.
\newtcolorbox{pw@primerbox}{breakable,enhanced,colback=pw@primer!6,colframe=pw@primer!60,
  boxrule=0.6pt,arc=2pt,left=8pt,right=8pt,top=6pt,bottom=6pt,before skip=1.5em,
  before upper={\setlength{\parskip}{0.5em}}}
\NewDocumentEnvironment{primer}{O{} m m}
  {\pw@checkorder{primer}{#2}\def\pw@type{primer}\def\pw@id{#2}\pw@contributionfalse
   \pw@auxwrite\pw@settitle{#2}{#3}\expandafter\gdef\csname pw@t@#2\endcsname{#3}%
   \ifpw@suppress\pw@auxwrite\pw@setsuppressed{#2}{}\setbox0\vbox\bgroup\pw@discardingtrue
   \else\begin{pw@primerbox}\hypertarget{node:#2}{}%
     {\small\sffamily\bfseries\color{pw@primer}PRIMER}\par\nobreak
     {\large\bfseries\boldmath #3\par}\nobreak\fi}
  {\ifpw@suppress\egroup\else\end{pw@primerbox}\fi}

\newcommand\includeprimer[1]{%
  \ifpw@noprimers\pw@suppresstrue\fi
  \input{primers/#1}%
  \pw@suppressfalse}

%% ---- Numbered equations (Equation labels) ----------------------------------
%% \begin{equation}\label{eq-x} ... \end{equation}, with the label first. Numbers run
%% across the Work in Paper order, counted in every tier whether printed or not, as in
%% the app; an equation repeated in another tier of its Node keeps its number.
\newcount\pw@eqcount
\newcommand\pw@seteq[2]{\expandafter\gdef\csname pw@eqn@#1\endcsname{#2}}
\newcommand\pw@seteqshown[2]{\expandafter\gdef\csname pw@eqs@#1\endcsname{}}
\AtBeginDocument{%
  \immediate\write\@auxout{\string\providecommand\string\pw@seteq[2]{}}%
  \immediate\write\@auxout{\string\providecommand\string\pw@seteqshown[2]{}}}
\RenewEnviron{equation}{\expandafter\pw@equation\BODY\pw@endeq}
\long\def\pw@equation#1#2\pw@endeq{%
  \ifx\label#1\else
    \ClassError{paperweave}{A numbered equation must start with \string\label{eq-...}}{Unlabelled equations are written \string\[ ... \string\].}%
  \fi
  \pw@numbered#2\pw@endeq}
\long\def\pw@numbered#1#2\pw@endeq{% {label} body
  \ifcsname pw@eqnl@#1\endcsname\else
    \global\advance\pw@eqcount\@ne
    \expandafter\xdef\csname pw@eqnl@#1\endcsname{\the\pw@eqcount}%
    \immediate\write\@auxout{\string\pw@seteq{#1}{\the\pw@eqcount}}%
  \fi
  \edef\pw@n{\csname pw@eqnl@#1\endcsname}%
  \let\pw@anchor\@empty
  \ifpw@discarding\else\ifcsname pw@eqsl@#1\endcsname\else
    \expandafter\gdef\csname pw@eqsl@#1\endcsname{}%
    \immediate\write\@auxout{\string\pw@seteqshown{#1}{}}%
    \def\pw@anchor{\hypertarget{eq:#1}{}}%
  \fi\fi
  \[#2\tag{\pw@anchor\pw@n}\]}
\renewcommand\eqref[1]{%
  \ifcsname pw@eqn@#1\endcsname
    (\ifcsname pw@eqs@#1\endcsname\hyperlink{eq:#1}{\csname pw@eqn@#1\endcsname}\else\csname pw@eqn@#1\endcsname\fi)%
  \else (\textbf{??})\ClassWarning{paperweave}{Unknown equation `#1' (rerun LaTeX?)}\fi}

%% ---- Edges -----------------------------------------------------------------
\ExplSyntaxOn
\cs_new_protected:Npn \pw_edge:nn #1#2
  {
    \legacy_if:nF { pw@suppress }
      {
        \par{\small\sffamily\textcolor{black!55}{#1:}~
        \clist_set:Nn \l_tmpa_clist {#2}
        \seq_clear:N \l_tmpa_seq
        \clist_map_inline:Nn \l_tmpa_clist { \seq_put_right:Nn \l_tmpa_seq { \pw@link{##1}{\pw@title{##1}} } }
        \seq_use:Nn \l_tmpa_seq { ,~ }
        \par}
      }
  }
\NewDocumentCommand \uses { m } { \pw_edge:nn { Uses } {#1} }
\NewDocumentCommand \reliesOn { m } { \pw_edge:nn { Relies~on } {#1} }
\NewDocumentCommand \supports { m } { \pw_edge:nn { Supports } {#1} }
\NewDocumentCommand \explains { m } { \pw_edge:nn { Explains } {#1} }
\NewDocumentCommand \discusses { m } { \pw_edge:nn { Discusses } {#1} }
\NewDocumentCommand \situates { m } { \pw_edge:nn { Situates } {#1} }
\NewDocumentCommand \synthesises { m } { \pw_edge:nn { Synthesises } {#1} }

%% The Results list at the front: each Result's title and Gist.
\cs_new_protected:Npn \pw_resultslist:
  {
    \tl_if_empty:NF \pw@results
      {
        \section*{Results}
        \begin{itemize}
        \clist_set:No \l_tmpb_clist { \pw@results }
        \clist_map_inline:Nn \l_tmpb_clist
          {
            \item \pw@link{##1}{\textbf{\pw@title{##1}}}
              \cs_if_exist:cT { pw@g@##1 } { \\ \use:c { pw@g@##1 } }
          }
        \end{itemize}
      }
  }
\ExplSyntaxOff

%% A bare link written <url> in Markdown; # and % arrive escaped.
\newcommand\autolink[1]{\href{#1}{\nolinkurl{#1}}}

%% ---- Figures and tables ----------------------------------------------------
\newcommand\showfigure[1]{%
  \ifcsname pw@ff@#1\endcsname
    \par\begin{center}%
      \includegraphics[max width=\linewidth,max height=0.5\textheight]{\csname pw@ff@#1\endcsname}\par
      \vspace{0.3em}\parbox{0.92\linewidth}{\small\csname pw@fc@#1\endcsname}%
    \end{center}%
  \else\ClassError{paperweave}{Unknown figure `#1'}{Declare it with \string\declarefigure.}\fi}

\NewEnviron{pwtable}[1]{%
  \par\begin{center}\small
  \adjustbox{max width=\linewidth}{\begin{tabular}{#1}\toprule\BODY\bottomrule\end{tabular}}%
  \end{center}}

%% ---- Front matter and references ---------------------------------------------
\renewcommand\maketitle{%
  \begingroup\centering
  {\LARGE\bfseries\@title\par}\vspace{0.8em}
  {\large\def\and{, }\@author\par}\vspace{0.4em}
  {\small\pw@venue\ifx\pw@workyear\@empty\else\ifx\pw@venue\@empty\else\ \textperiodcentered\ \fi\pw@workyear\fi\par}
  \ifx\pw@doi\@empty\else{\small\url{\pw@doi}\par}\fi
  \ifx\pw@code\@empty\else{\small Code: \url{\pw@code}\par}\fi
  \endgroup\vspace{1.2em}
  \ifx\pw@abstract\@empty\else
    \begin{center}\begin{minipage}{0.9\linewidth}\small\textbf{Abstract.}\ \pw@abstract
      \ifx\pw@keywords\@empty\else\par\textbf{Keywords:}\ \pw@keywords\fi
    \end{minipage}\end{center}\fi
  \csname pw_resultslist:\endcsname
  \par\bigskip\hrule\bigskip}

\renewcommand\bibsection{\section*{References}}
%% The reference list is the Work's, whichever Detail tier is printed.
\AtBeginDocument{\nocite{*}}
\endinput
