<%def name="pdoc()">
  html, body {
    margin: 0;
    padding: 0;
    background: #ddd;
    height: 100%;
  }

  #container {
    width: 840px;
    background-color: #fdfdfd;
    color: #111;
    margin: 0 auto;
    border-left: 1px solid #000;
    border-right: 1px solid #000;
    padding: 10px 25px;
    min-height: 100%;
  }

  #nav {
    font-size: 130%;
    margin: 0 0 15px 0;
  }

  #top {
    display: block;
    position: fixed;
    top: 5px;
    left: 5px;
    font-size: 140%;
  }

  h1 {
    margin: 0 0 10px 0;
  }

  h2 {
    margin: 25px 0 10px 0;
  }

  h3 {
    margin: 25px 0 10px 0;
  }

  h4 {
    margin: 0;
    font-size: 105%;
  }

  a {
    color: #058;
    text-decoration: none;
  }

  a:hover {
    color: #e08524;
  }

  p {
    line-height: 1.35em;
  }

  pre, code, .mono, .name {
    font-family: "Ubuntu Mono", "Cousine", "DejaVu Sans Mono", monospace;
  }

  .ident {
    color: #900;
  }

  code {
    background: #e8e8e8;
  }

  pre {
    background: #e8e8e8;
    padding: 6px;
    margin: 0 30px;
  }

  .codehilite {
    margin: 0 30px 10px 30px;
  }

    .codehilite pre {
      margin: 0;
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

  .def {
    display: table;
  }

    .def p {
      display: table-cell;
      vertical-align: top;
      text-align: left;
    }

    .def p:first-child {
      white-space: nowrap;
    }

    .def p:last-child {
      width: 100%;
    }

  ul#index {
    padding: 0;
    margin: 0;
  }

    ul#index .class_name {
      /* font-size: 110%; */
      font-weight: bold;
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
      margin: 0 0 10px 20px;
      padding: 0;
    }

  .column_list {
    width: 100%;
    display: inline-block;
    margin-left: 20px;
  }

  .column_list:after {
    visibility: hidden;
    display: block;
    font-size: 0;
    height: 0;
    content: " ";
    clear: both;
  }

    .column_list ul {
      float: left;
      text-align: left;
      width: 32%;
      margin: 0 !important;
    }

      .column_list li {
          overflow: hidden;
          text-overflow: ellipsis;
      }

  .item {
    margin: 0 0 25px 0;
  }

    .item .class {
      margin: 0 0 25px 30px;
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
      margin: 0;
    }

      .item .desc p {
        margin: 0 0 10px 0;
      }

    .source_cont {
      margin: 10px 8px 0 8px;
      padding: 0;
    }

    .source_link {
      font-weight: bold;
    }

    .source {
      display: none;
      max-height: 600px;
      overflow-y: scroll;
      margin-bottom: 15px;
    }

      .source .codehilite {
        margin: 0;
      }

  .desc h1, .desc h2, .desc h3 {
    font-size: 100% !important;
  }

  /*****************************/
</%def>
<%def name="pre()">
/*! normalize.css v1.1.1 | MIT License | git.io/normalize */

/* ==========================================================================
   HTML5 display definitions
   ========================================================================== */

/**
 * Correct `block` display not defined in IE 6/7/8/9 and Firefox 3.
 */

article,
aside,
details,
figcaption,
figure,
footer,
header,
hgroup,
main,
nav,
section,
summary {
    display: block;
}

/**
 * Correct `inline-block` display not defined in IE 6/7/8/9 and Firefox 3.
 */

audio,
canvas,
video {
    display: inline-block;
    *display: inline;
    *zoom: 1;
}

/**
 * Prevent modern browsers from displaying `audio` without controls.
 * Remove excess height in iOS 5 devices.
 */

audio:not([controls]) {
    display: none;
    height: 0;
}

/**
 * Address styling not present in IE 7/8/9, Firefox 3, and Safari 4.
 * Known issue: no IE 6 support.
 */

[hidden] {
    display: none;
}

/* ==========================================================================
   Base
   ========================================================================== */

/**
 * 1. Prevent system color scheme's background color being used in Firefox, IE,
 *    and Opera.
 * 2. Prevent system color scheme's text color being used in Firefox, IE, and
 *    Opera.
 * 3. Correct text resizing oddly in IE 6/7 when body `font-size` is set using
 *    `em` units.
 * 4. Prevent iOS text size adjust after orientation change, without disabling
 *    user zoom.
 */

html {
    background: #fff; /* 1 */
    color: #000; /* 2 */
    font-size: 100%; /* 3 */
    -webkit-text-size-adjust: 100%; /* 4 */
    -ms-text-size-adjust: 100%; /* 4 */
}

/**
 * Address `font-family` inconsistency between `textarea` and other form
 * elements.
 */

html,
button,
input,
select,
textarea {
    font-family: sans-serif;
}

/**
 * Address margins handled incorrectly in IE 6/7.
 */

body {
    margin: 0;
}

/* ==========================================================================
   Links
   ========================================================================== */

