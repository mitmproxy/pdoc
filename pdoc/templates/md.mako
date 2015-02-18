## Define mini-templates for each portion of the doco.

<%!
  import re

  def docstring(d):
      if len(d.docstring) == 0 and hasattr(d, 'inherits'):
          return d.inherits.docstring
      else:
          return d.docstring

  def nl2br(str):
      str = str.replace("\r\n\r\n", "\r\n\r\n    ")
      str.replace("\r\n", "  \r\n")
      str = str.replace("\n\n", "\n\n    ")
      str.replace("\n", "  \n")
      str = str.replace("\r\r", "\r\r    ")
      str.replace("\r", "  \r")
      return str

  def h1(str):
      str = "# " + str
      return str

  def h2(str):
      str = "## " + str
      return str

  def h3(str):
      str = "### " + str
      return str

  def h4(str):
      str = "#### " + str
      return str

  def h6(str):
      str = "##### " + str
      return str

  def h6(str):
      str = "###### " + str
      return str

%>

<%def name="function(func)" filter="trim">
**${func.name}** (${func.spec()})

    ${docstring(func) | nl2br}  

</%def>

<%def name="variable(var)" filter="trim">
**${var.name}**

    ${docstring(var) | nl2br}  

</%def>

<%def name="class_(cls)" filter="trim">
${cls.name | h4} \
% if len(cls.docstring) > 0:

${cls.docstring}  

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
% if not module._filtering:
${module.docstring}
% endif


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
- ${m.name}

% endfor
% endif
