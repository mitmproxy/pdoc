## -*- coding: utf-8 -*-
<%!
import pdoc
import pdoc.html_helpers as hh
%>


<!doctype html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, minimum-scale=1" />

  <%block name="title"/>

  <link href='https://fonts.googleapis.com/css?family=Source+Sans+Pro:400,300' rel='stylesheet' type='text/css'>
  <%namespace name="css" file="css.mako" />
  <style type="text/css">${css.pre()}</style>
  <style type="text/css">${css.pdoc()}</style>
  <style type="text/css">${css.post()}</style>

  <script type="text/javascript">
  function toggle(id, $link) {
    $node = document.getElementById(id);
    if (!$node)
    return;
    if (!$node.style.display || $node.style.display == 'none') {
    $node.style.display = 'block';
    $link.innerHTML = 'Hide source &nequiv;';
    } else {
    $node.style.display = 'none';
    $link.innerHTML = 'Show source &equiv;';
    }
  }
  </script>
</head>
<body>
<a href="#" id="top">Top</a>
<div id="container">
  ${next.body()}
  <div class="clear"> </div>
  <footer id="footer">
    <p>
      Generated by <a href="https://github.com/mitmproxy/pdoc">pdoc ${pdoc.__version__}</a>
    </p>
  </footer>
</div>

<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/9.12.0/styles/github.min.css">
<script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/9.12.0/highlight.min.js"></script>
<script>hljs.initHighlightingOnLoad();</script>
</body>
</html>
