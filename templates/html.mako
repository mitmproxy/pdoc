<%
  import re
  import sys

  import markdown
  try:
      import pygments.formatters
      use_pygments = True
  except ImportError:
      use_pygments = False

  import pdoc

  # From language reference, but adds '.' to allow fully qualified names.
  pyident = re.compile('^[a-zA-Z_][a-zA-Z0-9_.]+$')

  # Whether we're showing the module list or a single module.
  module_list = 'modules' in context.keys()


  def eprint(s):
      print >> sys.stderr, s


  def ident(s):
      return '<span class="ident">%s</span>' % s


  def linkify(match):
      matched = match.group(0)
      ident = matched[1:-1]
      name, url = lookup(ident)
      if name is None:
          return matched
      return '[`%s`](%s)' % (name, url)


  def mark(s):
      s, _ = re.subn('\b\n\b', ' ', s)
      if not module_list:
          s, _ = re.subn('`[^`]+`', linkify, s)
      
      extensions = []
      if use_pygments:
          extensions = ['codehilite(linenums=False)']
      s = markdown.markdown(s.strip(), extensions=extensions)
      return s


  def glimpse(s, length=100):
      if len(s) < length:
          return s
      return s[0:length] + '...'


  def module_url(m):
      """
      Returns a URL for `m`, which must be an instance of `Module`.
      Also, `m` must be a submodule of the module being documented.

      Namely, '.' import separators are replaced with '/' URL
      separators. Also, packages are translated as directories
      containing `index.html` corresponding to the `__init__` module,
      while modules are translated as regular HTML files with an
      `.m.html` suffix. (Given default values of 
      `pdoc.html_module_suffix` and `pdoc.html_package_name`.)
      """
      if module.name == m.name:
          return ''

      if len(link_prefix) > 0:
          base = m.name
      else:
          base = m.name[len(module.name)+1:]
      url = base.replace('.', '/')
      if m.is_package():
          url += '/%s' % pdoc.html_package_name
      else:
          url += pdoc.html_module_suffix
      return link_prefix + url


  def external_url(refname):
      """
      Attempts to guess an absolute URL for the external identifier
      given.

      Note that this just returns the refname with an ".ext" suffix.
      It will be up to whatever is interpreting the URLs to map it
      to an appropriate documentation page.
      """
      return '/%s.ext' % refname


  def is_external_linkable(name):
      return external_links and pyident.match(name) and '.' in name


  def lookup(refname):
      """
      Given a fully qualified identifier name, return its refname
      with respect to the current module and a value for a `href`
      attribute. If `refname` is not in the public interface of
      this module or its submodules, then `None` is returned for
      both return values. (Unless this module has enabled external
      linking.)

      In particular, this takes into account sub-modules and external
      identifiers. If `refname` is in the public API of the current
      module, then a local anchor link is given. If `refname` is in the
      public API of a sub-module, then a link to a different page with
      the appropriate anchor is given. Otherwise, `refname` is
      considered external and no link is used.
      """
      d = module.find_ident(refname)
      if isinstance(d, pdoc.External):
          if is_external_linkable(refname):
              return d.refname, external_url(d.refname)
          else:
              return None, None
      if isinstance(d, pdoc.Module):
          return d.refname, module_url(d)
      if module.is_public(d.refname):
          return d.name, '#%s' % d.refname
      return d.refname, '%s#%s' % (module_url(d.module), d.refname)

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
<%def name="show_desc(d, limit=None)">
  <%
    inherits = hasattr(d, 'inherits') and len(d.docstring) == 0
    docstring = (d.inherits.docstring if inherits else d.docstring).strip()
    if limit is not None:
        docstring = glimpse(docstring, limit)
  %>
  % if len(docstring) > 0:
    % if inherits:
      <div class="desc inherited">${docstring | mark}</div>
    % else:
      <div class="desc">${docstring | mark}</div>
    % endif
  % else:
      <div class="empty_desc">&nbsp;</div>
  % endif
</%def>

