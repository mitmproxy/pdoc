/**
 * This script is invoked by pdoc to precompile the search index.
 * Precompiling the search index increases file size, but skips the CPU-heavy index building in the browser.
 */
let elasticlunr = require("./resources/elasticlunr.min");

let fs = require("fs");
let docs = JSON.parse(fs.readFileSync(0, "utf-8"));

/* mirrored in search.js.jinja2  (part 1) */
elasticlunr.tokenizer.setSeperator(/[\s\-.;&_'"=,()]+|<[^>]*>/);

/* mirrored in search.js.jinja2  (part 2) */
searchIndex = elasticlunr(function () {
    this.pipeline.remove(elasticlunr.stemmer);
    this.pipeline.remove(elasticlunr.stopWordFilter);
    this.addField("qualname");
    this.addField("fullname");
    this.addField("annotation");
    this.addField("default_value");
    this.addField("signature");
    this.addField("bases");
    this.addField("doc");
    this.setRef("fullname");
});
for (let doc of docs) {
    searchIndex.addDoc(doc);
}

process.stdout.write(JSON.stringify(searchIndex.toJSON()));
