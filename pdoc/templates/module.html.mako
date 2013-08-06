<%
  import re
  import sys

  import markdown
  import pygments.formatters

  import pdoc

  def eprint(s):
      print >> sys.stderr, s

  def linkify(match):
      matched = match.group(0)
      ident = matched[1:-1]
      name, url = lookup(ident)
      if name is None:
          return matched
      return '[`%s`](%s)' % (name, url)

  def mark(s):
      s, _ = re.subn('\b\n\b', ' ', s)
      s, _ = re.subn('`[^`]+`', linkify, s)
      s = markdown.markdown(s.strip(),
                            extensions=['codehilite(linenums=False)'])
      return s

  def glimpse(s, length=100):
      if len(s) < length:
          return s
      return s[0:length] + '...'

  def lookup(refname):
      """
      Given a fully qualified identifier name, return its refname
      with respect to the current module and a value for a `href`
      attribute. If `refname` is not in the public interface of
      this module or its submodules, then `None` is returned for
      both return values.

      In particular, this takes into account sub-modules and external
      identifiers. If `refname` is in the public API of the current
      module, then a local anchor link is given. If `refname` is in the
      public API of a sub-module, then a link to a different page with
      the appropriate anchor is given. Otherwise, `refname` is
      considered external and no link is used.
      """
      d = module.find_ident(refname)
      if isinstance(d, pdoc.External):
          return None, None
      if isinstance(d, pdoc.Module):
          return d.refname, '%s.html' % d.refname
      if module.is_public(d.refname):
          return d.name, '#%s' % d.refname
      return d.refname, '%s.html#%s' % (d.module.refname, d.refname)

  def link(refname):
      """
      A convenience wrapper around `href` to produce the full
      `a` tag if `refname` is found. Otherwise, plain text of
      `refname` is returned.
      """
      name, url = lookup(refname)
      if name is None:
          return refname
      return '<a href="%s">%s</a>' % (url, name)
%>
<%def name="show_desc(docstring)">
  % if len(docstring.strip()) > 0:
      <div class="desc">${docstring | mark}</div>
  % else:
      <div class="empty_desc">&nbsp;</div>
  % endif
</%def>

<!doctype html>
<!--[if lt IE 7]> <html class="no-js lt-ie9 lt-ie8 lt-ie7" lang="en"> <![endif]-->
<!--[if IE 7]>		<html class="no-js lt-ie9 lt-ie8" lang="en"> <![endif]-->
<!--[if IE 8]>		<html class="no-js lt-ie9" lang="en"> <![endif]-->
<!--[if gt IE 8]><!--> <html class="no-js" lang="en"> <!--<![endif]-->
<head>
	<meta charset="utf-8">

  <title>${module.name} API documentation</title>

	<meta name="description" content="${module.docstring | glimpse, trim}">

  <%namespace name="css" file="module.css.mako" />
  <style type="text/css">
  ${css.pre()}
  </style>

  <style type="text/css">
  /*****************************/
  /**
   * Above and below this section is HTML5 Boilerplate.
   * In this section is specific CSS for pdoc.
   */

  html, body {
    margin: 0;
    padding: 0;
    background: #ddd;
    height: 100%;
  }

  #container {
    width: 840px;
    background-color: #fdfdfd;
    color: #333;
    margin: 0 auto;
    border-left: 1px solid #000;
    border-right: 1px solid #000;
    padding: 20px;
    min-height: 100%;
  }

  h1 {
    margin: 0 0 10px 0;
  }

  h2 {
    margin: 25px 0 10px 0;
  }

  h3 {
    margin: 0;
    font-size: 110%;
  }

  a {
    color: #069;
    text-decoration: none;
  }

  a:hover {
    color: #e08524;
  }

  p {
    line-height: 1.35em;
  }

  code {
    font-family: "Cousine", "Ubuntu Mono", "DejaVu Sans Mono", monospace;
  }

  .codehilite {
    margin: 0 30px 0 30px;
  }
  
  pre {
    background: #e8e8e8;
    padding: 6px;
  }

  ul#index {
    padding: 0;
    margin: 0;
  }

    ul#index li {
      margin-bottom: 18px;
    }

      ul#index ul li {
        margin-bottom: 8px;
      }

  ul#index, ul#index ul {
    list-style-type: none;
  }

  ul#index ul {
    margin: 0 0 10px 30px;
    padding: 0;
  }

  .item {
  }

    .item .class {
      margin: 0 0 25px 30px;
    }

      .item .class ul.class_list {
        margin: 0 0 20px 0;
      }

    .item .name {
      background: #e8e8e8;
      padding: 6px 8px;
      margin: 0 0 8px 0;
      font-size: 110%;
      font-weight: bold;
    }

    .item .empty_desc {
      margin: 0 0 5px 0;
      padding: 0;
    }

    .item .desc {
      padding: 0 8px;
      margin: 0 0 25px 0;
    }

      .item .desc p {
        margin: 0 0 10px 0;
      }

      .item .desc h1, .item .desc h2, .item .desc h3 {
        font-size: 110%;
      }

  /*****************************/
  </style>

  <style type="text/css">
  ${pygments.formatters.HtmlFormatter().get_style_defs('.codehilite')}
  </style>

  <style type="text/css">
  ${css.post()}
  </style>