/**
 * Address `outline` inconsistency between Chrome and other browsers.
 */

a:focus {
    outline: thin dotted;
}

/**
 * Improve readability when focused and also mouse hovered in all browsers.
 */

a:active,
a:hover {
    outline: 0;
}

/* ==========================================================================
   Typography
   ========================================================================== */

/**
 * Address font sizes and margins set differently in IE 6/7.
 * Address font sizes within `section` and `article` in Firefox 4+, Safari 5,
 * and Chrome.
 */

h1 {
    font-size: 2em;
    margin: 0.67em 0;
}

h2 {
    font-size: 1.5em;
    margin: 0.83em 0;
}

h3 {
    font-size: 1.17em;
    margin: 1em 0;
}

h4 {
    font-size: 1em;
    margin: 1.33em 0;
}

h5 {
    font-size: 0.83em;
    margin: 1.67em 0;
}

h6 {
    font-size: 0.67em;
    margin: 2.33em 0;
}

/**
 * Address styling not present in IE 7/8/9, Safari 5, and Chrome.
 */

abbr[title] {
    border-bottom: 1px dotted;
}

/**
 * Address style set to `bolder` in Firefox 3+, Safari 4/5, and Chrome.
 */

b,
strong {
    font-weight: bold;
}

blockquote {
    margin: 1em 40px;
}

/**
 * Address styling not present in Safari 5 and Chrome.
 */

dfn {
    font-style: italic;
}

/**
 * Address differences between Firefox and other browsers.
 * Known issue: no IE 6/7 normalization.
 */

hr {
    -moz-box-sizing: content-box;
    box-sizing: content-box;
    height: 0;
}

/**
 * Address styling not present in IE 6/7/8/9.
 */

mark {
    background: #ff0;
    color: #000;
}

/**
 * Address margins set differently in IE 6/7.
 */

p,
pre {
    margin: 1em 0;
}

/**
 * Correct font family set oddly in IE 6, Safari 4/5, and Chrome.
 */

code,
kbd,
pre,
samp {
    font-family: monospace, serif;
    _font-family: 'courier new', monospace;
    font-size: 1em;
}

/**
 * Improve readability of pre-formatted text in all browsers.
 */

pre {
    white-space: pre;
    white-space: pre-wrap;
    word-wrap: break-word;
}

/**
 * Address CSS quotes not supported in IE 6/7.
 */

q {
    quotes: none;
}

/**
 * Address `quotes` property not supported in Safari 4.
 */

q:before,
q:after {
    content: '';
    content: none;
}

/**
 * Address inconsistent and variable font size in all browsers.
 */

small {
    font-size: 80%;
}

/**
 * Prevent `sub` and `sup` affecting `line-height` in all browsers.
 */

sub,
sup {
    font-size: 75%;
    line-height: 0;
    position: relative;
    vertical-align: baseline;
}

sup {
    top: -0.5em;
}

sub {
    bottom: -0.25em;
}

/* ==========================================================================
   Lists
   ========================================================================== */

/**
 * Address margins set differently in IE 6/7.
 */

dl,
menu,
ol,
ul {
    margin: 1em 0;
}

dd {
    margin: 0 0 0 40px;
}

/**
 * Address paddings set differently in IE 6/7.
 */

menu,
ol,
ul {
    padding: 0 0 0 40px;
}

/**
 * Correct list images handled incorrectly in IE 7.
 */

nav ul,
nav ol {
    list-style: none;
    list-style-image: none;
}

/* ==========================================================================
   Embedded content
   ========================================================================== */

/**
 * 1. Remove border when inside `a` element in IE 6/7/8/9 and Firefox 3.
 * 2. Improve image quality when scaled in IE 7.
 */

img {
    border: 0; /* 1 */
    -ms-interpolation-mode: bicubic; /* 2 */
}

/**
 * Correct overflow displayed oddly in IE 9.
 */

svg:not(:root) {
    overflow: hidden;
}

/* ==========================================================================
   Figures
   ========================================================================== */

/**
 * Address margin not present in IE 6/7/8/9, Safari 5, and Opera 11.
 */

figure {
    margin: 0;
}

/* ==========================================================================
   Forms
   ========================================================================== */

/**
 * Correct margin displayed oddly in IE 6/7.
 */

form {
    margin: 0;
}

/**
 * Define consistent border, margin, and padding.
 */

fieldset {
    border: 1px solid #c0c0c0;
    margin: 0 2px;
    padding: 0.35em 0.625em 0.75em;
}

/**
 * 1. Correct color not being inherited in IE 6/7/8/9.
 * 2. Correct text not wrapping in Firefox 3.
 * 3. Correct alignment displayed oddly in IE 6/7.
 */

legend {
    border: 0; /* 1 */
    padding: 0;
    white-space: normal; /* 2 */
    *margin-left: -7px; /* 3 */
}

/**
 * 1. Correct font size not being inherited in all browsers.
 * 2. Address margins set differently in IE 6/7, Firefox 3+, Safari 5,
 *    and Chrome.
 * 3. Improve appearance and consistency in all browsers.
 */

