## -*- coding: utf-8 -*-
<%!
import pygments
import pdoc.doc
import pdoc.html_helpers as hh
%>

<%inherit file="html_frame.mako"/>

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
        <div class="desc">${desc | hh.mark}</div>
      % endif
      </td>
    </tr>
  % endfor
  </table>
% endif
</%def>

<%block name="title">
  <title>Python module index</title>
  <meta name="description" content="Python module index" />
</%block>

<article id="content">${show_module_list(modules)}</article>