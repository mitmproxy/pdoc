## -*- coding: utf-8 -*-
<%!
import pygments
import pdoc.doc
import pdoc.html_helpers as hh
%>

<%inherit file="html_frame.mako"/>

<%def name="show_module_list(roots)">
<h1>Python module list</h1>
  <table id="module-list">
  % for name, doc in roots:
    <tr>
      <td><a href="${link_prefix}${name}">${name}</a></td>
      <td>
      % if len(doc.strip()) > 0:
        <div class="desc">${doc | hh.mark}</div>
      % endif
      </td>
    </tr>
  % endfor
  </table>
</%def>

<%block name="title">
  <title>Python module index</title>
  <meta name="description" content="Python module index" />
</%block>

<article id="content">${show_module_list(roots)}</article>