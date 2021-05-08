/**
 * This script is invoked by pdoc to precompile the search index.
 * Precompiling the search index increases file size, but skips the CPU-heavy index building in the browser.
 */
let elasticlunr = require('./elasticlunr.min');

let fs = require('fs');
let docs = JSON.parse(fs.readFileSync(0, 'utf-8'));

/* mirrored in module.html.jinja2  (part 1) */
elasticlunr.tokenizer.setSeperator(/[\s\-.;&]+|<[^>]*>/);

/* mirrored in module.html.jinja2  (part 2) */
searchIndex = elasticlunr(function () {
    this.addField('qualname');
    this.addField('fullname');
    this.addField('doc');
    this.setRef('fullname');
});
for (let doc of docs) {
    searchIndex.addDoc(doc);
}

process.stdout.write(JSON.stringify(searchIndex.toJSON()));
