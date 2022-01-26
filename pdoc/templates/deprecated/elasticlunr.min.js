{%- set oldname = self._TemplateReference__context.name -%}
{{- warn(oldname + " has moved to resources/" + oldname + ". Please adjust your custom pdoc template.") -}}
{%- include "resources/" + oldname -%}
