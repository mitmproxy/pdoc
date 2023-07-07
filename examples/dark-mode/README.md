# 🌒 pdoc dark mode

[**Demo**](https://pdoc.dev/docs/dark-mode/demo.html)

This is an example showing how to style pdoc in dark mode using custom stylesheets.
pdoc defines all colors as CSS variables, so we only need to adjust pdoc's color scheme (`theme.css`)
and pygments' syntax highlighting theme (`syntax-highlighting.css`).

This theme automatically switches between light and dark mode based on the user's system preferences.

Run `cd examples/dark-mode && pdoc -t . pdoc` to see it in action!