button,
input,
select,
textarea {
    font-size: 100%; /* 1 */
    margin: 0; /* 2 */
    vertical-align: baseline; /* 3 */
    *vertical-align: middle; /* 3 */
}

/**
 * Address Firefox 3+ setting `line-height` on `input` using `!important` in
 * the UA stylesheet.
 */

button,
input {
    line-height: normal;
}

/**
 * Address inconsistent `text-transform` inheritance for `button` and `select`.
 * All other form control elements do not inherit `text-transform` values.
 * Correct `button` style inheritance in Chrome, Safari 5+, and IE 6+.
 * Correct `select` style inheritance in Firefox 4+ and Opera.
 */

button,
select {
    text-transform: none;
}

/**
 * 1. Avoid the WebKit bug in Android 4.0.* where (2) destroys native `audio`
 *    and `video` controls.
 * 2. Correct inability to style clickable `input` types in iOS.
 * 3. Improve usability and consistency of cursor style between image-type
 *    `input` and others.
 * 4. Remove inner spacing in IE 7 without affecting normal text inputs.
 *    Known issue: inner spacing remains in IE 6.
 */

button,
html input[type="button"], /* 1 */
input[type="reset"],
input[type="submit"] {
    -webkit-appearance: button; /* 2 */
    cursor: pointer; /* 3 */
    *overflow: visible;  /* 4 */
}

/**
 * Re-set default cursor for disabled elements.
 */

button[disabled],
html input[disabled] {
    cursor: default;
}

/**
 * 1. Address box sizing set to content-box in IE 8/9.
 * 2. Remove excess padding in IE 8/9.
 * 3. Remove excess padding in IE 7.
 *    Known issue: excess padding remains in IE 6.
 */

input[type="checkbox"],
input[type="radio"] {
    box-sizing: border-box; /* 1 */
    padding: 0; /* 2 */
    *height: 13px; /* 3 */
    *width: 13px; /* 3 */
}

/**
 * 1. Address `appearance` set to `searchfield` in Safari 5 and Chrome.
 * 2. Address `box-sizing` set to `border-box` in Safari 5 and Chrome
 *    (include `-moz` to future-proof).
 */

input[type="search"] {
    -webkit-appearance: textfield; /* 1 */
    -moz-box-sizing: content-box;
    -webkit-box-sizing: content-box; /* 2 */
    box-sizing: content-box;
}

/**
 * Remove inner padding and search cancel button in Safari 5 and Chrome
 * on OS X.
 */

input[type="search"]::-webkit-search-cancel-button,
input[type="search"]::-webkit-search-decoration {
    -webkit-appearance: none;
}

/**
 * Remove inner padding and border in Firefox 3+.
 */

button::-moz-focus-inner,
input::-moz-focus-inner {
    border: 0;
    padding: 0;
}

/**
 * 1. Remove default vertical scrollbar in IE 6/7/8/9.
 * 2. Improve readability and alignment in all browsers.
 */

textarea {
    overflow: auto; /* 1 */
    vertical-align: top; /* 2 */
}

/* ==========================================================================
   Tables
   ========================================================================== */

/**
 * Remove most spacing between table cells.
 */

table {
    border-collapse: collapse;
    border-spacing: 0;
}
</%def>

<%def name="post()">
/* ==========================================================================
   EXAMPLE Media Queries for Responsive Design.
   These examples override the primary ('mobile first') styles.
   Modify as content requires.
   ========================================================================== */

@media only screen and (min-width: 35em) {
    /* Style adjustments for viewports that meet the condition */
}

@media print,
       (-o-min-device-pixel-ratio: 5/4),
       (-webkit-min-device-pixel-ratio: 1.25),
       (min-resolution: 120dpi) {
    /* Style adjustments for high resolution devices */
}

/* ==========================================================================
   Print styles.
   Inlined to avoid required HTTP connection: h5bp.com/r
   ========================================================================== */

@media print {
    * {
        background: transparent !important;
        color: #000 !important; /* Black prints faster: h5bp.com/s */
        box-shadow: none !important;
        text-shadow: none !important;
    }

    a,
    a:visited {
        text-decoration: underline;
    }

    a[href]:after {
        content: " (" attr(href) ")";
    }

    abbr[title]:after {
        content: " (" attr(title) ")";
    }

    /*
     * Don't show links for images, or javascript/internal links
     */

    .ir a:after,
    a[href^="javascript:"]:after,
    a[href^="#"]:after {
        content: "";
    }

    pre,
    blockquote {
        border: 1px solid #999;
        page-break-inside: avoid;
    }

    thead {
        display: table-header-group; /* h5bp.com/t */
    }

    tr,
    img {
        page-break-inside: avoid;
    }

    img {
        max-width: 100% !important;
    }

    @page {
        margin: 0.5cm;
    }

    p,
    h2,
    h3 {
        orphans: 3;
        widows: 3;
    }

    h2,
    h3 {
        page-break-after: avoid;
    }
}
</%def>