</head>
<body>
<div id="container">

<%
  variables = module.variables()
  classes = module.classes()
  functions = module.functions()
  submodules = module.submodules()
%>

<h1>Module ${module.name}</h1>
${module.docstring | mark}

<h2>Index</h2>

<ul id="index">
% if len(variables) > 0:
  <li><a href="#header-variables">Module variables</a>
    <ul>
      % for v in variables:
        <li>${link(v.refname)}</li>
      % endfor
    </ul>
  </li>
% endif

% if len(functions) > 0:
  <li><a href="#header-functions">Functions</a>
    <ul>
      % for f in functions:
        <li>${link(f.refname) | trim}(${f.spec()})</li>
      % endfor
    </ul>
  </li>
% endif

% if len(classes) > 0:
  <li><a href="#header-classes">Classes</a>
    <ul>
      % for c in classes:
        <li>${link(c.refname)}
          <%
            smethods = c.functions()
            methods = c.methods()
          %>
          % if len(smethods) > 0:
            <ul>
            % for f in smethods:
              <li>${link(f.refname)}</li>
            % endfor
            </ul>
          % endif
          % if len(methods) > 0:
            <ul>
            % for f in methods:
              <li>${link(f.refname)}</li>
            % endfor
            </ul>
          % endif
        </li>
      % endfor
    </ul>
  </li>
% endif

% if len(submodules) > 0:
  <li><a href="#header-submodules">Sub-modules</a>
    <ul>
      % for m in submodules:
        <li>${link(m.refname)}</li>
      % endfor
    </ul>
  </li>
% endif
</ul>

% if len(variables) > 0:
<a name="header-variables"></a>
<h2>Module variables</h2>
% for v in variables:
    <div class="item">
      <a name="${v.refname}"></a>
      <p class="name">${v.name}</p>
      ${show_desc(v.docstring)}
    </div>
% endfor
% endif

% if len(functions) > 0:
<a name="header-functions"></a>
<h2>Functions</h2>
% for f in functions:
    <div class="item">
      <a name="${f.refname}"></a>
      <p class="name">${f.name}(${f.spec()})</p>
      ${show_desc(f.docstring)}
    </div>
% endfor
% endif

% if len(classes) > 0:
<a name="header-classes"></a>
<h2>Classes</h2>
% for c in classes:
    <%
      class_vars = c.class_variables()
      smethods = c.functions()
      inst_vars = c.instance_variables()
      methods = c.methods()
      mro = c.module.mro(c)
    %>
    <div class="item">
      <a name="${c.refname}"></a>
      <p class="name">${c.name}</p>
      ${show_desc(c.docstring)}

      <div class="class">
        % if len(mro) > 0:
            <h3>Ancestors (in MRO)</h3>
            <ul class="class_list">
            % for cls in mro:
              <li>${link(cls.refname)}</li>
            % endfor
            </ul>
        % endif
        % if len(class_vars) > 0:
            <h3>Class variables</h3>
            % for v in class_vars:
                <div class="item">
                  <a name="${v.refname}"></a>
                  <p class="name">${v.name}</p>
                  ${show_desc(v.docstring)}
                </div>
            % endfor
        % endif
        % if len(smethods) > 0:
            <h3>Static methods</h3>
            % for f in smethods:
                <div class="item">
                  <a name="${f.refname}"></a>
                  <p class="name">${f.name}(${f.spec()})</p>
                  ${show_desc(f.docstring)}
                </div>
            % endfor
        % endif
        % if len(inst_vars) > 0:
            <h3>Instance variables</h3>
            % for v in inst_vars:
                <div class="item">
                  <a name="${v.refname}"></a>
                  <p class="name">${v.name}</p>
                  ${show_desc(v.docstring)}
                </div>
            % endfor
        % endif
        % if len(methods) > 0:
            <h3>Methods</h3>
            % for f in methods:
                <div class="item">
                  <a name="${f.refname}"></a>
                  <p class="name">${f.name}(${f.spec()})</p>
                  ${show_desc(f.docstring)}
                </div>
            % endfor
        % endif
      </div>
    </div>
% endfor
% endif

% if len(submodules) > 0:
<a name="header-submodules"></a>
<h2>Sub-modules</h2>
% for m in submodules:
    <div class="item">
      <p class="name">${link(m.refname)}</p>
      ${show_desc(glimpse(m.docstring, 300))}
    </div>
% endfor
% endif

</div>
</body>
</html>