<%def name="show_inheritance(d)">
  % if hasattr(d, 'inherits'):
      <p class="inheritance">
         <strong>Inheritance:</strong>
         % if hasattr(d.inherits, 'cls'):
           <code>${link(d.inherits.cls.refname)}</code>.<code>${link(d.inherits.refname)}</code>
         % else:
           <code>${link(d.inherits.refname)}</code>
         % endif
      </p>
  % endif
</%def>

<%def name="show_module_list(modules)">
<h1>Python module list</h1>

% if len(modules) == 0:
    <p>No modules found.</p>
% else:
    <table id="module-list">
    % for name, desc in modules:
        <tr>
          <td><a href="${link_prefix}${name}">${name}</a></td>
          <td>
            % if len(desc.strip()) > 0:
              <div class="desc">${desc | mark}</div>
            % endif
          </td>
        </tr>
    % endfor
    </table>
% endif
</%def>

<%def name="show_module(module)">
  <%
    variables = module.variables()
    classes = module.classes()
    functions = module.functions()
    submodules = module.submodules()
  %>

  <%def name="show_func(f)">
    <div class="item">
      <div class="name" id="${f.refname}">
        <table>
          <tr><td>def ${ident(f.name)}(</td><td>${f.spec()})</td></tr>
        </table>
      </div>
      ${show_inheritance(f)}
      ${show_desc(f)}
    </div>
  </%def>

  % if 'http_server' in context.keys() and http_server:
      <p id="nav">
          <a href="/">All packages</a>
      <% parts = module.name.split('.')[:-1] %>
      % for i, m in enumerate(parts):
          <% parent = '.'.join(parts[:i+1]) %>
          :: <a href="/${parent.replace('.', '/')}">${parent}</a>
      % endfor
      </p>
  % endif

  <h1>Module ${module.name}</h1>
  ${module.docstring | mark}

  <h2>Index</h2>

  <ul id="index">
  % if len(variables) > 0:
    <li><a href="#header-variables">Module variables</a>
      <ul>
        % for v in variables:
          <li class="mono">${link(v.refname)}</li>
        % endfor
      </ul>
    </li>
  % endif

  % if len(functions) > 0:
    <li><a href="#header-functions">Functions</a>
      <ul>
        % for f in functions:
          <li class="mono">${link(f.refname) | trim}(${f.spec()})</li>
        % endfor
      </ul>
    </li>
  % endif

  % if len(classes) > 0:
    <li><a href="#header-classes">Classes</a>
      <ul>
        % for c in classes:
          <li class="mono">${link(c.refname)}
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
          <li class="mono">${link(m.refname)}</li>
        % endfor
      </ul>
    </li>
  % endif
  </ul>

  % if len(variables) > 0:
  <h2 id="header-variables">Module variables</h2>
  % for v in variables:
      <div class="item">
        <p id="${v.refname}" class="name">var ${ident(v.name)}</p>
        ${show_desc(v)}
      </div>
  % endfor
  % endif

  % if len(functions) > 0:
  <h2 id="header-functions">Functions</h2>
  % for f in functions:
      ${show_func(f)}
  % endfor
  % endif

  % if len(classes) > 0:
  <h2 id="header-classes">Classes</h2>
  % for c in classes:
      <%
        class_vars = c.class_variables()
        smethods = c.functions()
        inst_vars = c.instance_variables()
        methods = c.methods()
        mro = c.module.mro(c)
      %>
      <div class="item">
        <p id="${c.refname}" class="name">class ${ident(c.name)}</p>
        ${show_desc(c)}

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
                    <p id="${v.refname}" class="name">var ${ident(v.name)}</p>
                    ${show_inheritance(v)}
                    ${show_desc(v)}
                  </div>
              % endfor
          % endif
          % if len(smethods) > 0:
              <h3>Static methods</h3>
              % for f in smethods:
                  ${show_func(f)}
              % endfor
          % endif
          % if len(inst_vars) > 0:
              <h3>Instance variables</h3>
              % for v in inst_vars:
                  <div class="item">
                    <p id="${v.refname}" class="name">var ${ident(v.name)}</p>
                    ${show_inheritance(v)}
                    ${show_desc(v)}
                  </div>
              % endfor
          % endif
          % if len(methods) > 0:
              <h3>Methods</h3>
              % for f in methods:
                  ${show_func(f)}
              % endfor
          % endif
        </div>
      </div>
  % endfor
  % endif

  % if len(submodules) > 0:
  <h2 id="header-submodules">Sub-modules</h2>
  % for m in submodules:
      <div class="item">
        <p class="name">${link(m.refname)}</p>
        ${show_desc(m, limit=300)}
      </div>
  % endfor
  % endif
