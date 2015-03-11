## Define mini-templates for each portion of the doco.

<%!
  import re
  from os.path import join
  from pdoc import markdown_module_suffix, markdown_package_name

  def docstring(d):
      if len(d.docstring) == 0 and hasattr(d, 'inherits'):
          return d.inherits.docstring
      else:
          return d.docstring

  def nl2br(string):
      string = string.replace("\r\n\r\n", "\r\n\r\n    ")
      string.replace("\r\n", "  \r\n")
      string = string.replace("\n\n", "\n\n    ")
      string.replace("\n", "  \n")
      string = string.replace("\r\r", "\r\r    ")
      string.replace("\r", "  \r")
      return string

  def h1(string):
      string = "# " + string
      return string

  def h2(string):
      string = "## " + string
      return string

  def h3(string):
      string = "### " + string
      return string

  def h4(string):
      string = "#### " + string
      return string

  def h6(string):
      string = "##### " + string
      return string

  def h6(string):
      string = "###### " + string
      return string

  def makeup(string):
      strings = string.splitlines()
      dd = re.compile(r':')
      li = re.compile(r'^([0-9]+[\.)]|\*|\-\+)')
      snc = re.compile(r'^[A-Z]\w?')
      code = re.compile(r'^(#!|\.{1,3}|>{1,3})')
      qu = re.compile(r'^`{1,3}')
      codeblock = False
      for i, s in enumerate(strings):
          s = s.lstrip()
          if snc.search(s) and i != 0:
              strings[i-1] += '  '
          if dd.search(s):
              s += '  '
          if li.search(s):
              s = '\n' + s
          if qu.search(s):
              codeblock = not codeblock
          if code.search(s) and not codeblock:
              s = '```\n' + s
              codeblock = True
          if s == '' and codeblock:
              s = '```'
              codeblock = False
          strings[i] = s
      if codeblock:
          strings.append('```')
          codeblock = False
      return '\n'.join(strings)

  def submodule_link(submodule, module):
      path = submodule.name
      path = path.replace(module.name, '', 1)
      path = path.lstrip('.')
      path = path.split('.')
      if submodule.is_package():
          path.append(markdown_package_name)
      else:
          e = path[-1]
          del path[-1]
          path.append(e + markdown_module_suffix)
      path = join(*path)
      return path
%>

<%def name="function(func)" filter="trim">
**${func.name}** (${func.spec()})

    ${docstring(func) | makeup,nl2br}

</%def>

<%def name="variable(var)" filter="trim">
**${var.name}**

    ${docstring(var) | makeup,nl2br}

</%def>

<%def name="class_(cls)" filter="trim">
${cls.name | h4} \
% if len(cls.docstring) > 0:

${cls.docstring | makeup}

% endif
<%
  class_vars = cls.class_variables()
  static_methods = cls.functions()
  inst_vars = cls.instance_variables()
  methods = cls.methods()
  mro = cls.module.mro(cls)
  descendents = cls.module.descendents(cls)
%>
% if len(mro) > 0:
${"Ancestors (in MRO)" | h6}
% for c in mro:
- ${c.refname}

% endfor
% endif

% if len(descendents) > 0:
${"Descendents" | h6}
% for c in descendents:
- ${c.refname}

% endfor
% endif

% if len(class_vars) > 0:
${"Class variables" | h6}
% for v in class_vars:
- ${capture(variable, v)}

% endfor
% endif

% if len(static_methods) > 0:
${"Static methods" | h6}
% for f in static_methods:
- ${capture(function, f)}

% endfor
% endif

% if len(inst_vars) > 0:
${"Instance variables" | h6}
% for v in inst_vars:
- ${capture(variable, v)}

% endfor
% endif

% if len(methods) > 0:
${"Methods" | h6}
% for m in methods:
- ${capture(function, m)}

% endfor
% endif
</%def>

## Start the output logic for an entire module.

<%
  variables = module.variables()
  classes = module.classes()
  functions = module.functions()
  submodules = module.submodules()
%>

Module ${module.name}
-------${'-' * len(module.name)}

${module.docstring | makeup}



% if len(variables) > 0:
Variables
---------
% for v in variables:
- ${variable(v)}

% endfor
% endif


% if len(functions) > 0:
Functions
---------
% for f in functions:
- ${function(f)}

% endfor
% endif


% if len(classes) > 0:
Classes
-------
% for c in classes:
${class_(c)}

% endfor
% endif


% if len(submodules) > 0:
Sub-modules
-----------
% for m in submodules:
- [${m.name}](${submodule_link(m, module)})

% endfor
% endif
