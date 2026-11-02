const fs = require("fs");
const path = require("path");

// Static hosts (GitHub Pages, OSS, ...) only serve the 404 document built for
// the default locale, so /en/<missing-page> renders the Chinese 404 page.
// Redirect such requests to the English 404 document that Docusaurus does
// build (build/en/404.html), before the Chinese page is painted.
const REDIRECT_MARKER = "data-localized-404-redirect";

/**
 * @param {import('@docusaurus/types').LoadContext} context
 */
function localized404RedirectPlugin(context) {
  function buildRedirectScript(baseUrl, localeSegments) {
    const prefixes = localeSegments.map((segment) => `${baseUrl}${segment}/`);

    return [
      "<script>",
      `(function(){var p=window.location.pathname;var l=${JSON.stringify(prefixes)};`,
      "for(var i=0;i<l.length;i++){var x=l[i];",
      "if(p===x.slice(0,-1)||p.indexOf(x)===0){",
      "window.location.replace(x+'404.html');return;}}}());",
      "</script>",
    ].join("");
  }

  return {
    name: "localized-404-redirect-plugin",

    async postBuild({ outDir, baseUrl }) {
      const { currentLocale, defaultLocale, locales } = context.i18n;
      // This hook runs once per locale build, so the localized 404.html files
      // may not exist yet; the deployed build always includes every locale.
      const localeSegments = locales.filter(
        (locale) => locale !== defaultLocale,
      );
      if (currentLocale !== defaultLocale || localeSegments.length === 0) {
        return;
      }

      // Only the default locale's 404.html is written at the site root.
      const default404Path = path.join(outDir, "404.html");
      if (!fs.existsSync(default404Path)) {
        return;
      }

      const html = fs.readFileSync(default404Path, "utf8");
      if (html.includes(REDIRECT_MARKER)) {
        return;
      }

      const script = buildRedirectScript(baseUrl, localeSegments).replace(
        "<script>",
        `<script ${REDIRECT_MARKER}>`,
      );
      const headMatch = html.match(/<head[^>]*>/i);
      if (!headMatch) {
        return;
      }

      const insertAt = headMatch.index + headMatch[0].length;
      const updatedHtml =
        html.slice(0, insertAt) + script + html.slice(insertAt);
      fs.writeFileSync(default404Path, updatedHtml);
    },
  };
}

module.exports = localized404RedirectPlugin;