</%def>

<!doctype html>
<!--[if lt IE 7]> <html class="no-js lt-ie9 lt-ie8 lt-ie7" lang="en"> <![endif]-->
<!--[if IE 7]>		<html class="no-js lt-ie9 lt-ie8" lang="en"> <![endif]-->
<!--[if IE 8]>		<html class="no-js lt-ie9" lang="en"> <![endif]-->
<!--[if gt IE 8]><!--> <html class="no-js" lang="en"> <!--<![endif]-->
<head>
	<meta charset="utf-8">

  % if module_list:
      <title>Python module list</title>
      <meta name="description" content="A list of Python modules in sys.path">
  % else:
      <title>${module.name} API documentation</title>
      <meta name="description" content="${module.docstring | glimpse, trim}">
  % endif

  <%namespace name="css" file="css.mako" />
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
    clear: both;
  }

  h3 {
    margin: 0;
    font-size: 110%;
  }

  #nav {
    font-size: 130%;
    margin: 0 0 15px 0;
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

  code, .mono, .name {
    font-family: "Cousine", "Ubuntu Mono", "DejaVu Sans Mono", monospace;
  }

  .ident {
    color: #900;
  }

  code {
    background: #e8e8e8;
  } 

  .codehilite {
    margin: 0 30px 0 30px;
  }
  
  pre {
    background: #e8e8e8;
    padding: 6px;
  }

  table#module-list {
    font-size: 110%;
  }

    table#module-list tr td:first-child {
      padding-right: 10px;
      white-space: nowrap;
    }

    table#module-list td {
      vertical-align: top;
      padding-bottom: 8px;
    }

      table#module-list td p {
        margin: 0 0 7px 0;
      }

  .name table {
  }

    .name table tr td:first-child {
      white-space: nowrap;
    }

    .name table tr td {
      vertical-align: top;
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
      margin: -15px 0 25px 30px;
    }

      .item .class ul.class_list {
        margin: 0 0 20px 0;
      }

    .item .name {
      background: #e8e8e8;
      padding: 4px;
      margin: 0 0 8px 0;
      font-size: 110%;
      font-weight: bold;
    }

    .item .empty_desc {
      margin: 0 0 5px 0;
      padding: 0;
    }

    .item .inheritance {
      margin: 3px 0 10px 0;
      padding: 0 8px;
    }

    .item .inherited {
      color: #666;
    }

    .item .desc {
      padding: 0 8px;
      margin: 0 0 25px 0;
    }

      .item .desc p {
        margin: 0 0 10px 0;
      }

  .desc h1, .desc h2, .desc h3 {
    font-size: 100% !important;
  }

  /*****************************/
  </style>

  % if use_pygments:
    <style type="text/css">
    ${pygments.formatters.HtmlFormatter().get_style_defs('.codehilite')}
    </style>
  % endif

  <style type="text/css">
  ${css.post()}
  </style>
</head>
<body>
<div id="container">

% if module_list:
    ${show_module_list(modules)}
% else:
    ${show_module(module)}
% endif

<hr>
<p style="text-align: right;">
  Documentation generated by
  <code><a href="https://github.com/BurntSushi/pdoc">pdoc</a></code>
  with the <a href="http://unlicense.org">UNLICENSE</a>.
</p>
</div>
</body>
</html>
